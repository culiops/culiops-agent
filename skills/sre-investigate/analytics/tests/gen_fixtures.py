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


def _cf_body(rng: random.Random, day: dt.date, hour: int, records: int, json_fmt: bool) -> str:
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
        rows.append(vals)
    if json_fmt:
        names = [f.replace("(", "_").replace(")", "") for f in fields.split()]
        return "".join(json.dumps(dict(zip(names, r))) + "\n" for r in rows)
    out = ["#Version: 1.0", "#Fields: " + fields]
    out.extend("\t".join(r) for r in rows)
    return "\n".join(out) + "\n"


def _alb_body(rng: random.Random, end: dt.datetime, records: int) -> str:
    lines = []
    for _ in range(records):
        t = end - dt.timedelta(seconds=rng.randrange(1, 300))
        ts = t.strftime("%Y-%m-%dT%H:%M:%S") + ".%06dZ" % rng.randrange(1000000)
        client = "%s:%d" % (rng.choice(IPS), rng.randrange(1024, 65535))
        target = "198.51.100.%d:8080" % rng.randrange(2, 250)
        status = rng.choice([200, 200, 200, 301, 404, 502])
        path = rng.choice(PATHS)
        lines.append(
            'https %s app/%s/%s %s %s 0.001 0.%03d 0.000 %d %d %d %d '
            '"GET https://www.example.com:443%s HTTP/1.1" "%s" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 '
            'arn:aws:elasticloadbalancing:%s:%s:targetgroup/example-tg/0123456789abcdef '
            '"Root=1-%s-%s" "www.example.com" "arn:aws:acm:%s:%s:certificate/12345678-1234-1234-1234-123456789012" 0 %s "forward" "-" "-" "%s" "%d" "-" "-"'
            % (ts, LB_NAME, LB_ID, client, target, rng.randrange(1000), status, status,
               rng.randrange(100, 900), rng.randrange(100, 90000), path, rng.choice(AGENTS),
               REGION, ACCOUNT, _rand_id(rng, 8), _rand_id(rng, 24), REGION, ACCOUNT, ts, target, status))
    return "\n".join(lines) + "\n"


def _waf_body(rng: random.Random, end: dt.datetime, records: int) -> str:
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
                "args": "q=%d" % rng.randrange(100),
                "httpVersion": "HTTP/1.1",
                "httpMethod": "GET",
                "requestId": _rand_id(rng, 24),
            },
        }
        lines.append(json.dumps(rec, sort_keys=True))
    return "\n".join(lines) + "\n"


def make(root, kind: str, day: dt.date, **opts) -> List[str]:
    """Write synthetic gzip logs for one day under root/<bucket>/ and return their keys.

    Options: bucket, prefix (key prefix), hours (iterable, default 0..23), records (per
    file, default 3). cloudfront: fmt="legacy"|"json", dist. alb/waf: minutes (the
    minute marks within each listed hour that get an end-time file, default (0, 30)).
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
            put(key, _cf_body(rng, day, hh, records, json_fmt))
    else:
        for hh in hours:
            for mm in opts.get("minutes", (0, 30)):
                end = midnight + dt.timedelta(hours=hh, minutes=mm)
                if kind == "alb":
                    put(alb_key(day, end, prefix=opts.get("prefix", ""), rand=_rand_id(rng)),
                        _alb_body(rng, end, records))
                else:
                    put(waf_key(end, prefix=opts.get("prefix", ""), rand=_rand_id(rng)),
                        _waf_body(rng, end, records))
    return written
