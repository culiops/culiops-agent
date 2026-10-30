from __future__ import annotations

import json
import os
import stat
import threading
from dataclasses import replace

import pytest

from s3logs import paths, redact
from s3logs.config import Config
from s3logs.validate import Refused

SENSITIVE = Config().sensitive_params
SALT = bytes(range(32))

EXPECTED_KEYS = {
    "ts", "action", "terminating_rule_id", "terminating_rule_type", "rule_group_matches",
    "non_terminating_rules", "labels", "client_ip", "country", "asn", "host", "uri",
    "query_masked", "http_method", "http_version", "request_id", "ja3", "ja4", "header_names",
    "user_agent", "referer_masked", "client_key", "identity_hashes", "response_code_sent",
    "matched_field", "match_type", "matched_hash",
}


# Record shape: https://docs.aws.amazon.com/waf/latest/developerguide/logging-fields.html and
# https://docs.aws.amazon.com/waf/latest/developerguide/logging-examples.html
def make_record(headers=None, **over):
    rec = {
        "timestamp": 1773057600123,
        "formatVersion": 1,
        "webaclId": "arn:aws:wafv2:us-east-1:111122223333:regional/webacl/ExampleAcl/EXAMPLE-ID",
        "terminatingRuleId": "ExampleRateRule",
        "terminatingRuleType": "RATE_BASED",
        "action": "BLOCK",
        "terminatingRuleMatchDetails": [],
        "httpSourceName": "ALB",
        "httpSourceId": "example-alb",
        "ruleGroupList": [],
        "rateBasedRuleList": [],
        "nonTerminatingMatchingRules": [],
        "requestHeadersInserted": None,
        "responseCodeSent": None,
        "ja3Fingerprint": "00000000000000000000000000000001",
        "ja4Fingerprint": "t13d0000h2_000000000000_000000000000",
        "httpRequest": {
            "clientIp": "192.0.2.10",
            "country": "US",
            "headers": headers if headers is not None else [
                {"name": "Host", "value": "www.example.com"},
                {"name": "User-Agent", "value": "ExampleAgent/1.0"},
                {"name": "Accept", "value": "*/*"},
            ],
            "uri": "/orders",
            "args": "page=2&token=SECRETTOKEN",
            "httpVersion": "HTTP/1.1",
            "httpMethod": "GET",
            "requestId": "ExampleRequestId=",
        },
        "labels": [{"name": "awswaf:example:label"}],
    }
    rec.update(over)
    return rec


# ---- mask_query -------------------------------------------------------------------------

def test_masks_sensitive_param():
    assert redact.mask_query("a=1&token=abc&B=2", SENSITIVE) == "a=1&token=***&B=2"


def test_param_name_match_after_decoding():
    assert redact.mask_query("%74oken=abc", SENSITIVE) == "%74oken=***"


def test_name_match_is_case_insensitive():
    assert redact.mask_query("TOKEN=abc&Api_Key=zzz", SENSITIVE) == "TOKEN=***&Api_Key=***"


def test_double_encoded_masks_whole():
    assert redact.mask_query("token%253Dabc", SENSITIVE) == "***"


def test_invalid_utf8_masks_whole():
    assert redact.mask_query("x=%ff%fe", SENSITIVE) == "***"


def test_empty_and_dash_returned_as_is():
    assert redact.mask_query("", SENSITIVE) == ""
    assert redact.mask_query("-", SENSITIVE) == "-"


def test_order_and_raw_spelling_of_other_pairs_kept():
    qs = "z=a%20b&session=s1&q=x+y&flag&k=v%2Fw"
    assert redact.mask_query(qs, SENSITIVE) == "z=a%20b&session=***&q=x+y&flag&k=v%2Fw"


def test_param_without_equals_kept_as_is():
    assert redact.mask_query("token&a=1", SENSITIVE) == "token&a=1"


def test_semicolon_separator_is_also_split():
    assert redact.mask_query("a=1;token=abc", SENSITIVE) == "a=1;token=***"


def test_bracketed_param_names_masked():
    assert redact.mask_query("password[]=abc&token[x]=d", SENSITIVE) == "password[]=***&token[x]=***"


def test_value_with_equals_fully_masked():
    assert redact.mask_query("token=a=b&c=1", SENSITIVE) == "token=***&c=1"


def test_leading_question_mark_does_not_hide_first_param():
    assert redact.mask_query("?token=abc&a=1", SENSITIVE) == "?token=***&a=1"


def test_custom_sensitive_set_used():
    assert redact.mask_query("acct=1&token=2", frozenset({"acct"})) == "acct=***&token=2"


def test_uppercase_entries_in_sensitive_set_still_match():
    assert redact.mask_query("token=1", frozenset({"TOKEN"})) == "token=***"


def test_no_secret_in_exception_path():
    # Fail-closed paths return a constant, never echo the input.
    assert "SECRET" not in redact.mask_query("x=%ffSECRET", SENSITIVE)


# ---- hash_value -------------------------------------------------------------------------

def test_hash_value_shape_and_determinism():
    h = redact.hash_value("abc", SALT)
    assert len(h) == 12 and all(c in "0123456789abcdef" for c in h)
    assert h == redact.hash_value("abc", SALT)
    assert h != redact.hash_value("abd", SALT)
    assert h != redact.hash_value("abc", b"\x01" * 32)


# ---- waf_record -------------------------------------------------------------------------

def test_waf_record_keys_exact():
    out = redact.waf_record(make_record(), Config(), SALT)
    assert set(out) == EXPECTED_KEYS


def test_waf_record_basic_fields():
    out = redact.waf_record(make_record(), Config(), SALT)
    assert out["ts"] == "2026-03-09T12:00:00.123Z"
    assert out["action"] == "BLOCK"
    assert out["terminating_rule_id"] == "ExampleRateRule"
    assert out["terminating_rule_type"] == "RATE_BASED"
    assert out["labels"] == ["awswaf:example:label"]
    assert out["client_ip"] == "192.0.2.10"
    assert out["country"] == "US"
    assert out["host"] == "www.example.com"
    assert out["uri"] == "/orders"
    assert out["query_masked"] == "page=2&token=***"
    assert out["http_method"] == "GET"
    assert out["http_version"] == "HTTP/1.1"
    assert out["request_id"] == "ExampleRequestId="
    assert out["ja3"] == "00000000000000000000000000000001"
    assert out["ja4"].startswith("t13d")
    assert out["header_names"] == ["host", "user-agent", "accept"]
    assert out["user_agent"] == "ExampleAgent/1.0"
    assert out["response_code_sent"] is None
    assert out["asn"] is None
    assert out["client_key"] is None
    assert out["identity_hashes"] == []
    assert out["matched_field"] is None and out["match_type"] is None and out["matched_hash"] is None


def test_rule_group_and_non_terminating_fields():
    rec = make_record(
        ruleGroupList=[{
            "ruleGroupId": "arn:aws:wafv2:us-east-1:111122223333:global/rulegroup/Example/EX",
            "terminatingRule": {"ruleId": "ExampleGroupRule", "action": "BLOCK", "ruleMatchDetails": None},
            "nonTerminatingMatchingRules": [{"ruleId": "ExampleCountRule", "action": "COUNT"}],
            "excludedRules": None,
        }],
        nonTerminatingMatchingRules=[{"ruleId": "ExampleTopCount", "action": "COUNT", "ruleMatchDetails": []}],
    )
    out = redact.waf_record(rec, Config(), SALT)
    assert out["rule_group_matches"] == ["ExampleGroupRule", "ExampleCountRule"]
    assert out["non_terminating_rules"] == ["ExampleTopCount:COUNT"]


def test_asn_taken_from_documented_field():
    rec = make_record()
    rec["httpRequest"]["clientAsn"] = 64500
    assert redact.waf_record(rec, Config(), SALT)["asn"] == "64500"
    rec2 = make_record(clientAsn="64501")
    assert redact.waf_record(rec2, Config(), SALT)["asn"] == "64501"


def test_cookie_values_never_survive():
    headers = [
        {"name": "Host", "value": "www.example.com"},
        {"name": "Cookie", "value": "session=SECRETVALUE; other=ALSOSECRET"},
        {"name": "Authorization", "value": "Bearer XYZ"},
        {"name": "X-Custom", "value": "CUSTOMSECRET"},
    ]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    blob = json.dumps(out)
    for s in ("SECRETVALUE", "ALSOSECRET", "XYZ", "CUSTOMSECRET", "Bearer"):
        assert s not in blob
    assert out["header_names"] == ["host", "cookie", "authorization", "x-custom"]


def test_secret_in_args_and_referer_never_survives():
    headers = [{"name": "Referer", "value": "https://www.example.com/p?access_token=REFSECRET&a=1#frag=FRAGSECRET"}]
    rec = make_record(headers=headers)
    rec["httpRequest"]["args"] = "password=ARGSECRET"
    blob = json.dumps(redact.waf_record(rec, Config(), SALT))
    for s in ("REFSECRET", "ARGSECRET", "FRAGSECRET"):
        assert s not in blob


def test_referer_masked_keeps_other_parts():
    headers = [{"name": "referer", "value": "https://www.example.com/p?a=1&token=T&b=2"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["referer_masked"] == "https://www.example.com/p?a=1&token=***&b=2"


def test_referer_without_query_and_absent():
    headers = [{"name": "referer", "value": "https://www.example.com/p"}]
    assert redact.waf_record(make_record(headers=headers), Config(), SALT)["referer_masked"] == "https://www.example.com/p"
    assert redact.waf_record(make_record(), Config(), SALT)["referer_masked"] is None


def test_referer_userinfo_dropped():
    headers = [{"name": "referer", "value": "https://user:PASSWORDX@www.example.com/p?a=1"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert "PASSWORDX" not in json.dumps(out)
    assert out["referer_masked"] == "https://www.example.com/p?a=1"


def test_unparseable_referer_masked_whole():
    headers = [{"name": "referer", "value": "http://[::1/SECRETPATH?token=x"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["referer_masked"] == "***"
    assert "SECRETPATH" not in json.dumps(out)


def test_referer_double_encoded_query_masked_whole_query():
    headers = [{"name": "referer", "value": "https://www.example.com/p?token%253Dabc"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["referer_masked"] == "https://www.example.com/p?***"


def test_matched_data_value_never_survives():
    rec = make_record(terminatingRuleMatchDetails=[{
        "conditionType": "SQL_INJECTION",
        "sensitivityLevel": "HIGH",
        "location": "HEADER",
        "matchedData": ["10", "AND", "MATCHEDSECRET"],
    }])
    out = redact.waf_record(rec, Config(), SALT)
    assert "MATCHEDSECRET" not in json.dumps(out)
    assert out["matched_field"] == "HEADER"
    assert out["match_type"] == "SQL_INJECTION"
    assert len(out["matched_hash"]) == 12
    out2 = redact.waf_record(rec, Config(), b"\x07" * 32)
    assert out2["matched_hash"] != out["matched_hash"]


def test_matched_data_from_rule_group_terminating_rule():
    rec = make_record(ruleGroupList=[{
        "ruleGroupId": "g",
        "terminatingRule": {"ruleId": "r", "action": "BLOCK", "ruleMatchDetails": [
            {"conditionType": "XSS", "location": "URI", "matchedData": ["<", "GROUPSECRET"]}]},
        "nonTerminatingMatchingRules": [],
    }])
    out = redact.waf_record(rec, Config(), SALT)
    assert out["match_type"] == "XSS" and out["matched_field"] == "URI"
    assert "GROUPSECRET" not in json.dumps(out)


def _ident_headers(**kw):
    return [
        {"name": "Host", "value": "www.example.com"},
        {"name": "Cookie", "value": "session=S1; acct=A1"},
        {"name": "cookie", "value": "sid=SID1"},
        {"name": "Authorization", "value": "Bearer T1"},
    ]


def test_client_key_stable_across_calls_same_salt():
    a = redact.waf_record(make_record(headers=_ident_headers()), Config(), SALT)
    b = redact.waf_record(make_record(headers=_ident_headers()), Config(), SALT)
    assert a["client_key"] == b["client_key"] is not None


def test_client_key_differs_with_other_salt():
    a = redact.waf_record(make_record(headers=_ident_headers()), Config(), SALT)
    b = redact.waf_record(make_record(headers=_ident_headers()), Config(), b"\x09" * 32)
    assert a["client_key"] != b["client_key"]


def test_identity_order_headers_then_cookies_and_multiple_cookie_headers():
    out = redact.waf_record(make_record(headers=_ident_headers()), Config(), SALT)
    names = [x.split(":", 1)[0] for x in out["identity_hashes"]]
    assert names == ["authorization", "session", "sid"]
    first = out["identity_hashes"][0].split(":", 1)[1]
    assert out["client_key"] == first == redact.hash_value("Bearer T1", SALT)
    assert "acct" not in json.dumps(out["identity_hashes"])


def test_client_key_falls_back_to_cookie_when_no_header():
    headers = [{"name": "Cookie", "value": "other=1; session=S1"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["client_key"] == redact.hash_value("S1", SALT)


def test_identity_lists_from_config():
    cfg = replace(Config(), identity_cookies=("acct",), identity_headers=())
    out = redact.waf_record(make_record(headers=_ident_headers()), cfg, SALT)
    assert [x.split(":", 1)[0] for x in out["identity_hashes"]] == ["acct"]
    assert out["client_key"] == redact.hash_value("A1", SALT)
    assert "S1" not in json.dumps(out)


def test_cookie_names_case_sensitive_header_names_not():
    headers = [{"name": "COOKIE", "value": "SESSION=UP; session=low"}, {"name": "AUTHORIZATION", "value": "x"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["identity_hashes"][0].startswith("authorization:")
    assert out["identity_hashes"][1] == "session:" + redact.hash_value("low", SALT)
    assert len(out["identity_hashes"]) == 2


def test_empty_identity_values_are_ignored():
    headers = [{"name": "Cookie", "value": "session=; sid="}, {"name": "Authorization", "value": ""}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert out["client_key"] is None and out["identity_hashes"] == []


def test_malformed_record_does_not_crash_or_leak():
    rec = make_record(headers=[{"name": "Cookie"}, "junk", {"name": 5, "value": "x"}, {"name": "myHeader", "myValue": "LEAK"}])
    rec["httpRequest"]["args"] = None
    rec["timestamp"] = "bad"
    out = redact.waf_record(rec, Config(), SALT)
    assert set(out) == EXPECTED_KEYS
    assert out["ts"] is None
    assert "LEAK" not in json.dumps(out)


def test_non_dict_http_request_gives_nulls():
    out = redact.waf_record({"httpRequest": "oops", "action": "ALLOW"}, Config(), SALT)
    assert set(out) == EXPECTED_KEYS and out["client_ip"] is None and out["header_names"] == []


def test_uri_with_query_is_masked():
    rec = make_record()
    rec["httpRequest"]["uri"] = "/cb?code=ABC&a=1"
    assert redact.waf_record(rec, Config(), SALT)["uri"] == "/cb?code=***&a=1"


# ---- salt -------------------------------------------------------------------------------

def salt_path():
    return paths.state_root() / "salt"


def test_salt_created_hex_mode_0600(home):
    old = os.umask(0o022)
    try:
        s = redact.load_or_create_salt()
    finally:
        os.umask(old)
    assert isinstance(s, bytes) and len(s) == 32
    p = salt_path()
    text = p.read_text()
    assert len(text) == 64 and bytes.fromhex(text) == s
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    assert redact.load_or_create_salt() == s
    assert [x.name for x in p.parent.iterdir() if x.name.startswith("salt")] == ["salt"]


def test_salt_races_read_the_winner(home):
    results = []
    barrier = threading.Barrier(8)

    def run():
        barrier.wait()
        results.append(redact.load_or_create_salt())

    ts = [threading.Thread(target=run) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(results) == 8 and len(set(results)) == 1


def test_salt_symlink_refused(home, tmp_path):
    paths.ensure_private_dirs()
    real = tmp_path / "real"
    real.write_text("a" * 64)
    real.chmod(0o600)
    salt_path().symlink_to(real)
    with pytest.raises(Refused) as e:
        redact.load_or_create_salt()
    assert "salt" in str(e.value)


def test_salt_dangling_symlink_refused(home, tmp_path):
    paths.ensure_private_dirs()
    salt_path().symlink_to(tmp_path / "nowhere")
    with pytest.raises(Refused):
        redact.load_or_create_salt()
    assert not (tmp_path / "nowhere").exists()


@pytest.mark.parametrize("mode", [0o644, 0o640, 0o604, 0o700])
def test_salt_loose_mode_refused(home, mode):
    redact.load_or_create_salt()
    os.chmod(salt_path(), mode)
    with pytest.raises(Refused) as e:
        redact.load_or_create_salt()
    assert "salt" in str(e.value)


def test_salt_stricter_mode_ok(home):
    s = redact.load_or_create_salt()
    os.chmod(salt_path(), 0o400)
    assert redact.load_or_create_salt() == s


@pytest.mark.parametrize("content", ["", "abc", "g" * 64, "A" * 64, "a" * 63, "a" * 65, "a" * 64 + "\n"])
def test_salt_malformed_refused_without_echo(home, content):
    paths.ensure_private_dirs()
    p = salt_path()
    p.write_text(content)
    p.chmod(0o600)
    with pytest.raises(Refused) as e:
        redact.load_or_create_salt()
    assert "salt" in str(e.value)
    if content:
        assert content not in str(e.value)


def test_salt_wrong_owner_refused(home, monkeypatch):
    redact.load_or_create_salt()
    monkeypatch.setattr(os, "getuid", lambda: os.stat(salt_path()).st_uid + 1)
    with pytest.raises(Refused) as e:
        redact.load_or_create_salt()
    assert "salt" in str(e.value)


def test_salt_directory_refused(home):
    paths.ensure_private_dirs()
    salt_path().mkdir()
    with pytest.raises(Refused):
        redact.load_or_create_salt()
