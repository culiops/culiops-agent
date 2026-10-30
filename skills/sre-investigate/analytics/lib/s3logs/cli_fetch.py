"""logs-fetch <dataset> <day> [<H>|<H-H>|<HH:MM-HH:MM>] [--every N] [--max-files N]
                [--yes --run <run-id>] [--force]      and      logs-fetch --purge <run-id>

A dry run by default: it reads the inventory manifest, selects the slice (widened by one unit,
see layout.py), samples it, and prints what a real run would download and which caps it would
hit. Only `--yes --run <run-id>` downloads, and that spends money, so every step fails closed:

* an exclusive non-blocking flock on budgets/.fetch.lock is held for the whole real run (a
  second one is refused) so two fetches cannot both pass the cap check and overshoot it;
* before EACH batch budget.check runs again with that batch's bytes, so a cap reached
  part-way stops the fetch;
* objects come down through `s5cmd run` over a validated run file into a private batch dir
  under staging/ (0700), at most MAX_BATCH_FILES files or MAX_BATCH_BYTES per batch;
* every byte that arrived in the batch dir is charged (budget.charge), whether or not s5cmd
  succeeded and whether or not it matches the manifest: the ledger must never under-count. Only
  objects whose local size equals the manifest size are then converted to redacted Parquet
  (convert.to_parquet, which deletes the raw files) and recorded in fetched.jsonl. A file larger
  than listed means the object changed since the inventory: the batch is charged and the whole
  fetch stops (exit 3). A re-run skips recorded keys;
* the dataset dir data/<run>/<dataset>/ is kept 0555 (Parquet 0444) and made 0700 only while a
  batch is written; SIGINT/SIGTERM/SIGHUP clean up like `finally` (staging batch dir removed,
  dataset dir back to 0555) and exit 130/143/129. A signal that arrives while a batch is being
  charged and stored is held until that step ends (a second signal acts at once), so the ledger
  and fetched.jsonl are never left half written.

Exit codes: 0 ok, 2 refused (input, guard, cap, missing manifest, lock), 3 AWS/S3/s5cmd error or
a size mismatch, 4 conversion or DuckDB error.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import secrets
import signal
import stat
import sys
import threading
from pathlib import Path
from typing import Dict, Iterator, List, NamedTuple, Optional, Tuple

if __name__ == "__main__":
    # python3 -I drops the script dir from sys.path; add the lib dir that holds this package.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from s3logs import budget, config, convert, duck, layout, paths, redact, s5, validate  # noqa: E402
from s3logs.awscli import AwsError, Entry  # noqa: E402
from s3logs.cli_inventory import estimate_cost  # noqa: E402
from s3logs.validate import Refused  # noqa: E402

MIB = 1024 * 1024
MAX_BATCH_BYTES = 32 * MIB
MAX_BATCH_FILES = 200
MAX_MANIFEST_BYTES = 64 * MIB
MAX_EVERY = 100000
MAX_FILES_OPTION = 1000000
_UTC = dt.timezone.utc
_MANIFEST_NAME_RE = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})_([0-9]{4}-[0-9]{2}-[0-9]{2})\.json")
_PART_RE = re.compile(r"part-([0-9]{6})\.parquet")
_SIGNAL_CODES = ((signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129))
_ASK_LINE = "ask the user; an override needs their marker file plus --force"
_GAP_SENTENCE = "0 files — logging may be off or delivery late; this is a gap, not zero traffic"


class _Interrupted(BaseException):
    """A termination signal arrived; unwinds through the `finally` blocks, then main exits."""

    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


class _Signals:
    """Turn SIGINT/SIGTERM/SIGHUP into _Interrupted, except inside `critical()`, where the first
    signal is held until the section ends and a second one acts at once."""

    def __init__(self) -> None:
        self.depth = 0
        self.pending = None  # type: Optional[int]
        self._old = {}       # type: Dict[int, object]

    def install(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return
        codes = dict(_SIGNAL_CODES)

        def handler(signum, _frame):
            code = codes[signum]
            if self.depth > 0 and self.pending is None:
                self.pending = code
                return
            raise _Interrupted(code)

        for sig, _code in _SIGNAL_CODES:
            self._old[sig] = signal.signal(sig, handler)

    def restore(self) -> None:
        for sig, old in self._old.items():
            signal.signal(sig, old)
        self._old = {}

    @contextlib.contextmanager
    def critical(self) -> Iterator[None]:
        self.depth += 1
        try:
            yield
        finally:
            self.depth -= 1
            if self.depth == 0 and self.pending is not None:
                code, self.pending = self.pending, None
                raise _Interrupted(code)


# ---- small helpers -----------------------------------------------------------------------------

def _now() -> dt.datetime:
    return dt.datetime.now(_UTC)


def _iso(t: dt.datetime) -> str:
    return t.astimezone(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _out(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def _load_config() -> config.Config:
    cfg_path = paths.config_path()
    if not (cfg_path.exists() or cfg_path.is_symlink()):
        raise Refused("S3 log module: off (not configured)")
    try:
        return config.load(cfg_path)
    except config.ConfigError as e:
        raise Refused("S3 log module: off (config error: %s)" % e)


@contextlib.contextmanager
def _fetch_lock() -> Iterator[None]:
    """Exclusive, non-blocking. Held for a whole real fetch and for --purge."""
    paths.ensure_private_dirs()
    lock = paths.state_root() / "budgets" / ".fetch.lock"
    try:
        fd = os.open(str(lock), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError as e:
        raise Refused("cannot open %s: %s" % (lock, e.strerror or "error"))
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise Refused("another fetch is running (or a purge); wait for it to finish")
        yield
    finally:
        os.close(fd)        # closing releases the flock


# ---- manifests ---------------------------------------------------------------------------------

class Plan(NamedTuple):
    cfg: config.Config
    ds: config.Dataset
    day: dt.date
    slice_label: str
    hours: Optional[Tuple[int, int]]
    minutes: Optional[Tuple[int, int]]
    every: int
    max_files: Optional[int]
    matched: int                 # files in the slice before sampling and --max-files
    selected: List[Entry]        # after sampling and --max-files, in file-time order


def _needs_next_day(ds: config.Dataset, day: dt.date, hours, minutes) -> bool:
    """Does the widened slice reach into the next day's first unit (R4)?"""
    # A file starting within one file-width after the window end is taken too (widen). For the
    # 5-minute types the interval ending exactly at midnight sits in the NEXT day's directory
    # and starts 5 minutes before it, so the reach is two widths: any end after 23:50 needs
    # day+1. CloudFront files are hourly and start on the hour: one width.
    if ds.type == "cloudfront":
        reach = dt.timedelta(hours=1)
    else:
        reach = dt.timedelta(minutes=10)
    midnight = dt.datetime(day.year, day.month, day.day, tzinfo=_UTC)
    if hours is not None:
        end = midnight + dt.timedelta(hours=hours[1] + 1)
    elif minutes is not None:
        end = midnight + dt.timedelta(minutes=minutes[1])
    else:
        end = midnight + dt.timedelta(days=1)
    return end + reach > midnight + dt.timedelta(days=1)


def _read_manifest(path: Path, ds: config.Dataset, frm: dt.date, to: dt.date) -> Tuple[str, List[Entry]]:
    """Strictly parse one manifest. Any problem is a Refused naming the file."""
    name = path.name

    def bad(why: str) -> Refused:
        return Refused("manifest %s is not usable (%s); run logs-inventory %s %s %s again"
                       % (name, why, ds.name, frm.isoformat(), to.isoformat()))

    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        raise bad(e.strerror or "cannot open")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_size > MAX_MANIFEST_BYTES:
            raise bad("not a regular file of mine, or too large")
        with os.fdopen(fd, "rb", closefd=False) as f:
            raw = f.read(MAX_MANIFEST_BYTES + 1)
    finally:
        os.close(fd)
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        raise bad("not valid JSON")
    if not isinstance(doc, dict):
        raise bad("unexpected shape")
    for field, want in (("dataset", ds.name), ("type", ds.type), ("bucket", ds.bucket),
                        ("from", frm.isoformat()), ("to", to.isoformat())):
        if doc.get(field) != want:
            raise bad("%s does not match the configuration" % field)
    files = doc.get("files")
    if not isinstance(files, list):
        raise bad("no file list")
    entries = []
    for f in files:
        if not isinstance(f, dict):
            raise bad("unexpected file entry")
        key, size, etag = f.get("key"), f.get("size"), f.get("etag")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0 or not isinstance(etag, str):
            raise bad("unexpected file entry")
        try:
            validate.safe_key(key)
        except Refused:
            raise bad("it holds an unsafe key")
        entries.append(Entry(key, size, etag))
    listed = doc.get("listed_at")
    return (listed if isinstance(listed, str) else ""), entries


def _manifest_entries(ds: config.Dataset, needed: List[dt.date]) -> List[Entry]:
    """Entries of every manifest that covers a needed day; every needed day must be covered."""
    root = paths.state_root() / "manifests" / ds.name
    try:
        names = sorted(os.listdir(str(root)))
    except OSError:
        names = []
    covering = []  # type: List[Tuple[str, str, Path, dt.date, dt.date]]
    covered = set()
    for name in names:
        m = _MANIFEST_NAME_RE.fullmatch(name)
        if not m:
            continue
        try:
            frm, to = validate.day(m.group(1)), validate.day(m.group(2))
        except Refused:
            continue
        days = [d for d in needed if frm <= d <= to]
        if not days:
            continue
        covered.update(days)
        covering.append((name, "", root / name, frm, to))
    missing = [d for d in needed if d not in covered]
    if missing:
        last = needed[-1] if len(needed) > 1 else needed[0] + dt.timedelta(days=1)
        raise Refused("no manifest covers %s; run logs-inventory %s %s %s first"
                      % (missing[0].isoformat(), ds.name, needed[0].isoformat(), last.isoformat()))
    parsed = []
    for name, _x, path, frm, to in covering:
        listed, entries = _read_manifest(path, ds, frm, to)
        parsed.append((listed, name, entries))
    parsed.sort(key=lambda t: (t[0], t[1]))         # a later listing wins for the same key
    merged = {}  # type: Dict[str, Entry]
    for _l, _n, entries in parsed:
        for e in entries:
            merged[e.key] = e
    return list(merged.values())


def _plan(cfg: config.Config, ds: config.Dataset, day: dt.date, slice_arg: Optional[str],
          every: int, max_files: Optional[int]) -> Plan:
    hours = minutes = None
    if slice_arg is None:
        label = "all"
    else:
        label = slice_arg
        if ":" in slice_arg:
            minutes = validate.minute_range(slice_arg)
        else:
            hours = validate.hour_range(slice_arg)
    if minutes is not None and ds.type == "cloudfront":
        raise Refused("minute slices are not available for CloudFront (hour granularity only)")
    needed = [day]
    if _needs_next_day(ds, day, hours, minutes):
        needed.append(day + dt.timedelta(days=1))
    entries = _manifest_entries(ds, needed)
    matched = layout.select(ds, entries, day, hours, minutes)
    sampled = matched[::every]
    if max_files is not None:
        sampled = sampled[:max_files]
    return Plan(cfg, ds, day, label, hours, minutes, every, max_files, len(matched), sampled)


# ---- output ------------------------------------------------------------------------------------

def _mb(nbytes: float) -> str:
    return "%.1f" % (nbytes / MIB)


class Caps(NamedTuple):
    ok: bool
    over: List[str]
    override_used: bool
    line: str


def _caps(cfg: config.Config, planned: int, run_id: Optional[str], force: bool) -> Caps:
    now = _now()
    hr = budget.headroom(cfg, run_id, now)
    verdict = budget.check(cfg, planned, run_id, force, now)
    over = list(verdict.over)
    ok, used = verdict.ok, verdict.override_used
    if run_id is None and planned > cfg.run_max_mb * MIB and "run" not in over:
        over.append("run")          # a fresh run id starts at 0, so this fetch alone would pass the run cap
        ok, used = (force, force)
    over = [w for w in ("fetch", "run", "24h") if w in over]
    verdict_txt = "OK" if not over else "OVER (%s)" % ", ".join(over)
    line = "caps: fetch %s/%d MB  run %s %s/%d MB  24h %s/%d MB  → %s" % (
        _mb(planned), cfg.max_mb, run_id or "-", "%.1f" % (hr.run_mb_used + planned / MIB), cfg.run_max_mb,
        "%.1f" % (hr.day_mb_used + planned / MIB), cfg.day_max_mb, verdict_txt)
    return Caps(ok, over, used, line)


def _head(plan: Plan, files: List[Entry], planned: int, caps: Caps, dry: bool) -> List[str]:
    cfg = plan.cfg
    lines = []
    if dry:
        lines.append("DRY RUN — nothing downloaded")
    lines.append("dataset %s (%s)  slice %s %s (+1 widen)  every %d" % (
        plan.ds.name, plan.ds.type, plan.day.isoformat(), plan.slice_label, plan.every))
    lines.append("files %d  MB %s  est_cost %s" % (
        len(files), _mb(planned), estimate_cost(cfg.price_per_gb, cfg.price_per_1k_get, planned, len(files))))
    if plan.max_files is not None and len(plan.selected) < (plan.matched + plan.every - 1) // plan.every:
        lines.append("note: --max-files %d applied; %d files matched the slice (every %d)" % (
            plan.max_files, plan.matched, plan.every))
    lines.append(caps.line)
    if not caps.ok:
        lines.append(_ASK_LINE)
    elif caps.over:
        lines.append("override: the user's marker file is fresh and --force was given; the cap is being overridden")
    return lines


def _command(plan: Plan) -> str:
    parts = ["logs-fetch", plan.ds.name, plan.day.isoformat()]
    if plan.slice_label != "all":
        parts.append(plan.slice_label)
    if plan.every != 1:
        parts += ["--every", str(plan.every)]
    if plan.max_files is not None:
        parts += ["--max-files", str(plan.max_files)]
    return " ".join(parts)


# ---- dataset dir files -------------------------------------------------------------------------

def _read_meta(d: Path) -> Optional[dict]:
    p = d / "meta.json"
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as e:
        raise Refused("cannot read %s: %s" % (p, e.strerror or "error"))
    try:
        meta = json.loads(raw.decode("utf-8"))
        every = meta["sample_every"]
        if isinstance(every, bool) or not isinstance(every, int) or every < 1:
            raise ValueError("sample_every")
        if not isinstance(meta.get("day_slices", []), list):
            raise ValueError("day_slices")
    except (ValueError, KeyError, TypeError, RecursionError, UnicodeDecodeError):
        raise Refused("%s is corrupt; remove the run's data with logs-fetch --purge <run-id>" % (p,))
    return meta


def _read_fetched(d: Path) -> Dict[str, int]:
    p = d / "fetched.jsonl"
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise Refused("cannot read %s: %s" % (p, e.strerror or "error"))
    out = {}  # type: Dict[str, int]
    try:
        text = raw.decode("utf-8")
        if text and not text.endswith("\n"):
            raise ValueError("truncated")
        for line in text.split("\n")[:-1] if text else []:
            rec = json.loads(line)
            if not isinstance(rec, dict) or not isinstance(rec.get("key"), str):
                raise ValueError("entry")
            out[rec["key"]] = int(rec.get("size", 0))
    except (ValueError, TypeError, RecursionError, UnicodeDecodeError):
        raise Refused("%s is corrupt; remove the run's data with logs-fetch --purge <run-id>" % (p,))
    return out


def _append_fetched(d: Path, records: List[dict]) -> None:
    data = "".join(json.dumps(r, separators=(", ", ": ")) + "\n" for r in records).encode("utf-8")
    fd = os.open(str(d / "fetched.jsonl"), os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        before = os.fstat(fd).st_size
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
            os.fsync(fd)
        except BaseException:
            try:
                os.ftruncate(fd, before)         # no half-written record is left behind
            except OSError:
                pass
            raise
    finally:
        os.close(fd)


def _write_meta(d: Path, meta: dict) -> None:
    tmp = d / ".meta.json.tmp"
    try:
        os.unlink(str(tmp))
    except FileNotFoundError:
        pass
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(str(tmp), str(d / "meta.json"))


def _next_part(d: Path) -> int:
    best = 0
    for name in os.listdir(str(d)):
        m = _PART_RE.fullmatch(name)
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


def _existing_ds_dir(ds: config.Dataset, run_id: str) -> Optional[Path]:
    """The dataset dir if it exists (refusing a symlink or non-directory), else None."""
    d = paths.state_root() / "data" / run_id / ds.name
    try:
        st = os.lstat(str(d))
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise Refused("%s is not a plain directory; refusing to use it" % (d,))
    return d


@contextlib.contextmanager
def _writable(d: Path) -> Iterator[None]:
    os.chmod(str(d), 0o700)
    try:
        yield
    finally:
        os.chmod(str(d), 0o555)


def _clear_dir(d: Path) -> None:
    for name in os.listdir(str(d)):
        p = d / name
        if p.is_symlink() or not p.is_dir():
            os.unlink(str(p))
        else:
            paths.rmtree_force(p)


# ---- the real run ------------------------------------------------------------------------------

class _Totals:
    def __init__(self) -> None:
        self.files = 0
        self.verified = 0     # bytes of the files that were converted and recorded
        self.charged = 0      # bytes charged to the ledger this run (everything that arrived)
        self.rows = 0
        self.skipped_lines = 0
        self.dropped = []   # type: List[str]
        self.bad = []       # type: List[Entry]


def _batches(entries: List[Entry]) -> List[List[Entry]]:
    out = []   # type: List[List[Entry]]
    cur = []   # type: List[Entry]
    size = 0
    for e in entries:
        if cur and (len(cur) >= MAX_BATCH_FILES or size + e.size > MAX_BATCH_BYTES):
            out.append(cur)
            cur, size = [], 0
        cur.append(e)
        size += e.size
    if cur:
        out.append(cur)
    return out


def _summary(plan: Plan, d: Path, t: _Totals, skipped_present: int) -> List[str]:
    return [
        "fetched %d files %s MB verified; charged %s MB; skipped %d present; data: %s; sample: 1/%d" % (
            t.files, _mb(t.verified), _mb(t.charged), skipped_present, d, plan.every),
        "converted: rows %d; skipped lines %d; dropped columns %s" % (
            t.rows, t.skipped_lines, ",".join(t.dropped) if t.dropped else "none"),
    ]


def _slice_key(plan: Plan) -> str:
    return "%s %s" % (plan.day.isoformat(), plan.slice_label)


def _real(plan: Plan, run_id: str, force: bool, sigs: _Signals) -> int:
    cfg, ds = plan.cfg, plan.ds
    validate.run_id(run_id)
    if not plan.selected:
        _out(_GAP_SENTENCE)
        return 0
    salt = redact.load_or_create_salt()      # before anything is paid for; also creates the state dirs
    paths.ensure_private_dirs()
    with _fetch_lock():
        swept = paths.sweep_staging()
        if swept:
            _out("swept %d stale staging dirs" % len(swept))
        d = _existing_ds_dir(ds, run_id)
        present = {}  # type: Dict[str, int]
        if d is not None:
            meta = _read_meta(d)
            if meta is not None and meta["sample_every"] != plan.every:
                raise Refused("this run and dataset were fetched with sample 1/%d; use --every %d, "
                              "or a new run id" % (meta["sample_every"], meta["sample_every"]))
            present = _read_fetched(d)
        todo = [e for e in plan.selected if e.key not in present]
        skipped = len(plan.selected) - len(todo)
        planned = sum(e.size for e in todo)
        data_dir = d or (paths.state_root() / "data" / run_id / ds.name)
        totals = _Totals()
        if not todo:
            for line in _summary(plan, data_dir, totals, skipped):
                _out(line)
            return 0
        caps = _caps(cfg, planned, run_id, force)
        for line in _head(plan, todo, planned, caps, dry=False):
            _out(line)
        if not caps.ok:
            raise Refused("over the cap (%s); nothing was downloaded" % ", ".join(caps.over))

        run_dir = paths.private_subdir(paths.state_root() / "data", run_id)
        d = run_dir / ds.name
        batchdir = paths.state_root() / "staging" / secrets.token_hex(16)
        try:
            # The paths are fixed before anything is created, so `finally` can always seal the
            # dataset dir (0555) and remove the batch dir, whatever fails or interrupts below.
            d = paths.private_subdir(run_dir, ds.name)       # created or re-opened 0700
            os.chmod(str(d), 0o555)
            paths.private_subdir(paths.state_root() / "staging", batchdir.name)
            try:
                _fetch_batches(plan, todo, run_id, force, sigs, salt, d, batchdir, totals)
            except (Refused, AwsError, convert.ConvertError, duck.DuckError):
                for line in _summary(plan, d, totals, skipped):
                    _out(line)
                raise
            for line in _summary(plan, d, totals, skipped):
                _out(line)
            if totals.bad:
                shown = ", ".join(e.key for e in totals.bad[:10])
                more = " (and %d more)" % (len(totals.bad) - 10) if len(totals.bad) > 10 else ""
                raise AwsError("%d file(s) failed size verification (charged, not converted): %s%s"
                               % (len(totals.bad), shown, more),
                               "re-run the same command to retry them; if the objects changed since the "
                               "listing, run logs-inventory again first")
            return 0
        finally:
            with sigs.critical():
                try:
                    paths.rmtree_force(batchdir)
                finally:
                    _seal(d)


def _seal(d: Path) -> None:
    """Dataset dir back to 0555, never through a symlink and never failing if it was not created."""
    try:
        if stat.S_ISDIR(os.lstat(str(d)).st_mode):
            os.chmod(str(d), 0o555)
    except FileNotFoundError:
        pass


def _received(batchdir: Path, run_file: Path) -> Dict[str, int]:
    """Every regular file now in the batch dir (except the run file) -> its size on disk.
    This is what actually came down, whatever the manifest said and however s5cmd ended."""
    out = {}  # type: Dict[str, int]
    for name in os.listdir(str(batchdir)):
        if name == run_file.name:
            continue
        st = os.lstat(str(batchdir / name))
        if stat.S_ISREG(st.st_mode):
            out[name] = st.st_size
    return out


def _fetch_batches(plan: Plan, todo: List[Entry], run_id: str, force: bool, sigs: _Signals, salt: bytes,
                   d: Path, batchdir: Path, totals: _Totals) -> None:
    cfg, ds = plan.cfg, plan.ds
    batches = _batches(todo)
    for bi, batch in enumerate(batches, 1):
        planned = sum(e.size for e in batch)
        verdict = budget.check(cfg, planned, run_id, False, _now())
        if not verdict.ok and force:
            verdict = budget.check(cfg, planned, run_id, True, _now())   # the marker is needed only now
        if not verdict.ok:
            raise Refused("a cap was reached before batch %d/%d (%s); stopped. Data fetched so far is "
                          "kept; ask the user before going on" % (bi, len(batches), ", ".join(verdict.over)))
        _clear_dir(batchdir)
        text = s5.build_run_file(ds.bucket, [e.key for e in batch], str(batchdir))
        s5.validate_run_file(text, ds.bucket, str(batchdir))
        run_file = batchdir / ("batch-%06d.run" % bi)
        fd = os.open(str(run_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(text)
        run_err = None  # type: Optional[AwsError]
        try:
            s5.run(run_file, cfg.aws_profile, cfg.aws_region, str(batchdir), ds.bucket)
        except AwsError as e:
            run_err = e                   # files that did arrive are still charged (and converted) below
        except BaseException:
            # A refusal or an interrupt: whatever came down is paid for, but nothing is converted.
            with sigs.critical():
                got = sum(_received(batchdir, run_file).values())
                if got:
                    budget.charge(run_id, ds.name, got, _now())
                    totals.charged += got
            raise

        res = None
        # From here until the batch is charged, converted and recorded nothing may be skipped by a
        # first signal (it is held until this block ends): the ledger must never under-count.
        with sigs.critical():
            received = _received(batchdir, run_file)
            good = []  # type: List[Tuple[Entry, Path]]
            bad = []   # type: List[Entry]
            oversize = []  # type: List[Entry]
            for n, e in enumerate(batch, 1):
                name = "%06d.gz" % n
                if name not in received:
                    if run_err is None:
                        bad.append(e)          # s5cmd said ok but the file is not there
                    continue
                if received[name] == e.size:
                    good.append((e, batchdir / name))
                else:
                    bad.append(e)
                    if received[name] > e.size:
                        oversize.append(e)
            totals.bad.extend(bad)
            arrived = sum(received.values())
            verified = sum(e.size for e, _p in good)
            # Every byte that arrived is charged, verified or not (verification only decides
            # what is converted and recorded), so a re-run can never re-download for free.
            if arrived:
                budget.charge(run_id, ds.name, arrived, _now())
                totals.charged += arrived
            if good:
                with _writable(d):
                    part = "part-%06d.parquet" % _next_part(d)
                    res = convert.to_parquet(ds.type, [p for _e, p in good], d / part, cfg, salt)
                    ts = _iso(_now())
                    try:
                        _append_fetched(d, [{"key": e.key, "size": e.size, "part": part, "ts": ts}
                                            for e, _p in good])
                    except BaseException:
                        try:
                            os.unlink(str(d / part))     # rows without recorded keys would be duplicated
                        except OSError:
                            pass
                        raise
                    meta = _read_meta(d) or {"sample_every": plan.every, "dataset": ds.name, "type": ds.type,
                                             "day_slices": []}
                    key = _slice_key(plan)
                    if key not in meta["day_slices"]:
                        meta["day_slices"].append(key)
                    meta.update({"sample_every": plan.every, "dataset": ds.name, "type": ds.type})
                    _write_meta(d, meta)
                totals.files += len(good)
                totals.verified += verified
                totals.rows += res.rows
                totals.skipped_lines += res.skipped_lines
                for name in res.dropped_columns:
                    if name not in totals.dropped:
                        totals.dropped.append(name)
        _out("batch %d/%d: %d files %s MB verified, %s MB received; rows %d%s" % (
            bi, len(batches), len(good), _mb(verified), _mb(arrived), res.rows if res else 0,
            "; %d failed size verification" % len(bad) if bad else ""))
        _clear_dir(batchdir)
        if oversize:
            shown = ", ".join(e.key for e in oversize[:5])
            raise AwsError("objects changed since the listing (%d larger than listed: %s); stopped after "
                           "charging what arrived" % (len(oversize), shown),
                           "run logs-inventory again, then re-run")
        if run_err is not None:
            raise run_err


# ---- purge ------------------------------------------------------------------------------------

def _purge(run_id: str) -> int:
    validate.run_id(run_id)
    root = paths.state_root()
    if not root.exists() and not root.is_symlink():
        _out("nothing to purge: no logs state exists")
        return 0
    with _fetch_lock():
        removed = []   # type: List[str]
        target = root / "data" / run_id
        try:
            st = os.lstat(str(target))
        except FileNotFoundError:
            st = None
        if st is not None:
            paths.rmtree_force(target)
            removed.append(str(target))
        for name in paths.sweep_staging():
            removed.append(str(root / "staging" / name))
    if not removed:
        _out("nothing to purge for %s (no data and no stale staging)" % run_id)
    for p in removed:
        _out("removed: %s" % p)
    _out("ledger kept: downloads already charged still count toward the caps")
    return 0


# ---- entry point -------------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused(message)


def _parser() -> _Parser:
    p = _Parser(prog="logs-fetch", allow_abbrev=False,
                description="Dry-run or download an S3 log slice into redacted Parquet; --purge removes a run.")
    p.add_argument("dataset", nargs="?")
    p.add_argument("day", nargs="?")
    p.add_argument("slice", nargs="?", help="H, H-H or HH:MM-HH:MM (UTC); default the whole day")
    p.add_argument("--every", default=None)
    p.add_argument("--max-files", dest="max_files", default=None)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--run", default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--purge", default=None, metavar="RUN_ID")
    return p


def run_cli(argv: Optional[List[str]], sigs: _Signals) -> int:
    args = _parser().parse_args(argv)
    if args.purge is not None:
        if (args.dataset or args.day or args.slice or args.every or args.max_files or args.yes
                or args.run or args.force):
            raise Refused("--purge takes only a run id")
        return _purge(args.purge)
    if args.dataset is None or args.day is None:
        raise Refused("usage: logs-fetch <dataset> <day> [<H>|<H-H>|<HH:MM-HH:MM>] [--every N] [--max-files N] "
                      "[--yes --run <run-id>] [--force]  |  logs-fetch --purge <run-id>")
    dataset = validate.dataset_name(args.dataset)
    day = validate.day(args.day)
    every = validate.pos_int(args.every, "--every", MAX_EVERY) if args.every is not None else 1
    max_files = validate.pos_int(args.max_files, "--max-files", MAX_FILES_OPTION) if args.max_files is not None else None
    if args.yes != (args.run is not None):
        raise Refused("--yes and --run <run-id> go together: a real download needs both")
    run_id = validate.run_id(args.run) if args.run is not None else None
    cfg = _load_config()
    ds = cfg.datasets.get(dataset)
    if ds is None:
        raise Refused("unknown dataset %r (configured: %s)" % (dataset, ", ".join(cfg.datasets) or "none"))
    plan = _plan(cfg, ds, day, args.slice, every, max_files)
    if run_id is not None:
        return _real(plan, run_id, args.force, sigs)

    planned = sum(e.size for e in plan.selected)
    caps = _caps(cfg, planned, None, args.force)
    for line in _head(plan, plan.selected, planned, caps, dry=True):
        _out(line)
    if not plan.selected:
        _out(_GAP_SENTENCE)
    _out("to run: %s --yes --run <run-id>" % _command(plan))
    if not caps.ok:
        sys.stderr.write("refused: over the cap (%s)\n" % ", ".join(caps.over))
        return 2
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    sigs = _Signals()
    sigs.install()
    try:
        return run_cli(argv, sigs)
    except _Interrupted as e:
        sys.stderr.write("interrupted; cleaned up\n")
        return e.code
    except Refused as e:
        sys.stderr.write("refused: %s\n" % e)
        return 2
    except AwsError as e:
        sys.stderr.write("aws error: %s\n" % e.msg)
        if e.hint:
            sys.stderr.write("%s\n" % e.hint)
        return 3
    except convert.ConvertError as e:
        sys.stderr.write("conversion failed (exit 4): %s\n" % e)
        return 4
    except duck.DuckError as e:
        sys.stderr.write("conversion failed, duckdb error (exit 4): %s\n" % e.msg)
        return 4
    except OSError as e:
        sys.stderr.write("refused: %s\n" % (e.strerror or e))
        return 2
    finally:
        sigs.restore()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="backslashreplace")   # type: ignore[attr-defined]
        sys.stderr.reconfigure(errors="backslashreplace")   # type: ignore[attr-defined]
    except AttributeError:
        pass
    sys.exit(main(sys.argv[1:]))
