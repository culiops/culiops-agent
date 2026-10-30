"""Deterministic synthetic access logs for CloudFront, ALB and WAF (placeholders only).

make(root, kind, day, **opts) writes gzip files under root/<bucket>/<key> and returns
the list of keys. Everything derives from random.Random(7), so two calls with the same
arguments write byte-identical files. Hosts are example.com, IPs come from the
documentation ranges, the account is 111122223333.

Key layouts follow the AWS docs (see s3logs/layout.py for the URLs):
  cloudfront  <prefix><DIST>.<YYYY-MM-DD>-<HH>.<unique>.gz          (legacy standard logging)
              ... with fmt="json": <DIST>.<YYYY-MM-DD>-<HH>.<unique>.json.gz (v2 JSON, unsupported)
  alb         <prefix>AWSLogs/<acct>/elasticloadbalancing/<region>/<Y>/<M>/<D>/
              <acct>_elasticloadbalancing_<region>_app.<lb>.<id>_<end>_<ip>_<rand>.log.gz
              (the date directory is the delivery date, i.e. the date of the end time)
  waf         <prefix>AWSLogs/<acct>/WAFLogs/<region>/<acl>/<Y>/<M>/<D>/<HH>/<mm>/
              <acct>_waflogs_<region>_<acl>_<end>_<rand>.log.gz
"""
from __future__ import annotations

import datetime as dt
import gzip
import io
import json
import random
from pathlib import Path
from typing import List

ACCOUNT = "111122223333"
REGION = "us-east-1"
BUCKET = "example-logs-bucket"
DIST_ID = "E2EXAMPLE"
LB_NAME = "example-alb"
LB_ID = "1234567890abcdef"
ACL = "example-acl"
IPS = ["192.0.2.10", "192.0.2.77", "198.51.100.7", "198.51.100.23", "203.0.113.5", "203.0.113.99"]
PATHS = ["/", "/api/orders", "/api/catalog", "/login", "/static/app.js"]
AGENTS = ["curl/8.0", "Mozilla/5.0 (X11; Linux x86_64)", "example-monitor/1.0"]


def _rand_id(rng: random.Random, n: int = 8) -> str:
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(n))


def cf_key(day: dt.date, hour: int, prefix: str = "cf/", dist: str = DIST_ID,
           unique: str = "RT4KCN4SGK9", ext: str = "gz") -> str:
    return "%s%s.%s-%02d.%s.%s" % (prefix, dist, day.isoformat(), hour, unique, ext)


def alb_key(delivery_day: dt.date, end: dt.datetime, prefix: str = "", rand: str = "20sg8hgm") -> str:
    return ("%sAWSLogs/%s/elasticloadbalancing/%s/%04d/%02d/%02d/"
            "%s_elasticloadbalancing_%s_app.%s.%s_%s_192.0.2.200_%s.log.gz") % (
        prefix, ACCOUNT, REGION, delivery_day.year, delivery_day.month, delivery_day.day,
        ACCOUNT, REGION, LB_NAME, LB_ID, end.strftime("%Y%m%dT%H%MZ"), rand)


def waf_key(end: dt.datetime, prefix: str = "", rand: str = "e0ca43b5") -> str:
    return ("%sAWSLogs/%s/WAFLogs/%s/%s/%04d/%02d/%02d/%02d/%02d/"
            "%s_waflogs_%s_%s_%s_%s.log.gz") % (
        prefix, ACCOUNT, REGION, ACL, end.year, end.month, end.day, end.hour, end.minute,
        ACCOUNT, REGION, ACL, end.strftime("%Y%m%dT%H%MZ"), rand)


def _gz(text: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as g:
        g.write(text.encode("utf-8"))
    return buf.getvalue()


SECRET_TOKEN = "SECRETTOKEN"      # appears only where redaction must remove it
SECRET_COOKIE = "SECRETCOOKIE"


def _cf_body(rng: random.Random, day: dt.date, hour: int, records: int, json_fmt: bool,
             secrets: bool = False) -> str:
    fields = ("date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status "
              "cs(Referer) cs(User-Agent) cs-uri-query cs(Cookie) x-edge-result-type "
              "x-edge-request-id x-host-header cs-protocol cs-bytes time-taken")
    rows = []
    for _ in range(records):
        t = dt.time(hour, rng.randrange(60), rng.randrange(60))
        status = rng.choice([200, 200, 200, 304, 404, 502])
        vals = [day.isoformat(), t.strftime("%H:%M:%S"), "IAD89-C1", str(rng.randrange(200, 90000)),
                rng.choice(IPS), "GET", "d111111abcdef8.cloudfront.net", rng.choice(PATHS), str(status),
                "-", rng.choice(AGENTS).replace(" ", "%20"), "-", "-", "Hit", _rand_id(rng, 20),
                "www.example.com", "https", str(rng.randrange(100, 900)), "%.3f" % (rng.random() / 5)]
        if secrets:  # cs(Referer), cs-uri-query and cs(Cookie) carry placeholder secrets
            vals[9] = "https://www.example.com/p?token=%s&a=1" % SECRET_TOKEN
            vals[11] = "page=2&token=%s" % SECRET_TOKEN
            vals[12] = "sessionid=%s" % SECRET_COOKIE
        rows.append(vals)
    if json_fmt:
        names = [f.replace("(", "_").replace(")", "") for f in fields.split()]
        return "".join(json.dumps(dict(zip(names, r))) + "\n" for r in rows)
    out = ["#Version: 1.0", "#Fields: " + fields]
    out.extend("\t".join(r) for r in rows)
    return "\n".join(out) + "\n"


def _alb_body(rng: random.Random, end: dt.datetime, records: int, secrets: bool = False,
              extra_trailing: bool = False) -> str:
    lines = []
    for _ in range(records):
        t = end - dt.timedelta(seconds=rng.randrange(1, 300))
        ts = t.strftime("%Y-%m-%dT%H:%M:%S") + ".%06dZ" % rng.randrange(1000000)
        client = "%s:%d" % (rng.choice(IPS), rng.randrange(1024, 65535))
        target = "198.51.100.%d:8080" % rng.randrange(2, 250)
        status = rng.choice([200, 200, 200, 301, 404, 502])
        path = rng.choice(PATHS)
        if secrets:
            path += "?page=2&token=%s" % SECRET_TOKEN
        lines.append(
            'https %s app/%s/%s %s %s 0.001 0.%03d 0.000 %d %d %d %d '
            '"GET https://www.example.com:443%s HTTP/1.1" "%s" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 '
            'arn:aws:elasticloadbalancing:%s:%s:targetgroup/example-tg/0123456789abcdef '
            '"Root=1-%s-%s" "www.example.com" "arn:aws:acm:%s:%s:certificate/12345678-1234-1234-1234-123456789012" 0 %s "forward" "-" "-" "%s" "%d" "-" "-"'
            % (ts, LB_NAME, LB_ID, client, target, rng.randrange(1000), status, status,
               rng.randrange(100, 900), rng.randrange(100, 90000), path, rng.choice(AGENTS),
               REGION, ACCOUNT, _rand_id(rng, 8), _rand_id(rng, 24), REGION, ACCOUNT, ts, target, status))
        if extra_trailing:  # AWS appends new fields at the end, sometimes first as a lone "-"
            lines[-1] += ' "-" new-field'
    return "\n".join(lines) + "\n"


def _waf_body(rng: random.Random, end: dt.datetime, records: int, secrets: bool = False) -> str:
    lines = []
    for _ in range(records):
        t = end - dt.timedelta(seconds=rng.randrange(1, 300))
        ms = int(t.timestamp() * 1000)
        rec = {
            "timestamp": ms,
            "formatVersion": 1,
            "webaclId": "arn:aws:wafv2:%s:%s:regional/webacl/%s/0123abcd" % (REGION, ACCOUNT, ACL),
            "terminatingRuleId": rng.choice(["Default_Action", "example-rate-limit", "example-geo-block"]),
            "terminatingRuleType": "REGULAR",
            "action": rng.choice(["ALLOW", "ALLOW", "BLOCK"]),
            "httpSourceName": "ALB",
            "httpSourceId": "%s-app/%s/%s" % (ACCOUNT, LB_NAME, LB_ID),
            "ruleGroupList": [],
            "httpRequest": {
                "clientIp": rng.choice(IPS),
                "country": "US",
                "headers": [{"name": "Host", "value": "www.example.com"},
                            {"name": "User-Agent", "value": rng.choice(AGENTS)}],
                "uri": rng.choice(PATHS),
                "args": "q=%d" % rng.randrange(100) + ("&token=%s" % SECRET_TOKEN if secrets else ""),
                "httpVersion": "HTTP/1.1",
                "httpMethod": "GET",
                "requestId": _rand_id(rng, 24),
            },
        }
        if secrets:
            rec["httpRequest"]["headers"].append({"name": "Cookie", "value": "sessionid=%s" % SECRET_COOKIE})
        lines.append(json.dumps(rec, sort_keys=True))
    return "\n".join(lines) + "\n"


def make(root, kind: str, day: dt.date, **opts) -> List[str]:
    """Write synthetic gzip logs for one day under root/<bucket>/ and return their keys.

    Options: bucket, prefix (key prefix), hours (iterable, default 0..23), records (per
    file, default 3). cloudfront: fmt="legacy"|"json", dist. alb/waf: minutes (the
    minute marks within each listed hour that get an end-time file, default (0, 30)).
    secrets=True puts placeholder secrets (SECRET_TOKEN in query strings/args/referer,
    SECRET_COOKIE in cookies) where redaction must remove them; alb also takes
    extra_trailing=True (two fields past the documented last one).
    """
    if kind not in ("cloudfront", "alb", "waf"):
        raise ValueError("unknown kind %r" % (kind,))
    root = Path(root)
    bucket = opts.get("bucket", BUCKET)
    hours = list(opts.get("hours", range(24)))
    records = int(opts.get("records", 3))
    rng = random.Random(7)
    written: List[str] = []

    def put(key: str, text: str) -> None:
        p = root / bucket / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(_gz(text))
        written.append(key)

    midnight = dt.datetime(day.year, day.month, day.day)
    if kind == "cloudfront":
        json_fmt = opts.get("fmt", "legacy") == "json"
        for hh in hours:
            key = cf_key(day, hh, prefix=opts.get("prefix", "cf/"), dist=opts.get("dist", DIST_ID),
                         unique=_rand_id(rng, 11).upper(), ext="json.gz" if json_fmt else "gz")
            put(key, _cf_body(rng, day, hh, records, json_fmt, bool(opts.get("secrets"))))
    else:
        for hh in hours:
            for mm in opts.get("minutes", (0, 30)):
                end = midnight + dt.timedelta(hours=hh, minutes=mm)
                if kind == "alb":
                    put(alb_key(day, end, prefix=opts.get("prefix", ""), rand=_rand_id(rng)),
                        _alb_body(rng, end, records, bool(opts.get("secrets")),
                                  bool(opts.get("extra_trailing"))))
                else:
                    put(waf_key(end, prefix=opts.get("prefix", ""), rand=_rand_id(rng)),
                        _waf_body(rng, end, records, bool(opts.get("secrets"))))
    return written


# ---- query fixtures ---------------------------------------------------------------------------
# make_queries() writes a small, fixed data set per type so that every named query returns rows
# and the value tests can pin exact numbers. All numbers are in QUERY_FACTS.

BOT_UA = "ExampleBot/1.0 (crawler)"
WEB_UA = "Mozilla/5.0 (X11; Linux x86_64)"
SQLI_VALUE = "SECRETMATCH"            # a matched value; only its salted hash may reach a query

QUERY_FACTS = {
    "cloudfront": {"rows": 32, "hit": 24, "miss": 8, "bot_rows": 6, "top_client": IPS[0],
                   "top_client_rows": 11, "clients": 6, "big_object": "/media/big.bin",
                   "big_rows": 10, "big_clients": 2, "big_size": 1000000, "big_bytes": 8800000,
                   "aborted": 2, "range_object": "/media/part.bin", "range_rows": 4,
                   "status": {"200": 25, "206": 4, "404": 2, "502": 1}},
    "waf": {"rows": 100, "top_ip": IPS[0], "top_rows": 40, "top_keys": 25, "clients": 6,
            "day_a_offset": 0, "day_b_offset": 1,
            "rules_a": {"Default_Action": 25, "example-rate-limit": 10, "example-geo-block": 5},
            "rules_b": {"Default_Action": 25, "example-rate-limit": 25, "example-geo-block": 5,
                        "example-bot-control": 5}},
    "alb": {"rows": 34, "lb_502": 5, "target_502": 3, "ok": 22, "not_found": 4},
}


def _cf_query_rows(day: dt.date):
    rows = []

    def add(**kw):
        rows.append(kw)

    for k in range(8):                                             # one client downloads the same file again
        aborted = k < 2
        add(stem="/media/big.bin", client=IPS[0], status=200, bytes=400000 if aborted else 1000000,
            ua="curl/8.0", length=1000000, detail="ClientCommError" if aborted else "Hit")
    for k in range(2):
        add(stem="/media/big.bin", client=IPS[2], status=200, bytes=1000000, ua=WEB_UA, length=1000000)
    for k in range(4):
        add(stem="/media/part.bin", client=IPS[4], status=206, bytes=100000, ua=WEB_UA, length=1000000,
            rng=(k * 100000, k * 100000 + 99999))
    for j in range(18):
        status = 404 if j % 9 == 8 else (502 if j == 5 else 200)
        add(stem="/static/app.js", client=IPS[j % 6], status=status, bytes=5000,
            ua=BOT_UA if j % 3 == 0 else WEB_UA, length=5000,
            referer=("https://www.example.com/blog/post-1?utm=x" if j < 6 else
                     "https://news.example.com/item/9?id=4" if j < 9 else "-"))
    return rows


def _cf_query_files(day: dt.date):
    fields = ("date time x-edge-location sc-bytes c-ip cs-method cs(Host) cs-uri-stem sc-status "
              "cs(Referer) cs(User-Agent) cs-uri-query x-edge-result-type x-edge-request-id "
              "x-host-header cs-protocol cs-bytes time-taken x-edge-detailed-result-type "
              "sc-content-len sc-range-start sc-range-end")
    by_hour = {0: [], 1: [], 2: []}
    for g, r in enumerate(_cf_query_rows(day)):
        rng = r.get("rng")
        by_hour[g % 3].append("\t".join([
            day.isoformat(), "%02d:%02d:00" % (g % 3, g), "IAD89-C1" if g % 2 else "FRA56-P2",
            str(r["bytes"]), r["client"], "GET", "d111111abcdef8.cloudfront.net", r["stem"],
            str(r["status"]), r.get("referer", "-"), r["ua"].replace(" ", "%20"), "-",
            "Miss" if g % 4 == 3 else "Hit", "req%05d" % g, "www.example.com", "https", "300", "0.050",
            r.get("detail", "Hit" if g % 4 != 3 else "Miss"), str(r["length"]),
            str(rng[0]) if rng else "-", str(rng[1]) if rng else "-"]))
    return fields, by_hour


def _alb_query_line(ts: dt.datetime, client: str, target: str, elb_status: int, target_status: str,
                    path: str, tproc: float) -> str:
    t = ts.strftime("%Y-%m-%dT%H:%M:%S") + ".000000Z"
    lb_made = target == "-"
    times = "-1 -1 -1" if lb_made else "0.001 %.3f 0.000" % tproc
    return (
        'https %s app/%s/%s %s:40000 %s %s %d %s 300 500 "GET https://www.example.com:443%s HTTP/1.1" '
        '"%s" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 '
        'arn:aws:elasticloadbalancing:%s:%s:targetgroup/example-tg/0123456789abcdef '
        '"Root=1-q-%s" "www.example.com" "arn:aws:acm:%s:%s:certificate/12345678-1234-1234-1234-123456789012" '
        '0 %s "forward" "-" "-" "%s" "%s" "-" "-"'
        % (t, LB_NAME, LB_ID, client, "-" if lb_made else target + ":8080", times, elb_status,
           target_status, path, WEB_UA, REGION, ACCOUNT, "%024d" % int(ts.timestamp() % 10**9), REGION,
           ACCOUNT, t, "-" if lb_made else target + ":8080", target_status))


def _alb_query_body(day: dt.date) -> str:
    base = dt.datetime(day.year, day.month, day.day)
    specs = []
    for i in range(5):
        specs.append((IPS[0], "-", 502, "-", "/api/orders", 0.0))                 # produced by the LB
    for i in range(3):
        specs.append((IPS[1], "198.51.100.10", 502, "502", "/api/orders", 0.9))   # produced by a target
    for i in range(22):
        specs.append((IPS[i % 6], "198.51.100.%d" % (10 + i % 2), 200, "200",
                      "/api/catalog" if i % 2 else "/", 0.01 * (i + 1)))
    for i in range(4):
        specs.append((IPS[3], "198.51.100.11", 404, "404", "/missing", 0.005))
    return "\n".join(_alb_query_line(base + dt.timedelta(seconds=10 * i), *spec)
                     for i, spec in enumerate(specs)) + "\n"


def _waf_query_records(day: dt.date):
    """100 records: 40 from IPS[0] (25 distinct session cookies), 60 spread over five other IPs.
    The first 40 are on `day` and the other 60 on the next day."""
    def day_rules(counts):
        out = []
        for rule, n in counts.items():
            out += [rule] * n
        return out
    rules = (day_rules(QUERY_FACTS["waf"]["rules_a"]) + day_rules(QUERY_FACTS["waf"]["rules_b"]))
    recs = []
    top = other = 0
    for j, rule in enumerate(rules):
        a_day = j < 40
        if j % 5 < 2:
            ip, cookie = IPS[0], "sessionid=sid%02d" % (top % 25)
            top += 1
        else:
            ip, cookie = IPS[1 + other % 5], None
            other += 1
        recs.append((j, a_day, rule, ip, cookie))
    return recs


def _waf_query_files(day: dt.date):
    out = {}
    for j, a_day, rule, ip, cookie in _waf_query_records(day):
        d = day if a_day else day + dt.timedelta(days=1)
        t = dt.datetime(d.year, d.month, d.day, 1, 0, 0) + dt.timedelta(seconds=j)
        bot = j % 10 == 9
        headers = [{"name": "Host", "value": "www.example.com"},
                   {"name": "User-Agent", "value": "ExampleBot/2.0 (spider)" if bot else WEB_UA}]
        if not bot:
            headers.append({"name": "Accept", "value": "*/*"})
        if cookie:
            headers.append({"name": "Cookie", "value": cookie})
        rec = {
            "timestamp": int(t.replace(tzinfo=dt.timezone.utc).timestamp() * 1000),
            "formatVersion": 1,
            "webaclId": "arn:aws:wafv2:%s:%s:regional/webacl/%s/0123abcd" % (REGION, ACCOUNT, ACL),
            "terminatingRuleId": rule,
            "terminatingRuleType": "REGULAR",
            "action": "ALLOW" if rule == "Default_Action" else "BLOCK",
            "httpSourceName": "ALB",
            "httpSourceId": "%s-app/%s/%s" % (ACCOUNT, LB_NAME, LB_ID),
            "ruleGroupList": [],
            "nonTerminatingMatchingRules": ([{"ruleId": "example-count-rule", "action": "COUNT"}]
                                            if j % 7 == 0 else []),
            "labels": [{"name": "example:rate:limited"}] if rule == "example-rate-limit" else [],
            "ja3Fingerprint": ("a" * 32) if ip == IPS[0] else ("b" * 32),
            "ja4Fingerprint": "t13d1516h2_example_" + ("a" if ip == IPS[0] else "b"),
            "httpRequest": {
                "clientIp": ip,
                "country": "US" if ip == IPS[0] else ["DE", "FR", "US"][j % 3],
                "clientAsn": "64500" if ip == IPS[0] else "64501",
                "headers": headers,
                "uri": ["/", "/api/orders", "/login"][j % 3],
                "args": "q=%d" % (j % 5),
                "httpVersion": "HTTP/1.1",
                "httpMethod": "GET",
                "requestId": "req-%04d" % j,
            },
        }
        if rule == "example-bot-control":
            rec["terminatingRuleMatchDetails"] = [{"conditionType": "SQL_INJECTION",
                                                   "location": "QUERY_STRING",
                                                   "matchedData": [SQLI_VALUE]}]
        out.setdefault(t.replace(second=0), []).append(json.dumps(rec, sort_keys=True))
    return out


def make_queries(root, kind: str, day: dt.date, bucket: str = BUCKET) -> List[str]:
    """Write the fixed query data set for one type under root/<bucket>/ and return its keys.
    WAF writes records onto `day` and `day`+1 (see QUERY_FACTS)."""
    if kind not in QUERY_FACTS:
        raise ValueError("unknown kind %r" % (kind,))
    root = Path(root)
    written: List[str] = []

    def put(key: str, text: str) -> None:
        p = root / bucket / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(_gz(text))
        written.append(key)

    if kind == "cloudfront":
        fields, by_hour = _cf_query_files(day)
        for hh, lines in by_hour.items():
            put(cf_key(day, hh, unique="Q%010d" % hh),
                "\n".join(["#Version: 1.0", "#Fields: " + fields] + lines) + "\n")
    elif kind == "alb":
        end = dt.datetime(day.year, day.month, day.day, 0, 5)
        put(alb_key(day, end, rand="queries0"), _alb_query_body(day))
    else:
        for n, (minute, lines) in enumerate(sorted(_waf_query_files(day).items())):
            end = minute + dt.timedelta(minutes=1)
            put(waf_key(end, rand="q%07d" % n), "\n".join(lines) + "\n")
    return written
