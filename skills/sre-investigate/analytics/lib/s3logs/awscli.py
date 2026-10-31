"""The only ways this module talks to AWS, both through the `aws` CLI with shell=False:

* `aws s3api list-objects-v2`, read-only listing, and
* `aws configure export-credentials [--profile P] --format process`, which turns any
  profile (SSO included, which s5cmd cannot load itself) into short-lived keys for s5cmd.

argv is built from a fixed allow-list of shapes (`_check_argv` refuses everything else).
There is no generic "run aws" entry point on purpose; downloads go through s5cmd, not here.
The exported keys are secrets: they are returned to the caller and never put in an error,
a hint or a log line (stdout of the export command is never quoted).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Dict, Iterator, List, NamedTuple, Optional, Tuple

from s3logs import validate
from s3logs.validate import Refused

_TIMEOUT_S = 600
_EXPORT_TIMEOUT_S = 60
_MAX_PAGES = 10000
_PAGE_SIZE = "1000"
_ALLOWED_OPTIONS = frozenset(
    ["--bucket", "--prefix", "--profile", "--region", "--output", "--starting-token", "--page-size"])
# Same shapes config.py enforces; checked again here so this module is safe on its own.
_PROFILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}")
_REGION_RE = re.compile(r"[a-z]{2}(?:-[a-z]+)+-[0-9]")
_TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_.-]{1,4096}")
_EXPIRED_MARKERS = ("ExpiredToken", "Token has expired", "SSO session", "SSO Token")
_CRED_VALUE_RE = re.compile(r"[\x21-\x7e]{1,4096}")
_EXPORT_HINT = "aws configure export-credentials needs AWS CLI v2.9 or newer and a working profile"
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class Entry(NamedTuple):
    key: str
    size: int
    etag: str


class AwsError(Exception):
    """aws exited non-zero (or could not run). `hint` is a command for the user, if any."""

    def __init__(self, msg: str, hint: Optional[str] = None):
        super().__init__(msg)
        self.msg = msg
        self.hint = hint

    def __str__(self) -> str:
        return self.msg


def _check_export_argv(rest: List[str]) -> None:
    """`[--profile P] --format process` and nothing else, in that order."""
    if rest == ["--format", "process"]:
        return
    if len(rest) == 4 and rest[0] == "--profile" and rest[2:] == ["--format", "process"] \
            and _PROFILE_RE.fullmatch(rest[1]):
        return
    raise Refused("only aws configure export-credentials [--profile P] --format process is allowed")


def _check_argv(argv: List[str]) -> None:
    """Refuse any argv that is not `aws s3api list-objects-v2` plus allow-listed options, or
    exactly `aws configure export-credentials [--profile P] --format process`."""
    if argv[:3] == ["aws", "configure", "export-credentials"]:
        _check_export_argv(argv[3:])
        return
    if argv[:3] != ["aws", "s3api", "list-objects-v2"]:
        raise Refused("only aws s3api list-objects-v2 and aws configure export-credentials are allowed")
    rest = argv[3:]
    if len(rest) % 2:
        raise Refused("unexpected aws argument")
    seen = set()
    for i in range(0, len(rest), 2):
        name, value = rest[i], rest[i + 1]
        if name not in _ALLOWED_OPTIONS or name in seen:
            raise Refused("aws option %s is not allowed" % name)
        seen.add(name)
        if value.startswith("-"):
            raise Refused("aws option value may not start with '-'")
    if not {"--bucket", "--prefix", "--output", "--page-size"} <= seen:
        raise Refused("aws argv is incomplete")
    if rest[rest.index("--output") + 1] != "json":
        raise Refused("only --output json is allowed")


def _build_argv(bucket: str, prefix: str, profile: Optional[str], region: Optional[str],
                token: Optional[str]) -> List[str]:
    validate.bucket(bucket)
    validate.safe_key(prefix)
    if profile is not None and not _PROFILE_RE.fullmatch(profile):
        raise Refused("invalid AWS profile name")
    if region is not None and not _REGION_RE.fullmatch(region):
        raise Refused("invalid AWS region")
    if token is not None and not _TOKEN_RE.fullmatch(token):
        raise Refused("invalid pagination token")
    argv = ["aws", "s3api", "list-objects-v2", "--bucket", bucket, "--prefix", prefix]
    if profile:
        argv += ["--profile", profile]
    if region:
        argv += ["--region", region]
    argv += ["--output", "json", "--page-size", _PAGE_SIZE]
    if token:
        argv += ["--starting-token", token]
    _check_argv(argv)
    return argv


def _clean(text: str, limit: int = 400) -> str:
    text = _CONTROL_RE.sub(" ", text).strip()
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def _hint_for(stderr: str, profile: Optional[str]) -> Optional[str]:
    if any(marker in stderr for marker in _EXPIRED_MARKERS):
        return "! aws sso login --profile %s" % profile if profile else "! aws sso login"
    if "AccessDenied" in stderr:
        return "check that the role may s3:ListBucket on this bucket and prefix"
    return None


def _exec(argv: List[str], timeout: int, timeout_hint: str,
          region: Optional[str] = None) -> "subprocess.CompletedProcess[str]":
    """Run an already-checked aws argv: shell=False, no stdin, no pager, no prompt."""
    exe = shutil.which("aws")
    if not exe:
        raise AwsError("the aws CLI was not found on PATH", "install AWS CLI v2 and re-run")
    env = dict(os.environ)
    env["AWS_PAGER"] = ""            # never open a pager
    env["AWS_CLI_AUTO_PROMPT"] = "off"
    if region:
        env["AWS_REGION"] = region
    try:
        return subprocess.run([exe] + argv[1:], stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, errors="replace", timeout=timeout, env=env, shell=False)
    except subprocess.TimeoutExpired:
        raise AwsError("aws timed out after %d seconds" % timeout, timeout_hint)
    except OSError as e:
        raise AwsError("could not run aws: %s" % (e.strerror or e))


def _run(argv: List[str], profile: Optional[str]) -> str:
    r = _exec(argv, _TIMEOUT_S, "re-run with a narrower day range")
    if r.returncode != 0:
        raise AwsError("aws exited %d: %s" % (r.returncode, _clean(r.stderr) or "no error text"),
                       _hint_for(r.stderr, profile))
    return r.stdout


def _parse_page(text: str) -> Tuple[List[Entry], Optional[str]]:
    """One CLI response -> entries and the next token (if any). Empty output = no objects."""
    if not text.strip():
        return [], None
    try:
        doc = json.loads(text)
    except ValueError:
        raise AwsError("aws printed output that is not JSON")
    if not isinstance(doc, dict):
        raise AwsError("aws printed an unexpected listing shape")
    entries = []
    for obj in doc.get("Contents") or []:
        key, size, etag = (obj.get("Key"), obj.get("Size"), obj.get("ETag")) if isinstance(obj, dict) \
            else (None, None, None)
        if not isinstance(key, str) or isinstance(size, bool) or not isinstance(size, int) \
                or not isinstance(etag, str):
            raise AwsError("aws printed an unexpected listing shape")
        entries.append(Entry(key, size, etag.strip('"')))
    token = doc.get("NextToken")
    return entries, token if isinstance(token, str) and token else None


def list_objects(bucket: str, prefix: str, profile: Optional[str], region: Optional[str]) -> Iterator[Entry]:
    """Yield every object under bucket/prefix. Raises Refused for bad input, AwsError for aws failures."""
    token = None
    for _ in range(_MAX_PAGES):
        argv = _build_argv(bucket, prefix, profile, region, token)
        entries, token = _parse_page(_run(argv, profile))
        for e in entries:
            yield e
        if not token:
            return
    raise AwsError("listing did not finish after %d pages" % _MAX_PAGES)


def export_credentials(profile: Optional[str], region: Optional[str]) -> Dict[str, str]:
    """Short-lived keys for `profile` as AWS_* variables, via `aws configure export-credentials`.

    s5cmd cannot load SSO profiles, the aws CLI can. The result is a secret: callers put it in
    a child environment only. Any failure is an AwsError whose text never includes stdout
    (which holds the keys); stderr is cleaned like the other helpers."""
    if profile is not None and not _PROFILE_RE.fullmatch(profile):
        raise Refused("invalid AWS profile name")
    if region is not None and not _REGION_RE.fullmatch(region):
        raise Refused("invalid AWS region")
    argv = ["aws", "configure", "export-credentials"]
    if profile:
        argv += ["--profile", profile]
    argv += ["--format", "process"]
    _check_argv(argv)
    r = _exec(argv, _EXPORT_TIMEOUT_S, _EXPORT_HINT, region)
    if r.returncode != 0:
        hint = _hint_for(r.stderr, profile)
        if hint is None or hint.startswith("check that"):
            hint = _EXPORT_HINT
        raise AwsError("aws exited %d: %s" % (r.returncode, _clean(r.stderr) or "no error text"), hint)
    try:
        doc = json.loads(r.stdout)
    except ValueError:
        doc = None
    out = {}  # type: Dict[str, str]
    if isinstance(doc, dict) and doc.get("Version") == 1 and not isinstance(doc.get("Version"), bool):
        for src, dst, required in (("AccessKeyId", "AWS_ACCESS_KEY_ID", True),
                                   ("SecretAccessKey", "AWS_SECRET_ACCESS_KEY", True),
                                   ("SessionToken", "AWS_SESSION_TOKEN", False)):
            value = doc.get(src)
            if value is None and not required:
                continue
            if not isinstance(value, str) or not _CRED_VALUE_RE.fullmatch(value):
                out = {}
                break
            out[dst] = value
    if "AWS_ACCESS_KEY_ID" not in out or "AWS_SECRET_ACCESS_KEY" not in out:
        raise AwsError("aws configure export-credentials printed no usable credentials", _EXPORT_HINT)
    return out
