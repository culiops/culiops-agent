"""Argument validators. Every failure raises Refused; the CLIs map it to exit 2."""
from __future__ import annotations

import datetime
import re
from typing import Optional, Tuple


class Refused(Exception):
    """An input or guard was rejected. CLIs print the message and exit 2."""


_DATASET_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
_DAY_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_HOUR_RE = re.compile(r"([0-9]{1,2})(?:-([0-9]{1,2}))?")
_MINUTE_RE = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")
_INT_RE = re.compile(r"[0-9]{1,15}")
_RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,80}-[0-9]{8}-[0-9]{4}")
_BUCKET_RE = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")
# The deliberately small alphabet of characters a key may contain. Keys written by
# CloudFront, ALB and WAF delivery stay inside it; anything else (whitespace,
# control characters, shell or s5cmd wildcard metacharacters, non-ASCII) is refused.
_KEY_RE = re.compile(r"[A-Za-z0-9._/=@+:,-]+")
_MAX_KEY_LEN = 1024


def dataset_name(s: str) -> str:
    if not isinstance(s, str) or not _DATASET_RE.fullmatch(s):
        raise Refused("invalid dataset name %r (lowercase letters, digits, - and _; 1-32 chars)" % (s,))
    return s


def day(s: str) -> datetime.date:
    m = _DAY_RE.fullmatch(s) if isinstance(s, str) else None
    if not m:
        raise Refused("invalid day %r (expected YYYY-MM-DD)" % (s,))
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        raise Refused("invalid day %r (not a calendar date)" % (s,))


def hour_range(s: str) -> Tuple[int, int]:
    """'H' or 'H-H' -> (first, last), both inclusive, 0..23."""
    m = _HOUR_RE.fullmatch(s) if isinstance(s, str) else None
    if not m:
        raise Refused("invalid hour range %r (expected H or H-H)" % (s,))
    first = int(m.group(1))
    last = int(m.group(2)) if m.group(2) is not None else first
    if first > 23 or last > 23:
        raise Refused("invalid hour range %r (hours are 0-23)" % (s,))
    if first > last:
        raise Refused("invalid hour range %r (start after end)" % (s,))
    return first, last


def minute_range(s: str) -> Tuple[int, int]:
    """'HH:MM-HH:MM' -> (start, end) in minutes since midnight.

    Start is inclusive and end exclusive. The end may be 24:00 (= 1440).
    """
    m = _MINUTE_RE.fullmatch(s) if isinstance(s, str) else None
    if not m:
        raise Refused("invalid minute range %r (expected HH:MM-HH:MM)" % (s,))
    h1, m1, h2, m2 = (int(x) for x in m.groups())
    if h1 > 23 or m1 > 59 or m2 > 59 or h2 > 24 or (h2 == 24 and m2 != 0):
        raise Refused("invalid minute range %r (out of range)" % (s,))
    start, end = h1 * 60 + m1, h2 * 60 + m2
    if start >= end:
        raise Refused("invalid minute range %r (start must be before end)" % (s,))
    return start, end


def pos_int(s: str, name: str = "value", maximum: Optional[int] = None) -> int:
    if not isinstance(s, str) or not _INT_RE.fullmatch(s):
        raise Refused("invalid %s %r (expected a positive integer)" % (name, s))
    n = int(s)
    if n <= 0:
        raise Refused("invalid %s %r (expected a positive integer)" % (name, s))
    if maximum is not None and n > maximum:
        raise Refused("invalid %s %r (maximum is %d)" % (name, s, maximum))
    return n


def run_id(s: str) -> str:
    """<svc>-<env>-<YYYYMMDD-HHMM>, as the sre-investigate output directories are named."""
    if not isinstance(s, str) or not _RUN_ID_RE.fullmatch(s):
        raise Refused("invalid run id %r (expected <service>-<env>-<YYYYMMDD>-<HHMM>, lowercase)" % (s,))
    return s


def bucket(s: str) -> str:
    if (not isinstance(s, str) or not _BUCKET_RE.fullmatch(s)
            or ".." in s or ".-" in s or "-." in s):
        raise Refused("invalid bucket name %r" % (s,))
    return s


def safe_key(s: str) -> str:
    """An S3 key (or prefix) that is safe to put in an s5cmd run file and a path."""
    if not isinstance(s, str) or not s:
        raise Refused("empty key")
    if len(s) > _MAX_KEY_LEN:
        raise Refused("key too long")
    if not _KEY_RE.fullmatch(s):
        raise Refused("unsafe key %r (characters outside A-Z a-z 0-9 . _ / = @ + : , -)" % (s,))
    if s.startswith("/"):
        raise Refused("unsafe key %r (leading slash)" % (s,))
    if any(seg in ("..", ".") for seg in s.split("/")):
        raise Refused("unsafe key %r (dot segment)" % (s,))
    return s
