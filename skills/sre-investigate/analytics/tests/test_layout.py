from __future__ import annotations

import datetime as dt

import pytest

import gen_fixtures as gf
from s3logs import layout
from s3logs.awscli import Entry
from s3logs.config import Dataset
from s3logs.validate import Refused

UTC = dt.timezone.utc

CF = Dataset("cf", "cloudfront", "example-logs-bucket", "cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}")
CF_V2 = Dataset("cfv2", "cloudfront", "example-logs-bucket",
                "AWSLogs/111122223333/CloudFront/E2EXAMPLE/{yyyy}/{MM}/{dd}/{HH}/")
ALB = Dataset("alb", "alb", "example-logs-bucket",
              "AWSLogs/111122223333/elasticloadbalancing/us-east-1/{yyyy}/{MM}/{dd}/")
WAF = Dataset("waf", "waf", "example-logs-bucket",
              "AWSLogs/111122223333/WAFLogs/us-east-1/example-acl/{yyyy}/{MM}/{dd}/{HH}/")
DAY = dt.date(2026, 3, 9)
NEXT = dt.date(2026, 3, 10)


def entry(key):
    return Entry(key, 100, "abc")


def alb_entry(delivery_day, hh, mm, day_offset=0):
    end = dt.datetime(delivery_day.year, delivery_day.month, delivery_day.day) + dt.timedelta(
        days=day_offset, hours=hh, minutes=mm)
    return entry(gf.alb_key(delivery_day, end))


def cf_entry(day, hh):
    return entry(gf.cf_key(day, hh))


def keys(entries):
    return [e.key for e in entries]


def test_cloudfront_legacy_prefixes():
    got = layout.list_prefixes(CF, DAY)
    assert got == ["cf/E2EXAMPLE.2026-03-09-%02d" % h for h in range(24)]
    assert got[0] == "cf/E2EXAMPLE.2026-03-09-00" and got[23] == "cf/E2EXAMPLE.2026-03-09-23"


def test_cloudfront_v2_and_waf_hour_prefixes():
    assert layout.list_prefixes(CF_V2, DAY)[5] == "AWSLogs/111122223333/CloudFront/E2EXAMPLE/2026/03/09/05/"
    assert len(layout.list_prefixes(WAF, DAY)) == 24


def test_alb_prefix_is_day_dir():
    assert layout.list_prefixes(ALB, DAY) == [
        "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/"]


def test_cloudfront_file_time_hour():
    ft = layout.file_time(CF, gf.cf_key(DAY, 7))
    assert ft.start == dt.datetime(2026, 3, 9, 7, 0, tzinfo=UTC)
    assert ft.end == dt.datetime(2026, 3, 9, 8, 0, tzinfo=UTC)
    assert ft.start.utcoffset() == dt.timedelta(0)


def test_cloudfront_v2_file_time_from_path_hour():
    ft = layout.file_time(CF_V2, "AWSLogs/111122223333/CloudFront/E2EXAMPLE/2026/03/09/23/x_1.gz")
    assert (ft.start.hour, ft.end) == (23, dt.datetime(2026, 3, 10, 0, 0, tzinfo=UTC))


def test_alb_file_time_from_end_time():
    end = dt.datetime(2026, 3, 9, 23, 40)
    ft = layout.file_time(ALB, gf.alb_key(DAY, end))
    assert ft.start == dt.datetime(2026, 3, 9, 23, 35, tzinfo=UTC)
    assert ft.end == dt.datetime(2026, 3, 9, 23, 40, tzinfo=UTC)


def test_waf_file_time_minute():
    ft = layout.file_time(WAF, gf.waf_key(dt.datetime(2026, 3, 9, 19, 50)))
    assert ft.start == dt.datetime(2026, 3, 9, 19, 45, tzinfo=UTC)
    assert ft.end == dt.datetime(2026, 3, 9, 19, 50, tzinfo=UTC)


@pytest.mark.parametrize("ds,key", [
    (CF, "cf/E2EXAMPLE.not-a-date.abc.gz"),
    (CF, "cf/E2EXAMPLE.2026-13-09-00.abc.gz"),
    (CF, "other/E2EXAMPLE.2026-03-09-00.abc.gz"),
    (ALB, "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/readme.txt"),
    (ALB, "AWSLogs/x/y_20261340T9999Z_z.log.gz"),
])
def test_unparsable_file_time_is_none(ds, key):
    assert layout.file_time(ds, key) is None


def test_alb_slice_widens_into_next_day_dir():
    # Requests at 23:57 land in the file ending 00:00, which lives in the NEXT day's directory.
    listing = [
        alb_entry(DAY, 23, 50), alb_entry(DAY, 23, 55),
        alb_entry(NEXT, 0, 0), alb_entry(NEXT, 0, 5), alb_entry(NEXT, 0, 10),
    ]
    got = layout.select(ALB, listing, DAY, hours=(23, 23))
    names = keys(got)
    assert listing[2].key in names                 # ..._20260310T0000Z_...: 23:55-00:00
    assert listing[3].key in names                 # widen by one 5-minute unit
    assert listing[4].key not in names             # but nothing later
    assert listing[0].key in names and listing[1].key in names


def test_whole_day_widens_to_next_day_first_hour():
    listing = [cf_entry(DAY, h) for h in (0, 12, 23)] + [cf_entry(NEXT, h) for h in (0, 1)]
    got = layout.select(CF, listing, DAY)
    assert keys(got) == [e.key for e in listing[:4]]       # day + next day's hour 00
    assert listing[4].key not in keys(got)                  # hour 01 of the next day stays out


def test_whole_day_widens_alb_to_next_days_first_file():
    listing = [alb_entry(DAY, 0, 0), alb_entry(DAY, 0, 5), alb_entry(DAY, 12, 0),
               alb_entry(NEXT, 0, 0), alb_entry(NEXT, 0, 5), alb_entry(NEXT, 0, 10)]
    got = keys(layout.select(ALB, listing, DAY))
    assert listing[0].key not in got        # ends 00:00 on the day: covers the previous day
    assert listing[1].key in got and listing[2].key in got
    assert listing[3].key in got and listing[4].key in got
    assert listing[5].key not in got


def test_hour_range_inclusive():
    listing = [cf_entry(DAY, h) for h in range(8, 16)]
    got = keys(layout.select(CF, listing, DAY, hours=(10, 12)))
    # 10, 11, 12 inclusive, plus the widened hour 13; 9 and 14 stay out
    assert got == [cf_entry(DAY, h).key for h in (10, 11, 12, 13)]


def test_minute_range_start_inclusive_end_exclusive():
    listing = [alb_entry(DAY, 10, m) for m in (0, 5, 10, 15, 20)]
    got = keys(layout.select(ALB, listing, DAY, minutes=(10 * 60, 10 * 60 + 10)))
    # window [10:00, 10:10): files ending 10:05 and 10:10; widen takes 10:15; 10:00 ends at window start
    assert got == [listing[i].key for i in (1, 2, 3)]


def test_waf_minute_slice():
    listing = [entry(gf.waf_key(dt.datetime(2026, 3, 9, 19, m))) for m in (40, 45, 50, 55)]
    got = layout.select(WAF, listing, DAY, minutes=(19 * 60 + 45, 19 * 60 + 50))
    assert keys(got) == [listing[i].key for i in (2, 3)]    # 19:50 covers [19:45,19:50), 19:55 is the widen


def test_minute_range_to_end_of_day():
    listing = [alb_entry(DAY, 23, 55), alb_entry(NEXT, 0, 0), alb_entry(NEXT, 0, 5)]
    got = layout.select(ALB, listing, DAY, minutes=(23 * 60 + 55, 1440))
    # 23:55 ends where the window starts, so it is out; 00:00 closes the last minutes of the
    # day (next day's directory); 00:05 is the widen.
    assert keys(got) == [listing[1].key, listing[2].key]


def test_cloudfront_minute_slice_refused():
    with pytest.raises(Refused):
        layout.select(CF, [cf_entry(DAY, 1)], DAY, minutes=(60, 120))


def test_hours_and_minutes_together_refused():
    with pytest.raises(Refused):
        layout.select(ALB, [], DAY, hours=(1, 2), minutes=(60, 120))


def test_select_drops_unparsable_and_sorts_by_time():
    listing = [cf_entry(DAY, 5), entry("cf/junk.gz"), cf_entry(DAY, 3)]
    got = layout.select(CF, listing, DAY, hours=(0, 23))
    assert keys(got) == [cf_entry(DAY, 3).key, cf_entry(DAY, 5).key]


@pytest.mark.parametrize("key,expected", [
    ("cf/E2EXAMPLE.2026-03-09-00.abc.gz", False),
    ("AWSLogs/x/CloudFront/E2EXAMPLE/2026/03/09/00/part.json.gz", True),
    ("AWSLogs/x/CloudFront/E2EXAMPLE/2026/03/09/00/part.parquet", True),
    ("x/y.JSON", True),
])
def test_unsupported_format_cloudfront(key, expected):
    assert layout.is_unsupported_format(CF, key) is expected


def test_unsupported_format_only_for_cloudfront():
    assert layout.is_unsupported_format(WAF, "x/y.json.gz") is False
    assert layout.is_unsupported_format(ALB, "x/y.parquet") is False


@pytest.mark.parametrize("ds,key", [
    (ALB, "AWSLogs/x/y_00010101T0000Z_z.log.gz"),            # end - 5 min underflows year 1
    (WAF, "AWSLogs/x/y_00010101T0004Z_z.log.gz"),
    (CF, "cf/E2EXAMPLE.9999-12-31-23.abc.gz"),               # start + 1 h overflows year 9999
])
def test_overflowing_stamp_is_unparsable_not_a_crash(ds, key):
    assert layout.file_time(ds, key) is None


def test_valid_extreme_stamps_still_parse():
    ft = layout.file_time(ALB, "AWSLogs/x/y_99991231T2359Z_z.log.gz")
    assert ft.end == dt.datetime(9999, 12, 31, 23, 59, tzinfo=UTC)
    ft = layout.file_time(ALB, "AWSLogs/x/y_00010101T0005Z_z.log.gz")
    assert ft.start == dt.datetime(1, 1, 1, 0, 0, tzinfo=UTC)


def test_select_on_last_calendar_day_refuses_instead_of_crashing():
    listing = [entry("AWSLogs/x/y_99991231T2359Z_z.log.gz")]
    with pytest.raises(Refused):
        layout.select(ALB, listing, dt.date(9999, 12, 31))                     # day+1 does not exist
    got = layout.select(ALB, listing, dt.date(9999, 12, 31), minutes=(23 * 60, 23 * 60 + 59))
    assert keys(got) == [listing[0].key]                                       # widen overflow is tolerated
