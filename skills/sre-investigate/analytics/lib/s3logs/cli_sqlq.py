"""sqlq: run named or ad-hoc read-only SQL over fetched request logs.

    sqlq <dataset> --run <run-id> <named-query> [--param k=v]...
    sqlq <dataset> --run <run-id> --sql '<statement>' [--param k=v]...
    sqlq <dataset> --run <run-id> --list
    sqlq run:<dir> --sql '<statement>' | --list

stdout is CSV with a header row (the hostile-field rule: DuckDB does the quoting, nothing here
re-formats a row). Notices go to stderr as lines starting ``-- ``. Exit codes: 0 ok, 2 refused
(arguments, SQL guard, missing data), 4 DuckDB error.

Two layers stand between the SQL and the machine. ``sqlguard.check`` screens an ad-hoc
statement; ``duck.run`` locks DuckDB down (allowed directories, no external access, locked
configuration, symlink and hard-link refusal) and is always called with ``allow_writes=False``;
dataset directories are also kept read-only on disk by logs-fetch (R28).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if __name__ == "__main__":
    # python3 -I drops the script dir from sys.path; add the lib dir that holds this package.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from s3logs import config, duck, paths, sqlguard, validate  # noqa: E402
from s3logs.validate import Refused  # noqa: E402

# Named queries live next to the code and are resolved from this file, never from the cwd.
SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"
ROW_LIMIT = 200
MAX_NAMED_SQL_BYTES = 64 * 1024

_QUERY_NAME_RE = re.compile(r"[a-z0-9_]{1,64}")
_PARAM_KEY_RE = re.compile(r"[a-z_]{1,32}")
_PARAM_VAL_RE = re.compile(r"[\x20-\x7e]{1,512}")
_PART_RE = re.compile(r"part-[0-9]{6,}\.parquet")
_MAX_PARAMS = 32
_RUN_FILE_KINDS = {
    ".json": ("json", "json"),
    ".jsonl": ("json", "ndjson"),
    ".ndjson": ("json", "ndjson"),
    ".csv": ("csv", "csv"),
    ".tsv": ("csv", "tsv"),
}
# Exactly DuckDB 2.0's appended line: "hint: -agent renders errors as JSON and results ...".
# Anchored, so a real error line that mentions a "user-agent" column is never dropped.
_HINT_LINE_RE = re.compile(r"\s*hint:\s*-agent\b", re.IGNORECASE)
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
_CSV_SPECIAL_RE = re.compile(r'["\n]')


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused(message)


# ---- helpers --------------------------------------------------------------------------------

def _load_config() -> config.Config:
    cfg_path = paths.config_path()
    if not (cfg_path.exists() or cfg_path.is_symlink()):
        raise Refused("S3 log module: off (not configured)")
    try:
        return config.load(cfg_path)
    except config.ConfigError as e:
        raise Refused("S3 log module: off (config error: %s)" % e)


def _printable(s: str) -> str:
    return _CTRL_RE.sub("?", s)


def _regular_files(d: Path) -> List[Tuple[str, int]]:
    """Names of the regular, non-symlink entries of ``d`` (sorted). Anything else is left out;
    duck.run refuses the whole run when it finds a link, so nothing is silently read through one."""
    out = []
    with os.scandir(str(d)) as it:
        for ent in it:
            try:
                st = ent.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                out.append((ent.name, st.st_size))
    out.sort()
    return out


def strip_hint(msg: str) -> str:
    """DuckDB 2.0 appends a 'hint: -agent renders errors as JSON ...' line to every error."""
    return "\n".join(ln for ln in msg.split("\n") if not _HINT_LINE_RE.match(ln)).rstrip()


def _cap_csv_rows(text: str, max_rows: int) -> Tuple[str, bool]:
    """Keep the header plus the first ``max_rows`` records of DuckDB's CSV text, verbatim.
    Records end at a newline outside double quotes (DuckDB doubles quotes inside a field).
    Returns (text, whether anything was cut)."""
    want = max_rows + 1
    inq = False
    seen = 0
    for m in _CSV_SPECIAL_RE.finditer(text):
        if m.group(0) == '"':
            inq = not inq
        elif not inq:
            seen += 1
            if seen == want:
                end = m.end()
                return text[:end], len(text) > end
    return text, False


def _with_header(out: str, script: List[str], sql: str, allowed: Path) -> str:
    """DuckDB 1.4 prints nothing at all for a result with no rows (1.5 and later print the
    header). Give callers the same shape on every version by asking for the column names."""
    if out != "":
        return out
    names = duck.run(script, "SELECT column_name FROM (DESCRIBE %s)" % sql, [allowed], allow_writes=False)
    cols = [r[0] for r in list(csv.reader(io.StringIO(names)))[1:] if r]
    if not cols:
        return out
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(cols)
    return buf.getvalue()


def _read_sample_every(d: Path) -> int:
    p = d / "meta.json"
    try:
        fd = os.open(str(p), os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return 1
    except OSError as e:
        raise Refused("cannot read %s: %s" % (p, e.strerror or "error"))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > 1 << 20:
            raise Refused("%s is not a regular file of reasonable size; remove the run's data with "
                          "logs-fetch --purge <run-id>" % (p,))
        raw = os.read(fd, (1 << 20) + 1)
    finally:
        os.close(fd)
    try:
        every = json.loads(raw.decode("utf-8"))["sample_every"]
        if isinstance(every, bool) or not isinstance(every, int) or every < 1:
            raise ValueError("sample_every")
    except (ValueError, KeyError, TypeError, RecursionError, UnicodeDecodeError):
        raise Refused("%s is corrupt; remove the run's data with logs-fetch --purge <run-id>" % (p,))
    return every


def _parse_params(items: List[str]) -> List[Tuple[str, str]]:
    if len(items) > _MAX_PARAMS:
        raise Refused("too many --param options (maximum %d)" % _MAX_PARAMS)
    out = []  # type: List[Tuple[str, str]]
    seen = set()
    for item in items:
        k, sep, v = item.partition("=")
        if not sep or not _PARAM_KEY_RE.fullmatch(k):
            raise Refused("invalid --param %r (expected key=value, key is 1-32 chars of a-z and _)" % _printable(item))
        if not _PARAM_VAL_RE.fullmatch(v):
            raise Refused("invalid value for --param %s (1-512 printable ASCII characters)" % k)
        if k in seen:
            raise Refused("--param %s given twice" % k)
        seen.add(k)
        out.append((k, v))
    return out


def _param_statement(k: str, v: str) -> str:
    # The name is quoted so a reserved word as key cannot break the statement; the value is
    # a plain literal with ' doubled (DuckDB strings have no backslash escapes).
    return 'SET VARIABLE "%s" = %s;' % (k, duck.quote_literal(v))


# ---- named queries --------------------------------------------------------------------------

def _read_sql_file(p: Path) -> str:
    try:
        fd = os.open(str(p), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        raise Refused("named query file %s is not readable" % p.name)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_NAMED_SQL_BYTES:
            raise Refused("named query file %s is not a regular file of reasonable size" % p.name)
        raw = os.read(fd, MAX_NAMED_SQL_BYTES + 1)
    finally:
        os.close(fd)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("named query file %s is not valid UTF-8" % p.name)


def _purpose(text: str) -> str:
    first = text.split("\n", 1)[0].strip()
    if first.startswith("--"):
        return _printable(first[2:].strip()) or "(no description)"
    return "(no description)"


def _list_named(ds_type: str) -> List[Tuple[str, str]]:
    d = SQL_DIR / ds_type
    out = []  # type: List[Tuple[str, str]]
    try:
        names = sorted(n for n, _ in _regular_files(d))
    except OSError:
        return out
    for fname in names:
        if not fname.endswith(".sql") or not _QUERY_NAME_RE.fullmatch(fname[:-4]):
            continue
        try:
            out.append((fname[:-4], _purpose(_read_sql_file(d / fname))))
        except Refused:
            out.append((fname[:-4], "(unreadable)"))
    return out


def _load_named(ds_type: str, name: str) -> str:
    if not _QUERY_NAME_RE.fullmatch(name):
        raise Refused("invalid query name %r (a-z, 0-9 and _, 1-64 chars)" % _printable(name))
    p = SQL_DIR / ds_type / (name + ".sql")
    try:
        if not stat.S_ISREG(os.lstat(str(p)).st_mode):
            raise Refused("named query %s is not a regular file" % name)
    except FileNotFoundError:
        have = ", ".join(n for n, _ in _list_named(ds_type)) or "none"
        raise Refused("unknown query %r for %s datasets (available: %s)" % (name, ds_type, have))
    except OSError as e:
        raise Refused("cannot read named query %s: %s" % (name, e.strerror or "error"))
    try:
        return sqlguard.check_named(_read_sql_file(p))
    except Refused as e:
        raise Refused("named query %s failed its integrity check (%s); the installed query files may be corrupted" % (name, e))


# ---- what to query --------------------------------------------------------------------------

class _Source:
    """The views a query sees, as SQL to run before the lock, plus where it may read."""

    def __init__(self, allowed: Path, script: List[str], views: List[str],
                 ds_type: Optional[str], sample_every: int, files: Optional[Dict[str, str]] = None):
        self.files = files or {}    # view -> source file name (run directories only)
        self.allowed = allowed
        self.script = script
        self.views = views
        self.ds_type = ds_type
        self.sample_every = sample_every


def _dataset_source(ds: config.Dataset, run: str) -> _Source:
    d = paths.state_root() / "data" / run / ds.name
    msg = "no data for %s in run %s; run logs-fetch first" % (ds.name, run)
    try:
        if not stat.S_ISDIR(os.lstat(str(d)).st_mode):
            raise Refused(msg)
    except OSError:
        raise Refused(msg)
    parts = [n for n, _ in _regular_files(d) if _PART_RE.fullmatch(n)]
    if not parts:
        raise Refused(msg)
    listing = ", ".join(duck.quote_literal(str(d / n)) for n in parts)
    script = ["CREATE VIEW logs AS SELECT * FROM read_parquet([%s], union_by_name = true);" % listing]
    return _Source(d, script, ["logs"], ds.type, _read_sample_every(d))


def _resolve_run_dir(arg: str) -> Path:
    if not arg or "\x00" in arg:
        raise Refused("run:<dir> needs a directory")
    real = os.path.realpath(arg)
    if not os.path.isdir(real):
        raise Refused("run directory %r does not exist" % _printable(arg))
    parts = Path(real).parts
    if not any(parts[i] == "sre-investigate" and parts[i + 1] == "runs" and i + 2 < len(parts)
               for i in range(len(parts) - 2)):
        raise Refused("run:<dir> must be a directory under .../sre-investigate/runs/ "
                      "(the resolved path is %s)" % _printable(real))
    return Path(real)


def _run_dir_source(arg: str, notices: List[str]) -> _Source:
    d = _resolve_run_dir(arg)
    script = []  # type: List[str]
    views = []  # type: List[str]
    files = {}  # type: Dict[str, str]
    for name, _size in _regular_files(d):
        stem, dot, ext = name.rpartition(".")
        kind = _RUN_FILE_KINDS.get("." + ext.lower()) if dot else None
        if kind is None or name.startswith("."):
            continue
        prefix, fmt = kind
        base = prefix + "_" + (re.sub(r"[^a-z0-9_]", "_", stem.lower()) or "file")
        view, n = base, 1
        while view in views:
            n += 1
            view = "%s_%d" % (base, n)
        try:
            lit = duck.quote_literal(str(d / name))
        except Refused:
            notices.append("-- skipped a file whose name has control characters")
            continue
        if fmt == "json":
            src = "read_json_auto(%s)" % lit
        elif fmt == "ndjson":
            src = "read_json_auto(%s, format = 'newline_delimited')" % lit
        elif fmt == "csv":
            src = "read_csv_auto(%s)" % lit
        else:
            src = "read_csv(%s, delim = chr(9), header = true, auto_detect = true)" % lit
        script.append("CREATE VIEW %s AS SELECT * FROM %s;" % (view, src))
        views.append(view)
        files[view] = name
    if not views:
        raise Refused("no .json, .jsonl, .ndjson, .csv or .tsv files at the top level of the run directory")
    return _Source(d, script, views, None, 1, files)


# ---- main flow ------------------------------------------------------------------------------

def _write(stream, text: str) -> None:
    stream.write(text)
    stream.flush()


def _list_output(src: _Source) -> str:
    sel = " UNION ALL ".join(
        "SELECT %s AS v, column_name, column_type FROM (DESCRIBE %s)" % (duck.quote_literal(v), v)
        for v in src.views)
    out = duck.run(src.script, sel, [src.allowed], allow_writes=False)
    rows = list(csv.reader(io.StringIO(out)))[1:]
    lines = []  # type: List[str]
    current = None
    for row in rows:
        if len(row) < 3:
            continue
        if row[0] != current:
            current = row[0]
            origin = src.files.get(current)
            lines.append("view %s" % _printable(current) + (" (%s)" % _printable(origin) if origin else ""))
        lines.append("column %s %s" % (_printable(row[1]), _printable(row[2])))
    if src.ds_type is not None:
        for qname, purpose in _list_named(src.ds_type):
            lines.append("query %s — %s" % (qname, purpose))
    return "\n".join(lines) + "\n"


def run_cli(argv: Optional[List[str]]) -> int:
    p = _Parser(prog="sqlq", allow_abbrev=False,
                description="Run read-only SQL over fetched request logs.")
    p.add_argument("dataset", help="a configured dataset name, or run:<dir> for a run directory")
    p.add_argument("query", nargs="?", help="name of a stored query (see --list)")
    p.add_argument("--run", help="run id the data was fetched under")
    p.add_argument("--sql", help="one ad-hoc SELECT/WITH/DESCRIBE/SUMMARIZE/FROM statement")
    p.add_argument("--list", action="store_true", help="show the views, columns and stored queries")
    p.add_argument("--param", action="append", default=[], help="key=value for a stored query (getvariable('key'))")
    args = p.parse_intermixed_args(argv)

    modes = int(args.query is not None) + int(args.sql is not None) + int(bool(args.list))
    if modes != 1:
        raise Refused("give exactly one of: a query name, --sql '<statement>', --list")
    params = _parse_params(args.param)

    notices = []  # type: List[str]
    if args.dataset.startswith("run:"):
        if args.run is not None:
            raise Refused("--run does not go with run:<dir>")
        if args.query is not None:
            raise Refused("stored queries need a dataset; run:<dir> takes --sql or --list")
        src = _run_dir_source(args.dataset[4:], notices)
    else:
        ds_name = validate.dataset_name(args.dataset)
        if args.run is None:
            raise Refused("--run <run-id> is required")
        run = validate.run_id(args.run)
        cfg = _load_config()
        ds = cfg.datasets.get(ds_name)
        if ds is None:
            raise Refused("unknown dataset %r (configured: %s)" % (ds_name, ", ".join(cfg.datasets) or "none"))
        src = _dataset_source(ds, run)

    for n in notices:
        _write(sys.stderr, n + "\n")
    script = list(src.script) + [_param_statement(k, v) for k, v in params]

    if args.list:
        _write(sys.stdout, _list_output(src))
        return 0

    if src.sample_every > 1:
        _write(sys.stderr, "-- sampled 1/%d: multiply counts by %d\n" % (src.sample_every, src.sample_every))

    if args.query is not None:
        assert src.ds_type is not None
        sql = _load_named(src.ds_type, args.query)
        for k, _v in params:
            if not re.search(r"getvariable\s*\(\s*'%s'\s*\)" % re.escape(k), sql, re.IGNORECASE):
                _write(sys.stderr, "-- param %s is not used by query %s\n" % (k, args.query))
        out = duck.run(script, sql, [src.allowed], allow_writes=False)
        _write(sys.stdout, _with_header(out, script, sql, src.allowed))
        return 0

    stmt = sqlguard.check(args.sql)
    wrapped = "SELECT * FROM (\n%s\n) AS q LIMIT %d" % (stmt, ROW_LIMIT + 1)
    out = duck.run(script, wrapped, [src.allowed], allow_writes=False)
    out, cut = _cap_csv_rows(_with_header(out, script, wrapped, src.allowed), ROW_LIMIT)
    _write(sys.stdout, out)
    if cut:
        _write(sys.stderr, "-- truncated at %d rows; aggregate in SQL\n" % ROW_LIMIT)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    try:
        return run_cli(argv)
    except Refused as e:
        sys.stderr.write("refused: %s\n" % e)
        return 2
    except duck.DuckError as e:
        sys.stderr.write("duckdb error (exit 4): %s\n" % strip_hint(e.msg))
        return 4
    except OSError as e:
        sys.stderr.write("refused: %s\n" % (e.strerror or e))
        return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    except AttributeError:
        pass
    sys.exit(main(sys.argv[1:]))
