from __future__ import annotations

import os
import stat

import pytest

from s3logs import paths
from s3logs.validate import Refused


def mode(p):
    return stat.S_IMODE(os.stat(p).st_mode)


def test_state_root(home):
    assert paths.state_root() == home / ".local/share/culiops/sre-investigate"
    assert paths.config_path() == home / ".config/culiops/sre-investigate/logs.env"
    assert paths.marker_path() == home / ".config/culiops/sre-investigate/over-cap.allow"


def test_ensure_private_dirs_modes_and_idempotent(home):
    old = os.umask(0o022)
    try:
        paths.ensure_private_dirs()
        paths.ensure_private_dirs()
    finally:
        os.umask(old)
    root = paths.state_root()
    assert mode(root) == 0o700
    for sub in ["budgets", "manifests", "data"]:
        assert mode(root / sub) == 0o700
    assert mode(root / "staging") == 0o300


def test_ensure_private_dirs_refuses_symlink(home, tmp_path):
    root = paths.state_root()
    root.parent.mkdir(parents=True)
    target = tmp_path / "elsewhere"
    target.mkdir()
    root.symlink_to(target)
    with pytest.raises(Refused):
        paths.ensure_private_dirs()
