"""Budget, caps and the override marker. Money depends on this module: it fails closed."""
from __future__ import annotations

import datetime
import json
import multiprocessing
import os
from pathlib import Path

import pytest

from s3logs import budget, paths
from s3logs.config import Config
from s3logs.validate import Refused

MIB = 1024 * 1024
NOW = datetime.datetime(2026, 3, 9, 12, 0, 0, tzinfo=datetime.timezone.utc)
RUN = "orders-api-prod-20260309-1200"
OTHER_RUN = "catalog-api-prod-20260309-1100"


def ledger_path() -> Path:
    return paths.state_root() / "budgets" / "ledger.jsonl"


def stamp(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_ledger(entries, raw_extra=None):
    paths.ensure_private_dirs()
    lines = [json.dumps({"ts": stamp(ts), "run": run, "dataset": "ds", "bytes": n})
             for ts, run, n in entries]
    if raw_extra is not None:
        lines.append(raw_extra)
    ledger_path().write_text("\n".join(lines) + "\n")


def make_marker(age_s=0, now=NOW):
    p = paths.marker_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("")
    t = now.timestamp() - age_s
    os.utime(str(p), (t, t))
    return p


# ---- caps -----------------------------------------------------------------

def test_fetch_cap(home):
    cfg = Config()
    v = budget.check(cfg, 201 * MIB, RUN, False, NOW)
    assert v.ok is False and v.over == ["fetch"] and v.override_used is False


def test_exactly_at_cap_is_allowed(home):
    v = budget.check(Config(), 200 * MIB, RUN, False, NOW)
    assert v.ok is True and v.over == []
    v = budget.check(Config(), 200 * MIB + 1, RUN, False, NOW)
    assert v.over == ["fetch"]


def test_run_cap_sums_ledger(home):
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 900 * MIB),
                  (NOW - datetime.timedelta(hours=1), OTHER_RUN, 500 * MIB)])
    v = budget.check(Config(), 100 * MIB, RUN, False, NOW)
    assert v.ok is True
    v = budget.check(Config(), 125 * MIB, RUN, False, NOW)
    assert v.ok is False and v.over == ["run"]


def test_run_usage_ignores_age(home):
    write_ledger([(NOW - datetime.timedelta(days=3), RUN, 1000 * MIB)])
    h = budget.headroom(Config(), RUN, NOW)
    assert h.run_mb_used == 1000.0
    assert h.day_mb_used == 0.0


def test_day_cap_and_multiple_over(home):
    cfg = Config(day_max_mb=300, run_max_mb=150, max_mb=100)
    write_ledger([(NOW - datetime.timedelta(hours=2), OTHER_RUN, 250 * MIB),
                  (NOW - datetime.timedelta(hours=2), RUN, 100 * MIB)])
    v = budget.check(cfg, 101 * MIB, RUN, False, NOW)
    assert v.over == ["fetch", "run", "24h"]


def test_rolling_24h_excludes_old_entries(home):
    write_ledger([(NOW - datetime.timedelta(hours=25), OTHER_RUN, 2000 * MIB),
                  (NOW - datetime.timedelta(hours=23), OTHER_RUN, 1000 * MIB)])
    h = budget.headroom(Config(), RUN, NOW)
    assert h.day_mb_used == 1000.0
    v = budget.check(Config(), 100 * MIB, RUN, False, NOW)
    assert v.over == []
    big = Config(max_mb=5000, run_max_mb=5000)
    v = budget.check(big, 1100 * MIB, RUN, False, NOW)  # 1000 used + 1100 > 2048
    assert v.over == ["24h"]


def test_exactly_24h_old_entry_is_excluded(home):
    write_ledger([(NOW - datetime.timedelta(hours=24), OTHER_RUN, 500 * MIB)])
    assert budget.headroom(Config(), RUN, NOW).day_mb_used == 0.0


def test_future_dated_entry_counts(home):
    write_ledger([(NOW + datetime.timedelta(hours=3), OTHER_RUN, 500 * MIB)])
    assert budget.headroom(Config(), RUN, NOW).day_mb_used == 500.0


def test_run_id_none_checks_fetch_and_day_only(home):
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 1000 * MIB)])
    h = budget.headroom(Config(), None, NOW)
    assert h.run_mb_used == 0.0 and h.day_mb_used == 1000.0
    v = budget.check(Config(), 100 * MIB, None, False, NOW)
    assert v.ok is True


def test_headroom_fetch_mb_is_effective_allowance(home):
    assert budget.headroom(Config(), RUN, NOW).fetch_mb == 200.0
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 1000 * MIB)])
    assert budget.headroom(Config(), RUN, NOW).fetch_mb == 24.0
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 5000 * MIB)])
    assert budget.headroom(Config(), RUN, NOW).fetch_mb == 0.0


def test_no_ledger_means_zero_usage_and_no_files_created(home):
    h = budget.headroom(Config(), RUN, NOW)
    assert (h.run_mb_used, h.day_mb_used) == (0.0, 0.0)
    assert not (home / ".local").exists()


def test_caps_come_from_config_not_env(home, monkeypatch):
    monkeypatch.setenv("MAX_MB", "999999")
    monkeypatch.setenv("S3LOGS_MAX_MB", "999999")
    v = budget.check(Config(), 201 * MIB, RUN, False, NOW)
    assert v.over == ["fetch"]


# ---- override marker --------------------------------------------------------

def test_force_without_marker_refused(home):
    with pytest.raises(Refused) as e:
        budget.check(Config(), 201 * MIB, RUN, True, NOW)
    assert "override needs the user's marker file (created by the user, not the agent) and --force" in str(e.value)


def test_force_without_marker_refused_even_when_under_cap(home):
    with pytest.raises(Refused):
        budget.check(Config(), 1, RUN, True, NOW)


def test_marker_without_force_does_not_override(home):
    make_marker()
    v = budget.check(Config(), 201 * MIB, RUN, False, NOW)
    assert v.ok is False and v.over == ["fetch"] and v.override_used is False


def test_stale_marker_refused(home):
    make_marker(age_s=1800)  # equal to the TTL is stale
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)
    make_marker(age_s=3600)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)


def test_fresh_marker_plus_force_allows(home):
    make_marker(age_s=1799)
    v = budget.check(Config(), 201 * MIB, RUN, True, NOW)
    assert v.ok is True and v.over == ["fetch"] and v.override_used is True


def test_fresh_marker_plus_force_under_cap_not_marked_used(home):
    make_marker(age_s=10)
    v = budget.check(Config(), 1 * MIB, RUN, True, NOW)
    assert v.ok is True and v.over == [] and v.override_used is False


def test_marker_ttl_from_config(home):
    make_marker(age_s=100)
    with pytest.raises(Refused):
        budget.check(Config(marker_ttl_s=60), 201 * MIB, RUN, True, NOW)


def test_future_mtime_marker_not_fresh(home):
    make_marker(age_s=-3600)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)


def test_symlink_marker_refused(home, tmp_path):
    target = tmp_path / "elsewhere"
    target.write_text("")
    os.utime(str(target), (NOW.timestamp(), NOW.timestamp()))
    p = paths.marker_path()
    p.parent.mkdir(parents=True)
    p.symlink_to(target)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)


def test_directory_marker_refused(home):
    p = paths.marker_path()
    p.mkdir(parents=True)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)


def test_marker_owned_by_someone_else_refused(home, monkeypatch):
    make_marker()
    real = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: real + 1)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)


def test_code_never_creates_or_touches_marker(home):
    for force in (False,):
        budget.check(Config(), 201 * MIB, RUN, force, NOW)
    with pytest.raises(Refused):
        budget.check(Config(), 201 * MIB, RUN, True, NOW)
    budget.charge(RUN, "ds", 5, NOW)
    assert not paths.marker_path().exists()


# ---- ledger: fail closed -------------------------------------------------------

@pytest.mark.parametrize("bad", [
    "not json",
    "",
    "[]",
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d"}',
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d", "bytes": "5"}',
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d", "bytes": 5.0}',
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d", "bytes": -1}',
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d", "bytes": true}',
    '{"ts": "2026-03-09T11:00:00Z", "run": "r", "dataset": "d", "bytes": NaN}',
    '{"ts": "yesterday", "run": "r", "dataset": "d", "bytes": 5}',
    '{"ts": "2026-03-09T11:00:00", "run": "r", "dataset": "d", "bytes": 5}',
    '{"ts": 5, "run": "r", "dataset": "d", "bytes": 5}',
    '{"ts": "2026-03-09T11:00:00Z", "run": 7, "dataset": "d", "bytes": 5}',
])
def test_ledger_bytes_are_ints_only(home, bad):
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 10 * MIB)], raw_extra=bad)
    for call in (lambda: budget.headroom(Config(), RUN, NOW),
                 lambda: budget.check(Config(), 1, RUN, False, NOW)):
        with pytest.raises(Refused) as e:
            call()
        assert str(ledger_path()) in str(e.value)


def test_truncated_last_line_refused(home):
    write_ledger([(NOW - datetime.timedelta(hours=1), RUN, 10 * MIB)])
    with open(str(ledger_path()), "a") as f:
        f.write('{"ts": "2026-03-09T11:00:00Z", "run"')
    with pytest.raises(Refused) as e:
        budget.headroom(Config(), RUN, NOW)
    assert str(ledger_path()) in str(e.value)


def test_non_utf8_ledger_refused(home):
    paths.ensure_private_dirs()
    ledger_path().write_bytes(b"\xff\xfe\n")
    with pytest.raises(Refused):
        budget.headroom(Config(), RUN, NOW)


def test_symlink_ledger_refused(home, tmp_path):
    paths.ensure_private_dirs()
    t = tmp_path / "real.jsonl"
    t.write_text("")
    ledger_path().symlink_to(t)
    with pytest.raises(Refused):
        budget.headroom(Config(), RUN, NOW)
    with pytest.raises(Refused):
        budget.charge(RUN, "ds", 1, NOW)


def test_naive_now_rejected(home):
    naive = datetime.datetime(2026, 3, 9, 12, 0, 0)
    with pytest.raises(ValueError):
        budget.headroom(Config(), RUN, naive)
    with pytest.raises(ValueError):
        budget.check(Config(), 1, RUN, False, naive)
    with pytest.raises(ValueError):
        budget.charge(RUN, "ds", 1, naive)


def test_non_utc_aware_now_is_normalised(home):
    plus7 = datetime.timezone(datetime.timedelta(hours=7))
    budget.charge(RUN, "ds", 5, NOW.astimezone(plus7))
    rec = json.loads(ledger_path().read_text().splitlines()[0])
    assert rec["ts"] == "2026-03-09T12:00:00Z"


def test_bad_planned_bytes_is_value_error(home):
    for bad in (-1, 1.5, "5", True, None):
        with pytest.raises(ValueError):
            budget.check(Config(), bad, RUN, False, NOW)


# ---- charge -----------------------------------------------------------------

def test_charge_writes_exact_line_and_private_modes(home):
    budget.charge(RUN, "cf-main", 12345, NOW)
    budget.charge(RUN, "cf-main", 0, NOW)
    lines = ledger_path().read_text().splitlines()
    assert json.loads(lines[0]) == {"ts": "2026-03-09T12:00:00Z", "run": RUN,
                                    "dataset": "cf-main", "bytes": 12345}
    assert json.loads(lines[1])["bytes"] == 0
    assert oct(ledger_path().stat().st_mode & 0o777) == oct(0o600)
    assert (paths.state_root() / "budgets" / ".lock").exists()
    h = budget.headroom(Config(), RUN, NOW)
    assert h.run_mb_used == pytest.approx(12345 / MIB)


@pytest.mark.parametrize("run,ds,n", [
    ("Bad Run", "ds", 1), (RUN, "Bad/Dataset", 1), (RUN, "ds", -1),
    (RUN, "ds", 1.5), (RUN, "ds", "5"), (RUN, "ds", True), (RUN, "ds", None),
])
def test_charge_validates_inputs_before_writing(home, run, ds, n):
    with pytest.raises(Refused):
        budget.charge(run, ds, n, NOW)
    assert not ledger_path().exists()


def _worker(n):
    now = datetime.datetime(2026, 3, 9, 12, 0, 0, tzinfo=datetime.timezone.utc)
    for _ in range(n):
        budget.charge(RUN, "ds", 7, now)


def test_concurrent_charges_not_lost(home):
    paths.ensure_private_dirs()
    ctx = multiprocessing.get_context("spawn")
    procs = [ctx.Process(target=_worker, args=(50,)) for _ in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(120)
        assert p.exitcode == 0
    lines = ledger_path().read_text().split("\n")
    assert lines[-1] == ""
    recs = [json.loads(x) for x in lines[:-1]]
    assert len(recs) == 100
    assert all(r == {"ts": "2026-03-09T12:00:00Z", "run": RUN, "dataset": "ds", "bytes": 7} for r in recs)
    assert budget.headroom(Config(), RUN, NOW).run_mb_used == pytest.approx(700 / MIB)


# ---- write failures and the documented limitation --------------------------

def test_charge_write_failure_is_refused_naming_the_ledger(home, monkeypatch):
    import errno

    def boom(fd, data):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(budget.os, "write", boom)
    with pytest.raises(Refused) as ei:
        budget.charge(RUN, "ds", 10, NOW)
    msg = str(ei.value)
    assert "ledger.jsonl" in msg and "remove only the last partial line" in msg


def test_charge_fsync_failure_is_refused_naming_the_ledger(home, monkeypatch):
    import errno

    def boom(fd):
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(budget.os, "fsync", boom)
    with pytest.raises(Refused) as ei:
        budget.charge(RUN, "ds", 10, NOW)
    assert "ledger.jsonl" in str(ei.value) and "remove only the last partial line" in str(ei.value)


def test_module_docstring_states_the_marker_limitation():
    doc = " ".join(budget.__doc__.split())
    assert "same user" in doc and "can create the marker" in doc
    assert "the instruction" in doc and "credentials" in doc
