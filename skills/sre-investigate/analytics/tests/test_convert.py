"""Raw access logs -> redacted Parquet. Inputs come from gen_fixtures (placeholders only)."""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import os
import stat
from pathlib import Path

import pytest

from s3logs import convert, duck, paths, redact
from s3logs.config import Config
from s3logs.duck import DuckError
from s3logs.validate import Refused

import gen_fixtures as gf

CFG = Config()
SALT = bytes(range(32))
DAY = dt.date(2026, 3, 9)


@pytest.fixture(autouse=True)
def _duck_on_path(duckdb_bin, monkeypatch):
    monkeypatch.setenv("PATH", os.path.dirname(duckdb_bin) + os.pathsep + os.environ.get("PATH", ""))


@pytest.fixture
def work(home, tmp_path):
    """tmp HOME with the state tree, an input dir and an output dir."""
    paths.ensure_private_dirs()
    (tmp_path / "in").mkdir()
    (tmp_path / "out").mkdir()
    return tmp_path


def staging_entries():
    d = paths.state_root() / "staging"
    os.chmod(str(d), 0o700)
    try:
        return sorted(os.listdir(str(d)))
    finally:
        os.chmod(str(d), 0o300)


def gz_file(path: Path, text: str) -> Path:
    path.write_bytes(gf._gz(text))
    return path


def query(out: Path, sql: str):
    """Rows (list of dicts) of `sql` where {t} is the parquet file."""
    text = duck.run([], sql.format(t=duck.quote_literal(str(out))), [out.parent])
    return list(csv.DictReader(io.StringIO(text)))


def columns(out: Path):
    return {r["column_name"]: r["column_type"] for r in query(out, "FROM (DESCRIBE SELECT * FROM read_parquet({t}))")}


def all_text(out: Path) -> str:
    return duck.run([], "SELECT * FROM read_parquet(%s)" % duck.quote_literal(str(out)), [out.parent])


def make_raw(work, kind, **opts):
    keys = gf.make(work / "in", kind, DAY, **opts)
    return [work / "in" / gf.BUCKET / k for k in keys]


# ---- CloudFront ---------------------------------------------------------------------------

def test_cloudfront_roundtrip(work):
    raws = make_raw(work, "cloudfront", hours=[0, 1], records=3, secrets=True)
    out = work / "out" / "cf.parquet"
    res = convert.to_parquet("cloudfront", raws, out, CFG, SALT)
    assert res.rows == 6
    cols = columns(out)
    assert cols["ts"] == "TIMESTAMP"
    assert cols["sc_bytes"] == "BIGINT" and cols["time_taken"] == "DOUBLE" and cols["sc_status"] == "INTEGER"
    text = all_text(out)
    assert "SECRETTOKEN" not in text and "SECRETCOOKIE" not in text
    rows = query(out, "SELECT ts, cs_uri_query, cs_referer, cs_user_agent FROM read_parquet({t}) ORDER BY ts")
    assert rows[0]["ts"].startswith("2026-03-09 00:")
    assert rows[0]["cs_uri_query"] == "page=2&token=***"
    assert rows[0]["cs_referer"] == "https://www.example.com/p?token=***&a=1"
    assert "cs_cookie" not in cols
    assert res.dropped_columns == ("cs(Cookie)",)
    assert res.skipped_lines == 0


def test_cloudfront_inputs_are_deleted_and_staging_empty(work):
    raws = make_raw(work, "cloudfront", hours=[0], records=2)
    out = work / "out" / "cf.parquet"
    convert.to_parquet("cloudfront", raws, out, CFG, SALT)
    assert not any(p.exists() for p in raws)
    assert staging_entries() == []
    assert stat.S_IMODE(out.stat().st_mode) == 0o444


def test_cloudfront_ts_is_utc_date_plus_time(work):
    f = gz_file(work / "in" / "a.gz", "#Version: 1.0\n#Fields: date time c-ip\n2026-03-09\t23:59:58\t192.0.2.10\n")
    out = work / "out" / "o.parquet"
    convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert query(out, "SELECT strftime(ts, '%Y-%m-%dT%H:%M:%S') AS s FROM read_parquet({t})")[0]["s"] == "2026-03-09T23:59:58"


def test_cloudfront_v2_custom_fields(work):
    text = ("#Version: 1.0\n#Fields: date time c-ip cs-uri-stem sc-status x-custom-secret cs(Cookie)\n"
            "2026-03-09\t10:00:00\t192.0.2.10\t/api/orders\t200\tCUSTOMSECRET\tsessionid=SECRETCOOKIE\n")
    f = gz_file(work / "in" / "a.gz", text)
    out = work / "out" / "o.parquet"
    res = convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert res.rows == 1
    assert res.dropped_columns == ("x-custom-secret", "cs(Cookie)")
    rows = query(out, "SELECT c_ip, cs_uri_stem, sc_status, x_edge_location, cs_uri_query FROM read_parquet({t})")
    assert rows == [{"c_ip": "192.0.2.10", "cs_uri_stem": "/api/orders", "sc_status": "200",
                     "x_edge_location": "NULL", "cs_uri_query": "NULL"}]
    assert "CUSTOMSECRET" not in all_text(out) and "SECRETCOOKIE" not in all_text(out)


def test_cloudfront_schema_is_stable_across_files_with_different_headers(work):
    a = gz_file(work / "in" / "a.gz", "#Version: 1.0\n#Fields: date time c-ip\n2026-03-09\t10:00:00\t192.0.2.10\n")
    b = gz_file(work / "in" / "b.gz", "#Version: 1.0\n#Fields: date time cs-method sc-bytes\n2026-03-09\t10:00:01\tGET\t42\n")
    o1, o2 = work / "out" / "1.parquet", work / "out" / "2.parquet"
    convert.to_parquet("cloudfront", [a], o1, CFG, SALT)
    convert.to_parquet("cloudfront", [b], o2, CFG, SALT)
    assert columns(o1) == columns(o2)
    both = duck.run([], "SELECT count(*) AS n FROM read_parquet([%s, %s])" % (
        duck.quote_literal(str(o1)), duck.quote_literal(str(o2))), [work / "out"])
    assert both == "n\n2\n"


def test_cloudfront_trailing_tab_and_bad_rows(work):
    text = ("#Version: 1.0\n#Fields: date time c-ip\n"
            "2026-03-09\t10:00:00\t192.0.2.10\t\n"       # docs example rows can end in a tab
            "2026-03-09\t10:00:01\n"                      # too short
            "2026-03-09\t10:00:02\t192.0.2.11\tEXTRA\n"   # too long
            "2026-03-09\t10:00:03\t192.0.2.12\n")
    f = gz_file(work / "in" / "a.gz", text)
    out = work / "out" / "o.parquet"
    res = convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert res.rows == 2 and res.skipped_lines == 2


def test_cloudfront_row_before_header_skipped(work):
    f = gz_file(work / "in" / "a.gz", "2026-03-09\t10:00:00\t192.0.2.10\n#Fields: date time c-ip\n2026-03-09\t10:00:03\t192.0.2.12\n")
    out = work / "out" / "o.parquet"
    res = convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert (res.rows, res.skipped_lines) == (1, 1)


def test_cloudfront_stem_matrix_params_masked(work):
    text = ("#Version: 1.0\n#Fields: date time cs-uri-stem cs-uri-query cs(Referer)\n"
            "2026-03-09\t10:00:00\t/app;jsessionid=SECRETJSESSION/x\ttoken=SECRETTOKEN\thttp://u:pw@www.example.com/p;jsessionid=SECRETJSESSION#frag\n")
    f = gz_file(work / "in" / "a.gz", text)
    out = work / "out" / "o.parquet"
    convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    t = all_text(out)
    assert "SECRET" not in t and "pw@" not in t and "frag" not in t
    row = query(out, "SELECT cs_uri_stem, cs_uri_query FROM read_parquet({t})")[0]
    assert row == {"cs_uri_stem": "/app;jsessionid=***/x", "cs_uri_query": "token=***"}


def test_cloudfront_dash_is_null(work):
    f = gz_file(work / "in" / "a.gz", "#Fields: date time c-ip cs-uri-query x-forwarded-for\n2026-03-09\t10:00:00\t192.0.2.10\t-\t-\n")
    out = work / "out" / "o.parquet"
    convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert query(out, "SELECT cs_uri_query, x_forwarded_for FROM read_parquet({t})") == [
        {"cs_uri_query": "NULL", "x_forwarded_for": "NULL"}]


def test_cloudfront_allow_list_names_and_normalisation():
    assert convert.normalize_field("cs(User-Agent)") == "cs_user_agent"
    assert convert.normalize_field("cs(Host)") == "cs_host"
    assert convert.normalize_field("x-edge-detailed-result-type") == "x_edge_detailed_result_type"
    assert convert.normalize_field("a--b((c))") == "a_b_c"
    assert "cs_cookie" not in convert.CF_ALLOWED
    assert {"cs_uri_query", "cs_uri_stem", "cs_referer", "cs_user_agent", "c_ip"} <= set(convert.CF_ALLOWED)


def test_cloudfront_dropped_names_are_sanitised_and_capped(work):
    names = ["x-f%d" % i for i in range(80)] + ["bad\x01name", "x" * 200]
    text = "#Fields: date time " + " ".join(names) + "\n2026-03-09\t10:00:00" + "\tv" * len(names) + "\n"
    f = gz_file(work / "in" / "a.gz", text)
    res = convert.to_parquet("cloudfront", [f], work / "out" / "o.parquet", CFG, SALT)
    assert len(res.dropped_columns) <= convert.MAX_DROPPED_NAMES + 1
    assert all(len(n) <= 64 and n.isprintable() for n in res.dropped_columns)


# ---- ALB ------------------------------------------------------------------------------------

def alb_line(request="GET https://www.example.com:443/api/orders?page=2&token=SECRETTOKEN HTTP/1.1",
             ua="curl/8.0", redirect="-", transformed_uri="-", extra="", typ="https",
             ts="2026-03-09T23:57:01.123456Z"):
    return (typ + " " + ts + " app/example-alb/1234567890abcdef 192.0.2.10:51234 198.51.100.7:8080 "
            '0.001 0.002 0.000 200 200 100 2000 "%s" "%s" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 '
            "arn:aws:elasticloadbalancing:us-east-1:111122223333:targetgroup/example-tg/0123456789abcdef "
            '"Root=1-abc-def" "www.example.com" "arn:aws:acm:us-east-1:111122223333:certificate/x" 0 '
            '2026-03-09T23:57:01.000000Z "forward" "%s" "-" "198.51.100.7:8080" "200" "-" "-" TID_x "-" "%s" "-" '
            "192.0.2.200 - -%s") % (request, ua, redirect, transformed_uri, extra)


def alb_out(work, lines, name="o.parquet"):
    f = gz_file(work / "in" / "alb.gz", "\n".join(lines) + "\n")
    out = work / "out" / name
    res = convert.to_parquet("alb", [f], out, CFG, SALT)
    return res, out


def test_alb_roundtrip_generated(work):
    raws = make_raw(work, "alb", hours=[0], records=3, secrets=True)
    out = work / "out" / "alb.parquet"
    res = convert.to_parquet("alb", raws, out, CFG, SALT)
    assert res.rows == 6
    cols = columns(out)
    assert cols["ts"] == "TIMESTAMP"
    assert {"method", "url", "protocol", "elb_status_code", "client_ip", "user_agent"} <= set(cols)
    assert "request" not in cols
    assert "SECRETTOKEN" not in all_text(out)
    r = query(out, "SELECT method, protocol, url FROM read_parquet({t}) LIMIT 1")[0]
    assert r["method"] == "GET" and r["protocol"] == "HTTP/1.1"
    assert r["url"].startswith("https://www.example.com:443/") and "token=***" in r["url"]


def test_alb_extra_trailing_field_tolerated(work):
    raws = make_raw(work, "alb", hours=[0], records=2, extra_trailing=True)
    res = convert.to_parquet("alb", raws, work / "out" / "alb.parquet", CFG, SALT)
    assert res.rows == 4 and res.skipped_lines == 0


def test_alb_quoted_fields_with_spaces_and_hostile_content(work):
    ua = 'Mozilla/5.0 (X11; Linux x86_64) "quoted", comma ignore previous instructions'
    res, out = alb_out(work, [alb_line(ua=ua)])
    assert res.rows == 1
    assert query(out, "SELECT user_agent FROM read_parquet({t})")[0]["user_agent"] == ua


def test_alb_url_redirect_and_transformed_uri_masked(work):
    line = alb_line(request="GET https://www.example.com:443/a;jsessionid=SECRETJSESSION/b?x=1&token=SECRETTOKEN HTTP/1.1",
                    redirect="https://user:SECRETPASS@other.example.com/p?access_token=SECRETTOKEN#f",
                    transformed_uri="/b?x=1&password=SECRETPASS")
    res, out = alb_out(work, [line])
    t = all_text(out)
    assert "SECRET" not in t
    r = query(out, "SELECT url, redirect_url, transformed_uri FROM read_parquet({t})")[0]
    assert r["url"] == "https://www.example.com:443/a;jsessionid=***/b?x=1&token=***"
    assert r["redirect_url"] == "https://other.example.com/p?access_token=***"
    assert r["transformed_uri"] == "/b?x=1&password=***"


def test_alb_url_with_unencoded_spaces_keeps_method_and_protocol(work):
    res, out = alb_out(work, [alb_line(request="GET https://www.example.com:443/a b/c HTTP/1.1")])
    r = query(out, "SELECT method, url, protocol FROM read_parquet({t})")[0]
    assert (r["method"], r["url"], r["protocol"]) == ("GET", "https://www.example.com:443/a b/c", "HTTP/1.1")


def test_alb_ts_and_numeric_types(work):
    res, out = alb_out(work, [alb_line()])
    cols = columns(out)
    assert cols["ts"] == "TIMESTAMP" and cols["request_creation_ts"] == "TIMESTAMP"
    assert cols["received_bytes"] == "BIGINT" and cols["request_processing_time"] == "DOUBLE"
    assert cols["elb_status_code"] == "INTEGER"
    r = query(out, "SELECT strftime(ts, '%Y-%m-%dT%H:%M:%S.%f') AS s, client_ip, client_port, target_ip FROM read_parquet({t})")[0]
    assert r == {"s": "2026-03-09T23:57:01.123456", "client_ip": "192.0.2.10", "client_port": "51234", "target_ip": "198.51.100.7"}


def test_alb_malformed_lines_skipped_and_counted(work):
    lines = [alb_line(), "garbage", "", "foo bar baz", alb_line(typ="notatype"),
             alb_line(request="not a request"), alb_line(ts="yesterday")]
    res, out = alb_out(work, lines)
    assert res.rows == 1 and res.skipped_lines == 5  # the empty line is not counted


def test_alb_dash_method_and_protocol_become_null(work):
    res, out = alb_out(work, [alb_line(request="- http://www.example.com:80- -")])
    r = query(out, "SELECT method, url, protocol FROM read_parquet({t})")[0]
    assert (r["method"], r["url"], r["protocol"]) == ("NULL", "http://www.example.com:80-", "NULL")


def test_alb_short_old_style_line_without_late_fields(work):
    full = alb_line()
    short = full[:full.index(" ECDHE")]  # through user_agent: 14 fields
    res, out = alb_out(work, [short])
    assert res.rows == 1
    assert query(out, "SELECT target_group_arn, ssl_cipher FROM read_parquet({t})")[0] == {
        "target_group_arn": "NULL", "ssl_cipher": "NULL"}


# ---- WAF -------------------------------------------------------------------------------------

WAF_COLUMNS = {
    "ts", "action", "terminating_rule_id", "terminating_rule_type", "rule_group_matches",
    "non_terminating_rules", "labels", "client_ip", "country", "asn", "host", "uri",
    "query_masked", "http_method", "http_version", "request_id", "ja3", "ja4", "header_names",
    "user_agent", "referer_masked", "client_key", "identity_hashes", "response_code_sent",
    "matched_field", "match_type", "matched_hash",
}


def test_waf_parquet_has_only_redacted_columns(work):
    raws = make_raw(work, "waf", hours=[0], records=3, secrets=True)
    out = work / "out" / "waf.parquet"
    res = convert.to_parquet("waf", raws, out, CFG, SALT)
    assert res.rows == 6
    cols = columns(out)
    assert set(cols) == WAF_COLUMNS
    assert cols["ts"] == "TIMESTAMP" and cols["header_names"] == "VARCHAR[]"
    text = all_text(out)
    assert "SECRETTOKEN" not in text and "SECRETCOOKIE" not in text
    r = query(out, "SELECT query_masked, client_key IS NOT NULL AS has_key FROM read_parquet({t}) LIMIT 1")[0]
    assert r["query_masked"].endswith("token=***") and r["has_key"] == "true"


def test_waf_bad_json_lines_skipped(work):
    rec = '{"timestamp": 1773057600123, "action": "ALLOW", "httpRequest": {"clientIp": "192.0.2.10"}}'
    f = gz_file(work / "in" / "w.gz", "\n".join([rec, "{not json", "[1,2]", "", rec]) + "\n")
    out = work / "out" / "w.parquet"
    res = convert.to_parquet("waf", [f], out, CFG, SALT)
    assert res.rows == 2 and res.skipped_lines == 2


def test_waf_uppercase_cookie_name_gives_client_key(work):
    rec = {"timestamp": 1773057600123, "action": "ALLOW",
           "httpRequest": {"clientIp": "192.0.2.10", "headers": [{"name": "Cookie", "value": "JSESSIONID=abc123"}]}}
    f = gz_file(work / "in" / "w.gz", json.dumps(rec) + "\n")
    out = work / "out" / "w.parquet"
    convert.to_parquet("waf", [f], out, CFG, SALT)
    r = query(out, "SELECT client_key, identity_hashes FROM read_parquet({t})")[0]
    assert r["client_key"] != "NULL" and r["client_key"] == redact.hash_value("abc123", SALT)
    assert "abc123" not in all_text(out)


def test_waf_uncompressed_firehose_file_converts(work):
    rec = ('{"timestamp": 1773057600123, "action": "ALLOW", '
           '"httpRequest": {"clientIp": "192.0.2.10", "uri": "/a?token=SECRETTOKEN"}}')
    f = work / "in" / "plain.json"
    f.write_bytes((rec + "\n" + rec + "\n").encode())
    out = work / "out" / "w.parquet"
    res = convert.to_parquet("waf", [f], out, CFG, SALT)
    assert res.rows == 2 and res.skipped_lines == 0
    assert "SECRETTOKEN" not in all_text(out)
    assert not f.exists()


def test_uncompressed_overlong_line_is_skipped_like_gz(work):
    rec = '{"timestamp": 1773057600123, "action": "ALLOW", "httpRequest": {"clientIp": "192.0.2.10"}}'
    f = work / "in" / "plain.json"
    f.write_bytes((rec + "\n" + "x" * (convert.MAX_LINE_BYTES + 10) + "\n" + rec + "\n").encode())
    res = convert.to_parquet("waf", [f], work / "out" / "w.parquet", CFG, SALT)
    assert res.rows == 2 and res.skipped_lines == 1


def test_gz_waf_file_still_converts_after_sniffing(work):
    rec = '{"timestamp": 1773057600123, "action": "ALLOW", "httpRequest": {"clientIp": "192.0.2.10"}}'
    f = gz_file(work / "in" / "w.gz", rec + "\n")
    assert f.read_bytes()[:2] == b"\x1f\x8b"
    res = convert.to_parquet("waf", [f], work / "out" / "w.parquet", CFG, SALT)
    assert res.rows == 1


@pytest.mark.parametrize("compressed", [True, False])
def test_decompressed_size_cap(work, monkeypatch, compressed):
    monkeypatch.setattr(convert, "MAX_DECOMPRESSED_BYTES", 1000)
    rec = '{"timestamp": 1773057600123, "action": "ALLOW", "httpRequest": {"clientIp": "192.0.2.10"}}\n'
    text = rec * 30
    f = work / "in" / "big"
    f.write_bytes(gf._gz(text) if compressed else text.encode())
    with pytest.raises(convert.ConvertError) as ei:
        convert.to_parquet("waf", [f], work / "out" / "w.parquet", CFG, SALT)
    assert "decompressed past the 4 GiB per-file limit" in str(ei.value)
    assert not f.exists() and staging_entries() == []


# ---- cleanup, failures, misc -------------------------------------------------------------------

def test_raw_deleted_even_on_error(work):
    good = make_raw(work, "cloudfront", hours=[0], records=1)[0]
    bad = work / "in" / "corrupt.gz"
    bad.write_bytes(b"\x1f\x8b\x08\x00 this is not a gzip body")
    out = work / "out" / "o.parquet"
    with pytest.raises(convert.ConvertError) as ei:
        convert.to_parquet("cloudfront", [good, bad], out, CFG, SALT)
    assert "corrupt.gz" in str(ei.value)
    assert not good.exists() and not bad.exists()
    assert staging_entries() == []
    assert not out.exists() and os.listdir(str(work / "out")) == []


def test_truncated_gzip_is_an_error_not_a_partial_result(work):
    data = gf._gz("#Fields: date time c-ip\n" + "2026-03-09\t10:00:00\t192.0.2.10\n" * 2000)
    f = work / "in" / "trunc.gz"
    f.write_bytes(data[:-20])
    with pytest.raises(convert.ConvertError):
        convert.to_parquet("cloudfront", [f], work / "out" / "o.parquet", CFG, SALT)
    assert not f.exists() and staging_entries() == []


def test_duckdb_failure_still_cleans_up(work, monkeypatch):
    raws = make_raw(work, "cloudfront", hours=[0], records=1)
    monkeypatch.setenv("PATH", "/nonexistent-dir")
    with pytest.raises(DuckError):
        convert.to_parquet("cloudfront", raws, work / "out" / "o.parquet", CFG, SALT)
    assert not any(p.exists() for p in raws) and staging_entries() == []


def test_unknown_type_refused_and_inputs_still_deleted(work):
    f = gz_file(work / "in" / "a.gz", "x\n")
    with pytest.raises(Refused):
        convert.to_parquet("s3", [f], work / "out" / "o.parquet", CFG, SALT)
    assert not f.exists() and staging_entries() == []


def test_plain_text_input_is_read_as_it_is(work):
    f = work / "in" / "plain.txt"
    f.write_text("#Fields: date time\n2026-03-09\t10:00:00\n")
    res = convert.to_parquet("cloudfront", [f], work / "out" / "o.parquet", CFG, SALT)
    assert res.rows == 1
    assert not f.exists()


def test_truncated_gzip_input_is_an_error(work):
    f = work / "in" / "cut.gz"
    f.write_bytes(gf._gz("#Fields: date time\n" + "2026-03-09\t10:00:00\n" * 200)[:-12])
    with pytest.raises(convert.ConvertError):
        convert.to_parquet("cloudfront", [f], work / "out" / "o.parquet", CFG, SALT)
    assert not f.exists()


def test_empty_input_list_writes_an_empty_table_with_the_schema(work):
    out = work / "out" / "o.parquet"
    res = convert.to_parquet("cloudfront", [], out, CFG, SALT)
    assert res.rows == 0 and "ts" in columns(out)


def test_overlong_line_is_skipped_not_loaded(work, monkeypatch):
    monkeypatch.setattr(convert, "MAX_LINE_BYTES", 200)
    text = ("#Fields: date time c-ip\n2026-03-09\t10:00:00\t192.0.2.10\n"
            "2026-03-09\t10:00:01\t" + "A" * 5000 + "\n2026-03-09\t10:00:02\t192.0.2.11\n")
    f = gz_file(work / "in" / "a.gz", text)
    res = convert.to_parquet("cloudfront", [f], work / "out" / "o.parquet", CFG, SALT)
    assert res.rows == 2 and res.skipped_lines == 1


def test_invalid_utf8_and_nul_do_not_break_conversion(work):
    body = b"#Fields: date time c-ip cs(User-Agent)\n2026-03-09\t10:00:00\t192.0.2.10\tbad\xff\xfe\x00agent\n"
    f = work / "in" / "a.gz"
    f.write_bytes(gzip.compress(body))
    out = work / "out" / "o.parquet"
    res = convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert res.rows == 1
    ua = query(out, "SELECT cs_user_agent FROM read_parquet({t})")[0]["cs_user_agent"]
    assert "agent" in ua and "\x00" not in ua


def test_output_replaced_atomically_even_if_read_only(work):
    out = work / "out" / "o.parquet"
    f1 = gz_file(work / "in" / "a.gz", "#Fields: date time c-ip\n2026-03-09\t10:00:00\t192.0.2.10\n")
    convert.to_parquet("cloudfront", [f1], out, CFG, SALT)
    f2 = gz_file(work / "in" / "b.gz", "#Fields: date time c-ip\n2026-03-09\t10:00:00\t192.0.2.11\n2026-03-09\t10:00:01\t192.0.2.12\n")
    res = convert.to_parquet("cloudfront", [f2], out, CFG, SALT)
    assert res.rows == 2
    assert query(out, "SELECT count(*) AS n FROM read_parquet({t})") == [{"n": "2"}]
    assert os.listdir(str(work / "out")) == ["o.parquet"]


def test_uses_sensitive_names_incl_identity_cookies(work):
    # jsessionid is an identity cookie, not in SENSITIVE_PARAMS: still masked via sensitive_names(cfg).
    f = gz_file(work / "in" / "a.gz", "#Fields: date time cs-uri-query\n2026-03-09\t10:00:00\tjsessionid=SECRETJSESSION&a=1\n")
    out = work / "out" / "o.parquet"
    convert.to_parquet("cloudfront", [f], out, CFG, SALT)
    assert query(out, "SELECT cs_uri_query FROM read_parquet({t})")[0]["cs_uri_query"] == "jsessionid=***&a=1"


def test_result_is_a_named_tuple_with_documented_fields():
    r = convert.ConvertResult(rows=3, dropped_columns=("x",), skipped_lines=1)
    assert (r.rows, r.dropped_columns, r.skipped_lines) == (3, ("x",), 1)


# ---- further cases ----------------------------------------------------------------------------

REDIRECT = "https://www.example.com:443/home?token=SECRETRED"
TRANSFORMED = "/b?password=SECRETPW"


@pytest.mark.parametrize("ua", ['evil" "x', 'evil\\" x', 'a" "-" "-" "-', 'evil" '])
def test_alb_quote_in_user_agent_cannot_shift_fields(work, ua):
    res, out = alb_out(work, [alb_line(ua=ua, redirect=REDIRECT, transformed_uri=TRANSFORMED)])
    assert (res.rows, res.skipped_lines) == (0, 1)
    assert "SECRET" not in all_text(out)


def test_alb_anchor_checks_pass_for_normal_and_http_listener_lines(work):
    http = alb_line(typ="http").replace(" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2", " - -")
    http = http.replace('"arn:aws:acm:us-east-1:111122223333:certificate/x"', '"-"')
    res, out = alb_out(work, [alb_line(redirect=REDIRECT), http])
    assert (res.rows, res.skipped_lines) == (2, 0)
    assert "SECRETRED" not in all_text(out)


def test_alb_second_layer_masks_urls_in_shifted_free_text_columns(work, monkeypatch):
    # Even if the anchors were fooled, no later free-text column keeps a URL secret.
    monkeypatch.setattr(convert, "_anchors_ok", lambda toks: True)
    line = alb_line(ua='evil" "x', redirect=REDIRECT, transformed_uri=TRANSFORMED)
    row = convert._alb_row(line, redact.sensitive_names(CFG))
    assert row is not None
    assert "SECRET" not in json.dumps(row)
    assert row["error_reason"] == "https://www.example.com:443/home?token=***"


def test_alb_second_layer_leaves_ordinary_free_text_alone(work):
    line = alb_line()
    row = convert._alb_row(line, redact.sensitive_names(CFG))
    assert row["trace_id"] == "Root=1-abc-def" and row["target_port_list"] == "198.51.100.7:8080"
    assert row["chosen_cert_arn"].startswith("arn:aws:acm:")


def test_lone_surrogate_in_waf_record_does_not_lose_the_batch(work):
    good = '{"timestamp": 1773057600123, "action": "ALLOW", "httpRequest": {"clientIp": "192.0.2.10"}}'
    bad = ('{"timestamp": 1773057600124, "action": "BLOCK", "httpRequest": {"clientIp": "192.0.2.11", '
           '"uri": "/a\\ud800b", "headers": [{"name": "User-Agent", "value": "x\\udfffy"}]}}')
    f = gz_file(work / "in" / "w.gz", "\n".join([good, bad, good]) + "\n")
    out = work / "out" / "w.parquet"
    res = convert.to_parquet("waf", [f], out, CFG, SALT)
    assert res.rows == 3
    row = query(out, "SELECT uri, user_agent FROM read_parquet({t}) WHERE action = 'BLOCK'")[0]
    assert row["uri"].startswith("/a") and row["uri"].endswith("b")
    assert row["user_agent"].startswith("x") and row["user_agent"].endswith("y")


# ---- more cases ------------------------------------------------------------------------

def _forged_ua(injected: int) -> str:
    """A user agent that closes its quotes and adds `injected` more tokens, all "-" (so the
    shape checks pass), pushing the real fields to the right."""
    return 'a"' + ' "-"' * (injected - 1) + ' "z'


@pytest.mark.parametrize("injected", [3, 4, 5, 22, 23, 29, 60])
def test_alb_token_injection_is_skipped_at_any_size(work, injected):
    ua = _forged_ua(injected)
    line = alb_line(ua=ua, redirect=REDIRECT, transformed_uri=TRANSFORMED)
    toks = convert._tokenize(line, 200)
    assert len(toks) == 36 + injected  # the forgery does what the test says
    res, out = alb_out(work, [line])
    assert (res.rows, res.skipped_lines) == (0, 1)
    assert "SECRET" not in all_text(out)


def test_alb_documented_field_count_and_trailing_tolerance():
    assert len(convert._ALB_FIELDS) == 36  # the doc's 36 fields
    assert convert._ALB_MAX_FIELDS == 36 + convert._ALB_TRAILING_TOLERANCE
    assert convert._ALB_TRAILING_TOLERANCE == 4


def test_alb_trailing_tolerance_boundary(work):
    base = alb_line()
    ok = base + ' "-"' * convert._ALB_TRAILING_TOLERANCE
    too_many = base + ' "-"' * (convert._ALB_TRAILING_TOLERANCE + 1)
    res, out = alb_out(work, [ok, too_many])
    assert (res.rows, res.skipped_lines) == (1, 1)
