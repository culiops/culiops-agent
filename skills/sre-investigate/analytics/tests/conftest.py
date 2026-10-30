"""Shared fixtures for the S3 log module tests.

Tests never touch real AWS or the real home directory: HOME points at a tmp dir
and external tools are replaced by stub scripts on PATH.
"""
from __future__ import annotations

import os
import shlex
import shutil
import stat
import sys
from pathlib import Path

import pytest

ANALYTICS = Path(__file__).resolve().parent.parent
LIB = ANALYTICS / "lib"
BIN = ANALYTICS / "bin"

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

# Captured at import time, before any fixture re-points HOME or PATH at a tmp dir.
_REAL_HOME = os.path.expanduser("~")
_ORIGINAL_PATH = os.environ.get("PATH", "")
STUBS = ANALYTICS / "tests" / "stubs"


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A tmp dir set as HOME, so Path.home() resolves to it."""
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    yield h
    # staging/ is mode 0300 and dataset dirs 0555; make everything removable so pytest can clean up.
    for dirpath, dirnames, _files in os.walk(str(h)):
        for d in dirnames:
            full = os.path.join(dirpath, d)
            if not os.path.islink(full):
                os.chmod(full, 0o700)


class StubPath:
    """A tmp bin dir prepended to PATH, plus helpers to write stub executables."""

    def __init__(self, directory: Path, monkeypatch):
        self.dir = directory
        self._monkeypatch = monkeypatch
        self._original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", str(directory) + os.pathsep + self._original_path)

    def isolate(self) -> None:
        """PATH becomes only the stub dir, so real s5cmd/duckdb are not found."""
        self._monkeypatch.setenv("PATH", str(self.dir))

    def write_script(self, name: str, body: str) -> Path:
        """Write an executable /bin/sh script with the given body."""
        p = self.dir / name
        p.write_text("#!/bin/sh\n" + body.rstrip("\n") + "\n")
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return p

    def write(self, name: str, stdout: str = "", exit_code: int = 0) -> Path:
        """Write a stub that prints `stdout` (whatever its arguments) and exits."""
        body = "printf '%s\\n' {}\nexit {}".format(shlex.quote(stdout), int(exit_code))
        return self.write_script(name, body)


@pytest.fixture
def stub_path(tmp_path, monkeypatch):
    d = tmp_path / "stubbin"
    d.mkdir()
    return StubPath(d, monkeypatch)


@pytest.fixture
def duckdb_bin():
    """Path to the real duckdb CLI; skip when it is not installed."""
    found = (shutil.which("duckdb", path=_ORIGINAL_PATH)
             or os.path.join(_REAL_HOME, ".local", "bin", "duckdb"))
    if not os.access(found, os.X_OK):
        pytest.skip("duckdb CLI not installed (expected on PATH or ~/.local/bin/duckdb)")
    return found


class FakeS3:
    """Stub `aws` (and any other stub in tests/stubs) on PATH over a fake bucket tree."""

    def __init__(self, root: Path, argv_log: Path):
        self.root = root
        self.argv_log = argv_log

    def bucket(self, name: str) -> Path:
        """Create (if needed) and return the directory standing in for a bucket."""
        p = self.root / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def calls(self) -> list:
        """Every logged stub invocation, as a list of argv lists."""
        import json
        if not self.argv_log.exists():
            return []
        return [json.loads(line) for line in self.argv_log.read_text().splitlines() if line.strip()]


@pytest.fixture
def fake_s3(tmp_path, monkeypatch, stub_path):
    """Install the stubs from tests/stubs on PATH, backed by a tmp FAKE_S3_ROOT."""
    for stub in sorted(STUBS.iterdir()):
        if stub.is_file() and os.access(str(stub), os.X_OK):
            target = stub_path.dir / stub.name
            shutil.copyfile(str(stub), str(target))
            target.chmod(0o755)
    root = tmp_path / "fake-s3"
    root.mkdir()
    log = tmp_path / "argv.log"
    monkeypatch.setenv("FAKE_S3_ROOT", str(root))
    monkeypatch.setenv("FAKE_ARGV_LOG", str(log))
    for var in ("FAKE_AWS_ERROR", "FAKE_EXTRA_KEYS_JSON"):
        monkeypatch.delenv(var, raising=False)
    return FakeS3(root, log)
