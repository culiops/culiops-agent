from __future__ import annotations

import inspect
import json

import pytest

from s3logs import awscli
from s3logs.awscli import AwsError, Entry
from s3logs.validate import Refused

BUCKET = "example-logs-bucket"
ALLOWED_OPTIONS = {"--bucket", "--prefix", "--profile", "--region", "--output",
                   "--starting-token", "--page-size"}


def put(fake_s3, key, data=b"x" * 10):
    p = fake_s3.bucket(BUCKET) / key
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def test_lists_entries_with_size_and_unquoted_etag(fake_s3):
    put(fake_s3, "cf/a.gz", b"x" * 7)
    put(fake_s3, "cf/b.gz", b"y" * 9)
    put(fake_s3, "other/c.gz")
    got = list(awscli.list_objects(BUCKET, "cf/", None, None))
    assert [e.key for e in got] == ["cf/a.gz", "cf/b.gz"]
    assert [e.size for e in got] == [7, 9]
    assert all(isinstance(e, Entry) and e.etag and '"' not in e.etag for e in got)


def test_empty_listing_yields_nothing(fake_s3):
    fake_s3.bucket(BUCKET)
    assert list(awscli.list_objects(BUCKET, "cf/", None, None)) == []


def test_wrapper_argv_allow_list(fake_s3):
    put(fake_s3, "cf/a.gz")
    list(awscli.list_objects(BUCKET, "cf/", "sre-read", "eu-west-1"))
    list(awscli.list_objects(BUCKET, "cf/", None, None))
    calls = fake_s3.calls()
    assert len(calls) == 2
    for argv in calls:
        assert argv[:2] == ["s3api", "list-objects-v2"]
        options = [a for a in argv[2:] if a.startswith("--")]
        assert set(options) <= ALLOWED_OPTIONS
        assert {"--bucket", "--prefix", "--output", "--page-size"} <= set(options)
        assert argv[argv.index("--output") + 1] == "json"
        assert argv[argv.index("--page-size") + 1] == "1000"
    assert calls[0][calls[0].index("--profile") + 1] == "sre-read"
    assert calls[0][calls[0].index("--region") + 1] == "eu-west-1"
    assert "--profile" not in calls[1] and "--region" not in calls[1]


def test_no_other_aws_api_is_exposed():
    public_callables = {n for n, o in vars(awscli).items()
                        if inspect.isfunction(o) and not n.startswith("_") and o.__module__ == awscli.__name__}
    assert public_callables == {"list_objects", "export_credentials"}


def test_argv_check_rejects_anything_off_the_allow_list():
    good = ["aws", "s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", "cf/",
            "--output", "json", "--page-size", "1000"]
    awscli._check_argv(good)
    for bad in (good + ["--delete"], ["aws", "s3", "ls"], ["aws", "s3api", "get-object"] + good[3:],
                good + ["--endpoint-url", "http://192.0.2.1"], good + ["--no-sign-request"]):
        with pytest.raises(Refused):
            awscli._check_argv(bad)


@pytest.mark.parametrize("bucket,prefix", [
    ("Bad Bucket", "cf/"), ("example-logs-bucket;rm", "cf/"), (BUCKET, "-x"), (BUCKET, "cf/a b"),
    (BUCKET, ""), (BUCKET, "cf/../x"),
])
def test_bad_bucket_or_prefix_refused_before_running(fake_s3, bucket, prefix):
    with pytest.raises(Refused):
        list(awscli.list_objects(bucket, prefix, None, None))
    assert fake_s3.calls() == []


def test_bad_profile_or_region_refused(fake_s3):
    with pytest.raises(Refused):
        list(awscli.list_objects(BUCKET, "cf/", "--endpoint-url=x", None))
    with pytest.raises(Refused):
        list(awscli.list_objects(BUCKET, "cf/", None, "us east"))
    assert fake_s3.calls() == []


@pytest.mark.parametrize("text", [
    "An error occurred (ExpiredToken) when calling the ListObjectsV2 operation: The security token expired",
    "Error when retrieving token from sso: Token has expired and refresh failed",
    "The SSO session associated with this profile has expired or is otherwise invalid.",
])
def test_expired_session_gets_sso_login_hint(fake_s3, monkeypatch, text):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_AWS_ERROR", text)
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", "sre-read", None))
    assert ei.value.hint == "! aws sso login --profile sre-read"
    assert ei.value.msg


def test_expired_session_hint_without_profile(fake_s3, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_AWS_ERROR", "ExpiredToken")
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", None, None))
    assert ei.value.hint == "! aws sso login"


def test_other_aws_errors_map_to_aws_error_without_login_hint(fake_s3, monkeypatch):
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_AWS_ERROR", "An error occurred (AccessDenied) when calling the ListObjectsV2 operation")
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", "sre-read", None))
    assert "sso login" not in (ei.value.hint or "")
    assert "AccessDenied" in ei.value.msg


def test_missing_bucket_is_an_aws_error(fake_s3):
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects("example-missing-bucket", "cf/", None, None))
    assert "NoSuchBucket" in ei.value.msg


def test_aws_cli_not_installed_is_an_aws_error(stub_path):
    stub_path.isolate()
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", None, None))
    assert "aws" in ei.value.msg.lower() and ei.value.hint


def test_parse_page_tolerates_empty_output_and_empty_object():
    assert awscli._parse_page("") == ([], None)
    assert awscli._parse_page("{}") == ([], None)
    entries, token = awscli._parse_page(json.dumps(
        {"Contents": [{"Key": "k", "Size": 3, "ETag": "\"e\""}], "NextToken": "t1"}))
    assert entries == [Entry("k", 3, "e")] and token == "t1"


@pytest.mark.parametrize("payload", ["not json", "[]", '{"Contents": [{"Key": 5, "Size": 1, "ETag": "x"}]}',
                                     '{"Contents": [{"Key": "k", "Size": "big", "ETag": "x"}]}'])
def test_unexpected_listing_shape_is_an_aws_error(payload):
    with pytest.raises(AwsError):
        awscli._parse_page(payload)


def test_pagination_follows_next_token(monkeypatch):
    pages = [
        json.dumps({"Contents": [{"Key": "a", "Size": 1, "ETag": "\"1\""}], "NextToken": "tok1"}),
        json.dumps({"Contents": [{"Key": "b", "Size": 2, "ETag": "\"2\""}]}),
    ]
    seen = []

    def fake_run(argv, profile):
        seen.append(argv)
        return pages[len(seen) - 1]

    monkeypatch.setattr(awscli, "_run", fake_run)
    got = list(awscli.list_objects(BUCKET, "cf/", None, None))
    assert [e.key for e in got] == ["a", "b"]
    assert "--starting-token" not in seen[0]
    assert seen[1][seen[1].index("--starting-token") + 1] == "tok1"


# ---- export_credentials ------------------------------------------------------------------

SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
EXPORT_GOOD = ["aws", "configure", "export-credentials", "--profile", "sre-read", "--format", "process"]


def export_calls(fake_s3):
    return [c for c in fake_s3.calls() if c[:2] == ["configure", "export-credentials"]]


def test_export_credentials_returns_env_keys_and_builds_exact_argv(fake_s3):
    got = awscli.export_credentials("sre-read", "eu-west-1")
    assert got == {"AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE", "AWS_SECRET_ACCESS_KEY": SECRET,
                   "AWS_SESSION_TOKEN": "IQoJb3JpZ2luX2VjEXAMPLETOKEN"}
    assert export_calls(fake_s3) == [["configure", "export-credentials", "--profile", "sre-read",
                                      "--format", "process"]]


def test_export_credentials_without_profile_has_no_profile_option(fake_s3):
    awscli.export_credentials(None, None)
    assert export_calls(fake_s3) == [["configure", "export-credentials", "--format", "process"]]


def test_export_credentials_omits_token_key_when_absent(fake_s3, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_CREDS_NO_TOKEN", "1")
    got = awscli.export_credentials("sre-read", None)
    assert set(got) == {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}


def test_export_credentials_runs_without_shell_with_timeout_and_pager_off(fake_s3, monkeypatch):
    seen = {}
    real = awscli.subprocess.run

    def spy(cmd, **kw):
        seen.update(kw)
        seen["cmd"] = cmd
        return real(cmd, **kw)

    monkeypatch.setattr(awscli.subprocess, "run", spy)
    monkeypatch.setenv("AWS_PAGER", "less")
    awscli.export_credentials("sre-read", None)
    assert seen["shell"] is False and seen["timeout"] == 60
    assert seen["env"]["AWS_PAGER"] == "" and seen["env"]["AWS_CLI_AUTO_PROMPT"] == "off"
    assert seen["stdin"] == awscli.subprocess.DEVNULL
    assert seen["cmd"][1:3] == ["configure", "export-credentials"]


def test_export_credentials_timeout_is_an_aws_error(fake_s3, monkeypatch):
    def boom(cmd, **kw):
        raise awscli.subprocess.TimeoutExpired(cmd, 60)

    monkeypatch.setattr(awscli.subprocess, "run", boom)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert "60" in ei.value.msg


@pytest.mark.parametrize("profile,region", [("--endpoint-url=x", None), ("a b", None), ("-x", None),
                                            (None, "us east"), ("sre-read", "us-east-1;id")])
def test_export_credentials_refuses_bad_profile_or_region(fake_s3, profile, region):
    with pytest.raises(Refused):
        awscli.export_credentials(profile, region)
    assert fake_s3.calls() == []


def test_export_credentials_failure_hides_stdout_and_scrubs_stderr(fake_s3, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_CREDS_STDOUT_AND_FAIL", '{"SecretAccessKey": "%s"}' % SECRET)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert SECRET not in ei.value.msg and SECRET not in str(ei.value) and SECRET not in repr(ei.value.hint)
    assert "export-credentials failed" in ei.value.msg
    assert ei.value.hint == "aws configure export-credentials needs AWS CLI v2.9 or newer and a working profile"


def test_export_credentials_stderr_is_cleaned(fake_s3, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_CREDS_ERROR", "bad\x1b[31m profile" + "x" * 5000)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert "\x1b" not in ei.value.msg and len(ei.value.msg) < 700


@pytest.mark.parametrize("text", [
    "The SSO session associated with this profile has expired or is otherwise invalid.",
    "Error when retrieving token from sso: Token has expired and refresh failed",
    "An error occurred (ExpiredToken) when calling the AssumeRole operation",
    "Error loading SSO Token: Token for https://example.com/start does not exist",
])
def test_export_credentials_login_hint(fake_s3, monkeypatch, text):
    monkeypatch.setenv("FAKE_AWS_CREDS_ERROR", text)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert ei.value.hint == "! aws sso login --profile sre-read"
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials(None, None)
    assert ei.value.hint == "! aws sso login"


@pytest.mark.parametrize("out", [
    "", "not json", "[]", "{}", '{"Version": 2, "AccessKeyId": "A", "SecretAccessKey": "B"}',
    '{"Version": 1, "SecretAccessKey": "B"}', '{"Version": 1, "AccessKeyId": "A"}',
    '{"Version": 1, "AccessKeyId": "", "SecretAccessKey": "B"}',
    '{"Version": 1, "AccessKeyId": 7, "SecretAccessKey": "B"}',
    '{"Version": 1, "AccessKeyId": "A", "SecretAccessKey": "B", "SessionToken": 5}',
    '{"Version": 1, "AccessKeyId": "A\\nB", "SecretAccessKey": "SECRETVALUE"}',
])
def test_export_credentials_bad_output_is_an_aws_error_without_the_output(fake_s3, monkeypatch, out):
    monkeypatch.setenv("FAKE_AWS_CREDS_STDOUT", out)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert "SECRETVALUE" not in ei.value.msg
    assert (out.strip() not in ei.value.msg) or not out.strip()
    assert ei.value.hint == "aws configure export-credentials needs AWS CLI v2.9 or newer and a working profile"


def test_export_credentials_aws_not_installed(stub_path):
    stub_path.isolate()
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert "aws" in ei.value.msg.lower() and ei.value.hint


def test_check_argv_allows_exactly_the_export_credentials_shapes():
    awscli._check_argv(EXPORT_GOOD)
    awscli._check_argv(["aws", "configure", "export-credentials", "--format", "process"])
    bad = [
        EXPORT_GOOD + ["--debug"],
        EXPORT_GOOD + ["--endpoint-url", "http://192.0.2.1"],
        EXPORT_GOOD + ["--region", "us-east-1"],
        EXPORT_GOOD[:-1] + ["env"],                                   # other format
        EXPORT_GOOD[:-2],                                             # no --format
        ["aws", "configure", "export-credentials"],
        ["aws", "configure", "export-credentials", "--format", "process", "--profile", "x"],   # order
        ["aws", "configure", "export-credentials", "--profile", "--format", "process"],
        ["aws", "configure", "export-credentials", "--profile", "-x", "--format", "process"],
        ["aws", "configure", "export-credentials", "--profile", "a", "--profile", "b", "--format", "process"],
        ["aws", "configure", "set", "aws_access_key_id", "x"],
        ["aws", "configure", "get", "aws_secret_access_key"],
        ["aws", "configure", "list"],
        ["aws", "configure"],
        ["aws", "sso", "login"],
        ["aws", "sts", "get-caller-identity"],
        ["aws", "configure", "export-credentials-x", "--format", "process"],
    ]
    for argv in bad:
        with pytest.raises(Refused):
            awscli._check_argv(argv)


def test_revoked_sso_token_gets_the_login_hint(fake_s3, monkeypatch):
    text = ("An error occurred (UnauthorizedException) when calling the GetRoleCredentials operation: "
            "Session token not found or invalid")
    monkeypatch.setenv("FAKE_AWS_CREDS_ERROR", text)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert ei.value.hint == "! aws sso login --profile sre-read"
    fake_s3.bucket(BUCKET)
    monkeypatch.setenv("FAKE_AWS_ERROR", text)
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", "sre-read", None))
    assert ei.value.hint == "! aws sso login --profile sre-read"


def test_export_timeout_has_its_own_hint_and_no_chained_traceback(fake_s3, monkeypatch):
    def boom(cmd, **kw):
        raise awscli.subprocess.TimeoutExpired(cmd, 60)

    monkeypatch.setattr(awscli.subprocess, "run", boom)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials("sre-read", None)
    assert ei.value.hint == ("the profile's credential lookup timed out; check the network or run "
                             "aws configure export-credentials --profile sre-read")
    assert ei.value.hint != awscli._EXPORT_HINT
    assert ei.value.__suppress_context__ and ei.value.__cause__ is None


def test_export_timeout_hint_without_a_profile(fake_s3, monkeypatch):
    def boom(cmd, **kw):
        raise awscli.subprocess.TimeoutExpired(cmd, 60)

    monkeypatch.setattr(awscli.subprocess, "run", boom)
    with pytest.raises(AwsError) as ei:
        awscli.export_credentials(None, None)
    assert ei.value.hint == ("the profile's credential lookup timed out; check the network or run "
                             "aws configure export-credentials")


def test_listing_timeout_hint_is_followable_for_a_one_day_range(fake_s3, monkeypatch):
    def boom(cmd, **kw):
        raise awscli.subprocess.TimeoutExpired(cmd, 600)

    monkeypatch.setattr(awscli.subprocess, "run", boom)
    with pytest.raises(AwsError) as ei:
        list(awscli.list_objects(BUCKET, "cf/", None, None))
    assert ei.value.hint == "re-run with a narrower day range, or check the network/prefix"
    assert ei.value.__suppress_context__


def test_long_session_tokens_are_accepted(fake_s3, monkeypatch):
    token = "T" * 10000
    monkeypatch.setenv("FAKE_AWS_CREDS_STDOUT", json.dumps(
        {"Version": 1, "AccessKeyId": "AKIAIOSFODNN7EXAMPLE", "SecretAccessKey": "k", "SessionToken": token}))
    assert awscli.export_credentials(None, None)["AWS_SESSION_TOKEN"] == token
    monkeypatch.setenv("FAKE_AWS_CREDS_STDOUT", json.dumps(
        {"Version": 1, "AccessKeyId": "AKIAIOSFODNN7EXAMPLE", "SecretAccessKey": "k", "SessionToken": "T" * 16385}))
    with pytest.raises(AwsError):
        awscli.export_credentials(None, None)
