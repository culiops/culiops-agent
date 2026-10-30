from __future__ import annotations

from decimal import Decimal

import pytest

from s3logs import config
from s3logs.config import Config, ConfigError, Dataset


def write_cfg(tmp_path, text):
    p = tmp_path / "logs.env"
    p.write_text(text)
    return p


def test_parses_strict_key_value(tmp_path):
    p = write_cfg(tmp_path, "DATASET_cdn=cloudfront:s3://logs-bucket/cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}\n")
    cfg = config.load(p)
    assert isinstance(cfg, Config)
    assert cfg.datasets == {
        "cdn": Dataset("cdn", "cloudfront", "logs-bucket", "cf/E2EXAMPLE.{yyyy}-{MM}-{dd}-{HH}")
    }
    assert cfg.max_mb == 200
    assert cfg.run_max_mb == 1024
    assert cfg.day_max_mb == 2048
    assert cfg.marker_ttl_s == 1800
    assert cfg.aws_profile is None and cfg.aws_region is None
    assert cfg.price_per_gb is None and cfg.price_per_1k_get is None
    assert cfg.identity_cookies == ("session", "sessionid", "sid", "jsessionid", "phpsessid", "connect.sid")
    assert cfg.identity_headers == ("authorization", "x-api-key")
    assert "token" in cfg.sensitive_params and "email" in cfg.sensitive_params
    assert isinstance(cfg.sensitive_params, frozenset)


def test_all_keys_parse(tmp_path):
    p = write_cfg(tmp_path, "\n".join([
        "AWS_PROFILE=example-profile",
        "AWS_REGION=eu-west-1",
        "DATASET_alb=alb:s3://example-logs-bucket/alb/AWSLogs/111122223333/elasticloadbalancing/eu-west-1/{yyyy}/{MM}/{dd}/",
        "DATASET_waf=waf:s3://example-logs-bucket/waf/{yyyy}/{MM}/{dd}/{HH}/",
        "PRICE_PER_GB=0.09",
        "PRICE_PER_1K_GET=0.0004",
        "MAX_MB=50",
        "RUN_MAX_MB=100",
        "DAY_MAX_MB=300",
        "MARKER_TTL_S=60",
        "WAF_IDENTITY_COOKIES=Sid,connect.sid",
        "WAF_IDENTITY_HEADERS=authorization",
        "SENSITIVE_PARAMS=token,Email",
    ]) + "\n")
    cfg = config.load(p)
    assert cfg.aws_profile == "example-profile" and cfg.aws_region == "eu-west-1"
    assert list(cfg.datasets) == ["alb", "waf"]
    assert cfg.datasets["waf"].type == "waf"
    assert cfg.price_per_gb == Decimal("0.09") and cfg.price_per_1k_get == Decimal("0.0004")
    assert (cfg.max_mb, cfg.run_max_mb, cfg.day_max_mb, cfg.marker_ttl_s) == (50, 100, 300, 60)
    assert cfg.identity_cookies == ("sid", "connect.sid")
    assert cfg.identity_headers == ("authorization",)
    assert cfg.sensitive_params == frozenset({"token", "email"})


def test_default_path_is_under_home(home):
    assert config.default_path() == home / ".config/culiops/sre-investigate/logs.env"
    d = home / ".config/culiops/sre-investigate"
    d.mkdir(parents=True)
    (d / "logs.env").write_text("DATASET_a=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/\n")
    assert list(config.load().datasets) == ["a"]


@pytest.mark.parametrize("line", [
    "X=$(id)", 'X="a"', "export X=1", "X=a;b", "X = 1", "X=a b",
    "AWS_PROFILE=$(id)", 'AWS_PROFILE="a"', "export AWS_PROFILE=1", "AWS_PROFILE=a;b",
    "AWS_PROFILE = a", "AWS_PROFILE=a b", "AWS_PROFILE=`id`", "AWS_PROFILE=a|b",
])
def test_rejects_shell_syntax(tmp_path, line):
    p = write_cfg(tmp_path, "# header\n\n" + line + "\n")
    with pytest.raises(ConfigError) as ei:
        config.load(p)
    assert ei.value.line == 3
    assert "line 3" in str(ei.value)


def test_unknown_key_rejected(tmp_path):
    for line in ["MAX_MBS=5", "max_mb=5", "dataset_cdn=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/",
                 "DATASET_CDN=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/", "DATASET_=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/",
                 "AWS_PROFILE_X=a"]:
        with pytest.raises(ConfigError) as ei:
            config.load(write_cfg(tmp_path, line + "\n"))
        assert ei.value.line == 1, line


def test_equals_allowed_in_value(tmp_path):
    p = write_cfg(tmp_path, "DATASET_waf=waf:s3://logs-bucket/year={yyyy}/month={MM}/day={dd}/\n")
    assert config.load(p).datasets["waf"].template == "year={yyyy}/month={MM}/day={dd}/"


def test_env_cannot_override_caps(tmp_path, monkeypatch):
    for k in ["MAX_MB", "RUN_MAX_MB", "DAY_MAX_MB", "MARKER_TTL_S"]:
        monkeypatch.setenv(k, "999999")
    p = write_cfg(tmp_path, "DATASET_a=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/\n")
    cfg = config.load(p)
    assert (cfg.max_mb, cfg.run_max_mb, cfg.day_max_mb, cfg.marker_ttl_s) == (200, 1024, 2048, 1800)


def test_template_requires_date_tokens(tmp_path):
    bad = [
        "cloudfront:s3://logs-bucket/cf/{yyyy}-{MM}",           # no {dd}
        "elb:s3://logs-bucket/{yyyy}/{MM}/{dd}/",               # unknown type
        "alb:s3://logs-bucket/{yyyy}/{dd}/",                    # no {MM}
        "alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/{mm}/",          # unknown token
        "alb:s3://logs-bucket/",                                # empty template
        "alb:s3://logs-bucket",                                 # no slash
        "alb:logs-bucket/{yyyy}/{MM}/{dd}/",                    # not s3://
        "alb:s3://Bad_Bucket/{yyyy}/{MM}/{dd}/",                # bad bucket
        "alb:s3://logs-bucket//{yyyy}/{MM}/{dd}/",              # leading slash
        "alb:s3://logs-bucket/../{yyyy}/{MM}/{dd}/",            # traversal
        "alb:s3://logs-bucket/a/{yyyy/{MM}/{dd}/",              # unbalanced
        "alb",                                                  # no colon
    ]
    for value in bad:
        with pytest.raises(ConfigError) as ei:
            config.load(write_cfg(tmp_path, "DATASET_a=" + value + "\n"))
        assert ei.value.line == 1, value
    # {HH} is optional
    ok = config.load(write_cfg(tmp_path, "DATASET_a=cloudfront:s3://logs-bucket/{yyyy}/{MM}/{dd}/{HH}/\n"))
    assert ok.datasets["a"].template == "{yyyy}/{MM}/{dd}/{HH}/"


def test_bad_values(tmp_path):
    for line in ["MAX_MB=0", "MAX_MB=-5", "MAX_MB=1.5", "MAX_MB=", "MARKER_TTL_S=abc",
                 "PRICE_PER_GB=abc", "PRICE_PER_GB=-1", "PRICE_PER_GB=NaN", "PRICE_PER_GB=Infinity",
                 "AWS_REGION=nowhere", "AWS_PROFILE=-x",
                 "WAF_IDENTITY_COOKIES=", "WAF_IDENTITY_COOKIES=a,,b", "SENSITIVE_PARAMS=a:b"]:
        with pytest.raises(ConfigError) as ei:
            config.load(write_cfg(tmp_path, line + "\n"))
        assert ei.value.line == 1, line


def test_duplicate_key_rejected(tmp_path):
    p = write_cfg(tmp_path, "MAX_MB=5\nMAX_MB=6\n")
    with pytest.raises(ConfigError) as ei:
        config.load(p)
    assert ei.value.line == 2


def test_comments_and_blank_lines_ignored(tmp_path):
    p = write_cfg(tmp_path, "\n# comment\n   # indented comment\n\nMAX_MB=10  # trailing comment\n  \n"
                            "DATASET_a=alb:s3://logs-bucket/{yyyy}/{MM}/{dd}/\n")
    cfg = config.load(p)
    assert cfg.max_mb == 10 and list(cfg.datasets) == ["a"]


def test_crlf_and_missing_file(tmp_path):
    cfg = config.load(write_cfg(tmp_path, "MAX_MB=10\r\n"))
    assert cfg.max_mb == 10
    with pytest.raises(ConfigError):
        config.load(tmp_path / "does-not-exist.env")
    with pytest.raises(ConfigError):
        config.load(tmp_path)  # a directory


def test_not_utf8(tmp_path):
    p = tmp_path / "logs.env"
    p.write_bytes(b"MAX_MB=\xff\xfe\n")
    with pytest.raises(ConfigError):
        config.load(p)


def test_example_file_parses_when_uncommented(tmp_path):
    import re
    from conftest import ANALYTICS

    src = (ANALYTICS / "logs.env.example").read_text().splitlines()
    # the file as shipped enables nothing
    shipped = tmp_path / "shipped.env"
    shipped.write_text("\n".join(src) + "\n")
    cfg = config.load(shipped)
    assert cfg.datasets == {} and cfg.max_mb == 200

    uncommented = [re.sub(r"^#(?=[A-Za-z][A-Za-z0-9_-]*=)", "", line) for line in src]
    p = tmp_path / "all.env"
    p.write_text("\n".join(uncommented) + "\n")
    cfg = config.load(p)
    assert set(cfg.datasets) == {"cdn", "cdn2", "alb", "waf", "waf-fh"}
    assert cfg.datasets["cdn"].type == "cloudfront" and cfg.aws_region == "us-east-1"
    assert cfg.price_per_gb == Decimal("0.09")
    assert cfg.sensitive_params == frozenset(config.DEFAULT_SENSITIVE_PARAMS)
    assert cfg.identity_cookies == config.DEFAULT_IDENTITY_COOKIES
