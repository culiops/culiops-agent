from __future__ import annotations

import subprocess

from conftest import BIN

from s3logs import cli_status

GOOD_DS = "DATASET_cdn=cloudfront:s3://example-logs-bucket/cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}\n"


def configure(home, text):
    d = home / ".config/culiops/sre-investigate"
    d.mkdir(parents=True, exist_ok=True)
    (d / "logs.env").write_text(text)


def run_status(capsys):
    rc = cli_status.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.count("\n") == 1  # exactly one line
    return out.rstrip("\n")


def good_tools(stub_path):
    stub_path.write("s5cmd", "v2.3.0-991c9fb")
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")


def test_status_off_not_configured(home, stub_path, capsys):
    good_tools(stub_path)
    assert run_status(capsys) == "S3 log module: off (not configured)"


def test_status_off_config_error(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, "# header\n" + GOOD_DS + "MAX_MB=$(id)\n")
    out = run_status(capsys)
    assert out.startswith("S3 log module: off (config error: line 3: ")
    assert out.endswith(")")


def test_status_config_error_beats_missing_tools(home, stub_path, capsys):
    stub_path.isolate()
    configure(home, "BOGUS=1\n")
    assert run_status(capsys).startswith("S3 log module: off (config error: line 1: ")


def test_status_off_old_s5cmd(home, stub_path, capsys):
    stub_path.write("s5cmd", "v2.1.0")
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd 2.1.0 < 2.2.0)"


def test_status_off_s5cmd_missing(home, stub_path, capsys):
    stub_path.isolate()
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd missing)"


def test_status_off_s5cmd_unreadable_version(home, stub_path, capsys):
    stub_path.write("s5cmd", "dev-build")
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd version unreadable)"


def test_status_off_old_duckdb(home, stub_path, capsys):
    stub_path.write("s5cmd", "v2.3.0")
    stub_path.write("duckdb", "v1.3.2 (Ossivalis) 0123456789")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (duckdb 1.3.2 < 1.4.0)"


def test_status_off_duckdb_missing(home, stub_path, capsys):
    stub_path.isolate()
    stub_path.write("s5cmd", "v2.3.0")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (duckdb missing)"


def test_status_s5cmd_reason_comes_before_duckdb(home, stub_path, capsys):
    stub_path.isolate()
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd missing)"


def test_status_off_no_datasets(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, "MAX_MB=10\n")
    assert run_status(capsys) == "S3 log module: off (no datasets configured)"


def test_status_on(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, GOOD_DS + "DATASET_alb-main=alb:s3://example-logs-bucket/alb/{yyyy}/{MM}/{dd}/\n")
    assert run_status(capsys) == (
        "S3 log module: on (datasets: cdn[cloudfront], alb-main[alb]; s5cmd 2.3.0, duckdb 1.5.6)"
    )


def test_status_never_creates_state(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, GOOD_DS)
    run_status(capsys)
    assert not (home / ".local").exists()


def test_bin_wrapper_runs_and_is_executable(home, stub_path):
    wrapper = BIN / "logs-status"
    assert wrapper.stat().st_mode & 0o111 == 0o111
    good_tools(stub_path)
    configure(home, GOOD_DS)
    r = subprocess.run([str(wrapper)], capture_output=True, text=True, cwd=str(home))
    assert r.returncode == 0, r.stderr
    assert r.stdout == "S3 log module: on (datasets: cdn[cloudfront]; s5cmd 2.3.0, duckdb 1.5.6)\n"
