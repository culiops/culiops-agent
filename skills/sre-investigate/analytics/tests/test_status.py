from __future__ import annotations

import subprocess

import pytest

from conftest import BIN

from s3logs import cli_status

AWS_OK = "aws-cli/2.15.0 Python/3.11.6 Linux/6.8.0 exe/x86_64.ubuntu.24"
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
    stub_path.write("aws", AWS_OK)


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
    stub_path.write("aws", AWS_OK)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd 2.1.0 < 2.2.0)"


def test_status_off_s5cmd_missing(home, stub_path, capsys):
    stub_path.isolate()
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    stub_path.write("aws", AWS_OK)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd missing)"


def test_status_off_s5cmd_unreadable_version(home, stub_path, capsys):
    stub_path.write("s5cmd", "dev-build")
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    stub_path.write("aws", AWS_OK)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd version unreadable)"


def test_status_off_old_duckdb(home, stub_path, capsys):
    stub_path.write("s5cmd", "v2.3.0")
    stub_path.write("duckdb", "v1.3.2 (Ossivalis) 0123456789")
    stub_path.write("aws", AWS_OK)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (duckdb 1.3.2 < 1.4.0)"


def test_status_off_duckdb_missing(home, stub_path, capsys):
    stub_path.isolate()
    stub_path.write("s5cmd", "v2.3.0")
    stub_path.write("aws", AWS_OK)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (duckdb missing)"


def test_status_s5cmd_reason_comes_before_duckdb(home, stub_path, capsys):
    stub_path.isolate()
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (s5cmd missing)"


def test_status_off_aws_missing(home, stub_path, capsys):
    stub_path.isolate()
    stub_path.write("s5cmd", "v2.3.0")
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (aws CLI 2.9+ not found)"


@pytest.mark.parametrize("banner,reason", [
    ("aws-cli/2.8.12 Python/3.11.6 Linux/6.8.0", "aws CLI 2.8.12 < 2.9.0"),
    ("aws-cli/1.27.0 Python/3.10.0 Linux/6.8.0 botocore/1.29.0", "aws CLI 1.27.0 < 2.9.0"),
    ("dev-build", "aws CLI version unreadable"),
])
def test_status_off_aws_too_old_or_unreadable(home, stub_path, capsys, banner, reason):
    good_tools(stub_path)
    stub_path.write("aws", banner)
    configure(home, GOOD_DS)
    assert run_status(capsys) == "S3 log module: off (%s)" % reason


def test_status_accepts_the_shared_aws_stub(home, fake_s3, stub_path, capsys):
    stub_path.write("duckdb", "v1.5.6 (Variegata) 9a8b7c6d5e")
    configure(home, GOOD_DS)
    out = run_status(capsys)
    assert out.startswith("S3 log module: on (") and "aws 2.15.0" in out


def test_status_aws_2_9_0_is_enough_and_is_reported(home, stub_path, capsys):
    good_tools(stub_path)
    stub_path.write("aws", "aws-cli/2.9.0 Python/3.9.11 Linux/6.8.0")
    configure(home, GOOD_DS)
    assert run_status(capsys).endswith("s5cmd 2.3.0, duckdb 1.5.6, aws 2.9.0)")


def test_status_aws_banner_on_stderr_is_read(home, stub_path, capsys):
    good_tools(stub_path)
    stub_path.write_script("aws", "echo 'aws-cli/2.15.0 Python/3.11.6' >&2")
    configure(home, GOOD_DS)
    assert "aws 2.15.0" in run_status(capsys)


def test_status_off_no_datasets(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, "MAX_MB=10\n")
    assert run_status(capsys) == "S3 log module: off (no datasets configured)"


def test_status_on(home, stub_path, capsys):
    good_tools(stub_path)
    configure(home, GOOD_DS + "DATASET_alb-main=alb:s3://example-logs-bucket/alb/{yyyy}/{MM}/{dd}/\n")
    assert run_status(capsys) == (
        "S3 log module: on (datasets: cdn[cloudfront], alb-main[alb]; s5cmd 2.3.0, duckdb 1.5.6, aws 2.15.0)"
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
    assert r.stdout == "S3 log module: on (datasets: cdn[cloudfront]; s5cmd 2.3.0, duckdb 1.5.6, aws 2.15.0)\n"
