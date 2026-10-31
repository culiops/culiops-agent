"""The only way this module downloads from S3: `s5cmd run <file>` over a validated run file.

A run file has one line per object, every line exactly
    cp -n --raw s3://<bucket>/<safe-key> <batchdir>/<NNNNNN>.gz
with a six-digit counter from 000001 and nothing else (no other command, option, wildcard,
second destination or trailing text). The file is built here, validated here, and validated
AGAIN from disk right before s5cmd reads it, so a key from a bucket that others can write to
(a space, `;`, `../`, a newline, a wildcard) can never reach s5cmd or a local path:
`validate.safe_key` accepts only A-Z a-z 0-9 . _ / = @ + : , - and no dot segments, and the
batch dir must be an absolute path of the same plain alphabet.

`cp -n` never overwrites and `--raw` turns off wildcard expansion. s5cmd runs with shell=False,
no stdin and an environment without endpoint overrides. A failure becomes `awscli.AwsError`
(exit 3 in the CLIs) with a scrubbed message and, for an expired or missing session, the
`! aws sso login` hint.

Credentials: s5cmd (aws-sdk-go v1) cannot load SSO profiles, so every `run` first asks the aws
CLI for short-lived keys (`awscli.export_credentials`, once per batch so a long fetch gets fresh
ones) and starts s5cmd WITHOUT `--profile`, with those keys in its environment and the profile and
shared-file variables removed. The keys are secrets: they live only in the child environment and
are stripped from any text taken from s5cmd's output before it reaches an error.
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from s3logs import awscli, validate
from s3logs.awscli import AwsError
from s3logs.validate import Refused

_TIMEOUT_S = 1800
_MAX_RUN_FILE_BYTES = 4 * 1024 * 1024
_MAX_MESSAGE = 400
_KEY_CHARS = r"[A-Za-z0-9._/=@+:,-]+"
_BATCHDIR_RE = re.compile(r"/[A-Za-z0-9._/-]+")
# Same shapes config.py enforces; checked again so this module is safe on its own.
_PROFILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}")
_REGION_RE = re.compile(r"[a-z]{2}(?:-[a-z]+)+-[0-9]")
_LOGIN_MARKERS = ("ExpiredToken", "Token has expired", "SSO session", "SSOProviderInvalidToken",
                  "NoCredentialProviders", "InvalidToken")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_ENV_DROP_PREFIXES = ("S5CMD_", "AWS_ENDPOINT_URL")
_ENV_DROP = ("S3_ENDPOINT_URL",)
# Dropped so s5cmd uses only the exported keys: a profile or shared file would be loaded (and fail)
# instead, and a stale session token would be paired with the fresh key.
_ENV_DROP_CREDS = ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE",
                   "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN",
                   "AWS_CREDENTIAL_EXPIRATION")


def _check_batchdir(batchdir: str) -> str:
    if (not isinstance(batchdir, str) or not _BATCHDIR_RE.fullmatch(batchdir)
            or os.path.normpath(batchdir) != batchdir):
        raise Refused("the staging path has characters that are unsafe for s5cmd or is not a plain "
                      "absolute path; it must use only A-Z a-z 0-9 . _ / - (check HOME)")
    return batchdir


def build_run_file(bucket: str, keys: List[str], batchdir: str) -> str:
    """The run-file text for `keys`, counters 000001.. in order. Refused for anything unsafe."""
    validate.bucket(bucket)
    _check_batchdir(batchdir)
    if not keys:
        raise Refused("nothing to download")
    lines = []
    for n, key in enumerate(keys, 1):
        validate.safe_key(key)
        lines.append("cp -n --raw s3://%s/%s %s/%06d.gz" % (bucket, key, batchdir, n))
    text = "\n".join(lines) + "\n"
    validate_run_file(text, bucket, batchdir)
    return text


def validate_run_file(text: str, bucket: str, batchdir: str) -> List[Tuple[str, str]]:
    """Check every line of `text`; return [(key, destination)] or raise Refused."""
    validate.bucket(bucket)
    _check_batchdir(batchdir)
    if not isinstance(text, str) or not text.endswith("\n"):
        raise Refused("run file must end with a newline")
    line_re = re.compile(r"cp -n --raw s3://%s/(?P<key>%s) %s/(?P<n>[0-9]{6})\.gz"
                         % (re.escape(bucket), _KEY_CHARS, re.escape(batchdir)))
    lines = text.split("\n")[:-1]
    if not lines:
        raise Refused("run file is empty")
    pairs = []  # type: List[Tuple[str, str]]
    for expected, line in enumerate(lines, 1):
        m = line_re.fullmatch(line)
        if not m:
            raise Refused("run file line %d is not a plain `cp -n --raw` of one safe key into the batch dir" % expected)
        validate.safe_key(m.group("key"))
        if int(m.group("n")) != expected:
            raise Refused("run file line %d has the wrong destination counter" % expected)
        pairs.append((m.group("key"), "%s/%s.gz" % (batchdir, m.group("n"))))
    return pairs


def _read_run_file(path: Path, batchdir: str) -> str:
    p = os.path.abspath(str(path))
    if os.path.dirname(p) != batchdir:
        raise Refused("the run file must sit inside the batch dir")
    try:
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        raise Refused("cannot read the run file: %s" % (e.strerror or "error"))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > _MAX_RUN_FILE_BYTES:
            raise Refused("the run file is not a regular file of a sane size")
        data = os.read(fd, _MAX_RUN_FILE_BYTES + 1)
    finally:
        os.close(fd)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("the run file is not UTF-8")


def _scrub(text: str, batchdir: str, secrets: Iterable[str] = ()) -> str:
    """One short printable-ASCII line: staging and home paths shortened, control chars gone,
    credential values replaced. s5cmd prefixes its real errors with ERROR; its warnings
    (instance-metadata noise) are left out when there is at least one."""
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = text.replace(secret, "<redacted>")
    errors = [ln for ln in text.splitlines() if ln.lstrip().startswith("ERROR")]
    if errors:
        text = " | ".join(errors[:3])
    if batchdir:
        text = text.replace(batchdir, "<staging>")
    home = str(Path.home())
    if len(home) > 1:
        text = text.replace(home, "~")
    text = _CONTROL_RE.sub(" ", text)
    text = "".join(c if ord(c) < 128 else "?" for c in text)
    text = " ".join(text.split())
    return text if len(text) <= _MAX_MESSAGE else text[:_MAX_MESSAGE] + "..."


def _hint(stderr: str, profile: Optional[str]) -> Optional[str]:
    if any(marker in stderr for marker in _LOGIN_MARKERS):
        return "! aws sso login --profile %s" % profile if profile else "! aws sso login"
    if "SharedCredsLoad" in stderr:
        return "run aws configure export-credentials%s to check the profile" % (
            " --profile %s" % profile if profile else "")
    if "AccessDenied" in stderr:
        return "check that the role may s3:GetObject on this bucket and prefix"
    return None


def _child_env(region: Optional[str], creds: Dict[str, str]) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in _ENV_DROP and k not in _ENV_DROP_CREDS and not k.startswith(_ENV_DROP_PREFIXES)}
    env.update(creds)
    env["AWS_PAGER"] = ""
    if region:
        env["AWS_REGION"] = region
    return env


def run(run_file: Path, profile: Optional[str], region: Optional[str], batchdir: str, bucket: str) -> None:
    """Run `s5cmd --log error run <run_file>` with keys exported from `profile` (see the module
    docstring). Raises Refused or AwsError.
    `bucket` is the configured bucket: every line of the file must name exactly that one."""
    validate.bucket(bucket)
    _check_batchdir(batchdir)
    if profile is not None and not _PROFILE_RE.fullmatch(profile):
        raise Refused("invalid AWS profile name")
    if region is not None and not _REGION_RE.fullmatch(region):
        raise Refused("invalid AWS region")
    text = _read_run_file(Path(run_file), batchdir)
    validate_run_file(text, bucket, batchdir)
    exe = shutil.which("s5cmd")
    if not exe:
        raise Refused("s5cmd was not found on PATH (run logs-status)")
    creds = awscli.export_credentials(profile, region)     # per call = per batch: always fresh
    argv = [exe, "--log", "error", "run", os.path.abspath(str(run_file))]
    try:
        r = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           errors="replace", timeout=_TIMEOUT_S, env=_child_env(region, creds), shell=False)
    except subprocess.TimeoutExpired:
        raise AwsError("s5cmd timed out after %d seconds" % _TIMEOUT_S, "re-run with a narrower slice") from None
    except OSError as e:
        raise AwsError("could not run s5cmd: %s" % (e.strerror or "error"))
    if r.returncode != 0:
        both = (r.stderr or "") + "\n" + (r.stdout or "")
        raise AwsError("s5cmd exited %d: %s" % (r.returncode, _scrub(both, batchdir, creds.values()) or "no error text"),
                       _hint(both, profile))
