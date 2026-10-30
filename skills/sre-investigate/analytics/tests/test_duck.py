"""The locked-down DuckDB runner. Layer 2 of the SQL defences: these tests never go through
the SQL guard, so they show the lockdown holds on its own."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from s3logs import duck
from s3logs.duck import DuckError
from s3logs.validate import Refused


@pytest.fixture(autouse=True)
def _duck_on_path(duckdb_bin, monkeypatch):
    monkeypatch.setenv("PATH", os.path.dirname(duckdb_bin) + os.pathsep + os.environ.get("PATH", ""))


@pytest.fixture
def data(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "t.csv").write_text("a,b\n1,x\n2,y\n")
    return d


def test_basic_select_returns_csv_with_header(data):
    assert duck.run([], "SELECT 1 AS x", [data]) == "x\n1\n"


def test_external_file_read_blocked(data):
    with pytest.raises(DuckError):
        duck.run([], "SELECT * FROM read_csv('/etc/hostname')", [data])


def test_file_outside_allowed_dir_blocked_but_inside_works(data, tmp_path):
    other = tmp_path / "other.csv"
    other.write_text("a\n1\n")
    out = duck.run([], "SELECT count(*) AS n FROM read_csv(%s)" % duck.quote_literal(str(data / "t.csv")), [data])
    assert out == "n\n2\n"
    with pytest.raises(DuckError):
        duck.run([], "SELECT * FROM read_csv(%s)" % duck.quote_literal(str(other)), [data])


def test_config_locked(data):
    with pytest.raises(DuckError):
        duck.run([], "SET enable_external_access=true", [data])
    with pytest.raises(DuckError):
        duck.run([], "SET allowed_directories=['/']", [data])
    with pytest.raises(DuckError):
        duck.run([], "SET lock_configuration=false", [data])


def test_extensions_cannot_be_installed_or_loaded(data):
    for sql in ("INSTALL httpfs", "LOAD httpfs", "ATTACH '/tmp/x-not-created.db' AS x",
                "COPY (SELECT 1) TO '/tmp/x-not-created.csv'"):
        with pytest.raises(DuckError):
            duck.run([], sql, [data])
    assert not os.path.exists("/tmp/x-not-created.db") and not os.path.exists("/tmp/x-not-created.csv")


def test_env_minimal(data, monkeypatch):
    monkeypatch.setenv("AWS_PROFILE", "SECRETPROFILE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "SECRETKEY")
    for var in ("AWS_PROFILE", "AWS_SECRET_ACCESS_KEY"):
        for script, sql in (([], "SELECT getenv('%s') AS v" % var),
                            (["SET VARIABLE v = getenv('%s');" % var], "SELECT getvariable('v') AS v")):
            try:
                out = duck.run(script, sql, [data])
            except DuckError:
                continue  # getenv is disabled by the lockdown on newer versions; that is fine too
            assert "SECRET" not in out
            assert out.split("\n")[1] in ("", "NULL")


def test_child_env_has_exactly_four_keys(data, monkeypatch):
    seen = {}

    real_run = duck.subprocess.run

    def spy(*a, **kw):
        seen["env"] = dict(kw["env"])
        seen["cwd"] = kw["cwd"]
        return real_run(*a, **kw)

    monkeypatch.setattr(duck.subprocess, "run", spy)
    monkeypatch.setenv("AI_AGENT", "1")
    out = duck.run([], "SELECT 1 AS x", [data])
    assert out == "x\n1\n"  # no agent-mode output change
    assert set(seen["env"]) == {"PATH", "HOME", "TZ", "LC_ALL"}
    assert seen["env"]["TZ"] == "UTC" and seen["env"]["LC_ALL"] == "C"
    assert seen["env"]["PATH"].endswith(":/usr/bin:/bin")
    assert seen["env"]["HOME"] == seen["cwd"]
    assert not os.path.exists(seen["env"]["HOME"])  # the tmp HOME is removed afterwards


def test_home_is_empty_so_no_duckdbrc_loads(data, monkeypatch, tmp_path):
    rc_home = tmp_path / "rchome"
    rc_home.mkdir()
    (rc_home / ".duckdbrc").write_text("SELECT 'RCLOADED';\n")
    monkeypatch.setenv("HOME", str(rc_home))
    assert duck.run([], "SELECT 1 AS x", [data]) == "x\n1\n"


def test_stderr_scrubbed(data):
    missing = data / "missing.csv"
    with pytest.raises(DuckError) as ei:
        duck.run([], "SELECT * FROM read_csv(%s)" % duck.quote_literal(str(missing)), [data])
    msg = str(ei.value)
    assert "<staging>" in msg
    assert str(data) not in msg and str(data.resolve()) not in msg


@pytest.mark.parametrize("sql", [
    ".shell touch DOTPWNED",
    "   .shell touch DOTPWNED",
    "\t.system touch DOTPWNED",
    "SELECT 1;\n.shell touch DOTPWNED",
    "SELECT 1;\r.shell touch DOTPWNED",
    "SELECT 1;\x0b.shell touch DOTPWNED",
    "SELECT 1;\x85.shell touch DOTPWNED",
    "SELECT 1; .shell touch DOTPWNED",
    "SELECT '\n.shell touch DOTPWNED\n'",
    ".open /tmp/DOTPWNED.db",
])
def test_dot_command_lines_refused_before_duckdb_runs(data, tmp_path, monkeypatch, sql):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(Refused):
        duck.run([], sql, [data])
    with pytest.raises(Refused):
        duck.run([sql], "SELECT 1", [data])
    assert not (tmp_path / "DOTPWNED").exists()


def test_dot_inside_a_line_is_fine(data):
    assert duck.run([], "SELECT 1.5 AS x -- a. b\n", [data]) == "x\n1.5\n"
    assert duck.run([], "SELECT 'a\n  b.c' AS x", [data]).startswith("x\n")


def test_nul_in_script_refused(data):
    with pytest.raises(Refused):
        duck.run([], "SELECT 1\x00", [data])


def test_failed_setup_statement_stops_everything(data):
    # Without -bail the CLI keeps executing after an error (and only exits non-zero at the
    # end), so the user's SQL would run unlocked. Observable effect: it must not run at all.
    ran = data / "ran.csv"
    with pytest.raises(DuckError):
        duck.run(["SET no_such_setting_xyz=1;"],
                 "COPY (SELECT 'RAN' AS x) TO %s (HEADER)" % duck.quote_literal(str(ran)), [data], allow_writes=True)
    assert not ran.exists()


def test_script_sql_views_and_variables_survive_the_lock(data):
    t = duck.quote_literal(str(data / "t.csv"))
    script = ["CREATE VIEW logs AS SELECT * FROM read_csv(%s);" % t, "SET VARIABLE n = 7;"]
    assert duck.run(script, "SELECT count(*) AS c, getvariable('n') AS n FROM logs", [data]) == "c,n\n2,7\n"
    assert duck.run(script, "FROM (DESCRIBE logs)", [data]).startswith("column_name,column_type")


def test_symlink_inside_allowed_dir_refused(data, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("SYMLINKSECRET\n")
    (data / "link.txt").symlink_to(secret)
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [data])


def test_symlinked_subdir_and_dangling_link_refused(data, tmp_path):
    (data / "sub").mkdir()
    (data / "sub" / "dangling").symlink_to(tmp_path / "nowhere")
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [data])


def test_allowed_dir_itself_symlink_refused(data, tmp_path):
    link = tmp_path / "linkdir"
    link.symlink_to(data)
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [link])


def test_hardlink_inside_allowed_dir_refused(data, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("HARDLINKSECRET\n")
    os.link(str(outside), str(data / "hard.txt"))
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [data])


def test_fifo_inside_allowed_dir_refused(data):
    os.mkfifo(str(data / "fifo"))
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [data])


def test_relative_or_missing_allowed_dir_refused(data, tmp_path):
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [Path("relative")])
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [tmp_path / "missing"])
    with pytest.raises(Refused):
        duck.run([], "SELECT 1", [])


def test_write_into_allowed_dir_is_detected(data):
    target = duck.quote_literal(str(data / "planted.csv"))
    with pytest.raises(DuckError):
        duck.run([], "COPY (SELECT 1 AS x) TO %s (HEADER)" % target, [data])
    (data / "planted.csv").unlink()
    duck.run([], "COPY (SELECT 1 AS x) TO %s (HEADER)" % target, [data], allow_writes=True)
    assert (data / "planted.csv").exists()


def test_timeout_raises_duckerror(data):
    with pytest.raises(DuckError, match="timed out"):
        duck.run([], "SELECT count(*) FROM range(100000000000) a, range(1000) b", [data], timeout_s=1)


def test_duckdb_missing_raises_duckerror(data, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent-dir")
    with pytest.raises(DuckError, match="not found"):
        duck.run([], "SELECT 1", [data])


def test_quote_literal():
    assert duck.quote_literal("a'b") == "'a''b'"
    for bad in ("a\nb", "a\x00b", "a\rb", "a b"):
        with pytest.raises(Refused):
            duck.quote_literal(bad)


def test_hostile_path_cannot_inject_a_dot_command(tmp_path):
    d = tmp_path / "x'; SELECT 1; --"
    d.mkdir()
    # The quote is doubled, so the path stays one literal; the run simply works.
    assert duck.run([], "SELECT 1 AS x", [d]) == "x\n1\n"
