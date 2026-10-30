"""Download budget: per-fetch, per-run and rolling 24 h caps, a ledger, and the override marker.

Money depends on this module, so it fails closed:
- a ledger line that is not exactly what `charge` writes raises Refused naming the file;
- an override needs both `force` and a marker file the USER created (regular file, owned
  by the current user, younger than the configured TTL). Code here never creates, touches
  or deletes the marker;
- caps come from the Config object (logs.env or defaults), never from the environment.

Units: caps and `Headroom` values are MiB (1024*1024 bytes), `planned_bytes` and ledger
`bytes` are integer bytes. The ledger is JSON lines:
    {"ts": "<ISO-8601 UTC, Z>", "run": "<run-id>", "dataset": "<name>", "bytes": <int >= 0>}
appended under an exclusive flock on budgets/.lock.
"""
from __future__ import annotations

import datetime
import errno
import fcntl
import json
import os
import re
import stat
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

from s3logs import paths
from s3logs.config import Config
from s3logs.validate import Refused, dataset_name, run_id as validate_run_id

MIB = 1024 * 1024
_UTC = datetime.timezone.utc
_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z")
_OVERRIDE_REFUSAL = ("override needs the user's marker file "
                     "(created by the user, not the agent) and --force")


class Headroom(NamedTuple):
    """fetch_mb: the largest single fetch allowed right now without an override, i.e.
    min(per-fetch cap, room left under the run cap, room left under the 24 h cap), >= 0.
    run_mb_used: everything charged to this run (0.0 when run_id is None).
    day_mb_used: everything charged in the last 24 h across all runs."""
    fetch_mb: float
    run_mb_used: float
    day_mb_used: float


class Verdict(NamedTuple):
    ok: bool
    over: List[str]
    override_used: bool


def _ledger_path() -> Path:
    return paths.state_root() / "budgets" / "ledger.jsonl"


def _lock_path() -> Path:
    return paths.state_root() / "budgets" / ".lock"


def _utc(now: datetime.datetime) -> datetime.datetime:
    if not isinstance(now, datetime.datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    return now.astimezone(_UTC)


def _parse_line(line: str) -> Tuple[datetime.datetime, str, int]:
    rec = json.loads(line)  # ValueError on bad JSON; caller maps to Refused
    if not isinstance(rec, dict):
        raise ValueError("not a JSON object")
    for key in ("ts", "run", "dataset", "bytes"):
        if key not in rec:
            raise ValueError("missing key %r" % key)
    ts, run, ds, n = rec["ts"], rec["run"], rec["dataset"], rec["bytes"]
    if not isinstance(ts, str) or not _TS_RE.fullmatch(ts):
        raise ValueError("bad ts")
    if not isinstance(run, str) or not isinstance(ds, str):
        raise ValueError("run and dataset must be strings")
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("bytes must be an integer >= 0")
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in ts else "%Y-%m-%dT%H:%M:%SZ"
    when = datetime.datetime.strptime(ts, fmt).replace(tzinfo=_UTC)
    return when, run, n


def _read_ledger() -> List[Tuple[datetime.datetime, str, int]]:
    """All ledger entries; Refused (naming the file) on anything unexpected."""
    path = _ledger_path()
    lock_fd = None
    try:
        try:
            # Shared lock so a concurrent charge cannot be seen half-written. If the lock
            # file does not exist yet, nothing has ever been charged.
            lock_fd = os.open(str(_lock_path()), os.O_RDONLY | os.O_NOFOLLOW)
            fcntl.flock(lock_fd, fcntl.LOCK_SH)
        except OSError as e:
            if e.errno not in (errno.ENOENT, errno.ENOTDIR):
                raise Refused("cannot lock %s: %s" % (_lock_path(), e.strerror))
        try:
            fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
        except OSError as e:
            if e.errno in (errno.ENOENT, errno.ENOTDIR):
                return []
            raise Refused("cannot read budget ledger %s: %s" % (path, e.strerror))
        try:
            with os.fdopen(fd, "rb") as f:
                raw = f.read()
        except OSError as e:
            raise Refused("cannot read budget ledger %s: %s" % (path, e.strerror))
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
    if not raw:
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("budget ledger %s is corrupt (not UTF-8); fix or remove it" % (path,))
    if not text.endswith("\n"):
        raise Refused("budget ledger %s is corrupt (truncated last line); fix or remove it" % (path,))
    entries = []
    for i, line in enumerate(text[:-1].split("\n"), 1):
        try:
            entries.append(_parse_line(line))
        except (ValueError, TypeError, RecursionError) as e:
            raise Refused("budget ledger %s is corrupt at line %d (%s); fix or remove it"
                          % (path, i, e))
    return entries


def _usage(run: Optional[str], now: datetime.datetime) -> Tuple[int, int]:
    """(run_bytes, day_bytes). Day window is (now-24h, +inf): entries stamped in the
    future are counted, not ignored."""
    entries = _read_ledger()
    cutoff = now - datetime.timedelta(hours=24)
    run_b = day_b = 0
    for when, r, n in entries:
        if run is not None and r == run:
            run_b += n
        if when > cutoff:
            day_b += n
    return run_b, day_b


def headroom(cfg: Config, run_id: Optional[str], now: datetime.datetime) -> Headroom:
    now = _utc(now)
    run_b, day_b = _usage(run_id, now)
    room = [cfg.max_mb * MIB, cfg.day_max_mb * MIB - day_b]
    if run_id is not None:
        room.append(cfg.run_max_mb * MIB - run_b)
    return Headroom(max(0, min(room)) / MIB, run_b / MIB, day_b / MIB)


def _marker_is_fresh(cfg: Config, now: datetime.datetime) -> bool:
    try:
        st = os.lstat(str(paths.marker_path()))
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        return False
    age = now.timestamp() - st.st_mtime
    return 0 <= age < cfg.marker_ttl_s


def check(cfg: Config, planned_bytes: int, run_id: Optional[str], force: bool,
          now: datetime.datetime) -> Verdict:
    """Compare a planned download with the caps.

    Raises Refused when `force` is set without a fresh user-created marker (even if no
    cap is exceeded: the user asked for an override that cannot be honoured), or when the
    ledger is unreadable. A dry run before a run id exists passes run_id=None: only the
    fetch and 24 h caps are checked and run usage is 0.
    """
    now = _utc(now)
    if isinstance(planned_bytes, bool) or not isinstance(planned_bytes, int) or planned_bytes < 0:
        raise ValueError("planned_bytes must be an integer >= 0")
    run_b, day_b = _usage(run_id, now)
    over = []
    if planned_bytes > cfg.max_mb * MIB:
        over.append("fetch")
    if run_id is not None and run_b + planned_bytes > cfg.run_max_mb * MIB:
        over.append("run")
    if day_b + planned_bytes > cfg.day_max_mb * MIB:
        over.append("24h")
    if force and not _marker_is_fresh(cfg, now):
        raise Refused(_OVERRIDE_REFUSAL)
    if not over:
        return Verdict(True, [], False)
    if force:
        return Verdict(True, over, True)
    return Verdict(False, over, False)


def charge(run_id: str, dataset: str, verified_bytes: int, now: datetime.datetime) -> None:
    """Append one ledger line under an exclusive lock. Call only for size-verified bytes."""
    now = _utc(now)
    validate_run_id(run_id)
    dataset_name(dataset)
    if (isinstance(verified_bytes, bool) or not isinstance(verified_bytes, int)
            or verified_bytes < 0):
        raise Refused("invalid byte count %r (expected an integer >= 0)" % (verified_bytes,))
    line = json.dumps({"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "run": run_id,
                       "dataset": dataset, "bytes": verified_bytes}, separators=(", ", ": "))
    data = (line + "\n").encode("utf-8")
    paths.ensure_private_dirs()
    try:
        lock_fd = os.open(str(_lock_path()), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError as e:
        raise Refused("cannot open %s: %s" % (_lock_path(), e.strerror))
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            fd = os.open(str(_ledger_path()),
                         os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        except OSError as e:
            raise Refused("cannot append to budget ledger %s: %s" % (_ledger_path(), e.strerror))
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        os.close(lock_fd)  # closing releases the flock
