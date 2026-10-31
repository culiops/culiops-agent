from __future__ import annotations

import datetime as dt
import json
import os
import subprocess

import pytest

import gen_fixtures as gf
from conftest import BIN

BUCKET = "example-logs-bucket"
ALB_TEMPLATE = "AWSLogs/111122223333/elasticloadbalancing/us-east-1/{yyyy}/{MM}/{dd}/"
CF_TEMPLATE = "cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}"
DAY = dt.date(2026, 3, 9)
NEXT = dt.date(2026, 3, 10)
GAP = "0 files — logging may be off or delivery late; this is a gap, not zero traffic"


def write_config(home, extra="", profile="sre-read"):
    d = home / ".config/culiops/sre-investigate"
    d.mkdir(parents=True, exist_ok=True)
    lines = []
    if profile:
        lines.append("AWS_PROFILE=%s" % profile)
    lines += [
        "DATASET_cf=cloudfront:s3://%s/%s" % (BUCKET, CF_TEMPLATE),
        "DATASET_alb=alb:s3://%s/%s" % (BUCKET, ALB_TEMPLATE),
        "DATASET_waf=waf:s3://%s/AWSLogs/111122223333/WAFLogs/us-east-1/example-acl/{yyyy}/{MM}/{dd}/{HH}/" % BUCKET,
    ]
    (d / "logs.env").write_text("\n".join(lines) + "\n" + extra)


def run(*args):
    return subprocess.run([str(BIN / "logs-inventory")] + list(args), capture_output=True, text=True,
                          env=os.environ.copy(), timeout=60)


def manifest_path(home, ds, frm, to):
    return home / ".local/share/culiops/sre-investigate/manifests" / ds / ("%s_%s.json" % (frm, to))


@pytest.fixture
def env(home, fake_s3):
    write_config(home)
    fake_s3.bucket(BUCKET)
    return fake_s3


def rows(out):
    return [l.split() for l in out.splitlines()]


def test_inventory_lists_day_and_writes_manifest(home, env):
    gf.make(env.root, "alb", DAY, hours=[0, 1], minutes=(0, 30))      # 4 files
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[0].split()[:4] == ["day", "files", "MB", "est_cost"]
    day_row = [l.split() for l in lines if l.startswith("2026-03-09")][0]
    assert day_row[1] == "4"
    total = [l.split() for l in lines if l.startswith("total")][0]
    assert total[1] == "4"
    mpath = manifest_path(home, "alb", "2026-03-09", "2026-03-09")
    assert lines[-1] == "manifest: %s" % mpath
    m = json.loads(mpath.read_text())
    assert m["dataset"] == "alb" and m["type"] == "alb" and m["bucket"] == BUCKET
    assert (m["from"], m["to"]) == ("2026-03-09", "2026-03-09")
    assert m["skipped_unsafe"] == 0 and m["skipped_unparsed"] == 0 and m["unsupported_format"] is False
    assert m["listed_at"].endswith("Z")
    assert len(m["files"]) == 4
    f0 = m["files"][0]
    assert set(f0) == {"key", "size", "etag", "start", "end"}
    assert f0["start"] == "2026-03-09T23:55:00Z" or f0["start"].endswith(":00Z")
    assert f0["end"] > f0["start"]
    assert oct(mpath.stat().st_mode & 0o777) == "0o600"


def test_inventory_hourly_template_lists_once_per_day(home, env):
    gf.make(env.root, "cloudfront", DAY, hours=[3, 4, 5])
    r = run("cf", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    assert len(env.calls()) == 1                        # one LIST for the whole day, not 24
    r = run("cf", "2026-03-09", "2026-03-11")
    assert r.returncode == 0, r.stderr
    assert len(env.calls()) == 1 + 3                    # one per day
    r = run("waf", "2026-03-09", "2026-03-10")
    assert r.returncode == 0, r.stderr
    assert len(env.calls()) == 1 + 3 + 2
    assert all(c[:2] == ["s3api", "list-objects-v2"] for c in env.calls())
    m = json.loads(manifest_path(home, "cf", "2026-03-09", "2026-03-09").read_text())
    assert [f["start"] for f in m["files"]] == ["2026-03-09T03:00:00Z", "2026-03-09T04:00:00Z",
                                                  "2026-03-09T05:00:00Z"]


def test_inventory_hourly_template_does_not_count_strays_under_the_day_prefix(home, env, tmp_path):
    gf.make(env.root, "cloudfront", DAY, hours=[3])
    b = env.bucket(BUCKET)
    (b / "cf/E2EXAMPLE.2026-03-09-7.AAA.gz").write_bytes(b"x")      # hour part does not match
    (b / "cf/E2EXAMPLE.2026-03-09-99.AAA.gz").write_bytes(b"x")     # not an hour
    (b / "cf/E2EXAMPLE.2026-03-09-.AAA.gz").write_bytes(b"x")
    (b / "cf/E2EXAMPLE.2026-03-10-03.AAA.gz").write_bytes(b"x")     # next day: outside the day prefix
    r = run("cf", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    m = json.loads(manifest_path(home, "cf", "2026-03-09", "2026-03-09").read_text())
    assert len(m["files"]) == 1 and m["files"][0]["start"] == "2026-03-09T03:00:00Z"
    assert m["skipped_unparsed"] == 3
    assert m["days"]["2026-03-09"]["files"] == 1


def test_inventory_waf_stray_key_directly_under_the_day_dir_is_not_counted(home, env):
    gf.make(env.root, "waf", DAY, hours=[3], minutes=(0,))
    b = env.bucket(BUCKET)
    stray = b / "AWSLogs/111122223333/WAFLogs/us-east-1/example-acl/2026/03/09/loose_20260309T0500Z_a.log.gz"
    stray.write_bytes(b"x")
    r = run("waf", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    m = json.loads(manifest_path(home, "waf", "2026-03-09", "2026-03-09").read_text())
    assert all("loose_" not in f["key"] for f in m["files"])
    assert m["skipped_unparsed"] == 1


def test_manifest_files_are_sorted_and_ranges_span_days(home, env):
    gf.make(env.root, "alb", DAY, hours=[5], minutes=(0,))
    gf.make(env.root, "alb", NEXT, hours=[5], minutes=(0,))
    r = run("alb", "2026-03-09", "2026-03-10")
    assert r.returncode == 0, r.stderr
    day_rows = [l for l in rows(r.stdout) if l and l[0].startswith("2026-03-")]
    assert [x[0] for x in day_rows] == ["2026-03-09", "2026-03-10"]
    m = json.loads(manifest_path(home, "alb", "2026-03-09", "2026-03-10").read_text())
    assert [f["start"] for f in m["files"]] == sorted(f["start"] for f in m["files"])
    assert len(m["files"]) == 2


def test_empty_day_reported_as_gap(home, env):
    gf.make(env.root, "alb", DAY, hours=[1], minutes=(0,))
    r = run("alb", "2026-03-09", "2026-03-10")
    assert r.returncode == 0, r.stderr
    assert "2026-03-10: " + GAP in r.stdout
    assert "2026-03-09: " + GAP not in r.stdout
    assert "zero traffic" in r.stdout and "no traffic" not in r.stdout


def test_range_over_92_days_refused(home, env):
    r = run("alb", "2026-01-01", "2026-04-03")           # 93 days inclusive
    assert r.returncode == 2
    assert "92" in r.stderr
    assert env.calls() == []
    ok = run("alb", "2026-01-01", "2026-04-02")          # exactly 92 days is allowed
    assert ok.returncode == 0, ok.stderr


@pytest.mark.parametrize("args", [
    ("alb", "2026-03-10", "2026-03-09"),
    ("alb", "2026-3-9", "2026-03-09"),
    ("nope", "2026-03-09", "2026-03-09"),
    ("ALB", "2026-03-09", "2026-03-09"),
    ("alb", "2026-03-09"),
])
def test_bad_arguments_exit_2(home, env, args):
    r = run(*args)
    assert r.returncode == 2
    assert env.calls() == []


def test_not_configured_exit_2(home, fake_s3):
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 2
    assert "S3 log module: off (not configured)" in r.stderr


def test_expired_session_exit_3_with_hint(home, env, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_ERROR", "An error occurred (ExpiredToken) when calling the ListObjectsV2 "
                                          "operation: The provided token has expired.")
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 3
    assert "! aws sso login --profile sre-read" in r.stderr
    assert not manifest_path(home, "alb", "2026-03-09", "2026-03-09").exists()


def test_unsafe_keys_skipped_in_manifest(home, env, tmp_path, monkeypatch):
    base = "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/"
    gf.make(env.root, "alb", DAY, hours=[1], minutes=(0,))
    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps([
        {"key": base + "../x.gz", "size": 10},
        {"key": base + "a b.gz", "size": 10},
        {"key": base + "a\nb.gz", "size": 10},
    ]))
    monkeypatch.setenv("FAKE_EXTRA_KEYS_JSON", str(extra))
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    mpath = manifest_path(home, "alb", "2026-03-09", "2026-03-09")
    text = mpath.read_text()
    m = json.loads(text)
    assert m["skipped_unsafe"] == 3
    assert len(m["files"]) == 1
    for needle in ("x.gz", "a b", "a\\nb", "a\nb", "../"):
        assert needle not in text
        assert needle not in r.stdout and needle not in r.stderr
    assert "3" in r.stdout and "unsafe" in r.stdout


def test_v2_json_marked_unsupported(home, env):
    gf.make(env.root, "cloudfront", DAY, hours=[1], fmt="json")
    gf.make(env.root, "cloudfront", DAY, hours=[2])
    r = run("cf", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    m = json.loads(manifest_path(home, "cf", "2026-03-09", "2026-03-09").read_text())
    assert m["unsupported_format"] is True
    assert [f["start"] for f in m["files"]] == ["2026-03-09T02:00:00Z"]      # the json.gz is not offered to fetch
    assert "format unsupported (v2 JSON/Parquet)" in r.stdout


def test_unparsed_files_counted(home, env):
    gf.make(env.root, "alb", DAY, hours=[1], minutes=(0,))
    (env.root / BUCKET / "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/readme.txt").write_text("x")
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    m = json.loads(manifest_path(home, "alb", "2026-03-09", "2026-03-09").read_text())
    assert m["skipped_unparsed"] == 1 and len(m["files"]) == 1
    assert "file time" in r.stdout


def thousand_files(tmp_path, monkeypatch):
    prefix = "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/"
    extra = tmp_path / "thousand.json"
    extra.write_text(json.dumps([
        {"key": "%s111122223333_elasticloadbalancing_us-east-1_app.example-alb.1234567890abcdef_20260309T%02d%02dZ_192.0.2.1_%04d.log.gz"
                % (prefix, i // 60 % 24, i % 60, i), "size": 1048576}
        for i in range(1000)]))
    monkeypatch.setenv("FAKE_EXTRA_KEYS_JSON", str(extra))


def test_cost_na_without_prices(home, env, tmp_path, monkeypatch):
    thousand_files(tmp_path, monkeypatch)
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    day_row = [l.split() for l in r.stdout.splitlines() if l.startswith("2026-03-09")][0]
    assert day_row[1] == "1000" and day_row[2] == "1000.00" and day_row[3] == "n/a"
    assert [l.split() for l in r.stdout.splitlines() if l.startswith("total")][0][3] == "n/a"


def test_cost_na_with_only_one_price(home, env, tmp_path, monkeypatch):
    write_config(home, "PRICE_PER_GB=0.09\n")
    thousand_files(tmp_path, monkeypatch)
    r = run("alb", "2026-03-09", "2026-03-09")
    assert "n/a" in r.stdout


def test_cost_estimate(home, env, tmp_path, monkeypatch):
    write_config(home, "PRICE_PER_GB=0.09\nPRICE_PER_1K_GET=0.0004\n")
    thousand_files(tmp_path, monkeypatch)
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    # GB = 1000 * 1 MiB / 1024^3 = 0.9765625 ; 0.9765625*0.09 + 1000/1000*0.0004 = 0.0882906...
    day_row = [l.split() for l in r.stdout.splitlines() if l.startswith("2026-03-09")][0]
    assert day_row[3] == "$0.0883"
    assert [l.split() for l in r.stdout.splitlines() if l.startswith("total")][0][3] == "$0.0883"


def test_estimate_cost_unit():
    from decimal import Decimal
    from s3logs import cli_inventory as ci
    assert ci.estimate_cost(Decimal("0.09"), Decimal("0.0004"), 1000 * 1048576, 1000) == "$0.0883"
    assert ci.estimate_cost(None, Decimal("0.0004"), 10, 1) == "n/a"
    assert ci.estimate_cost(Decimal("0.09"), None, 10, 1) == "n/a"
    assert ci.estimate_cost(Decimal("0.09"), Decimal("0.0004"), 0, 0) == "$0.0000"


def test_out_of_range_stamp_counted_unparsed(home, env):
    base = "AWSLogs/111122223333/elasticloadbalancing/us-east-1/2026/03/09/"
    gf.make(env.root, "alb", DAY, hours=[1], minutes=(0,))
    (env.root / BUCKET / (base + "planted_00010101T0000Z_y.log.gz")).write_bytes(b"x")
    r = run("alb", "2026-03-09", "2026-03-09")
    assert r.returncode == 0, r.stderr
    mpath = manifest_path(home, "alb", "2026-03-09", "2026-03-09")
    text = mpath.read_text()
    m = json.loads(text)
    assert m["skipped_unparsed"] >= 1 and len(m["files"]) == 1
    for out in (text, r.stdout, r.stderr):
        assert "planted" not in out and "00010101" not in out
    assert "Traceback" not in r.stderr
