"""logs-inventory <dataset> <from-day> <to-day>: list S3, count, estimate, write a manifest.

Exit codes: 0 ok, 2 refused (bad input, module off), 3 AWS/S3 error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Dict, List, Optional

if __name__ == "__main__":
    # python3 -I drops the script dir from sys.path; add the lib dir that holds this package.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from s3logs import awscli, config, layout, paths, validate  # noqa: E402
from s3logs.validate import Refused  # noqa: E402

MAX_DAYS = 92
GAP_SENTENCE = "0 files — logging may be off or delivery late; this is a gap, not zero traffic"
_MIB = 1024 * 1024
_GIB = Decimal(1024 ** 3)


def estimate_cost(price_per_gb: Optional[Decimal], price_per_1k_get: Optional[Decimal],
                  nbytes: int, nfiles: int) -> str:
    """GB * price_per_gb + files / 1000 * price_per_1k_get, GB = bytes / 1024^3, 4 decimals."""
    if price_per_gb is None or price_per_1k_get is None:
        return "n/a"
    cost = Decimal(nbytes) / _GIB * price_per_gb + Decimal(nfiles) / 1000 * price_per_1k_get
    return "$" + str(cost.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_manifest(path: Path, doc: dict) -> None:
    """Atomic write, mode 0600, into a private directory."""
    paths.ensure_private_dirs()
    paths.private_subdir(paths.state_root() / "manifests", path.parent.name)
    tmp = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(doc, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise


def _load_config() -> config.Config:
    cfg_path = paths.config_path()
    if not (cfg_path.exists() or cfg_path.is_symlink()):
        raise Refused("S3 log module: off (not configured)")
    try:
        return config.load(cfg_path)
    except config.ConfigError as e:
        raise Refused("S3 log module: off (config error: %s)" % e)


def run(dataset: str, day_from: dt.date, day_to: dt.date) -> int:
    if day_to < day_from:
        raise Refused("to-day is before from-day")
    ndays = (day_to - day_from).days + 1
    if ndays > MAX_DAYS:
        raise Refused("range of %d days is over the %d-day limit; split it" % (ndays, MAX_DAYS))
    cfg = _load_config()
    ds = cfg.datasets.get(dataset)
    if ds is None:
        raise Refused("unknown dataset %r (configured: %s)" % (dataset, ", ".join(cfg.datasets) or "none"))

    days = [day_from + dt.timedelta(days=i) for i in range(ndays)]
    files: List[dict] = []
    per_day: Dict[dt.date, Dict[str, int]] = {}
    seen = set()
    unsafe = unparsed = unsupported = 0
    for d in days:
        tally = per_day.setdefault(d, {"listed": 0, "files": 0, "bytes": 0})
        for prefix in layout.list_prefixes(ds, d):
            for e in awscli.list_objects(ds.bucket, prefix, cfg.aws_profile, cfg.aws_region):
                tally["listed"] += 1
                try:
                    validate.safe_key(e.key)
                except Refused:
                    unsafe += 1          # counted only: hostile key text is never kept or printed
                    continue
                if e.key in seen:
                    continue
                seen.add(e.key)
                if layout.is_unsupported_format(ds, e.key):
                    unsupported += 1
                    continue
                ft = layout.file_time(ds, e.key) if layout.in_day(ds, e.key, d) else None
                if ft is None:
                    unparsed += 1
                    continue
                tally["files"] += 1
                tally["bytes"] += e.size
                files.append({"key": e.key, "size": e.size, "etag": e.etag,
                              "start": _iso(ft.start), "end": _iso(ft.end)})
    files.sort(key=lambda f: (f["start"], f["key"]))

    now = dt.datetime.now(dt.timezone.utc)
    mpath = paths.manifest_path(ds.name, day_from.isoformat(), day_to.isoformat())
    _write_manifest(mpath, {
        "dataset": ds.name, "type": ds.type, "bucket": ds.bucket,
        "from": day_from.isoformat(), "to": day_to.isoformat(), "listed_at": _iso(now),
        "files": files, "skipped_unsafe": unsafe, "skipped_unparsed": unparsed,
        "skipped_unsupported": unsupported, "unsupported_format": unsupported > 0,
        "days": {d.isoformat(): {"listed": t["listed"], "files": t["files"], "bytes": t["bytes"]}
                 for d, t in per_day.items()},
    })

    out = ["%-10s  %8s  %10s  %9s" % ("day", "files", "MB", "est_cost")]
    tot_files = tot_bytes = 0
    for d in days:
        t = per_day[d]
        tot_files += t["files"]
        tot_bytes += t["bytes"]
        out.append("%-10s  %8d  %10.2f  %9s" % (
            d.isoformat(), t["files"], t["bytes"] / _MIB,
            estimate_cost(cfg.price_per_gb, cfg.price_per_1k_get, t["bytes"], t["files"])))
    out.append("%-10s  %8d  %10.2f  %9s" % (
        "total", tot_files, tot_bytes / _MIB,
        estimate_cost(cfg.price_per_gb, cfg.price_per_1k_get, tot_bytes, tot_files)))
    for d in days:
        if per_day[d]["listed"] == 0:
            out.append("%s: %s" % (d.isoformat(), GAP_SENTENCE))
    if unsupported:
        out.append("format unsupported (v2 JSON/Parquet): %d objects left out; this is a gap, "
                   "those logs cannot be queried" % unsupported)
    if unsafe:
        out.append("skipped %d objects with unsafe key names (not listed, never fetched)" % unsafe)
    if unparsed:
        out.append("skipped %d objects whose file time could not be read from the key" % unparsed)
    out.append("manifest: %s" % mpath)
    sys.stdout.write("\n".join(out) + "\n")
    return 0


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused(message)


def main(argv: Optional[List[str]] = None) -> int:
    p = _Parser(prog="logs-inventory", description="List an S3 log dataset for a day range and write a manifest.")
    p.add_argument("dataset")
    p.add_argument("from_day")
    p.add_argument("to_day")
    try:
        args = p.parse_args(argv)
        dataset = validate.dataset_name(args.dataset)
        return run(dataset, validate.day(args.from_day), validate.day(args.to_day))
    except Refused as e:
        sys.stderr.write("refused: %s\n" % e)
        return 2
    except awscli.AwsError as e:
        sys.stderr.write("aws error: %s\n" % e.msg)
        if e.hint:
            sys.stderr.write("%s\n" % e.hint)
        return 3
    except OSError as e:
        sys.stderr.write("refused: cannot write the manifest: %s\n" % (e.strerror or e))
        return 2


if __name__ == "__main__":
    sys.exit(main())
