"""The only way this module talks to AWS: `aws s3api list-objects-v2`, read-only.

argv is built from a fixed allow-list of options and run with shell=False. There is no
generic "run aws" entry point on purpose; downloads go through s5cmd, not here.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Iterator, List, NamedTuple, Optional, Tuple

from s3logs import validate
from s3logs.validate import Refused

_TIMEOUT_S = 600
_MAX_PAGES = 10000
_PAGE_SIZE = "1000"
_ALLOWED_OPTIONS = frozenset(
    ["--bucket", "--prefix", "--profile", "--region", "--output", "--starting-token", "--page-size"])
# Same shapes config.py enforces; checked again here so this module is safe on its own.
_PROFILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}")
_REGION_RE = re.compile(r"[a-z]{2}(?:-[a-z]+)+-[0-9]")
_TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_.-]{1,4096}")
_EXPIRED_MARKERS = ("ExpiredToken", "Token has expired", "SSO session")
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


def _check_argv(argv: List[str]) -> None:
    """Refuse any argv that is not `aws s3api list-objects-v2` plus allow-listed options."""
    if argv[:3] != ["aws", "s3api", "list-objects-v2"]:
        raise Refused("only aws s3api list-objects-v2 is allowed")
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


def _run(argv: List[str], profile: Optional[str]) -> str:
    exe = shutil.which("aws")
    if not exe:
        raise AwsError("the aws CLI was not found on PATH", "install AWS CLI v2 and re-run")
    env = dict(os.environ)
    env["AWS_PAGER"] = ""            # never open a pager
    env["AWS_CLI_AUTO_PROMPT"] = "off"
    try:
        r = subprocess.run([exe] + argv[1:], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, errors="replace", timeout=_TIMEOUT_S, env=env, shell=False)
    except subprocess.TimeoutExpired:
        raise AwsError("aws timed out after %d seconds" % _TIMEOUT_S, "re-run with a narrower day range")
    except OSError as e:
        raise AwsError("could not run aws: %s" % (e.strerror or e))
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
