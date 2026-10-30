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
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from s3logs import validate
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


def _scrub(text: str, batchdir: str) -> str:
    """One short printable-ASCII line: staging and home paths shortened, control chars gone.
    s5cmd prefixes its real errors with ERROR; its warnings (instance-metadata noise) are left
    out when there is at least one."""
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
    if "AccessDenied" in stderr:
        return "check that the role may s3:GetObject on this bucket and prefix"
    return None


def _child_env(region: Optional[str]) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in _ENV_DROP and not k.startswith(_ENV_DROP_PREFIXES)}
    env["AWS_PAGER"] = ""
    if region:
        env["AWS_REGION"] = region
    return env


def run(run_file: Path, profile: Optional[str], region: Optional[str], batchdir: str) -> None:
    """Run `s5cmd [--profile P] --log error run <run_file>`. Raises Refused or AwsError."""
    _check_batchdir(batchdir)
    if profile is not None and not _PROFILE_RE.fullmatch(profile):
        raise Refused("invalid AWS profile name")
    if region is not None and not _REGION_RE.fullmatch(region):
        raise Refused("invalid AWS region")
    text = _read_run_file(Path(run_file), batchdir)
    # The bucket is whatever the file names; it must be one safe bucket for every line.
    m = re.match(r"cp -n --raw s3://([^/ ]+)/", text)
    if not m:
        raise Refused("run file line 1 is not a plain `cp -n --raw`")
    validate_run_file(text, m.group(1), batchdir)
    exe = shutil.which("s5cmd")
    if not exe:
        raise Refused("s5cmd was not found on PATH (run logs-status)")
    argv = [exe]
    if profile:
        argv += ["--profile", profile]
    argv += ["--log", "error", "run", os.path.abspath(str(run_file))]
    try:
        r = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           errors="replace", timeout=_TIMEOUT_S, env=_child_env(region), shell=False)
    except subprocess.TimeoutExpired:
        raise AwsError("s5cmd timed out after %d seconds" % _TIMEOUT_S, "re-run with a narrower slice")
    except OSError as e:
        raise AwsError("could not run s5cmd: %s" % (e.strerror or "error"))
    if r.returncode != 0:
        both = (r.stderr or "") + "\n" + (r.stdout or "")
        raise AwsError("s5cmd exited %d: %s" % (r.returncode, _scrub(both, batchdir) or "no error text"),
                       _hint(both, profile))
