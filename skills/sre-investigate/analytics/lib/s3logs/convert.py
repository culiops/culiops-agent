"""Raw gzip access logs -> redacted Parquet.

Redaction happens in Python while each gz file is streamed into a private staging file (JSON
lines). DuckDB then only ever reads that already-masked file (through ``duck.run``, locked
down) and writes the Parquet. The raw inputs and every intermediate are deleted in a
``finally``, on success and on every failure.

Sources for the formats (checked 2026-10-30):
  CloudFront standard logs, field list and order, encoding rules:
    https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html
  ALB access-log entry syntax (36 fields in order, new fields are appended at the end):
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-entry-syntax
  WAF record shape: see redact.py.

CloudFront columns are an allow-list. Only the known, non-sensitive W3C fields below are kept;
``cs(Cookie)`` and any field not in the list (including new or custom ones) are dropped and
reported by name. Every kept file is converted to the same fixed schema, so Parquet files made
from different ``#Fields:`` headers can be read together. ALB keeps all documented fields but
masks the three that carry a URL (the request URL, ``redirect_url`` and ``transformed_uri``).

Known limits: a secret that sits in a non-sensitive part of a URL (an unlabelled path segment,
a query value that is not itself a query string) is not detected, and an unencoded space in an
ALB request URL can hide a ``name=value`` pair from the masker; the user agent and other
free-text fields are stored as sent.
"""
from __future__ import annotations

import errno
import gzip
import json
import os
import re
import secrets
import shutil
import zlib
from pathlib import Path
from typing import Iterator, List, NamedTuple, Optional, Sequence, Tuple

from s3logs import duck, paths, redact
from s3logs.validate import Refused

MAX_LINE_BYTES = 1 << 20          # a longer line is skipped, never loaded
MAX_DROPPED_NAMES = 50            # reported dropped-column names are capped
_MAX_NAME_LEN = 64
_NAME_OK_RE = re.compile(r"[A-Za-z0-9_().:-]{1,64}")


class ConvertError(Exception):
    """A raw file could not be read (corrupt, truncated or not gzip) or the result did not
    match what was written. The message names the file by base name only."""


class ConvertResult(NamedTuple):
    rows: int                              # rows in the Parquet file
    dropped_columns: Tuple[str, ...]       # CloudFront header fields not kept (names only, capped)
    skipped_lines: int                     # malformed or overlong lines that were not converted


# ---- CloudFront ------------------------------------------------------------------------------

def normalize_field(name: str) -> str:
    """Lowercase; ``-``, ``(`` and ``)`` become ``_``; repeats collapse; trailing ``_`` goes.
    ``cs(User-Agent)`` -> ``cs_user_agent``."""
    s = re.sub(r"[-()]", "_", name.lower())
    return re.sub(r"_+", "_", s).strip("_")


# normalized name -> parquet type. The W3C names are those of the standard-logs-reference page.
# Order is the output column order. ``date`` and ``time`` are consumed into ``ts``.
_CF_FIELDS = (
    ("date", "DATE"), ("time", "TIME"),
    ("x-edge-location", "VARCHAR"), ("sc-bytes", "BIGINT"), ("c-ip", "VARCHAR"),
    ("cs-method", "VARCHAR"), ("cs(Host)", "VARCHAR"), ("cs-uri-stem", "VARCHAR"),
    ("sc-status", "INTEGER"), ("cs(Referer)", "VARCHAR"), ("cs(User-Agent)", "VARCHAR"),
    ("cs-uri-query", "VARCHAR"), ("x-edge-result-type", "VARCHAR"),
    ("x-edge-request-id", "VARCHAR"), ("x-host-header", "VARCHAR"), ("cs-protocol", "VARCHAR"),
    ("cs-bytes", "BIGINT"), ("time-taken", "DOUBLE"), ("x-forwarded-for", "VARCHAR"),
    ("ssl-protocol", "VARCHAR"), ("ssl-cipher", "VARCHAR"),
    ("x-edge-response-result-type", "VARCHAR"), ("cs-protocol-version", "VARCHAR"),
    ("fle-status", "VARCHAR"), ("fle-encrypted-fields", "INTEGER"), ("c-port", "INTEGER"),
    ("time-to-first-byte", "DOUBLE"), ("x-edge-detailed-result-type", "VARCHAR"),
    ("sc-content-type", "VARCHAR"), ("sc-content-len", "BIGINT"),
    ("sc-range-start", "BIGINT"), ("sc-range-end", "BIGINT"),
)
CF_ALLOWED = {normalize_field(n): t for n, t in _CF_FIELDS}
_CF_OUT = [(n, t) for n, t in CF_ALLOWED.items() if n not in ("date", "time")]


# ---- ALB -------------------------------------------------------------------------------------

# Documented order (36 fields). Names follow the doc; ``request`` is split, ``client:port`` and
# ``target:port`` are split, and ``ip_address`` (the LB node) is stored as ``lb_ip``.
_ALB_FIELDS = (
    "type", "time", "elb", "client", "target", "request_processing_time", "target_processing_time",
    "response_processing_time", "elb_status_code", "target_status_code", "received_bytes",
    "sent_bytes", "request", "user_agent", "ssl_cipher", "ssl_protocol", "target_group_arn",
    "trace_id", "domain_name", "chosen_cert_arn", "matched_rule_priority", "request_creation_time",
    "actions_executed", "redirect_url", "error_reason", "target_port_list",
    "target_status_code_list", "classification", "classification_reason", "conn_trace_id",
    "transformed_host", "transformed_uri", "request_transform_status", "lb_ip",
    "target_error_code", "elb_error_code",
)
_ALB_MIN_FIELDS = 14   # through user_agent; older entries are shorter than today's 36
_ALB_TYPES = frozenset(["http", "https", "h2", "grpcs", "ws", "wss"])
_ALB_TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
_ALB_REQUEST_RE = re.compile(r"(\S+) (.*) (HTTP/\d+(?:\.\d+)?|-)")
# output column -> type, in order (``ts`` first)
_ALB_OUT = (
    ("type", "VARCHAR"), ("elb", "VARCHAR"), ("client_ip", "VARCHAR"), ("client_port", "INTEGER"),
    ("target_ip", "VARCHAR"), ("target_port", "INTEGER"), ("request_processing_time", "DOUBLE"),
    ("target_processing_time", "DOUBLE"), ("response_processing_time", "DOUBLE"),
    ("elb_status_code", "INTEGER"), ("target_status_code", "INTEGER"), ("received_bytes", "BIGINT"),
    ("sent_bytes", "BIGINT"), ("method", "VARCHAR"), ("url", "VARCHAR"), ("protocol", "VARCHAR"),
    ("user_agent", "VARCHAR"), ("ssl_cipher", "VARCHAR"), ("ssl_protocol", "VARCHAR"),
    ("target_group_arn", "VARCHAR"), ("trace_id", "VARCHAR"), ("domain_name", "VARCHAR"),
    ("chosen_cert_arn", "VARCHAR"), ("matched_rule_priority", "INTEGER"),
    ("request_creation_ts", "TIMESTAMP"), ("actions_executed", "VARCHAR"),
    ("redirect_url", "VARCHAR"), ("error_reason", "VARCHAR"), ("target_port_list", "VARCHAR"),
    ("target_status_code_list", "VARCHAR"), ("classification", "VARCHAR"),
    ("classification_reason", "VARCHAR"), ("conn_trace_id", "VARCHAR"),
    ("transformed_host", "VARCHAR"), ("transformed_uri", "VARCHAR"),
    ("request_transform_status", "VARCHAR"), ("lb_ip", "VARCHAR"), ("target_error_code", "VARCHAR"),
    ("elb_error_code", "VARCHAR"),
)

# ---- WAF -------------------------------------------------------------------------------------

_WAF_LIST_COLS = ("rule_group_matches", "non_terminating_rules", "labels", "header_names", "identity_hashes")
_WAF_COLS = tuple(k for k in redact._WAF_KEYS)


# ---- line reading ----------------------------------------------------------------------------

def _read_lines(path: Path) -> Iterator[Optional[str]]:
    """Decoded lines of a gz file without their newline. ``None`` stands for an overlong line
    that was skipped. NUL is removed, invalid UTF-8 is replaced. Any read problem becomes a
    ConvertError naming the file."""
    try:
        with gzip.open(str(path), "rb") as g:
            while True:
                chunk = g.readline(MAX_LINE_BYTES + 1)
                if not chunk:
                    return
                if len(chunk) > MAX_LINE_BYTES and not chunk.endswith(b"\n"):
                    while True:  # drain the rest of the overlong line in small pieces
                        rest = g.readline(1 << 16)
                        if not rest or rest.endswith(b"\n"):
                            break
                    yield None
                    continue
                text = chunk.decode("utf-8", "replace").replace("\x00", "")
                yield text.rstrip("\n").rstrip("\r")
    except (OSError, EOFError, zlib.error) as e:
        raise ConvertError("cannot read %s: %s" % (Path(path).name, type(e).__name__))


class _Writer:
    def __init__(self, path: Path):
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self._f = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
        self.rows = 0

    def write(self, row: dict) -> None:
        self._f.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
        self.rows += 1

    def close(self) -> None:
        self._f.close()


class _Counts:
    def __init__(self) -> None:
        self.skipped = 0
        self.dropped = []  # type: List[str]
        self.dropped_more = False

    def drop(self, name: str) -> None:
        shown = name if _NAME_OK_RE.fullmatch(name) else "<invalid-name>"
        if shown in self.dropped:
            return
        if len(self.dropped) >= MAX_DROPPED_NAMES:
            self.dropped_more = True
        else:
            self.dropped.append(shown)

    def dropped_tuple(self) -> Tuple[str, ...]:
        return tuple(self.dropped) + (("...",) if self.dropped_more else ())


# ---- per-type streaming ----------------------------------------------------------------------

def _stream_cloudfront(raw_files: Sequence[Path], w: _Writer, names: frozenset, counts: _Counts) -> None:
    for path in raw_files:
        keep = []  # type: List[Tuple[int, str]]   # (column index, normalized name)
        width = 0
        have_header = False
        for line in _read_lines(path):
            if line is None:
                counts.skipped += 1
                continue
            if line.startswith("#"):
                if line.startswith("#Fields:"):
                    header = line[len("#Fields:"):].split()
                    width = len(header)
                    have_header = True
                    keep = []
                    seen = set()
                    for i, orig in enumerate(header):
                        norm = normalize_field(orig)
                        if norm in CF_ALLOWED and norm not in seen:
                            seen.add(norm)
                            keep.append((i, norm))
                        else:
                            counts.drop(orig)
                continue
            if line == "":
                continue
            if not have_header:
                counts.skipped += 1
                continue
            cols = line.split("\t")
            if len(cols) > width and all(c == "" for c in cols[width:]):
                cols = cols[:width]  # some delivered lines end in a stray tab
            if len(cols) != width:
                counts.skipped += 1
                continue
            try:
                row = {norm: cols[i] for i, norm in keep}
                if "cs_uri_stem" in row:
                    row["cs_uri_stem"] = redact.mask_path(row["cs_uri_stem"], names)
                if "cs_uri_query" in row:
                    row["cs_uri_query"] = redact.mask_query(row["cs_uri_query"], names)
                if "cs_referer" in row:
                    row["cs_referer"] = redact.mask_url(row["cs_referer"], names)
            except Exception:
                counts.skipped += 1  # fail closed: a row we cannot mask is not kept
                continue
            w.write(row)


def _tokenize(line: str, limit: int) -> Optional[List[str]]:
    """Split an ALB entry: space-delimited, a field starting with a double quote runs to the
    next quote that is followed by a space or the end of the line. Stops after ``limit``
    fields. None when a quoted field is never closed."""
    toks = []  # type: List[str]
    i, n = 0, len(line)
    while i < n and len(toks) < limit:
        if line[i] == " ":
            i += 1
            continue
        if line[i] == '"':
            j = i + 1
            while True:
                k = line.find('"', j)
                if k == -1:
                    return None
                if k + 1 == n or line[k + 1] == " ":
                    break
                j = k + 1
            toks.append(line[i + 1:k])
            i = k + 1
        else:
            k = line.find(" ", i)
            if k == -1:
                k = n
            toks.append(line[i:k])
            i = k
    return toks


def _split_addr(value: str) -> Tuple[str, Optional[str]]:
    host, sep, port = value.rpartition(":")
    if sep and port.isascii() and port.isdigit() and len(port) <= 5:
        return host, port
    return value, None


def _alb_row(line: str, names: frozenset) -> Optional[dict]:
    toks = _tokenize(line, len(_ALB_FIELDS))
    if toks is None or len(toks) < _ALB_MIN_FIELDS:
        return None
    if toks[0] not in _ALB_TYPES or not _ALB_TIME_RE.fullmatch(toks[1]):
        return None
    m = _ALB_REQUEST_RE.fullmatch(toks[12])
    if not m:
        return None
    toks = toks + [""] * (len(_ALB_FIELDS) - len(toks))
    f = dict(zip(_ALB_FIELDS, toks))
    row = {k: v for k, v in f.items() if k not in ("time", "client", "target", "request")}
    row["ts"] = f["time"]
    row["client_ip"], row["client_port"] = _split_addr(f["client"])
    row["target_ip"], row["target_port"] = _split_addr(f["target"])
    row["method"], row["protocol"] = m.group(1), m.group(3)
    row["url"] = redact.mask_url(m.group(2), names)
    row["redirect_url"] = redact.mask_url(f["redirect_url"], names)
    row["transformed_uri"] = redact.mask_url(f["transformed_uri"], names)
    row["request_creation_ts"] = row.pop("request_creation_time")
    # Absent trailing fields (older or shorter entries) are NULL, not an empty string.
    for k, v in row.items():
        if v == "":
            row[k] = "-"
    return row


def _stream_alb(raw_files: Sequence[Path], w: _Writer, names: frozenset, counts: _Counts) -> None:
    for path in raw_files:
        for line in _read_lines(path):
            if line is None:
                counts.skipped += 1
                continue
            if line.strip() == "":
                continue
            try:
                row = _alb_row(line, names)
            except Exception:
                row = None
            if row is None:
                counts.skipped += 1
                continue
            w.write(row)


def _stream_waf(raw_files: Sequence[Path], w: _Writer, cfg, salt: bytes, counts: _Counts) -> None:
    for path in raw_files:
        for line in _read_lines(path):
            if line is None:
                counts.skipped += 1
                continue
            if line.strip() == "":
                continue
            try:
                rec = json.loads(line)
            except (ValueError, RecursionError):
                counts.skipped += 1
                continue
            if not isinstance(rec, dict):
                counts.skipped += 1
                continue
            w.write(redact.waf_record(rec, cfg, salt))


# ---- SQL -------------------------------------------------------------------------------------

def _q(name: str) -> str:
    return '"%s"' % name  # only ever called with constant identifiers


def _text_select(name: str, typ: str) -> str:
    base = "NULLIF(%s, '-')" % _q(name)
    if typ == "VARCHAR":
        return "%s AS %s" % (base, _q(name))
    return "TRY_CAST(%s AS %s) AS %s" % (base, typ, _q(name))


def _ts_expr(col: str) -> str:
    return ("COALESCE(TRY_STRPTIME(%(c)s, '%%Y-%%m-%%dT%%H:%%M:%%S.%%fZ'), "
            "TRY_STRPTIME(%(c)s, '%%Y-%%m-%%dT%%H:%%M:%%SZ'))") % {"c": col}


def _select_sql(ds_type: str, stage: Path) -> str:
    src = duck.quote_literal(str(stage))
    if ds_type == "cloudfront":
        cols = ["date", "time"] + [n for n, _ in _CF_OUT]
        spec = ", ".join("%s: 'VARCHAR'" % _q(c) for c in cols)
        sel = ["TRY_CAST(%s || ' ' || %s AS TIMESTAMP) AS ts" % (_q("date"), _q("time"))]
        sel += [_text_select(n, t) for n, t in _CF_OUT]
    elif ds_type == "alb":
        cols = ["ts"] + [n for n, _ in _ALB_OUT if n != "request_creation_ts"] + ["request_creation_ts"]
        spec = ", ".join("%s: 'VARCHAR'" % _q(c) for c in cols)
        sel = ["%s AS ts" % _ts_expr(_q("ts"))]
        for n, t in _ALB_OUT:
            if n == "request_creation_ts":
                sel.append("%s AS %s" % (_ts_expr(_q(n)), _q(n)))
            else:
                sel.append(_text_select(n, t))
    else:
        parts = []
        sel = []
        for c in _WAF_COLS:
            typ = "VARCHAR[]" if c in _WAF_LIST_COLS else ("BIGINT" if c == "response_code_sent" else "VARCHAR")
            parts.append("%s: '%s'" % (_q(c), typ))
            sel.append("%s AS ts" % _ts_expr(_q("ts")) if c == "ts" else _q(c))
        spec = ", ".join(parts)
    return "SELECT %s FROM read_json(%s, format='newline_delimited', columns={%s})" % (", ".join(sel), src, spec)


# ---- entry point -----------------------------------------------------------------------------

def _publish(src: Path, out: Path) -> None:
    """Move the finished Parquet into place, read-only, replacing any previous file."""
    os.chmod(str(src), 0o444)
    try:
        os.replace(str(src), str(out))
        return
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
    tmp = out.with_name(out.name + ".tmp-" + secrets.token_hex(4))
    try:
        shutil.copyfile(str(src), str(tmp))
        os.chmod(str(tmp), 0o444)
        os.replace(str(tmp), str(out))
    finally:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass


def to_parquet(ds_type: str, raw_files: Sequence[Path], out: Path, cfg, salt: bytes) -> ConvertResult:
    """Convert ``raw_files`` (gzip logs of one dataset type) into one redacted Parquet file at
    ``out`` (mode 0444, replaced atomically) and return a ConvertResult.

    ``raw_files`` are always deleted, as is the private staging directory under the state
    root, whatever happens. Raises ``ConvertError`` (unreadable input), ``duck.DuckError``
    (DuckDB failed) or ``validate.Refused`` (unknown type, bad output location).
    """
    raw = [Path(p) for p in raw_files]
    conv = None  # type: Optional[Path]
    try:
        if ds_type not in ("cloudfront", "alb", "waf"):
            raise Refused("unknown dataset type %r" % (ds_type,))
        out = Path(out)
        if not out.parent.is_dir():
            raise Refused("output directory %s does not exist" % (out.parent,))
        paths.ensure_private_dirs()
        conv = paths.private_subdir(paths.state_root() / "staging", "conv-" + secrets.token_hex(8))
        stage = conv / "stage.jsonl"
        parquet = conv / "out.parquet"
        names = redact.sensitive_names(cfg)
        counts = _Counts()
        w = _Writer(stage)
        try:
            if ds_type == "cloudfront":
                _stream_cloudfront(raw, w, names, counts)
            elif ds_type == "alb":
                _stream_alb(raw, w, names, counts)
            else:
                _stream_waf(raw, w, cfg, salt, counts)
        finally:
            w.close()
        script = ["COPY (%s) TO %s (FORMAT parquet, COMPRESSION zstd);" % (
            _select_sql(ds_type, stage), duck.quote_literal(str(parquet)))]
        csv_out = duck.run(script, "SELECT count(*) AS n FROM read_parquet(%s)" % duck.quote_literal(str(parquet)),
                           [conv], allow_writes=True)
        try:
            rows = int(csv_out.split("\n")[1])
        except (IndexError, ValueError):
            raise ConvertError("unexpected row count output from duckdb")
        if rows != w.rows:
            raise ConvertError("converted %d rows but wrote %d staged rows" % (rows, w.rows))
        _publish(parquet, out)
        return ConvertResult(rows=rows, dropped_columns=counts.dropped_tuple(), skipped_lines=counts.skipped)
    finally:
        for p in raw:
            try:
                os.unlink(str(p))
            except OSError:
                pass
        if conv is not None:
            shutil.rmtree(str(conv), ignore_errors=True)
