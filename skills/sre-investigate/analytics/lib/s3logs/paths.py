"""Fixed locations. The only environment input is HOME (via Path.home())."""
from __future__ import annotations

import os
from pathlib import Path

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
