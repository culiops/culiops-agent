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
    assert public_callables == {"list_objects"}


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
