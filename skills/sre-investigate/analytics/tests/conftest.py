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


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A tmp dir set as HOME, so Path.home() resolves to it."""
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    return h


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
    found = shutil.which("duckdb") or str(Path.home() / ".local/bin/duckdb")
    if not found or not os.access(found, os.X_OK):
        pytest.skip("duckdb CLI not installed (expected on PATH or ~/.local/bin/duckdb)")
    return found
