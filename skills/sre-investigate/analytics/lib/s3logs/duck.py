"""The locked-down DuckDB runner. Everything that executes SQL goes through ``run``.

``run`` must hold even if the SQL guard (sqlguard.py) is bypassed, so the lockdown does not
depend on what the SQL says. Layers, in the order the script applies them:

1. The child gets a four-key environment (PATH, an empty tmp HOME, TZ=UTC, LC_ALL=C), so no
   AWS credentials, no ``~/.duckdbrc`` and no ``AI_AGENT`` (DuckDB 2.0 changes its output mode
   when that is set) reach it. ``-init /dev/null`` skips any init file. cwd is the tmp HOME.
2. ``-bail``: the CLI stops at the first failing statement. Without it the CLI keeps going
   after an error, so a failed ``SET`` would leave later statements (the user's) running
   unlocked.
3. ``autoinstall/autoload_known_extensions=false``, then a check that ``json`` and ``parquet``
   are loaded (``duckdb_extensions()`` stops working once external access is off, so it must
   come first and never after the lock), then ``allowed_directories=[...]`` and
   ``enable_external_access=false``. Our views and conversions run next, then
   ``lock_configuration=true`` freezes all of it and only then does the user's SQL run.
4. CLI dot-commands (``.shell`` and friends) are not SQL and bypass every setting above on all
   DuckDB versions. Any line of the assembled script whose first non-blank character is ``.``
   is refused before DuckDB starts. ``-safe`` would also stop them but breaks
   ``SET allowed_directories``, so it is never used.
5. DuckDB 1.4.5 follows symlinks inside an allowed directory. Before every run each allowed
   directory is walked and refused if it holds a symlink (or special file) or a regular file
   with more than one hard link.

Known limits: the walk and the run are not atomic (a same-user process could swap a file in
between); ``allowed_directories`` permits writing as well as reading, so a bypassed guard
could ``COPY ... TO`` a new file inside an allowed directory. ``run`` therefore snapshots the
directories before and after and fails with a DuckError if anything changed, unless the
caller passes ``allow_writes=True`` (the converter does). The snapshot is detective, not
preventive: callers should also keep fetched data files read-only (mode 0444).
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

from s3logs.validate import Refused


class DuckError(Exception):
    """DuckDB failed, timed out, or could not be started. The CLIs map it to exit 4."""

    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


MAX_OUTPUT_BYTES = 64 * 1024 * 1024   # stdout cap; the process is killed when it is exceeded
_MAX_ERR_BYTES = 1 << 20
_POLL_S = 0.02
_MAX_ERR_CHARS = 2000
# Anything the CLI could treat as a line break, plus NUL. A dot-command is looked for after
# splitting on all of these (wider than the CLI's own "\n", which only makes us stricter).
_LINE_BREAKS_RE = re.compile("[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")
_LITERAL_BAD_RE = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")


def quote_literal(s: str) -> str:
    """A SQL single-quoted string literal. Refuses control characters (so a path can never
    smuggle a line break, and with it a dot-command, into the script)."""
    if not isinstance(s, str) or _LITERAL_BAD_RE.search(s):
        raise Refused("refusing to put a value with control characters into SQL")
    return "'" + s.replace("'", "''") + "'"


def _check_no_dot_commands(script: str) -> None:
    if "\x00" in script:
        raise Refused("refusing SQL that contains a NUL character")
    for line in _LINE_BREAKS_RE.split(script):
        if line.lstrip().startswith("."):
            raise Refused("refusing SQL with a line starting with '.' (DuckDB CLI dot-commands are not allowed)")


Snapshot = Dict[str, Tuple[int, int, int]]


def _walk_allowed(d: Path) -> Snapshot:
    """Refuse symlinks, special files and multiply-linked files under ``d`` (R12). Returns a
    snapshot of the regular files: relative path -> (size, mtime_ns, inode); directories are
    included as (-1, mtime_ns, inode) so added/removed entries show up."""
    try:
        st = os.lstat(str(d))
    except OSError as e:
        raise Refused("allowed directory is not accessible: %s" % (e.strerror or "error"))
    if stat.S_ISLNK(st.st_mode):
        raise Refused("allowed directory is a symlink; refusing to use it")
    if not stat.S_ISDIR(st.st_mode):
        raise Refused("allowed directory is not a directory")
    snap = {}  # type: Snapshot
    stack = [d]
    while stack:
        cur = stack.pop()
        try:
            entries = list(os.scandir(str(cur)))
        except OSError as e:
            raise Refused("cannot list an allowed directory: %s" % (e.strerror or "error"))
        for ent in entries:
            rel = os.path.relpath(ent.path, str(d))
            try:
                est = ent.stat(follow_symlinks=False)
            except OSError as e:
                raise Refused("cannot stat %r in an allowed directory: %s" % (rel, e.strerror or "error"))
            mode = est.st_mode
            if stat.S_ISLNK(mode):
                raise Refused("symlink %r inside an allowed directory; refusing to run" % (rel,))
            if stat.S_ISDIR(mode):
                snap[rel] = (-1, est.st_mtime_ns, est.st_ino)
                stack.append(Path(ent.path))
            elif stat.S_ISREG(mode):
                if est.st_nlink > 1:
                    raise Refused("%r inside an allowed directory has %d hard links; refusing to run"
                                  % (rel, est.st_nlink))
                snap[rel] = (est.st_size, est.st_mtime_ns, est.st_ino)
            else:
                raise Refused("special file %r inside an allowed directory; refusing to run" % (rel,))
    return snap


def _find_duckdb() -> str:
    exe = shutil.which("duckdb")
    if not exe:
        raise DuckError("duckdb not found on PATH")
    return os.path.abspath(exe)


def _scrub(text: str, subs: List[Tuple[str, str]]) -> str:
    for needle, repl in subs:
        if needle:
            text = text.replace(needle, repl)
    return text


def run(script_sql: List[str], user_sql: str, allowed_dirs: List[Path], timeout_s: int = 120,
        allow_writes: bool = False) -> str:
    """Run ``script_sql`` (views, ``SET VARIABLE``s, conversions) and then ``user_sql`` in a
    locked-down in-memory DuckDB and return its CSV output (header row included).

    Raises ``validate.Refused`` for a dot-command line or an unsafe allowed directory (exit 2)
    and ``DuckError`` for anything DuckDB itself does wrong (exit 4). Any allowed-directory
    path in the error text is replaced by ``<staging>``. ``allow_writes`` lifts the
    "directories must not change" check for the converter.
    """
    if not allowed_dirs:
        raise Refused("at least one allowed directory is required")
    real_dirs = []  # type: List[Path]
    for d in allowed_dirs:
        p = Path(d)
        if not p.is_absolute():
            raise Refused("allowed directories must be absolute paths")
        real_dirs.append(p)

    head = [
        "SET autoinstall_known_extensions=false;",
        "SET autoload_known_extensions=false;",
        # Cheap resource caps; the lock below makes them permanent.
        "SET memory_limit='2GB';",
        "SET threads=4;",
        # Must run before external access is disabled: duckdb_extensions() fails afterwards.
        "SET VARIABLE ext_ok = (SELECT CASE WHEN count(*) = 2 THEN 1 ELSE error('json and parquet must be loaded') END"
        " FROM duckdb_extensions() WHERE loaded AND extension_name IN ('json', 'parquet'));",
        "SET allowed_directories=[%s];" % ", ".join(quote_literal(str(d)) for d in real_dirs),
        "SET enable_external_access=false;",
    ]
    script = "\n".join(head + [str(s) for s in script_sql] + ["SET lock_configuration=true;", str(user_sql), ";", ""])
    _check_no_dot_commands(script)

    before = [_walk_allowed(d) for d in real_dirs]
    exe = _find_duckdb()

    home = tempfile.mkdtemp(prefix="duck-home-")   # the child's HOME and cwd: stays empty
    ctl = tempfile.mkdtemp(prefix="duck-ctl-")     # our stdin/stdout/stderr files
    try:
        env = {
            "PATH": "%s:/usr/bin:/bin" % os.path.dirname(exe),
            "HOME": home,
            "TZ": "UTC",
            "LC_ALL": "C",
        }
        subs = []  # type: List[Tuple[str, str]]
        for d in real_dirs:
            for form in {str(d), os.path.realpath(str(d))}:
                subs.append((form, "<staging>"))
        subs.append((home, "<home>"))
        subs.sort(key=lambda t: -len(t[0]))
        # stdin, stdout and stderr are files (no pipes, so no deadlock and no unbounded
        # buffering); stdout is polled against MAX_OUTPUT_BYTES while the child runs.
        script_f, out_f, err_f = (os.path.join(ctl, n) for n in ("in.sql", "out", "err"))
        with open(script_f, "wb") as f:
            f.write(script.encode("utf-8", "surrogateescape"))
        deadline = time.monotonic() + timeout_s
        too_big = timed_out = False
        try:
            with open(script_f, "rb") as fin, open(out_f, "wb") as fout, open(err_f, "wb") as ferr:
                proc = subprocess.Popen([exe, "-bail", "-csv", "-init", "/dev/null", ":memory:"],
                                        stdin=fin, stdout=fout, stderr=ferr, env=env, cwd=home)
                try:
                    while True:
                        try:
                            proc.wait(timeout=_POLL_S)
                            break
                        except subprocess.TimeoutExpired:
                            pass
                        if os.path.getsize(out_f) > MAX_OUTPUT_BYTES:
                            too_big = True
                        elif time.monotonic() > deadline:
                            timed_out = True
                        if too_big or timed_out:
                            proc.kill()
                            proc.wait()
                            break
                finally:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait()
        except OSError as e:
            raise DuckError("cannot run duckdb: %s" % (e.strerror or "error"))
        if timed_out:
            raise DuckError("duckdb timed out after %d s" % timeout_s)
        if too_big or os.path.getsize(out_f) > MAX_OUTPUT_BYTES:
            raise DuckError("output too large; aggregate in SQL")
        if proc.returncode != 0:
            with open(err_f, "rb") as f:
                raw_err = f.read(_MAX_ERR_BYTES)
            err = _scrub(raw_err.decode("utf-8", "replace"), subs).strip()
            if len(err) > _MAX_ERR_CHARS:
                err = err[:_MAX_ERR_CHARS] + " ..."
            raise DuckError("duckdb failed (exit %d): %s" % (proc.returncode, err or "no message"))
        with open(out_f, "rb") as f:
            out = f.read(MAX_OUTPUT_BYTES + 1).decode("utf-8", "replace")
    finally:
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(ctl, ignore_errors=True)

    if not allow_writes:
        after = [_walk_allowed(d) for d in real_dirs]
        if after != before:
            raise DuckError("the query changed files in the data directory")
    return out
