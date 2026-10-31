from __future__ import annotations

import datetime

import pytest

from s3logs import validate
from s3logs.validate import Refused


def test_run_id():
    assert validate.run_id("orders-api-prod-20261030-1405") == "orders-api-prod-20261030-1405"
    for bad in ["../x", "A-20261030-1405", "x-2026-1030", "", "-x-20261030-1405",
                "x-20261030-1405\n", "a/b-20261030-1405"]:
        with pytest.raises(Refused):
            validate.run_id(bad)


def test_safe_key_accepts_log_keys():
    for ok in ["cf/E2EXAMPLE.2026-10-30-14.abc.gz",
               "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/10/30/x_20261030T1405Z_192.0.2.1_ab.log.gz",
               "waf/year=2026/month=10/", "a_b-c.d"]:
        assert validate.safe_key(ok) == ok


def test_safe_key():
    bad = ["..", "a/../b", "/abs", "a b", "a\tb", "a\nb", "a\x00b", "a\x7fb", "", "a/./b"]
    bad += ["a" + c + "b" for c in ";|&$`\\\"'<>*?[]{}"]
    for key in bad:
        with pytest.raises(Refused):
            validate.safe_key(key)


def test_dataset_name():
    assert validate.dataset_name("cdn") == "cdn"
    assert validate.dataset_name("alb-main_2") == "alb-main_2"
    for bad in ["", "CDN", "-x", "a b", "../x", "a" * 33, "x/y"]:
        with pytest.raises(Refused):
            validate.dataset_name(bad)


def test_day():
    assert validate.day("2026-10-30") == datetime.date(2026, 10, 30)
    for bad in ["2026-13-01", "2026-02-30", "26-10-30", "2026-1-3", "2026-10-30\n", "x"]:
        with pytest.raises(Refused):
            validate.day(bad)


def test_hour_range():
    assert validate.hour_range("5") == (5, 5)
    assert validate.hour_range("05") == (5, 5)
    assert validate.hour_range("3-7") == (3, 7)
    assert validate.hour_range("0-23") == (0, 23)
    for bad in ["24", "-1", "7-3", "a", "1-2-3", "", "1-24"]:
        with pytest.raises(Refused):
            validate.hour_range(bad)


def test_minute_range():
    # minutes since midnight, start inclusive, end exclusive
    assert validate.minute_range("14:05-14:30") == (14 * 60 + 5, 14 * 60 + 30)
    assert validate.minute_range("23:00-24:00") == (23 * 60, 1440)
    for bad in ["14:30-14:05", "14:05-14:05", "25:00-26:00", "14:60-15:00", "1405-1430",
                "14:05", "24:00-24:00", "24:01-24:02"]:
        with pytest.raises(Refused):
            validate.minute_range(bad)


def test_pos_int():
    assert validate.pos_int("200") == 200
    for bad in ["0", "-1", "1.5", "abc", "", " 5", "5 ", "+5", "1e3"]:
        with pytest.raises(Refused):
            validate.pos_int(bad)
    with pytest.raises(Refused):
        validate.pos_int("11", maximum=10)


def test_bucket():
    assert validate.bucket("example-logs-bucket") == "example-logs-bucket"
    assert validate.bucket("logs.example.com") == "logs.example.com"
    for bad in ["ab", "UPPER", "-lead", "trail-", "a..b", "a b", "a/b", "x" * 64, "s3://b"]:
        with pytest.raises(Refused):
            validate.bucket(bad)
