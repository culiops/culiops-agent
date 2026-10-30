from __future__ import annotations

import datetime as dt
import gzip
import re

import pytest

import gen_fixtures as gf

DAY = dt.date(2026, 3, 9)
DOC_IP = re.compile(r"\b(192\.0\.2|198\.51\.100|203\.0\.113)\.\d+\b")
ANY_IP = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


@pytest.mark.parametrize("kind", ["cloudfront", "alb", "waf"])
def test_deterministic_and_placeholder_only(tmp_path, kind):
    a = gf.make(tmp_path / "a", kind, DAY, hours=[1, 2])
    b = gf.make(tmp_path / "b", kind, DAY, hours=[1, 2])
    assert a == b and a
    for key in a:
        pa = (tmp_path / "a" / gf.BUCKET / key).read_bytes()
        assert pa == (tmp_path / "b" / gf.BUCKET / key).read_bytes()
        text = gzip.decompress(pa).decode()
        assert text.strip()
        for ip in ANY_IP.findall(text):
            assert DOC_IP.fullmatch(ip), ip
        assert "example.com" in text or kind == "cloudfront"


def test_cloudfront_legacy_has_fields_header_and_json_variant(tmp_path):
    (key,) = gf.make(tmp_path, "cloudfront", DAY, hours=[3])
    assert gzip.decompress((tmp_path / gf.BUCKET / key).read_bytes()).decode().startswith("#Version: 1.0\n#Fields: ")
    (jkey,) = gf.make(tmp_path, "cloudfront", DAY, hours=[3], fmt="json")
    assert jkey.endswith(".json.gz")


@pytest.mark.parametrize("kind", ["cloudfront", "alb", "waf"])
def test_query_fixtures_deterministic_and_placeholder_only(tmp_path, kind):
    a = gf.make_queries(tmp_path / "a", kind, DAY)
    b = gf.make_queries(tmp_path / "b", kind, DAY)
    assert a == b and a
    for key in a:
        pa = (tmp_path / "a" / gf.BUCKET / key).read_bytes()
        assert pa == (tmp_path / "b" / gf.BUCKET / key).read_bytes()
        text = gzip.decompress(pa).decode()
        for ip in ANY_IP.findall(text):
            assert DOC_IP.fullmatch(ip), ip
    with pytest.raises(ValueError):
        gf.make_queries(tmp_path, "nope", DAY)
