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


def test_rmtree_force_removes_readonly_trees_and_never_follows_symlinks(home, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("x")
    tree = tmp_path / "tree"
    (tree / "a" / "b").mkdir(parents=True)
    (tree / "a" / "b" / "f").write_text("x")
    os.chmod(str(tree / "a" / "b" / "f"), 0o444)
    (tree / "a" / "link").symlink_to(outside)
    (tree / "a" / "flink").symlink_to(outside / "keep.txt")
    os.chmod(str(tree / "a" / "b"), 0o555)
    os.chmod(str(tree / "a"), 0o500)
    paths.rmtree_force(tree)
    assert not tree.exists() and (outside / "keep.txt").exists()


def test_rmtree_force_on_a_symlink_unlinks_only_the_link(home, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("x")
    link = tmp_path / "link"
    link.symlink_to(outside)
    paths.rmtree_force(link)
    assert not link.is_symlink() and (outside / "keep.txt").exists()


def test_sweep_staging_only_old_batch_dirs(home):
    import time
    paths.ensure_private_dirs()
    root = paths.state_root() / "staging"
    old = time.time() - 2 * 86400
    for name in ("a" * 32, "conv-" + "b" * 16, "c" * 32, "not-a-batch"):
        (root / name).mkdir()
    for name in ("a" * 32, "conv-" + "b" * 16, "not-a-batch"):
        os.utime(str(root / name), (old, old))
    removed = paths.sweep_staging()
    assert sorted(removed) == sorted(["a" * 32, "conv-" + "b" * 16])
    assert mode(root) == 0o300
    os.chmod(str(root), 0o700)
    assert sorted(os.listdir(str(root))) == sorted(["c" * 32, "not-a-batch"])
    os.chmod(str(root), 0o300)


def test_sweep_staging_restores_mode_on_error(home, monkeypatch):
    paths.ensure_private_dirs()
    root = paths.state_root() / "staging"

    def boom(p):
        raise OSError("boom")

    monkeypatch.setattr(paths.os, "listdir", boom)
    with pytest.raises(OSError):
        paths.sweep_staging()
    assert mode(root) == 0o300


def test_sweep_staging_without_state_is_empty(home):
    assert paths.sweep_staging() == []
    assert not (home / ".local").exists()
