"""Fixed locations. The only environment input is HOME (via Path.home())."""
from __future__ import annotations

import os
import re
import stat
import time
from pathlib import Path
from typing import List, Optional

from s3logs.validate import Refused

_CONFIG_SUB = Path(".config/culiops/sre-investigate")
_STATE_SUB = Path(".local/share/culiops/sre-investigate")


def config_dir() -> Path:
    return Path.home() / _CONFIG_SUB


def config_path() -> Path:
    return config_dir() / "logs.env"


def marker_path() -> Path:
    """The over-cap override marker. Only the user ever creates it."""
    return config_dir() / "over-cap.allow"


def state_root() -> Path:
    return Path.home() / _STATE_SUB


def _private_dir(p: Path, mode: int) -> None:
    if p.is_symlink():
        raise Refused("%s is a symlink; refusing to use it as private state" % (p,))
    if p.exists() and not p.is_dir():
        raise Refused("%s exists and is not a directory" % (p,))
    if not p.exists():
        try:
            p.mkdir(mode=mode)
        except FileExistsError:
            # Lost a creation race with another process; re-check what is there now.
            if p.is_symlink() or not p.is_dir():
                raise Refused("%s exists and is not a private directory" % (p,))
    os.chmod(str(p), mode)


def ensure_private_dirs() -> None:
    """Create the state tree: dirs 0700, staging/ 0300 (write+search, no listing)."""
    root = state_root()
    root.parent.mkdir(parents=True, exist_ok=True)
    _private_dir(root, 0o700)
    for name in ("budgets", "manifests", "data"):
        _private_dir(root / name, 0o700)
    _private_dir(root / "staging", 0o300)


def manifest_path(dataset: str, day_from: str, day_to: str) -> Path:
    """manifests/<dataset>/<from>_<to>.json under the state root (arguments pre-validated)."""
    return state_root() / "manifests" / dataset / ("%s_%s.json" % (day_from, day_to))


def private_subdir(parent: Path, name: str) -> Path:
    """Create parent/name (0700) if missing, refusing a symlink or non-directory there."""
    p = parent / name
    _private_dir(p, 0o700)
    return p


# ---- removal helpers (staging sweep, purge) --------------------------------------------------

STAGING_STALE_S = 24 * 60 * 60
# What logs-fetch itself creates under staging/: its batch dir and convert's private dirs.
_STAGING_NAME_RE = re.compile(r"(?:[0-9a-f]{32}|conv-[0-9a-f]{16})")


def _empty_dir(fd: int) -> None:
    """Delete everything inside the open directory `fd`, never following a symlink."""
    for name in os.listdir(fd):
        st = os.lstat(name, dir_fd=fd)
        if stat.S_ISDIR(st.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                os.fchmod(child, 0o700)
                _empty_dir(child)
            finally:
                os.close(child)
            os.rmdir(name, dir_fd=fd)
        else:
            os.unlink(name, dir_fd=fd)


def rmtree_force(path: Path) -> None:
    """Remove a directory tree even when parts of it are read-only (dataset dirs are 0555).

    Every directory is opened with O_NOFOLLOW and made writable before it is emptied, and
    entries are removed relative to the open directory, so a symlink anywhere in the tree is
    unlinked, never followed. A symlink at `path` itself is unlinked and its target left alone.
    """
    p = str(path)
    try:
        st = os.lstat(p)
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(st.st_mode):
        os.unlink(p)
        return
    fd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fchmod(fd, 0o700)
        _empty_dir(fd)
    finally:
        os.close(fd)
    os.rmdir(p)


def sweep_staging(max_age_s: int = STAGING_STALE_S, now: Optional[float] = None) -> List[str]:
    """Remove batch dirs in staging/ not touched for `max_age_s` (default one day).

    staging/ is mode 0300 (no listing), so it is made 0700 only for the listing and removals
    and put back to 0300 in `finally`. Only directories named like the ones logging creates are
    removed; symlinks and anything else are left alone. Returns the removed names.
    """
    root = state_root() / "staging"
    try:
        st = os.lstat(str(root))
    except FileNotFoundError:
        return []
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise Refused("%s is not a private directory" % (root,))
    cutoff = (time.time() if now is None else now) - max_age_s
    removed = []  # type: List[str]
    os.chmod(str(root), 0o700)
    try:
        for name in sorted(os.listdir(str(root))):
            if not _STAGING_NAME_RE.fullmatch(name):
                continue
            child = root / name
            cst = os.lstat(str(child))
            if not stat.S_ISDIR(cst.st_mode) or cst.st_mtime > cutoff:
                continue
            rmtree_force(child)
            removed.append(name)
    finally:
        os.chmod(str(root), 0o300)
    return removed
