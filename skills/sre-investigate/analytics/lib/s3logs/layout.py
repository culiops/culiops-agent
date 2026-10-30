"""Where log files live in S3, and which time each file covers.

A dataset URI is a time template (see config.py): {yyyy} {MM} {dd} are required and
{HH} is optional. Expanding it per day (or per hour when {HH} is present) gives the
LIST prefixes. The layouts this module knows, with the AWS documentation for each:

* ALB access logs: <prefix>/AWSLogs/<acct>/elasticloadbalancing/<region>/yyyy/mm/dd/
  <acct>_elasticloadbalancing_<region>_app.<lb-id>_<end-time>_<ip>_<rand>.log.gz
  The date directory is the DELIVERY date, and <end-time> (YYYYMMDDTHHMMZ) closes a
  5-minute interval, so the file ending 00:00 holds 23:55-00:00 of the previous day and
  sits in the next day's directory.
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
* AWS WAF logs straight to S3: <prefix>/AWSLogs/<acct>/WAFLogs/<region>/<acl>/yyyy/MM/dd/HH/mm/
  <acct>_waflogs_<region>_<acl>_<timestamp>_<hash>.log.gz, published every 5 minutes,
  each file holding the previous 5 minutes (so the timestamp is the interval end).
  https://docs.aws.amazon.com/waf/latest/developerguide/logging-s3.html
* CloudFront standard logging (legacy): <prefix>/<DIST>.YYYY-MM-DD-HH.<unique>.gz, UTC,
  hour granularity.
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging-legacy-s3.html
* CloudFront standard logging (v2): the object path is chosen by the user (hive-style or
  AWSLogs/.../yyyy/MM/dd/HH/); only the W3C text output is supported here, JSON and
  Parquet are reported as a gap.
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html

Time of a file, in order: for ALB and WAF the end-time stamp in the file name (the file
covers [end - 5 min, end)); otherwise the {HH} directory of the template (the file
covers that hour). CloudFront has hour granularity only.

Selection takes every file that overlaps the requested window, then WIDENS by one
unit: a file that begins within one file-width after the window ends is taken too.
Late delivery puts records in the next file, so a slice always carries one file more
at the end (the next hour; for ALB and WAF the next 5 minutes, which may sit in the
next day's directory). A whole-day slice therefore reaches into the next day's first
unit, so a fetch needs a manifest that covers day+1. Queries then filter on the
record's own time.
"""
from __future__ import annotations

import datetime as dt
import functools
import re
from typing import List, NamedTuple, Optional, Sequence, Tuple

from s3logs.awscli import Entry
from s3logs.config import Dataset
from s3logs.validate import Refused

UTC = dt.timezone.utc
_INTERVAL = dt.timedelta(minutes=5)
_NAME_TS_RE = re.compile(r"_([0-9]{8})T([0-9]{4})Z(?:_|\.)")
_TOKEN_RE = re.compile(r"\{(yyyy|MM|dd|HH)\}")
_WIDTHS = {"yyyy": 4, "MM": 2, "dd": 2, "HH": 2}
_UNSUPPORTED_SUFFIXES = (".json", ".json.gz", ".parquet")


class FileTime(NamedTuple):
    start: dt.datetime   # inclusive, UTC-aware
    end: dt.datetime     # exclusive, UTC-aware


def _expand(template: str, day: dt.date, hour: Optional[int]) -> str:
    values = {"yyyy": "%04d" % day.year, "MM": "%02d" % day.month, "dd": "%02d" % day.day,
              "HH": "%02d" % hour if hour is not None else ""}
    return _TOKEN_RE.sub(lambda m: values[m.group(1)], template)


def list_prefixes(ds: Dataset, day: dt.date) -> List[str]:
    """LIST prefixes for one day: one per hour when the template has {HH}, else one."""
    if "{HH}" in ds.template:
        return [_expand(ds.template, day, h) for h in range(24)]
    return [_expand(ds.template, day, None)]


@functools.lru_cache(maxsize=32)
def _template_regex(template: str):
    """Regex matching a key's leading template part, capturing yyyy/MM/dd/HH."""
    out, pos, seen = [], 0, set()
    for m in _TOKEN_RE.finditer(template):
        out.append(re.escape(template[pos:m.start()]))
        name = m.group(1)
        if name in seen:
            out.append("(?P=%s)" % name)
        else:
            seen.add(name)
            out.append("(?P<%s>[0-9]{%d})" % (name, _WIDTHS[name]))
        pos = m.end()
    out.append(re.escape(template[pos:]))
    return re.compile("".join(out))


def _utc(y: int, mo: int, d: int, h: int = 0, mi: int = 0) -> Optional[dt.datetime]:
    try:
        return dt.datetime(y, mo, d, h, mi, tzinfo=UTC)
    except ValueError:
        return None


def file_time(ds: Dataset, key: str) -> Optional[FileTime]:
    """The UTC interval a file covers, or None when it cannot be told from its key."""
    if ds.type in ("alb", "waf"):
        m = _NAME_TS_RE.search(key.rsplit("/", 1)[-1])
        if m:
            s = m.group(1)
            end = _utc(int(s[0:4]), int(s[4:6]), int(s[6:8]), int(m.group(2)[0:2]), int(m.group(2)[2:4]))
            return FileTime(end - _INTERVAL, end) if end else None
    if "{HH}" not in ds.template:
        return None
    m = _template_regex(ds.template).match(key)
    if not m:
        return None
    start = _utc(int(m.group("yyyy")), int(m.group("MM")), int(m.group("dd")), int(m.group("HH")))
    if start is None:
        return None
    return FileTime(start, start + dt.timedelta(hours=1))


def is_unsupported_format(ds: Dataset, key: str) -> bool:
    """CloudFront v2 JSON and Parquet output cannot be queried; they are a reported gap."""
    return ds.type == "cloudfront" and key.lower().endswith(_UNSUPPORTED_SUFFIXES)


def select(ds: Dataset, entries: Sequence[Entry], day: dt.date,
           hours: Optional[Tuple[int, int]] = None,
           minutes: Optional[Tuple[int, int]] = None) -> List[Entry]:
    """Entries whose interval overlaps the requested slice of `day`, widened by one unit.

    hours   = (first, last) inclusive, as validate.hour_range returns.
    minutes = (start, end) in minutes since midnight, start inclusive, end exclusive
              (end may be 1440), as validate.minute_range returns.
    Neither = the whole day. Entries whose time cannot be told are left out.
    Result is ordered by file start time, then key.
    """
    if hours is not None and minutes is not None:
        raise Refused("give an hour range or a minute range, not both")
    if minutes is not None and ds.type == "cloudfront":
        raise Refused("minute slices are not available for CloudFront (hour granularity only)")
    midnight = dt.datetime(day.year, day.month, day.day, tzinfo=UTC)
    if hours is not None:
        w_start = midnight + dt.timedelta(hours=hours[0])
        w_end = midnight + dt.timedelta(hours=hours[1] + 1)
    elif minutes is not None:
        w_start = midnight + dt.timedelta(minutes=minutes[0])
        w_end = midnight + dt.timedelta(minutes=minutes[1])
    else:
        w_start, w_end = midnight, midnight + dt.timedelta(days=1)
    picked = []
    for e in entries:
        ft = file_time(ds, e.key)
        if ft is None:
            continue
        # Widen by one unit of this file's own width: a file starting right after the
        # window (within one file-width) is taken too.
        if ft.end > w_start and ft.start < w_end + (ft.end - ft.start):
            picked.append((ft.start, e.key, e))
    picked.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in picked]
