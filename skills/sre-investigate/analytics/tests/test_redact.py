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


# ---- further cases ------------------------------------------------------------------------

def test_many_leading_question_marks_do_not_recurse():
    qs = "?" * 5000 + "token=abc&a=1"
    assert redact.mask_query(qs, SENSITIVE) == "?" * 5000 + "token=***&a=1"
    assert redact.mask_query("?" * 5000, SENSITIVE) == "?" * 5000
    out = redact.waf_record(make_record(**{}), Config(), SALT)
    rec = make_record()
    rec["httpRequest"]["args"] = "?" * 5000
    out = redact.waf_record(rec, Config(), SALT)
    assert out["query_masked"] == "?" * 5000
    assert out["terminating_rule_id"] == "ExampleRateRule"


@pytest.mark.parametrize(
    "bad",
    ["\u00b2", "\u2460", "1" * 5000, "\u0663", 10 ** 5000, "9" * 19, True, 1.5, "-1"],
    ids=["sup2", "circled1", "str5000", "arabic3", "bigint", "str19", "bool", "float", "neg"],
)
def test_odd_numbers_never_raise(bad):
    rec = make_record(timestamp=bad, responseCodeSent=bad)
    rec["httpRequest"]["clientAsn"] = bad
    out = redact.waf_record(rec, Config(), SALT)
    assert set(out) == EXPECTED_KEYS
    assert out["terminating_rule_id"] == "ExampleRateRule"  # a real record, not the fallback
    assert out["ts"] is None and out["response_code_sent"] is None


def test_int_boundaries():
    rec = make_record(responseCodeSent="403")
    assert redact.waf_record(rec, Config(), SALT)["response_code_sent"] == 403


def test_fallback_is_full_key_set_with_masks(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("SECRETDETAIL")
    monkeypatch.setattr(redact, "hash_value", boom)
    headers = [{"name": "Authorization", "value": "Bearer ZZ"}]
    out = redact.waf_record(make_record(headers=headers), Config(), SALT)
    assert set(out) == EXPECTED_KEYS
    for k, v in out.items():
        if k in ("query_masked", "referer_masked"):
            assert v == "***"
        else:
            assert v is None
    assert "ZZ" not in json.dumps(out) and "SECRETDETAIL" not in json.dumps(out)


def test_waf_record_never_raises_on_garbage():
    for junk in (None, 5, "x", [], {"httpRequest": []}, {"labels": 3, "ruleGroupList": [5, None, {"terminatingRule": 1}]}):
        assert set(redact.waf_record(junk, Config(), SALT)) == EXPECTED_KEYS


def test_mask_path_matrix_params():
    assert redact.mask_path("/a;jsessionid=ZZ", frozenset({"jsessionid"})) == "/a;jsessionid=***"
    assert redact.mask_path("/a;x=1;token=ZZ/b;y=2", SENSITIVE) == "/a;x=1;token=***/b;y=2"
    assert redact.mask_path("/plain/path", SENSITIVE) == "/plain/path"
    assert redact.mask_path("", SENSITIVE) == ""
    assert redact.mask_path("/a;%74oken=ZZ", SENSITIVE) == "/a;%74oken=***"
    assert redact.mask_path("/a;token%3DZZ", SENSITIVE) == "/a;***"
    assert redact.mask_path("/a;x=%ff", SENSITIVE) == "/a;***"
    assert redact.mask_path("/a;x=%2541", SENSITIVE) == "/a;***"
    assert redact.mask_path("/a;access.token=ZZ", SENSITIVE) == "/a;access.token=***"
    assert redact.mask_path("/a;flag;k=v", SENSITIVE) == "/a;flag;k=v"


def test_uri_and_referer_matrix_params_masked_by_default():
    rec = make_record(headers=[{"name": "Referer", "value": "https://x.example.com/a;jsessionid=REFZZ?a=1"}])
    rec["httpRequest"]["uri"] = "/a;jsessionid=URIZZ?a=1"
    out = redact.waf_record(rec, Config(), SALT)
    assert out["uri"] == "/a;jsessionid=***?a=1"
    assert out["referer_masked"] == "https://x.example.com/a;jsessionid=***?a=1"
    assert "ZZ" not in json.dumps(out)


def test_identity_cookie_names_masked_in_query_by_default():
    out = redact.waf_record(make_record(), Config(), SALT)
    rec = make_record()
    rec["httpRequest"]["args"] = "jsessionid=QQ&PHPSESSID=RR&a=1"
    out = redact.waf_record(rec, Config(), SALT)
    assert out["query_masked"] == "jsessionid=***&PHPSESSID=***&a=1"


def test_sensitive_names_helper():
    names = redact.sensitive_names(Config())
    assert "jsessionid" in names and "token" in names
    assert redact.sensitive_names(replace(Config(), identity_cookies=("Acct",))) >= {"acct", "token"}


def test_piece_without_equals_that_decodes_to_pair_is_masked():
    assert redact.mask_query("token%3Dabc&a=1", SENSITIVE) == "***&a=1"
    assert redact.mask_query("a=1&x%3Dy", SENSITIVE) == "a=1&***"
    assert redact.mask_query("plain%20word&a=1", SENSITIVE) == "plain%20word&a=1"


@pytest.mark.parametrize("qs,expected", [
    ("access.token=abc", "access.token=***"),
    ("api key=abc", "api key=***"),
    ("api+key=abc", "api+key=***"),
    ("token%00=abc", "token%00=***"),
    ("tok%00en=abc", "tok%00en=***"),
    ("Access.Token[]=abc", "Access.Token[]=***"),
    ("a.b=1", "a.b=1"),
])
def test_name_normalisation(qs, expected):
    assert redact.mask_query(qs, SENSITIVE) == expected


def test_salt_created_readable_under_restrictive_umask(home):
    paths.state_root().parent.mkdir(parents=True)
    old = os.umask(0o577)
    try:
        s = redact.load_or_create_salt()
    finally:
        os.umask(old)
    assert len(s) == 32
    assert redact.load_or_create_salt() == s


# ---- more cases ------------------------------------------------------------------------

@pytest.mark.parametrize("qs,expected", [
    ("redirect=%2Fx%3Ftoken%3Dabc", "redirect=***"),
    ("next=https%3A%2F%2Fh.example.com%2Fp%3Fsession%3DZZ&a=1", "next=***&a=1"),
    ("redirect=/x?token=abc&a=1", "redirect=***&a=1"),
    ("r=%2Fx%3Fa%3D1%26password%3DZZ", "r=***"),
    ("r=%2Fx%3Fa%3D1%3Bsid%3DZZ", "r=***"),
    ("r=%2Fp%3Bjsessionid%3DZZ", "r=***"),
    ("r=%2Fp%3Bjsessionid%3DZZ%3Fa%3D1", "r=***"),
    ("r=%2Fx%3Fa%3Db%3Ftoken%3Dabc", "r=***"),
    ("r=%2Fx%3Ftoken%3Dabc%00", "r=***"),
])
def test_nested_query_in_value_masked(qs, expected):
    names = redact.sensitive_names(Config())
    assert redact.mask_query(qs, names) == expected
    assert "abc" not in redact.mask_query(qs, names) and "ZZ" not in redact.mask_query(qs, names)


@pytest.mark.parametrize("qs", [
    "redirect=%2Fhome",
    "q=a%3Db",
    "q=a%3Db&x=1",
    "redirect=%2Fx%3Fpage%3D2",
    "u=https%3A%2F%2Fh.example.com%2Fp%3Fa%3D1%26b%3D2",
    "state=xyz==",
    "q=what%3F",
    "p=%2Fa%3Bv%3D1",
])
def test_benign_nested_value_kept(qs):
    assert redact.mask_query(qs, redact.sensitive_names(Config())) == qs


def test_nested_check_does_not_recurse_on_deep_values():
    qs = "r=" + "a%3D" * 5000 + "b"
    assert redact.mask_query(qs, SENSITIVE) == qs
    qs2 = "r=" + "%3F" * 5000 + "token%3Dabc"
    assert "abc" not in redact.mask_query(qs2, SENSITIVE)


def test_nested_query_masked_in_waf_record_args_and_referer():
    rec = make_record(headers=[{"name": "Referer", "value": "https://x.example.com/p?next=%2Fy%3Ftoken%3DREFZZ"}])
    rec["httpRequest"]["args"] = "redirect=%2Fx%3Ftoken%3DARGZZ&a=1"
    out = redact.waf_record(rec, Config(), SALT)
    assert out["query_masked"] == "redirect=***&a=1"
    assert out["referer_masked"] == "https://x.example.com/p?next=***"
    assert "ZZ" not in json.dumps(out)


@pytest.mark.parametrize("path,expected", [
    ("/a%3Bjsessionid=ZZ", "/a%3B***"),
    ("/a%3bjsessionid=ZZ", "/a%3B***"),
    ("/a%3Bx=1%3Btoken=ZZ", "/a%3B***"),
    ("/a;token=ZZ%3Bfoo=1", "/a;token=***%3B***"),
    ("/a%3B%ff", "/a%3B***"),
    ("/a%3Bx=%2541", "/a%3B***"),
    ("/a%3Bjsessionid%3DZZ", "/a%3B***"),
    ("/s/a%3Bjsessionid=ZZ/b;x=1", "/s/a%3B***/b;x=1"),
])
def test_mask_path_encoded_semicolon(path, expected):
    out = redact.mask_path(path, redact.sensitive_names(Config()))
    assert out == expected
    assert "ZZ" not in out


@pytest.mark.parametrize("path", ["/a%3Bx=1", "/a%3Bflag", "/a%3Bv%3D1", "/a%2Fb", "/a%3B"])
def test_mask_path_benign_encoded_semicolon_kept(path):
    assert redact.mask_path(path, redact.sensitive_names(Config())) == path


def test_uri_and_referer_encoded_semicolon_in_waf_record():
    rec = make_record(headers=[{"name": "Referer", "value": "https://x.example.com/a%3Bjsessionid=REFZZ?a=1"}])
    rec["httpRequest"]["uri"] = "/a%3Bjsessionid=URIZZ?a=1"
    out = redact.waf_record(rec, Config(), SALT)
    assert out["uri"] == "/a%3B***?a=1"
    assert out["referer_masked"] == "https://x.example.com/a%3B***?a=1"
    assert "ZZ" not in json.dumps(out)


# ---- fragments and userinfo inside a non-sensitive value; public mask_url -----------

@pytest.mark.parametrize("qs,expected", [
    ("r=%2Fx%23access_token%3DZZ", "r=***"),
    ("r=%2Fx%3Fa%3D1%23access_token%3DZZ", "r=***"),
    ("r=%2Fx%23%2Froute%3Ftoken%3DZZ", "r=***"),
    ("next=https%3A%2F%2Fuser%3Apass%40h.example.com%2Fp", "next=***"),
    ("next=https%3A%2F%2Fuser%40h.example.com", "next=***"),
    ("next=%2F%2Fuser%3Apass%40h.example.com%2Fp&a=1", "next=***&a=1"),
])
def test_fragment_and_userinfo_in_value_masked(qs, expected):
    out = redact.mask_query(qs, redact.sensitive_names(Config()))
    assert out == expected
    assert "ZZ" not in out and "pass" not in out


@pytest.mark.parametrize("qs", [
    "r=%2Fhome%23section",
    "r=%2Fhome%3Fa%3D1%23top",
    "r=%23",
    "next=https%3A%2F%2Fh.example.com%2Fp%3Fa%3D1%23frag",
    "email_to=a%40example.com",
    "next=https%3A%2F%2Fh.example.com%2Fuser%40home",
])
def test_benign_fragment_and_at_sign_kept(qs):
    assert redact.mask_query(qs, redact.sensitive_names(Config())) == qs


def test_fragment_check_does_not_recurse_on_deep_values():
    qs = "r=" + "a%3D%23" * 5000
    out = redact.mask_query(qs, SENSITIVE)  # must not raise RecursionError
    assert isinstance(out, str)
    qs2 = "r=" + "%23" * 5000 + "token%3DZZ"  # name "####...token" is not "token"; only no crash
    assert isinstance(redact.mask_query(qs2, SENSITIVE), str)
    qs3 = "r=" + "%3F" * 3000 + "%23token%3DZZ"
    assert "ZZ" not in redact.mask_query(qs3, SENSITIVE)


def test_fragment_and_userinfo_in_value_masked_in_waf_record():
    rec = make_record(headers=[{"name": "Referer", "value": "https://x.example.com/p?r=%2Fx%23access_token%3DREFZZ"}])
    rec["httpRequest"]["args"] = "next=https%3A%2F%2Fu%3Apw%40h.example.com&r=%2Fx%23access_token%3DARGZZ"
    out = redact.waf_record(rec, Config(), SALT)
    assert out["query_masked"] == "next=***&r=***"
    assert out["referer_masked"] == "https://x.example.com/p?r=***"


def test_mask_url_masks_query_path_and_drops_userinfo_fragment():
    names = redact.sensitive_names(Config())
    assert redact.mask_url("https://user:pw@www.example.com/p;jsessionid=ZZ?a=1&token=T#frag", names) == \
        "https://www.example.com/p;jsessionid=***?a=1&token=***"
    assert redact.mask_url("/relative?token=T&b=2", names) == "/relative?token=***&b=2"
    assert redact.mask_url("https://www.example.com/p", names) == "https://www.example.com/p"


def test_mask_url_unparseable_and_passthrough():
    names = redact.sensitive_names(Config())
    assert redact.mask_url("http://[::1/SECRETPATH?token=x", names) == "***"
    assert redact.mask_url("-", names) == "-"
    assert redact.mask_url("", names) == ""
    assert redact.mask_url(None, names) is None
    assert redact.mask_url(5, names) == "***"


# ---- userinfo inside a fragment, backslash spellings -------------------------

@pytest.mark.parametrize("qs", [
    "r=%2Fx%23https%3A%2F%2Fu%3Apw%40h.example.com",
    "r=%2Fx%23%2F%2Fu%3Apw%40h",
    "r=https%3A%5C%5Cu%3Apw%40h.example.com%2Fp",
    "r=%2F%2Fu%3Apw%40h",
    "r=%5C%5Cu%3Apw%40h",
    "r=%2Fx%23https%3A%5C%5Cu%3Apw%40h",
])
def test_userinfo_in_fragment_or_backslash_form_masked(qs):
    out = redact.mask_query(qs, redact.sensitive_names(Config()))
    assert out == "r=***"


def test_mask_url_backslash_userinfo_dropped():
    names = redact.sensitive_names(Config())
    out = redact.mask_url("https:\\\\u:SECRETPW@h.example.com/p?token=T", names)
    assert "SECRETPW" not in out and out.endswith("?token=***")


# ---- fail-closed userinfo rule, every '#' piece ---------------------------

@pytest.mark.parametrize("qs", [
    "r=https%3A%2Fu%3ASECPW%40h.example.com%2Fp",            # https:/u:pw@h/p
    "r=https%3Au%3ASECPW%40h.example.com%2Fp",               # https:u:pw@h/p
    "r=https%3A%5Cu%3ASECPW%40h.example.com%2Fp",            # https:\u:pw@h/p
    "r=https%3A%2F%2F%2Fu%3ASECPW%40h.example.com%2Fp",      # https:///u:pw@h/p
    "r=https%3A%5C%5C%5Cu%3ASECPW%40h.example.com",          # https:\\\u:pw@h
    "r=%2F%2Fu%3ASECPW%40h.example.com",                     # //u:pw@h
    "r=%5Cu%3ASECPW%40h.example.com",                        # \u:pw@h (scheme-less, conservative here)
    "r=%2Fu%3ASECPW%40h.example.com",                        # /u:pw@h (scheme-less, conservative here)
    "r=ht%09tps%3A%2F%2Fu%3ASECPW%40h.example.com",          # tab inside the scheme
    "r=%20https%3A%2F%2Fu%3ASECPW%40h.example.com",          # leading space
    "r=mailto%3Auser%40example.com",                         # documented: an address counts as userinfo
    "r=x%23a%23https%3A%2F%2Fu%3ASECPW%40h",                 # second '#'
    "r=x%23a%23access_token%3DSECPW",                        # second '#', query-shaped
    "r=x%23a%23b%23https%3Au%3ASECPW%40h",                   # third '#'
])
def test_userinfo_variants_and_every_hash_piece_masked(qs):
    out = redact.mask_query(qs, redact.sensitive_names(Config()))
    assert out == "r=***"


@pytest.mark.parametrize("qs", [
    "u=user%40example.com",
    "email_to=a%40example.com",
    "r=https%3A%2F%2Fh.example.com%2F%40user",
    "r=https%3A%2F%2Fh.example.com%2Fp%3Fa%3Db%40c",
    "r=https%3A%2F%2Fh.example.com%3A8443%2Fp",
    "r=%2Fhome%23a%23b",
    "t=12%3A30%40x",
])
def test_benign_at_signs_and_colons_kept(qs):
    assert redact.mask_query(qs, redact.sensitive_names(Config())) == qs


@pytest.mark.parametrize("url", [
    "https:/u:SECPW@h.example.com/p?token=T",
    "https:u:SECPW@h.example.com/p?token=T",
    "https:\\u:SECPW@h.example.com/p?token=T",
    "https:///u:SECPW@h.example.com/p?token=T",
    "https://u:SECPW@h.example.com/p?token=T",
    "//u:SECPW@h.example.com/p?token=T",
    "\\\\u:SECPW@h.example.com/p?token=T",
    "https://a@b:SECPW@h.example.com/p?token=T",
    "ht\ttps://u:SECPW@h.example.com/p?token=T",
])
def test_mask_url_drops_userinfo_in_every_variant(url):
    out = redact.mask_url(url, redact.sensitive_names(Config()))
    assert "SECPW" not in out and "u:" not in out
    assert "h.example.com/p" in out and out.endswith("?token=***")


def test_mask_url_userinfo_documented_choices():
    names = redact.sensitive_names(Config())
    assert redact.mask_url("https://u:SECPW@h.example.com/p", names) == "https://h.example.com/p"
    assert redact.mask_url("mailto:user@example.com", names) == "mailto:example.com"  # address is dropped
    assert redact.mask_url("/@user/profile?x=1", names) == "/@user/profile?x=1"        # one slash = a path
    assert redact.mask_url("https://medium.example.com/@user/p", names) == "https://medium.example.com/@user/p"
    assert redact.mask_url("user%40example.com", names) == "user%40example.com"
