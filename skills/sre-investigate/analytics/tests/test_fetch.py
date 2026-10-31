"""logs-fetch: dry run by default, capped, size-verified batches, redacted Parquet, clean staging."""
from __future__ import annotations

import csv
import datetime as dt
import fcntl
import io
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import time

import pytest

import gen_fixtures as gf
from conftest import BIN
from s3logs import budget, cli_fetch, cli_inventory, convert, duck, paths, s5

BUCKET = "example-logs-bucket"
ALB_TEMPLATE = "AWSLogs/111122223333/elasticloadbalancing/us-east-1/{yyyy}/{MM}/{dd}/"
CF_TEMPLATE = "cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}"
DAY = dt.date(2026, 3, 9)
RUN = "orders-api-prod-20260309-1200"
OTHER_RUN = "catalog-api-prod-20260309-1100"
MIB = 1024 * 1024
ASK = "ask the user; an override needs their marker file plus --force"


@pytest.fixture(autouse=True)
def _stub_tools_only(duckdb_bin, fake_s3, stub_path):
    """duckdb is symlinked INTO the stub dir (which is first on PATH); ~/.local/bin, where the real
    s5cmd lives, is never put on PATH. A test must never be able to run the real s5cmd or aws."""
    link = stub_path.dir / "duckdb"
    if not link.exists():
        link.symlink_to(duckdb_bin)
    for tool in ("s5cmd", "aws"):
        found = shutil.which(tool)
        assert found == str(stub_path.dir / tool), "%s on PATH is %s, not the stub" % (tool, found)
        assert os.path.realpath(found) == str(stub_path.dir / tool)


def write_config(home, extra=""):
    d = home / ".config/culiops/sre-investigate"
    d.mkdir(parents=True, exist_ok=True)
    (d / "logs.env").write_text("\n".join([
        "AWS_PROFILE=sre-read",
        "DATASET_cf=cloudfront:s3://%s/%s" % (BUCKET, CF_TEMPLATE),
        "DATASET_alb=alb:s3://%s/%s" % (BUCKET, ALB_TEMPLATE),
        "DATASET_waf=waf:s3://%s/AWSLogs/111122223333/WAFLogs/us-east-1/example-acl/{yyyy}/{MM}/{dd}/{HH}/" % BUCKET,
    ]) + "\n" + extra)


@pytest.fixture
def env(home, fake_s3):
    write_config(home)
    fake_s3.bucket(BUCKET)
    return fake_s3


@pytest.fixture
def cap(capsys):
    def run(*args):
        code = cli_fetch.main(list(args))
        out, err = capsys.readouterr()
        return code, out, err
    return run


def inventory(capsys, ds, frm, to):
    code = cli_inventory.main([ds, frm, to])
    capsys.readouterr()
    assert code == 0


def alb10(env, capsys, frm="2026-03-09", to="2026-03-10"):
    """10 ALB files (hours 1-5, minutes 0 and 30) on DAY plus a manifest for frm..to."""
    keys = gf.make(env.root, "alb", DAY, hours=range(1, 6))
    inventory(capsys, "alb", frm, to)
    return sorted(keys)


def s5_calls(env):
    return [c for c in env.calls() if c[:1] == ["s5cmd"]]


def run_file_lines(env):
    return [c[1:] for c in env.calls() if c[:1] == ["s5cmd-run-file"]]


def state():
    return paths.state_root()


def ds_dir(run=RUN, ds="alb"):
    return state() / "data" / run / ds


def ledger():
    p = state() / "budgets" / "ledger.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def staging_entries():
    d = state() / "staging"
    if not d.exists():
        return []
    os.chmod(str(d), 0o700)
    try:
        return sorted(os.listdir(str(d)))
    finally:
        os.chmod(str(d), 0o300)


def mode(p):
    return stat.S_IMODE(os.stat(str(p)).st_mode)


def count_rows(d):
    text = duck.run([], "SELECT count(*) AS n FROM read_parquet(%s)" % duck.quote_literal(str(d / "part-*.parquet")), [d])
    return int(list(csv.DictReader(io.StringIO(text)))[0]["n"])


def fetched_keys(d):
    p = d / "fetched.jsonl"
    return [json.loads(l)["key"] for l in p.read_text().splitlines()] if p.exists() else []


def go(cap, *args, run=RUN):
    return cap("alb", "2026-03-09", *args, "--yes", "--run", run)


# ---- dry run -----------------------------------------------------------------------------------

def test_default_is_dry_run(env, cap, capsys):
    alb10(env, capsys)
    before = len(env.calls())
    code, out, err = cap("alb", "2026-03-09")
    assert code == 0, err
    assert out.startswith("DRY RUN — nothing downloaded\n")
    assert [c for c in env.calls()[before:] if c[:1] in (["s5cmd"], ["s5cmd-run-file"])] == []
    assert s5_calls(env) == []
    assert not (state() / "data").exists() or os.listdir(str(state() / "data")) == []
    assert staging_entries() == []


def test_dry_run_lines(env, cap, capsys):
    alb10(env, capsys)
    code, out, err = cap("alb", "2026-03-09")
    assert code == 0
    assert out.splitlines() == [
        "DRY RUN — nothing downloaded",
        "dataset alb (alb)  slice 2026-03-09 all (+1 widen)  every 1",
        "files 10  MB 0.0  est_cost n/a",
        "caps: fetch 0.0/200 MB  run - 0.0/1024 MB  24h 0.0/2048 MB  → OK",
        "to run: logs-fetch alb 2026-03-09 --yes --run <run-id>",
    ]


def test_dry_run_slice_every_and_cost_in_lines(home, env, cap, capsys):
    write_config(home, "PRICE_PER_GB=0.5\nPRICE_PER_1K_GET=0.4\n")
    alb10(env, capsys)
    code, out, err = cap("alb", "2026-03-09", "1-2", "--every", "2")
    assert code == 0, err
    lines = out.splitlines()
    assert lines[1] == "dataset alb (alb)  slice 2026-03-09 1-2 (+1 widen)  every 2"
    assert re.fullmatch(r"files \d+  MB \d+\.\d  est_cost \$\d+\.\d{4}", lines[2])
    assert lines[-1] == "to run: logs-fetch alb 2026-03-09 1-2 --every 2 --yes --run <run-id>"


def test_yes_requires_run(env, cap, capsys):
    alb10(env, capsys)
    code, out, err = cap("alb", "2026-03-09", "--yes")
    assert code == 2 and "--run" in err
    code, out, err = cap("alb", "2026-03-09", "--run", RUN)
    assert code == 2 and "--yes" in err
    assert s5_calls(env) == []


def test_requires_manifest(env, cap):
    code, out, err = cap("alb", "2026-03-09")
    assert code == 2
    assert "run logs-inventory alb 2026-03-09 2026-03-10 first" in err


def test_module_off_without_config(home, fake_s3, cap):
    code, out, err = cap("alb", "2026-03-09")
    assert code == 2 and "S3 log module: off (not configured)" in err


@pytest.mark.parametrize("args", [
    ["nope", "2026-03-09"], ["alb", "2026-13-40"], ["alb", "2026-03-09", "25"], ["alb", "2026-03-09", "5-2"],
    ["alb", "2026-03-09", "10:00-09:00"], ["alb", "2026-03-09", "1", "--every", "0"],
    ["alb", "2026-03-09", "--max-files", "x"], ["alb"], [], ["alb", "2026-03-09", "1", "2"],
    ["alb", "2026-03-09", "--bogus"], ["alb", "2026-03-09", "--yes", "--run", "BAD"],
])
def test_bad_arguments_refused(env, cap, capsys, args):
    alb10(env, capsys)
    code, out, err = cap(*args)
    assert code == 2
    assert s5_calls(env) == []


def test_cloudfront_minute_slice_refused(env, cap, capsys):
    gf.make(env.root, "cloudfront", DAY, hours=range(3))
    inventory(capsys, "cf", "2026-03-09", "2026-03-09")
    code, out, err = cap("cf", "2026-03-09", "00:00-01:00")
    assert code == 2 and "CloudFront" in err


def test_slice_crossing_midnight_needs_next_day_manifest(env, cap, capsys):
    alb10(env, capsys, "2026-03-09", "2026-03-09")
    for sl in ([], ["23"], ["22-23"], ["23:50-24:00"], ["23:50-23:52"], ["23:00-23:55"], ["23:51-23:52"]):
        code, out, err = cap("alb", "2026-03-09", *sl)
        assert code == 2, sl
        assert "run logs-inventory alb 2026-03-09 2026-03-10 first" in err
    code, out, err = cap("alb", "2026-03-09", "3")      # does not reach midnight
    assert code == 0, err
    code, out, err = cap("alb", "2026-03-09", "10:00-11:00")
    assert code == 0, err
    for sl in ("22", "22:00-23:50", "23:40-23:50"):       # the widen stays inside the day
        code, out, err = cap("alb", "2026-03-09", sl)
        assert code == 0, (sl, err)


def test_waf_slice_crossing_midnight_needs_next_day_manifest(env, cap, capsys):
    gf.make(env.root, "waf", DAY, hours=range(20, 24), minutes=(0, 30))
    inventory(capsys, "waf", "2026-03-09", "2026-03-09")
    for sl in ("23:50-23:52", "23:00-23:55", "23"):
        code, out, err = cap("waf", "2026-03-09", sl)
        assert code == 2, sl
        assert "run logs-inventory waf 2026-03-09 2026-03-10 first" in err
    assert cap("waf", "2026-03-09", "22:00-23:50")[0] == 0
    inventory(capsys, "waf", "2026-03-10", "2026-03-10")
    assert cap("waf", "2026-03-09", "23:50-23:52")[0] == 0


def test_cloudfront_hour_22_does_not_need_next_day(env, cap, capsys):
    gf.make(env.root, "cloudfront", DAY, hours=range(24), records=1)
    inventory(capsys, "cf", "2026-03-09", "2026-03-09")
    assert cap("cf", "2026-03-09", "22")[0] == 0
    assert cap("cf", "2026-03-09", "23")[0] == 2


def test_manifests_for_each_day_are_combined(env, cap, capsys):
    gf.make(env.root, "alb", DAY, hours=range(1, 6))
    inventory(capsys, "alb", "2026-03-09", "2026-03-09")
    inventory(capsys, "alb", "2026-03-10", "2026-03-10")
    code, out, err = cap("alb", "2026-03-09")
    assert code == 0, err
    assert "files 10 " in out


def test_widen_by_one_hour_cloudfront(env, cap, capsys):
    keys = sorted(gf.make(env.root, "cloudfront", DAY, hours=range(24), records=2))
    inventory(capsys, "cf", "2026-03-09", "2026-03-10")
    code, out, err = cap("cf", "2026-03-09", "10")
    assert code == 0, err
    assert "files 2 " in out
    code, out, err = cap("cf", "2026-03-09", "10", "--yes", "--run", RUN)
    assert code == 0, err
    assert fetched_keys(ds_dir(ds="cf")) == [keys[10], keys[11]]
    sent = [l.split()[3] for l in run_file_lines(env)[0]]
    assert sent == ["s3://%s/%s" % (BUCKET, k) for k in (keys[10], keys[11])]


def test_alb_slice_widens_into_next_day_directory(env, cap, capsys):
    gf.make(env.root, "alb", DAY, hours=[22, 23], minutes=(0, 30))
    nxt = gf.make(env.root, "alb", DAY + dt.timedelta(days=1), hours=[0], minutes=(0, 5, 10))
    inventory(capsys, "alb", "2026-03-09", "2026-03-10")
    code, out, err = go(cap, "23")
    assert code == 0, err
    got = fetched_keys(ds_dir())
    assert any("T0000Z" in k for k in got) and any("T0005Z" in k for k in got)
    assert not any("T0010Z" in k for k in got)
    assert sorted(nxt)[2] not in got


# ---- caps -------------------------------------------------------------------------------------

def fill_day_cap(home, cap_mb=1):
    budget.charge(OTHER_RUN, "alb", cap_mb * MIB, dt.datetime.now(dt.timezone.utc))


def make_marker(home):
    p = home / ".config/culiops/sre-investigate/over-cap.allow"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")
    return p


def test_over_cap_refused_exit_2(home, env, cap, capsys):
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home)
    code, out, err = cap("alb", "2026-03-09")
    assert code == 2
    assert "→ OVER (24h)" in out and ASK in out.splitlines()
    assert out.splitlines()[0] == "DRY RUN — nothing downloaded"
    code, out, err = go(cap)
    assert code == 2
    assert "→ OVER (24h)" in out and ASK in out.splitlines()
    assert "DRY RUN" not in out
    assert s5_calls(env) == [] and staging_entries() == []
    assert len(ledger()) == 1
    assert not (state() / "data" / RUN).exists()


def test_over_fetch_cap_with_one_big_file(home, env, cap, capsys):
    write_config(home, "MAX_MB=1\n")
    key = gf.alb_key(DAY, dt.datetime(2026, 3, 9, 1, 0))
    p = env.root / BUCKET / key
    p.parent.mkdir(parents=True)
    p.write_bytes(os.urandom(MIB + MIB // 2))
    inventory(capsys, "alb", "2026-03-09", "2026-03-10")
    code, out, err = cap("alb", "2026-03-09")
    assert code == 2 and "→ OVER (fetch)" in out and ASK in out
    assert "fetch 1.5/1 MB" in out


def test_force_without_marker_refused(home, env, cap, capsys):
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home)
    code, out, err = go(cap, "--force")
    assert code == 2 and "marker" in err
    assert s5_calls(env) == []


def test_force_with_fresh_marker_proceeds(home, env, cap, capsys):
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home)
    make_marker(home)
    code, out, err = go(cap, "--force")
    assert code == 0, (out, err)
    assert len(s5_calls(env)) == 1
    assert len(ledger()) == 2 and ledger()[1]["run"] == RUN
    assert count_rows(ds_dir()) == 30


def test_dry_run_with_force_and_marker_reports_override(home, env, cap, capsys):
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home)
    make_marker(home)
    code, out, err = cap("alb", "2026-03-09", "--force")
    assert code == 0, err
    assert "→ OVER (24h)" in out and ASK not in out
    assert "override" in out


def test_cap_reached_mid_fetch_stops_the_fetch(home, env, cap, capsys, monkeypatch):
    """Before each batch budget.check runs again with that batch's bytes."""
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 3)
    alb10(env, capsys)
    real = convert.to_parquet
    seen = []

    def spy(*a, **kw):
        res = real(*a, **kw)
        if not seen:
            budget.charge(OTHER_RUN, "alb", 2048 * MIB, dt.datetime.now(dt.timezone.utc))   # someone else spends the day
        seen.append(1)
        return res

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", spy)
    code, out, err = go(cap)
    assert code == 2, (out, err)
    assert "cap" in err
    assert len(s5_calls(env)) == 1 and len(seen) == 1
    assert len(fetched_keys(ds_dir())) == 3
    assert mode(ds_dir()) == 0o555 and staging_entries() == []
    assert re.search(r"^fetched 3 files ", out, re.M)


def test_second_real_fetch_refused_while_lock_held(env, cap, capsys):
    alb10(env, capsys)
    paths.ensure_private_dirs()
    fd = os.open(str(state() / "budgets" / ".fetch.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        code, out, err = go(cap)
        assert code == 2 and "another fetch is running" in err
        assert s5_calls(env) == []
        code, out, err = cap("alb", "2026-03-09")           # a dry run does not need the lock
        assert code == 0
    finally:
        os.close(fd)
    code, out, err = go(cap)
    assert code == 0, err


# ---- real run ---------------------------------------------------------------------------------

def test_real_run_end_to_end(env, cap, capsys):
    keys = alb10(env, capsys)
    code, out, err = go(cap)
    assert code == 0, (out, err)
    d = ds_dir()
    lines = out.splitlines()
    assert lines[-2] == ("fetched 10 files 0.0 MB verified; charged 0.0 MB; skipped 0 present; data: %s; "
                         "sample: 1/1" % d)
    assert lines[-1] == "converted: rows 30; skipped lines 0; dropped columns none"
    assert fetched_keys(d) == keys
    assert count_rows(d) == 30
    total = sum(os.path.getsize(str(env.root / BUCKET / k)) for k in keys)
    assert [e["bytes"] for e in ledger()] == [total] and ledger()[0]["run"] == RUN and ledger()[0]["dataset"] == "alb"
    assert json.loads((d / "meta.json").read_text()) == {
        "sample_every": 1, "dataset": "alb", "type": "alb", "day_slices": ["2026-03-09 all"]}
    # raw files are gone, staging is empty, the dataset is read-only
    assert staging_entries() == []
    assert mode(d) == 0o555 and mode(state() / "data" / RUN) == 0o700
    parts = sorted(p for p in os.listdir(str(d)) if p.endswith(".parquet"))
    assert parts == ["part-000001.parquet"] and mode(d / parts[0]) == 0o444
    assert s5_calls(env)[0] == ["s5cmd", "--log", "error", "run", s5_calls(env)[0][-1]]
    assert [c for c in env.calls() if c[:2] == ["configure", "export-credentials"]] == [
        ["configure", "export-credentials", "--profile", "sre-read", "--format", "process"]]
    assert env.s5env()[0]["AWS_ACCESS_KEY_ID"] and "AWS_PROFILE" not in env.s5env()[0]
    assert all(re.fullmatch(r"cp -n --raw s3://%s/\S+ \S+/\d{6}\.gz" % BUCKET, l) for l in run_file_lines(env)[0])


def test_batch_dir_and_dataset_dir_modes_during_the_run(env, cap, capsys, monkeypatch):
    alb10(env, capsys)
    seen = {}
    real_run, real_conv = s5.run, convert.to_parquet

    def spy_run(rf, profile, region, batchdir, bucket):
        seen["batch"] = (os.path.basename(batchdir), mode(batchdir), mode(os.path.dirname(batchdir)))
        seen["run_file"] = mode(rf)
        seen["bucket"] = bucket
        return real_run(rf, profile, region, batchdir, bucket)

    def spy_conv(ds_type, raw, out, cfg, salt):
        seen["ds_during"] = mode(out.parent)
        return real_conv(ds_type, raw, out, cfg, salt)

    monkeypatch.setattr(cli_fetch.s5, "run", spy_run)
    monkeypatch.setattr(cli_fetch.convert, "to_parquet", spy_conv)
    assert go(cap)[0] == 0
    name, bmode, root_mode = seen["batch"]
    assert re.fullmatch(r"[0-9a-f]{32}", name) and bmode == 0o700 and root_mode == 0o300
    assert seen["ds_during"] == 0o700 and seen["bucket"] == BUCKET
    assert mode(ds_dir()) == 0o555


def test_batches_split_by_file_count(env, cap, capsys, monkeypatch):
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 4)
    alb10(env, capsys)
    code, out, err = go(cap)
    assert code == 0, err
    assert [len(l) for l in run_file_lines(env)] == [4, 4, 2]
    assert sorted(p for p in os.listdir(str(ds_dir())) if p.endswith(".parquet")) == [
        "part-000001.parquet", "part-000002.parquet", "part-000003.parquet"]
    assert len(ledger()) == 3 and count_rows(ds_dir()) == 30


def test_batches_split_by_bytes(env, cap, capsys, monkeypatch):
    keys = alb10(env, capsys)
    size = os.path.getsize(str(env.root / BUCKET / keys[0]))
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_BYTES", size * 2 + 1)
    assert go(cap)[0] == 0
    assert all(len(l) <= 3 for l in run_file_lines(env))
    assert sum(len(l) for l in run_file_lines(env)) == 10 and len(run_file_lines(env)) >= 4


def test_one_oversized_file_is_its_own_batch(env, cap, capsys, monkeypatch):
    alb10(env, capsys)
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_BYTES", 1)
    assert go(cap)[0] == 0
    assert [len(l) for l in run_file_lines(env)] == [1] * 10


def sizes(env, keys):
    return [os.path.getsize(str(env.root / BUCKET / k)) for k in keys]


def test_size_mismatch_is_charged_but_not_converted(env, cap, capsys, monkeypatch):
    """Every byte that arrived is charged; verification only decides conversion."""
    keys = alb10(env, capsys)
    bad = keys[3]
    monkeypatch.setenv("FAKE_S5CMD_TRUNCATE", bad)
    code, out, err = go(cap)
    assert code == 3, (out, err)
    assert bad in err and "size" in err
    arrived = sum(sizes(env, keys)) - 1                     # the truncated file is one byte short
    assert [e["bytes"] for e in ledger()] == [arrived]
    d = ds_dir()
    assert bad not in fetched_keys(d) and len(fetched_keys(d)) == 9
    assert count_rows(d) == 27
    assert staging_entries() == [] and mode(d) == 0o555
    assert "fetched 9 files" in out
    # a re-run (object fixed) fetches only the missing file
    monkeypatch.delenv("FAKE_S5CMD_TRUNCATE")
    code, out, err = go(cap)
    assert code == 0, err
    assert len(run_file_lines(env)[-1]) == 1 and run_file_lines(env)[-1][0].split()[3] == "s3://%s/%s" % (BUCKET, bad)
    assert count_rows(d) == 30
    assert [e["bytes"] for e in ledger()] == [arrived, sizes(env, [bad])[0]]


def test_partial_batch_is_charged_for_the_files_that_arrived(env, cap, capsys, monkeypatch):
    keys = alb10(env, capsys)
    monkeypatch.setenv("FAKE_S5CMD_MISSING", keys[2])
    code, out, err = go(cap)
    assert code == 3, (out, err)
    assert "NoSuchKey" in err
    others = [k for k in keys if k != keys[2]]
    assert [e["bytes"] for e in ledger()] == [sum(sizes(env, others))]
    d = ds_dir()
    assert fetched_keys(d) == others and count_rows(d) == 27     # what arrived intact is kept
    assert staging_entries() == [] and mode(d) == 0o555
    assert "fetched 9 files" in out
    monkeypatch.delenv("FAKE_S5CMD_MISSING")
    assert go(cap)[0] == 0
    assert [l.split()[3] for l in run_file_lines(env)[-1]] == ["s3://%s/%s" % (BUCKET, keys[2])]
    assert count_rows(d) == 30


def test_oversize_object_is_charged_and_stops_the_fetch(env, cap, capsys, monkeypatch):
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 4)
    keys = alb10(env, capsys)
    monkeypatch.setenv("FAKE_S5CMD_OVERSIZE", keys[3])
    code, out, err = go(cap)
    assert code == 3, (out, err)
    assert "objects changed since the listing" in err and "logs-inventory" in err
    assert [e["bytes"] for e in ledger()] == [sum(sizes(env, keys[:4])) + 10]
    assert len(run_file_lines(env)) == 1                       # batches 2 and 3 never started
    assert fetched_keys(ds_dir()) == keys[:3] and count_rows(ds_dir()) == 9
    assert staging_entries() == [] and mode(ds_dir()) == 0o555


def test_doctored_size_zero_manifest_is_charged_for_what_arrived(env, cap, capsys):
    keys = alb10(env, capsys)
    mp = state() / "manifests" / "alb" / "2026-03-09_2026-03-10.json"
    doc = json.loads(mp.read_text())
    for f in doc["files"]:
        f["size"] = 0
    mp.write_text(json.dumps(doc))
    code, out, err = cap("alb", "2026-03-09")
    assert code == 0 and "files 10  MB 0.0" in out
    code, out, err = go(cap)
    assert code == 3 and "objects changed since the listing" in err
    assert [e["bytes"] for e in ledger()] == [sum(sizes(env, keys))]     # charged what really came down
    assert fetched_keys(ds_dir()) == [] and staging_entries() == []


def test_run_that_dies_without_verifying_still_charges_what_is_on_disk(env, cap, capsys, monkeypatch):
    """An interrupt/refusal inside s5.run: files already down are paid for, nothing is converted."""
    alb10(env, capsys)

    def half_then_die(rf, profile, region, batchdir, bucket):
        for n in (1, 2):
            with open(os.path.join(batchdir, "%06d.gz" % n), "wb") as f:
                f.write(b"x" * 100)
        raise cli_fetch._Interrupted(143)

    monkeypatch.setattr(cli_fetch.s5, "run", half_then_die)
    code, out, err = go(cap)
    assert code == 143
    assert [e["bytes"] for e in ledger()] == [200]
    assert fetched_keys(ds_dir()) == [] and staging_entries() == [] and mode(ds_dir()) == 0o555


def test_credentials_are_exported_for_every_batch(env, cap, capsys, monkeypatch):
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 2)
    alb10(env, capsys)
    code, out, err = go(cap)
    assert code == 0, err
    assert len([c for c in env.calls() if c[:2] == ["configure", "export-credentials"]]) == len(s5_calls(env)) == 5
    assert "wJalrXUtnFEMI" not in out + err


def test_failed_credential_export_is_exit_3_with_login_hint_and_charges_nothing(env, cap, capsys, monkeypatch):
    alb10(env, capsys)
    monkeypatch.setenv("FAKE_AWS_CREDS_ERROR", "The SSO session associated with this profile has expired")
    code, out, err = go(cap)
    assert code == 3
    assert "! aws sso login --profile sre-read" in err
    assert ledger() == [] and s5_calls(env) == [] and staging_entries() == []


def test_aws_error_mid_fetch_charges_only_verified_batches(env, cap, capsys, monkeypatch):
    """Review Focus 4."""
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 2)
    keys = alb10(env, capsys)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "2")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "ERROR ExpiredToken: The provided token has expired.")
    code, out, err = go(cap)
    assert code == 3
    assert "! aws sso login --profile sre-read" in err
    batch1 = sum(os.path.getsize(str(env.root / BUCKET / k)) for k in keys[:2])
    assert [e["bytes"] for e in ledger()] == [batch1]
    assert fetched_keys(ds_dir()) == keys[:2]
    assert staging_entries() == [] and mode(ds_dir()) == 0o555
    # re-run: batch 1 keys are skipped
    monkeypatch.delenv("FAKE_S5CMD_FAIL_ON_BATCH")
    code, out, err = go(cap)
    assert code == 0, err
    later = [l.split()[3].split("/", 3)[3] for lines in run_file_lines(env)[2:] for l in lines]
    assert later == keys[2:] and not set(later) & set(keys[:2])
    assert "skipped 2 present" in out
    assert fetched_keys(ds_dir()) == keys and count_rows(ds_dir()) == 30


def test_already_fetched_everything_is_a_noop(env, cap, capsys):
    alb10(env, capsys)
    assert go(cap)[0] == 0
    n = len(s5_calls(env))
    code, out, err = go(cap)
    assert code == 0, err
    assert len(s5_calls(env)) == n and len(ledger()) == 1
    assert "fetched 0 files 0.0 MB verified; charged 0.0 MB; skipped 10 present" in out
    assert mode(ds_dir()) == 0o555


def test_empty_selection_is_a_gap_not_zero_traffic(env, cap, capsys):
    env.bucket(BUCKET)
    inventory(capsys, "alb", "2026-03-09", "2026-03-10")
    code, out, err = cap("alb", "2026-03-09")
    assert code == 0
    assert "files 0 " in out and "this is a gap, not zero traffic" in out
    code, out, err = go(cap)
    assert code == 0 and "this is a gap, not zero traffic" in out
    assert s5_calls(env) == []


def test_every_n_sampling_writes_meta(env, cap, capsys):
    keys = alb10(env, capsys)
    code, out, err = go(cap, "--every", "3")
    assert code == 0, err
    d = ds_dir()
    assert fetched_keys(d) == keys[::3]
    meta = json.loads((d / "meta.json").read_text())
    assert meta["sample_every"] == 3 and meta["dataset"] == "alb" and meta["type"] == "alb"
    assert out.splitlines()[-2].endswith("sample: 1/3")
    # a different N into the same run and dataset is refused before anything is downloaded
    n = len(s5_calls(env))
    code, out, err = go(cap, "--every", "2")
    assert code == 2 and "sample" in err
    assert len(s5_calls(env)) == n
    # the same N is fine and skips what is there
    code, out, err = go(cap, "--every", "3")
    assert code == 0 and "skipped 4 present" in out
    # another run id has its own sampling
    assert go(cap, "--every", "2", run=OTHER_RUN)[0] == 0


def test_max_files_caps_selection(env, cap, capsys):
    keys = alb10(env, capsys)
    code, out, err = cap("alb", "2026-03-09", "--max-files", "3")
    assert code == 0, err
    assert "files 3 " in out and "--max-files 3" in out and "10" in out
    code, out, err = go(cap, "--max-files", "3")
    assert code == 0
    assert fetched_keys(ds_dir()) == keys[:3]
    # --every is applied first, --max-files after it
    code, out, err = go(cap, "--every", "2", "--max-files", "2", run=OTHER_RUN)
    assert code == 0
    assert fetched_keys(ds_dir(OTHER_RUN)) == [keys[0], keys[2]]


def test_sweep_removes_stale_staging_only(env, cap, capsys, tmp_path):
    alb10(env, capsys)
    paths.ensure_private_dirs()
    root = state() / "staging"
    stale, fresh, other = "a" * 32, "b" * 32, "keep-me"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("x")
    old = time.time() - 3 * 86400
    for name in (stale, fresh, other):
        (root / name).mkdir()
        (root / name / "f").write_text("x")
        os.chmod(str(root / name / "f"), 0o400)
    (root / stale / "sub").mkdir()
    os.chmod(str(root / stale / "sub"), 0o500)
    for name in (stale, other):
        os.utime(str(root / name), (old, old))
    (root / ("c" * 32)).symlink_to(outside)
    os.utime(str(root / ("c" * 32)), (old, old), follow_symlinks=False)
    assert go(cap)[0] == 0
    left = staging_entries()
    assert stale not in left and fresh in left and other in left and "c" * 32 in left
    assert (outside / "precious.txt").exists()
    assert mode(root) == 0o300


@pytest.mark.parametrize("sig,code", [(signal.SIGTERM, 143), (signal.SIGINT, 130), (signal.SIGHUP, 129)])
def test_staging_empty_after_sigterm(env, capsys, monkeypatch, sig, code):
    alb10(env, capsys)
    monkeypatch.setenv("FAKE_S5CMD_SLEEP", "60")
    proc = subprocess.Popen([str(BIN / "logs-fetch"), "alb", "2026-03-09", "--yes", "--run", RUN],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ.copy())
    try:
        deadline = time.time() + 30
        while time.time() < deadline and not s5_calls(env):
            time.sleep(0.05)
        assert s5_calls(env), "s5cmd was never started"
        assert len(staging_entries()) == 1
        proc.send_signal(sig)
        out, err = proc.communicate(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == code, (out, err)
    assert staging_entries() == []
    assert mode(ds_dir()) == 0o555 and mode(state() / "staging") == 0o300
    assert ledger() == []


def test_staging_empty_after_success_and_dry_run_via_bin(env, capsys):
    alb10(env, capsys)
    r = subprocess.run([str(BIN / "logs-fetch"), "alb", "2026-03-09", "--yes", "--run", RUN],
                       capture_output=True, text=True, env=os.environ.copy(), timeout=60)
    assert r.returncode == 0, r.stderr
    assert staging_entries() == []
    r = subprocess.run([str(BIN / "logs-fetch"), "alb", "2026-03-09"], capture_output=True, text=True,
                       env=os.environ.copy(), timeout=60)
    assert r.returncode == 0 and r.stdout.startswith("DRY RUN")


def test_staging_empty_after_conversion_failure(env, cap, capsys, monkeypatch):
    alb10(env, capsys)

    def boom(*a, **kw):
        raise convert.ConvertError("cannot read x.gz: BadGzipFile")

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", boom)
    code, out, err = go(cap)
    assert code == 4 and "conversion failed (exit 4)" in err
    assert staging_entries() == [] and mode(ds_dir()) == 0o555
    assert len(ledger()) == 1                      # the bytes were downloaded, so they are charged
    assert fetched_keys(ds_dir()) == []


def test_duckdb_error_exit_4(env, cap, capsys, monkeypatch):
    alb10(env, capsys)

    def boom(*a, **kw):
        raise duck.DuckError("duckdb failed (exit 1): nope")

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", boom)
    code, out, err = go(cap)
    assert code == 4 and "duckdb" in err and "exit 4" in err
    assert staging_entries() == [] and mode(ds_dir()) == 0o555


def test_converted_line_reports_dropped_columns_and_skipped_lines(env, cap, capsys):
    gf.make(env.root, "cloudfront", DAY, hours=[3], records=2)
    inventory(capsys, "cf", "2026-03-09", "2026-03-10")
    code, out, err = cap("cf", "2026-03-09", "3", "--yes", "--run", RUN)
    assert code == 0, err
    assert out.splitlines()[-1] == "converted: rows 2; skipped lines 0; dropped columns cs(Cookie)"


def test_waf_dataset_converts_with_salt(env, cap, capsys):
    gf.make(env.root, "waf", DAY, hours=[3], minutes=(0, 30), records=2)
    inventory(capsys, "waf", "2026-03-09", "2026-03-10")
    code, out, err = cap("waf", "2026-03-09", "3", "--yes", "--run", RUN)
    assert code == 0, err
    assert (state() / "salt").exists()
    assert count_rows(ds_dir(ds="waf")) >= 2


def test_unsafe_manifest_key_is_refused_before_s5cmd(env, cap, capsys):
    """Review Focus 3, second line of defence: a doctored manifest never reaches s5cmd."""
    alb10(env, capsys)
    mp = state() / "manifests" / "alb" / "2026-03-09_2026-03-10.json"
    doc = json.loads(mp.read_text())
    doc["files"][0]["key"] = "AWSLogs/x/../../y;rm -rf ~.gz"
    mp.write_text(json.dumps(doc))
    code, out, err = go(cap)
    assert code == 2 and "manifest" in err
    assert s5_calls(env) == [] and staging_entries() == []


@pytest.mark.parametrize("field,value", [("bucket", "other-bucket"), ("dataset", "cf"), ("type", "waf")])
def test_manifest_not_matching_config_is_refused(env, cap, capsys, field, value):
    alb10(env, capsys)
    mp = state() / "manifests" / "alb" / "2026-03-09_2026-03-10.json"
    doc = json.loads(mp.read_text())
    doc[field] = value
    mp.write_text(json.dumps(doc))
    code, out, err = go(cap)
    assert code == 2 and "manifest" in err
    assert s5_calls(env) == []


def test_corrupt_manifest_is_refused_but_unrelated_one_is_ignored(env, cap, capsys):
    alb10(env, capsys)
    junk = state() / "manifests" / "alb" / "2026-01-01_2026-01-02.json"
    junk.write_text("{not json")
    assert cap("alb", "2026-03-09")[0] == 0
    (state() / "manifests" / "alb" / "2026-03-09_2026-03-10.json").write_text("{not json")
    code, out, err = cap("alb", "2026-03-09")
    assert code == 2 and "manifest" in err


def test_symlinked_dataset_dir_is_refused(env, cap, capsys, tmp_path):
    alb10(env, capsys)
    paths.ensure_private_dirs()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    run_dir = state() / "data" / RUN
    run_dir.mkdir(mode=0o700)
    (run_dir / "alb").symlink_to(elsewhere)
    code, out, err = go(cap)
    assert code == 2
    assert s5_calls(env) == [] and list(elsewhere.iterdir()) == []


def test_corrupt_fetched_jsonl_is_refused(env, cap, capsys):
    alb10(env, capsys)
    assert go(cap)[0] == 0
    d = ds_dir()
    os.chmod(str(d), 0o700)
    (d / "fetched.jsonl").write_text("not json\n")
    os.chmod(str(d), 0o555)
    n = len(s5_calls(env))
    code, out, err = go(cap)
    assert code == 2 and "fetched.jsonl" in err
    assert len(s5_calls(env)) == n


# ---- purge ------------------------------------------------------------------------------------

def test_purge_removes_run_data_and_stale_staging(env, cap, capsys):
    alb10(env, capsys)
    assert go(cap)[0] == 0
    assert go(cap, run=OTHER_RUN)[0] == 0
    root = state() / "staging"
    old = time.time() - 3 * 86400
    os.chmod(str(root), 0o700)
    (root / ("d" * 32)).mkdir()
    (root / ("d" * 32) / "x.gz").write_text("x")
    os.utime(str(root / ("d" * 32)), (old, old))
    (root / ("e" * 32)).mkdir()
    os.chmod(str(root), 0o300)
    ledger_before = (state() / "budgets" / "ledger.jsonl").read_text()
    code, out, err = cap("--purge", RUN)
    assert code == 0, err
    assert not (state() / "data" / RUN).exists()
    assert (state() / "data" / OTHER_RUN / "alb").is_dir()
    left = staging_entries()
    assert "d" * 32 not in left and "e" * 32 in left and mode(root) == 0o300
    assert str(state() / "data" / RUN) in out
    assert str(root / ("d" * 32)) in out
    assert all(l.startswith(str(state())) or l.startswith("removed") or "ledger" in l for l in out.splitlines())
    assert (state() / "budgets" / "ledger.jsonl").read_text() == ledger_before


def test_purge_unknown_run_is_not_an_error(env, cap):
    paths.ensure_private_dirs()
    code, out, err = cap("--purge", RUN)
    assert code == 0 and "nothing" in out.lower()


def test_purge_without_state_creates_nothing(home, fake_s3, cap):
    code, out, err = cap("--purge", RUN)
    assert code == 0
    assert not (home / ".local").exists()


def test_purge_refused_while_fetch_running(env, cap, capsys):
    alb10(env, capsys)
    assert go(cap)[0] == 0
    fd = os.open(str(state() / "budgets" / ".fetch.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        code, out, err = cap("--purge", RUN)
        assert code == 2 and "another fetch is running" in err
        assert (state() / "data" / RUN).exists()
    finally:
        os.close(fd)


@pytest.mark.parametrize("args", [["--purge"], ["--purge", "BAD ID"], ["--purge", RUN, "alb"], ["--purge", RUN, "--yes"],
                                  ["--purge", RUN, "--every", "2"]])
def test_purge_bad_arguments(env, cap, args):
    paths.ensure_private_dirs()
    code, out, err = cap(*args)
    assert code == 2


def test_purge_does_not_follow_symlinks(env, cap, tmp_path):
    paths.ensure_private_dirs()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("x")
    run_dir = state() / "data" / RUN
    run_dir.mkdir(mode=0o700)
    (run_dir / "alb").symlink_to(outside)
    (run_dir / "link-file").symlink_to(outside / "precious.txt")
    code, out, err = cap("--purge", RUN)
    assert code == 0
    assert (outside / "precious.txt").exists() and not run_dir.exists()


# ---- signal handling in the critical section ---------------------------------------------------

def test_signal_during_critical_section_is_held_until_it_ends():
    sigs = cli_fetch._Signals()
    sigs.install()
    try:
        done = []
        with pytest.raises(cli_fetch._Interrupted) as ei:
            with sigs.critical():
                os.kill(os.getpid(), signal.SIGTERM)
                time.sleep(0.05)
                done.append("finished the critical section")
        assert done and ei.value.code == 143
        with pytest.raises(cli_fetch._Interrupted) as ei:         # a second signal acts at once; the first one's code wins
            with sigs.critical():
                os.kill(os.getpid(), signal.SIGHUP)
                time.sleep(0.05)
                os.kill(os.getpid(), signal.SIGINT)
                time.sleep(0.05)
                done.append("not reached")
        assert ei.value.code == 129 and done == ["finished the critical section"]
        assert sigs.pending is None and sigs.depth == 0
    finally:
        sigs.restore()


def test_signal_outside_critical_section_raises_at_once():
    sigs = cli_fetch._Signals()
    sigs.install()
    try:
        with pytest.raises(cli_fetch._Interrupted) as ei:
            os.kill(os.getpid(), signal.SIGHUP)
            time.sleep(0.5)
        assert ei.value.code == 129
    finally:
        sigs.restore()
    assert signal.getsignal(signal.SIGTERM) in (signal.SIG_DFL, signal.default_int_handler) or callable(signal.getsignal(signal.SIGTERM))


def test_non_ascii_terminal_does_not_crash_the_dry_run(env, capsys):
    alb10(env, capsys)
    e = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0", PYTHONIOENCODING="ascii")
    r = subprocess.run([str(BIN / "logs-fetch"), "alb", "2026-03-09"], capture_output=True, text=True, env=e, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("DRY RUN")


def test_forced_fetch_past_the_marker_ttl_survives_when_within_caps(home, env, cap, capsys, monkeypatch):
    """The per-batch check only needs the marker when the batch is over a cap."""
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 3)
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home, cap_mb=0)           # nothing used yet: a plain ledger line of 0 bytes
    marker = make_marker(home)
    real = convert.to_parquet

    def age_marker(*a, **kw):
        old = time.time() - 7200
        os.utime(str(marker), (old, old))      # the marker expires after the first batch
        return real(*a, **kw)

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", age_marker)
    code, out, err = go(cap, "--force")
    assert code == 0, (out, err)
    assert len(fetched_keys(ds_dir())) == 10


def test_forced_fetch_over_a_cap_with_expired_marker_stops(home, env, cap, capsys, monkeypatch):
    monkeypatch.setattr(cli_fetch, "MAX_BATCH_FILES", 3)
    write_config(home, "DAY_MAX_MB=1\n")
    alb10(env, capsys)
    fill_day_cap(home)                      # already at the cap: every batch is over
    marker = make_marker(home)
    real = convert.to_parquet

    def age_marker(*a, **kw):
        old = time.time() - 7200
        os.utime(str(marker), (old, old))
        return real(*a, **kw)

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", age_marker)
    code, out, err = go(cap, "--force")
    assert code == 2 and "marker" in err
    assert len(fetched_keys(ds_dir())) == 3


def test_append_failure_removes_the_new_part(env, cap, capsys, monkeypatch):
    alb10(env, capsys)

    def boom(d, records):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(cli_fetch, "_append_fetched", boom)
    code, out, err = go(cap)
    assert code == 2 and "No space" in err
    assert [p for p in os.listdir(str(ds_dir())) if p.endswith(".parquet")] == []
    assert staging_entries() == [] and mode(ds_dir()) == 0o555
    assert len(ledger()) == 1                                       # the bytes were still paid for


def test_append_fetched_truncates_a_partial_write(home, tmp_path, monkeypatch):
    d = tmp_path / "ds"
    d.mkdir()
    cli_fetch._append_fetched(d, [{"key": "a"}])
    before = (d / "fetched.jsonl").read_bytes()
    real_write = os.write

    def short_then_fail(fd, data):
        real_write(fd, bytes(data)[:5])
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(cli_fetch.os, "write", short_then_fail)
    with pytest.raises(OSError):
        cli_fetch._append_fetched(d, [{"key": "bbbbbbbbbb"}])
    assert (d / "fetched.jsonl").read_bytes() == before


def test_dataset_dir_sealed_even_if_batch_dir_removal_fails(env, cap, capsys, monkeypatch):
    alb10(env, capsys)
    real = paths.rmtree_force

    def boom(p):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(cli_fetch.paths, "rmtree_force", boom)
    code, out, err = go(cap)
    assert code == 2
    assert mode(ds_dir()) == 0o555
    monkeypatch.setattr(cli_fetch.paths, "rmtree_force", real)
    real(state() / "staging" / staging_entries()[0])


def test_dataset_dir_sealed_when_interrupted_right_after_creation(env, cap, capsys, monkeypatch):
    alb10(env, capsys)

    def stop(*a, **kw):
        raise cli_fetch._Interrupted(143)

    monkeypatch.setattr(cli_fetch.paths, "private_subdir", _after_first(cli_fetch.paths.private_subdir, 2, stop))
    code, out, err = go(cap)
    assert code == 143
    assert mode(ds_dir()) == 0o555 and staging_entries() == []


def _after_first(real, n, boom):
    """private_subdir wrapper: the nth call creates the directory and then 'gets a signal'."""
    calls = []

    def wrapper(parent, name):
        r = real(parent, name)
        calls.append(name)
        if len(calls) == n:
            boom()
        return r

    return wrapper


def test_symlinked_dataset_dir_is_not_chmodded_through_the_link(env, cap, capsys, tmp_path):
    alb10(env, capsys)
    paths.ensure_private_dirs()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(mode=0o750)
    run_dir = state() / "data" / RUN
    run_dir.mkdir(mode=0o700)
    (run_dir / "alb").symlink_to(elsewhere)
    assert go(cap)[0] == 2
    assert mode(elsewhere) == 0o750


def test_signal_after_the_download_still_charges_and_stores_the_batch(env, cap, capsys, monkeypatch):
    """A first signal between s5.run and the charge is held until the batch is stored."""
    keys = alb10(env, capsys)
    real = cli_fetch._received
    calls = []

    def kill_then_look(batchdir, run_file):
        if not calls:
            calls.append(1)
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.05)
        return real(batchdir, run_file)

    monkeypatch.setattr(cli_fetch, "_received", kill_then_look)
    code, out, err = go(cap)
    assert code == 143, (out, err)
    assert [e["bytes"] for e in ledger()] == [sum(sizes(env, keys))]
    assert fetched_keys(ds_dir()) == keys and count_rows(ds_dir()) == 30
    assert staging_entries() == [] and mode(ds_dir()) == 0o555


def test_summary_charged_matches_the_ledger_when_conversion_fails(env, cap, capsys, monkeypatch):
    keys = alb10(env, capsys)

    def boom(*a, **kw):
        raise convert.ConvertError("cannot read x.gz")

    monkeypatch.setattr(cli_fetch.convert, "to_parquet", boom)
    code, out, err = go(cap)
    assert code == 4
    charged = ledger()[0]["bytes"]
    assert charged == sum(sizes(env, keys))
    assert "fetched 0 files 0.0 MB verified; charged %s MB; skipped 0 present" % ("%.1f" % (charged / MIB)) in out


def test_final_line_has_true_verified_and_charged_totals(env, cap, capsys, monkeypatch):
    # a truncated file is charged but not verified: the two figures differ by its size
    keys = alb10(env, capsys)
    monkeypatch.setenv("FAKE_S5CMD_TRUNCATE", keys[1])
    code, out, err = go(cap)
    assert code == 3
    line = [l for l in out.splitlines() if l.startswith("fetched ")][0]
    m = re.fullmatch(r"fetched 9 files (\d+\.\d) MB verified; charged (\d+\.\d) MB; skipped 0 present; data: \S+; sample: 1/1", line)
    assert m, line
    assert ledger()[0]["bytes"] == sum(sizes(env, keys)) - 1
