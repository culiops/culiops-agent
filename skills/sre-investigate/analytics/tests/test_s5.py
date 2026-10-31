"""s5cmd run-file builder, validator and runner. Review Focus 3: nothing but a safe key reaches s5cmd."""
from __future__ import annotations

import json
import subprocess

import pytest

from s3logs import s5
from s3logs.awscli import AwsError
from s3logs.validate import Refused

BUCKET = "example-logs-bucket"
BATCH = "/home/u/.local/share/culiops/sre-investigate/staging/0123456789abcdef0123456789abcdef"
KEYS = ["cf/E2EXAMPLE.2026-03-09-10.AAA.gz", "cf/E2EXAMPLE.2026-03-09-11.BBB.gz"]


def good():
    return s5.build_run_file(BUCKET, KEYS, BATCH)


def test_build_run_file_exact_lines():
    text = good()
    assert text == (
        "cp -n --raw s3://%s/%s %s/000001.gz\n"
        "cp -n --raw s3://%s/%s %s/000002.gz\n" % (BUCKET, KEYS[0], BATCH, BUCKET, KEYS[1], BATCH))
    s5.validate_run_file(text, BUCKET, BATCH)


@pytest.mark.parametrize("key", ["a b.gz", "a;b.gz", "../x.gz", "a/../x.gz", "a\nb.gz", "a*.gz", "a?b.gz",
                                 "a[1].gz", "$(id).gz", "a`id`.gz", "/abs.gz", "", "a'b.gz", "a\"b.gz",
                                 "a|b.gz", "a&b.gz", "a\\b.gz", "café.gz"])
def test_build_run_file_refuses_unsafe_keys(key):
    with pytest.raises(Refused):
        s5.build_run_file(BUCKET, [key], BATCH)


@pytest.mark.parametrize("batch", ["relative/dir", "/tmp/a b", "/tmp/a;b", "/tmp/$HOME", "/tmp/a\nb", "",
                                   "/tmp/it's", "/tmp/a*", "/tmp/café"])
def test_build_run_file_refuses_unsafe_batchdir(batch):
    with pytest.raises(Refused):
        s5.build_run_file(BUCKET, KEYS, batch)


def test_build_run_file_refuses_bad_bucket_and_empty():
    with pytest.raises(Refused):
        s5.build_run_file("Bad Bucket", KEYS, BATCH)
    with pytest.raises(Refused):
        s5.build_run_file(BUCKET, [], BATCH)


def line(n=1, key=KEYS[0], dest=None):
    return "cp -n --raw s3://%s/%s %s" % (BUCKET, key, dest or "%s/%06d.gz" % (BATCH, n))


@pytest.mark.parametrize("bad", [
    line(1, key="x;rm -rf ~"),                                    # shell metacharacter
    line(1) + " /tmp/other.gz",                                   # a second destination
    line(1, key="a b.gz"),                                        # space in the key
    line(1, key="../x.gz"),                                       # dot segment
    line(1, key="a/../../x.gz"),
    line(1, dest="/tmp/elsewhere/000001.gz"),                     # destination outside the batch dir
    line(1, dest=BATCH + "/../000001.gz"),
    line(1, dest=BATCH + "/sub/000001.gz"),
    line(1, dest=BATCH + "/1.gz"),                                # counter not zero padded
    line(1, dest=BATCH + "/000001.gz;id"),
    "cp -n --raw s3://other-bucket/k.gz %s/000001.gz" % BATCH,    # wrong bucket
    "cp --raw s3://%s/k.gz %s/000001.gz" % (BUCKET, BATCH),       # missing -n
    "cp -n s3://%s/k.gz %s/000001.gz" % (BUCKET, BATCH),          # missing --raw
    "rm s3://%s/k.gz" % BUCKET,                                   # another command
    "mv -n --raw s3://%s/k.gz %s/000001.gz" % (BUCKET, BATCH),
    "cp -n --raw  s3://%s/k.gz %s/000001.gz" % (BUCKET, BATCH),   # double space
    " " + line(1),
    line(1) + " ",
    line(1) + "\r",
    "",
])
def test_run_file_rejects_unsafe_line(bad):
    """Review Focus 3: a ';', a second destination or '../' raises Refused."""
    with pytest.raises(Refused):
        s5.validate_run_file(bad + "\n", BUCKET, BATCH)
    # also when it hides behind a legitimate first line
    with pytest.raises(Refused):
        s5.validate_run_file(line(1) + "\n" + bad.replace("000001", "000002") + "\n", BUCKET, BATCH)


def test_run_file_rejects_structural_problems():
    ok = good()
    s5.validate_run_file(ok, BUCKET, BATCH)
    for bad in ("", "\n", ok.rstrip("\n"), ok + "\n", line(2) + "\n",             # no newline, blank, not from 1
                line(1) + "\n" + line(1) + "\n",                                   # duplicate destination
                line(1) + "\n" + line(3) + "\n",                                   # gap in the counter
                "cp -n --raw s3://%s/k.gz %s/000001.gz\x0b\n" % (BUCKET, BATCH)):
        with pytest.raises(Refused):
            s5.validate_run_file(bad, BUCKET, BATCH)


def test_run_file_refuses_bad_batchdir_and_bucket():
    with pytest.raises(Refused):
        s5.validate_run_file(good(), BUCKET, "relative")
    with pytest.raises(Refused):
        s5.validate_run_file(good(), "Bad Bucket", BATCH)


def test_validate_returns_pairs():
    pairs = s5.validate_run_file(good(), BUCKET, BATCH)
    assert [k for k, _ in pairs] == KEYS
    assert [d for _, d in pairs] == ["%s/000001.gz" % BATCH, "%s/000002.gz" % BATCH]


# ---- runner -----------------------------------------------------------------------------------

@pytest.fixture
def batch(tmp_path):
    d = tmp_path / "batch"
    d.mkdir()
    return d


def write_run(batch, keys, name="batch.run"):
    text = s5.build_run_file(BUCKET, keys, str(batch))
    p = batch / name
    p.write_text(text)
    return p


def test_run_copies_files_and_builds_argv(fake_s3, batch):
    b = fake_s3.bucket(BUCKET)
    (b / "k").mkdir()
    (b / "k/a.gz").write_bytes(b"AAA")
    (b / "k/b.gz").write_bytes(b"BB")
    rf = write_run(batch, ["k/a.gz", "k/b.gz"])
    s5.run(rf, "sre-read", "us-east-1", str(batch), BUCKET)
    assert (batch / "000001.gz").read_bytes() == b"AAA"
    assert (batch / "000002.gz").read_bytes() == b"BB"
    calls = [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]]
    assert calls == [["s5cmd", "--log", "error", "run", str(rf)]]      # no --profile: keys come from the env


def test_run_without_profile_has_no_profile_option(fake_s3, batch):
    b = fake_s3.bucket(BUCKET)
    (b / "a.gz").write_bytes(b"A")
    s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    calls = [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]]
    assert calls[0][1:3] == ["--log", "error"]


def test_run_refuses_a_run_file_outside_the_batch_dir(fake_s3, batch, tmp_path):
    other = tmp_path / "other.run"
    other.write_text(s5.build_run_file(BUCKET, ["a.gz"], str(batch)))
    with pytest.raises(Refused):
        s5.run(other, None, None, str(batch), BUCKET)
    assert [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]] == []


@pytest.mark.parametrize("profile", ["-evil", "a b", "a;b", ""])
def test_run_refuses_bad_profile(fake_s3, batch, profile):
    fake_s3.bucket(BUCKET)
    rf = write_run(batch, ["a.gz"])
    with pytest.raises(Refused):
        s5.run(rf, profile, None, str(batch), BUCKET)


def test_run_refuses_bad_region(fake_s3, batch):
    fake_s3.bucket(BUCKET)
    with pytest.raises(Refused):
        s5.run(write_run(batch, ["a.gz"]), None, "us-east-1; id", str(batch), BUCKET)


def test_run_revalidates_the_run_file_content(fake_s3, batch):
    fake_s3.bucket(BUCKET)
    rf = batch / "batch.run"
    rf.write_text("cp -n --raw s3://%s/a.gz %s/000001.gz /tmp/x\n" % (BUCKET, batch))
    with pytest.raises(Refused):
        s5.run(rf, None, None, str(batch), BUCKET)
    assert [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]] == []


def test_expired_session_maps_to_aws_error_with_login_hint(fake_s3, batch, monkeypatch):
    b = fake_s3.bucket(BUCKET)
    (b / "a.gz").write_bytes(b"A")
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "ERROR ExpiredToken: The provided token has expired.")
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), "sre-read", None, str(batch), BUCKET)
    assert ei.value.hint == "! aws sso login --profile sre-read"


def test_expired_session_hint_without_profile(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "Token has expired and refresh failed")
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    assert ei.value.hint == "! aws sso login"


def test_other_failures_give_scrubbed_message_no_path_no_control_chars(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "ERROR AccessDenied: denied writing %s/000001.gz\x1b[31m\x07café" % batch)
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    msg = ei.value.msg
    assert str(batch) not in msg and "<staging>" in msg
    assert "\x1b" not in msg and "\x07" not in msg and all(ord(c) < 128 for c in msg)
    assert "AccessDenied" in msg
    assert len(msg) < 700


def test_partial_failure_message_does_not_leak_a_huge_stderr(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "ERROR " + "x" * 100000)
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    assert len(ei.value.msg) < 700


def test_missing_object_is_an_aws_error(fake_s3, batch):
    fake_s3.bucket(BUCKET)
    with pytest.raises(AwsError):
        s5.run(write_run(batch, ["nope.gz"]), None, None, str(batch), BUCKET)


def test_s5cmd_not_installed_is_refused(batch, stub_path):
    stub_path.isolate()
    rf = batch / "batch.run"
    rf.write_text(s5.build_run_file(BUCKET, ["a.gz"], str(batch)))
    with pytest.raises(Refused):
        s5.run(rf, None, None, str(batch), BUCKET)


def test_endpoint_override_env_is_not_passed_on(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    seen = {}
    real = subprocess.run

    def spy(cmd, **kw):
        seen["env"] = kw.get("env")
        seen["shell"] = kw.get("shell", False)
        return real(cmd, **kw)

    monkeypatch.setattr(s5.subprocess, "run", spy)
    monkeypatch.setenv("S5CMD_ENDPOINT_URL", "http://203.0.113.9")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://203.0.113.9")
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    s5.run(write_run(batch, ["a.gz"]), None, "eu-west-1", str(batch), BUCKET)
    env = seen["env"]
    assert "S5CMD_ENDPOINT_URL" not in env and "S3_ENDPOINT_URL" not in env
    assert env["AWS_REGION"] == "eu-west-1"
    assert seen["shell"] is False


def test_message_prefers_error_lines_over_warning_noise(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "2026/10/30 WARN: failed to get session token, falling back to IMDSv1\n"
                       "caused by: EC2MetadataError\nERROR session: fetching region failed: NoCredentialProviders: no valid providers")
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), "sre-read", None, str(batch), BUCKET)
    assert ei.value.msg.startswith("s5cmd exited 1: ERROR session:") and "IMDSv1" not in ei.value.msg
    assert ei.value.hint == "! aws sso login --profile sre-read"


def test_run_pins_the_configured_bucket(fake_s3, batch):
    """A run file naming a different (valid) bucket than the configured one is refused."""
    other = fake_s3.bucket("other-logs-bucket")
    (other / "a.gz").write_bytes(b"A")
    rf = batch / "batch.run"
    rf.write_text(s5.build_run_file("other-logs-bucket", ["a.gz"], str(batch)))
    with pytest.raises(Refused):
        s5.run(rf, None, None, str(batch), BUCKET)
    assert [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]] == []
    assert not (batch / "000001.gz").exists()


# ---- credentials exported for s5cmd (R45) -------------------------------------------------------

SECRETS = ["AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "IQoJb3JpZ2luX2VjEXAMPLETOKEN"]


def export_calls(fake_s3):
    return [c for c in fake_s3.calls() if c[:2] == ["configure", "export-credentials"]]


def test_run_exports_credentials_first_and_starts_s5cmd_without_profile(fake_s3, batch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    rf = write_run(batch, ["a.gz"])
    s5.run(rf, "sre-read", "us-east-1", str(batch), BUCKET)
    calls = fake_s3.calls()
    assert [c[:2] for c in calls if c[:1] != ["s5cmd-run-file"]] == [["configure", "export-credentials"], ["s5cmd", "--log"]]
    assert export_calls(fake_s3) == [["configure", "export-credentials", "--profile", "sre-read",
                                      "--format", "process"]]
    s5calls = [c for c in calls if c[:1] == ["s5cmd"]]
    assert s5calls == [["s5cmd", "--log", "error", "run", str(rf)]]
    assert "--profile" not in s5calls[0]


def test_run_exports_credentials_even_without_a_profile(fake_s3, batch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    assert export_calls(fake_s3) == [["configure", "export-credentials", "--format", "process"]]


def test_each_call_refreshes_credentials(fake_s3, batch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    s5.run(write_run(batch, ["a.gz"], "one.run"), "sre-read", None, str(batch), BUCKET)
    (batch / "000001.gz").unlink()
    s5.run(write_run(batch, ["a.gz"], "two.run"), "sre-read", None, str(batch), BUCKET)
    assert len(export_calls(fake_s3)) == 2


def test_s5cmd_gets_exported_keys_and_no_profile_or_shared_file_env(fake_s3, batch, monkeypatch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    for k, v in (("AWS_PROFILE", "other"), ("AWS_DEFAULT_PROFILE", "other"),
                 ("AWS_SHARED_CREDENTIALS_FILE", "/nonexistent/creds"), ("AWS_CONFIG_FILE", "/nonexistent/config"),
                 ("AWS_ACCESS_KEY_ID", "STALE"), ("AWS_SESSION_TOKEN", "STALE"),
                 ("AWS_ENDPOINT_URL_S3", "http://203.0.113.9"), ("S5CMD_ENDPOINT_URL", "http://203.0.113.9")):
        monkeypatch.setenv(k, v)
    s5.run(write_run(batch, ["a.gz"]), "sre-read", "eu-west-1", str(batch), BUCKET)
    [env] = fake_s3.s5env()
    assert env["AWS_ACCESS_KEY_ID"] == SECRETS[0]
    assert env["AWS_SECRET_ACCESS_KEY"] == SECRETS[1]
    assert env["AWS_SESSION_TOKEN"] == SECRETS[2]
    assert env["AWS_REGION"] == "eu-west-1"
    for gone in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE",
                 "AWS_ENDPOINT_URL_S3", "S5CMD_ENDPOINT_URL"):
        assert gone not in env


def test_a_stale_session_token_is_not_passed_when_the_export_has_none(fake_s3, batch, monkeypatch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    monkeypatch.setenv("FAKE_AWS_CREDS_NO_TOKEN", "1")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "STALE")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "STALE")
    s5.run(write_run(batch, ["a.gz"]), None, None, str(batch), BUCKET)
    [env] = fake_s3.s5env()
    assert "AWS_SESSION_TOKEN" not in env and "AWS_SECURITY_TOKEN" not in env
    assert env["AWS_ACCESS_KEY_ID"] == SECRETS[0]


def test_failing_export_stops_before_s5cmd(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_AWS_CREDS_ERROR", "The SSO session associated with this profile has expired")
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), "sre-read", None, str(batch), BUCKET)
    assert ei.value.hint == "! aws sso login --profile sre-read"
    assert [c for c in fake_s3.calls() if c[:1] == ["s5cmd"]] == []


def test_validation_failures_do_not_export_credentials(fake_s3, batch, tmp_path):
    other = tmp_path / "other.run"
    other.write_text(s5.build_run_file(BUCKET, ["a.gz"], str(batch)))
    with pytest.raises(Refused):
        s5.run(other, "sre-read", None, str(batch), BUCKET)
    assert fake_s3.calls() == []


def test_secrets_never_appear_in_a_failing_s5cmd_error(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", "ERROR AccessDenied: denied")
    monkeypatch.setenv("FAKE_S5CMD_ECHO_ENV", "1")
    with pytest.raises(AwsError) as ei:
        s5.run(write_run(batch, ["a.gz"]), "sre-read", None, str(batch), BUCKET)
    text = "%s | %s | %r | %s" % (ei.value.msg, ei.value, ei.value.args, ei.value.hint)
    for secret in SECRETS:
        assert secret not in text
    assert "AccessDenied" in ei.value.msg          # the rest of the message still tells the story


def test_secrets_are_not_in_the_run_file_or_argv(fake_s3, batch):
    (fake_s3.bucket(BUCKET) / "a.gz").write_bytes(b"A")
    rf = write_run(batch, ["a.gz"])
    s5.run(rf, "sre-read", None, str(batch), BUCKET)
    blob = rf.read_text() + json.dumps(fake_s3.calls())
    for secret in SECRETS:
        assert secret not in blob


def fail_with_shared_creds_load(monkeypatch):
    monkeypatch.setenv("FAKE_S5CMD_FAIL_ON_BATCH", "1")
    monkeypatch.setenv("FAKE_S5CMD_ERROR", 'ERROR "cp s3://x/y z": SharedCredsLoad: failed to get profile')


def test_shared_creds_load_failure_gets_a_profile_hint(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    fail_with_shared_creds_load(monkeypatch)
    rf = write_run(batch, ["a.gz"])
    with pytest.raises(AwsError) as ei:
        s5.run(rf, "sre-read", None, str(batch), BUCKET)
    assert ei.value.hint == "run aws configure export-credentials --profile sre-read to check the profile"


def test_shared_creds_load_failure_hint_without_a_profile(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    fail_with_shared_creds_load(monkeypatch)
    rf = write_run(batch, ["a.gz"])
    with pytest.raises(AwsError) as ei:
        s5.run(rf, None, None, str(batch), BUCKET)
    assert ei.value.hint == "run aws configure export-credentials to check the profile"


def test_s5cmd_timeout_has_no_chained_traceback(fake_s3, batch, monkeypatch):
    fake_s3.bucket(BUCKET)
    rf = write_run(batch, ["a.gz"])
    real = s5.subprocess.run

    def fake_run(cmd, **kw):
        if "timeout" in kw and kw["timeout"] == s5._TIMEOUT_S:
            raise s5.subprocess.TimeoutExpired(cmd, kw["timeout"])
        return real(cmd, **kw)

    monkeypatch.setattr(s5.subprocess, "run", fake_run)
    with pytest.raises(AwsError) as ei:
        s5.run(rf, None, None, str(batch), BUCKET)
    assert "timed out" in ei.value.msg
    assert ei.value.__suppress_context__ and ei.value.__cause__ is None
