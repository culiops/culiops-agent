"""Named queries, end to end: converted Parquet from the fixed query fixtures, run through the
real bin/sqlq (so the named-file check and the locked-down DuckDB are exercised)."""
from __future__ import annotations

import csv
import datetime as dt
import io
import itertools
import os
import re
import shutil
import subprocess

import pytest

from s3logs import cli_sqlq, convert, paths
from s3logs.config import Config

import gen_fixtures as gf
from conftest import BIN, _ORIGINAL_PATH

RUN = "orders-prod-20261030-1200"
DAY = dt.date(2026, 3, 9)
SQL_DIR = cli_sqlq.SQL_DIR
DS = {"cloudfront": "cdn1", "waf": "waf1", "alb": "alb1"}
CFG_LINES = (
    "DATASET_waf1=waf:s3://example-logs-bucket/waf/{yyyy}/{MM}/{dd}/{HH}/",
    "DATASET_cdn1=cloudfront:s3://example-logs-bucket/cf/{yyyy}/{MM}/{dd}/{HH}/",
    "DATASET_alb1=alb:s3://example-logs-bucket/alb/{yyyy}/{MM}/{dd}/",
)

BRIEF_NAMES = {
    "cloudfront": {"summary", "by_day", "by_hour", "top_objects", "top_referers", "referer_pages",
                   "user_agents", "top_clients", "client_concentration", "cache_results", "status_codes",
                   "range_requests", "edges", "aborted", "object_by_day", "bytes_per_viewer"},
    "waf": {"summary", "by_day", "by_minute", "top_rules", "rules_by_minute", "labels", "count_rules",
            "user_agents", "clients", "concentration", "client_keys", "fingerprints", "asns", "uris",
            "countries", "header_shape", "compare_days", "matched_data"},
    "alb": {"summary", "by_minute", "status_by_target", "target_latency_pct", "top_paths_5xx",
            "top_clients", "lb_vs_target_status"},
}
EXTRA_NAMES = {"cloudfront": {"by_object"}, "waf": set(), "alb": set()}   # R34: Task 8 added by_object

DAY_A = DAY.isoformat()
DAY_B = (DAY + dt.timedelta(days=1)).isoformat()
PARAMS = {
    ("cloudfront", "object_by_day"): {"object": "/media/big.bin"},
    ("cloudfront", "by_object"): {"object": "/media/big.bin"},
    ("waf", "compare_days"): {"a": DAY_A, "b": DAY_B},
}
ALL = sorted((t, n) for t in DS for n in BRIEF_NAMES[t] | EXTRA_NAMES[t])

# Time series are bounded by the window (minute/hour/day buckets); aggregates return one row.
BOUNDED_BY_WINDOW = {"by_day", "by_hour", "by_minute", "rules_by_minute", "object_by_day", "by_object"}
ONE_ROW = {"summary", "client_concentration", "concentration"}


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    duck = shutil.which("duckdb", path=_ORIGINAL_PATH) or os.path.join(os.path.expanduser("~"),
                                                                       ".local", "bin", "duckdb")
    if not os.access(duck, os.X_OK):
        pytest.skip("duckdb CLI not installed")
    home = tmp_path_factory.mktemp("home")
    mp = pytest.MonkeyPatch()
    mp.setenv("HOME", str(home))
    mp.setenv("PATH", os.path.dirname(duck) + os.pathsep + _ORIGINAL_PATH)
    cfgdir = home / ".config" / "culiops" / "sre-investigate"
    cfgdir.mkdir(parents=True)
    (cfgdir / "logs.env").write_text("\n".join(CFG_LINES) + "\n")
    paths.ensure_private_dirs()
    for kind, ds in DS.items():
        src = home / "in" / kind
        keys = gf.make_queries(src, kind, DAY)
        d = paths.state_root() / "data" / RUN / ds
        d.mkdir(parents=True)
        res = convert.to_parquet(kind, [src / gf.BUCKET / k for k in keys], d / "part-000001.parquet",
                                 Config(), bytes(range(32)))
        assert res.rows == gf.QUERY_FACTS[kind]["rows"], kind
        os.chmod(str(d), 0o555)
    yield home
    mp.undo()
    for dirpath, dirnames, _files in os.walk(str(home)):
        for d in dirnames:
            full = os.path.join(dirpath, d)
            if not os.path.islink(full):
                os.chmod(full, 0o700)


def sqlq(home, *args):
    cp = subprocess.run([str(BIN / "sqlq")] + [str(a) for a in args], capture_output=True,
                        env={"HOME": str(home), "PATH": os.environ["PATH"]}, timeout=120)
    cp.stdout = cp.stdout.decode("utf-8")
    cp.stderr = cp.stderr.decode("utf-8")
    return cp


def run(home, kind, name, **params):
    args = [DS[kind], "--run", RUN, name]
    for k, v in (params or PARAMS.get((kind, name), {})).items():
        args += ["--param", "%s=%s" % (k, v)]
    cp = sqlq(home, *args)
    assert cp.returncode == 0, (kind, name, cp.stderr)
    return list(csv.DictReader(io.StringIO(cp.stdout)))


def one(rows, **where):
    hit = [r for r in rows if all(r[k] == v for k, v in where.items())]
    assert len(hit) == 1, (where, rows)
    return hit[0]


# ---- structure ------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", sorted(DS))
def test_named_queries_present(kind):
    have = {p.stem for p in (SQL_DIR / kind).glob("*.sql")}
    assert BRIEF_NAMES[kind] <= have
    assert have - BRIEF_NAMES[kind] == EXTRA_NAMES[kind]


@pytest.mark.parametrize("kind,name", ALL)
def test_every_named_query_runs(env, kind, name):
    cp = sqlq(env, DS[kind], "--run", RUN, name,
              *[x for k, v in PARAMS.get((kind, name), {}).items() for x in ("--param", "%s=%s" % (k, v))])
    assert cp.returncode == 0, cp.stderr
    assert "is not used by query" not in cp.stderr
    recs = list(csv.reader(io.StringIO(cp.stdout)))
    assert len(recs) >= 2, "no data rows"
    text = (SQL_DIR / kind / (name + ".sql")).read_text()
    assert re.match(r"-- \S.{8,}\n", text), "first line must be a purpose comment"
    assert len(recs) - 1 <= 50 or name in BOUNDED_BY_WINDOW


@pytest.mark.parametrize("kind,name", ALL)
def test_output_is_bounded_by_design(kind, name):
    text = (SQL_DIR / kind / (name + ".sql")).read_text()
    assert name in BOUNDED_BY_WINDOW or name in ONE_ROW or "LIMIT 50" in text, \
        "%s/%s is neither top-N, a time series nor a single aggregate row" % (kind, name)
    assert all(int(n) <= 50 for n in re.findall(r"\bLIMIT\s+(\d+)", text))


@pytest.mark.parametrize("kind,name", ALL)
def test_reads_only_the_logs_view_and_no_query_strings(kind, name):
    text = (SQL_DIR / kind / (name + ".sql")).read_text()
    code = "\n".join(ln for ln in text.splitlines() if not ln.startswith("--"))
    ctes = set(re.findall(r"\b(\w+)\s+AS\s*\(", code, flags=re.I))
    tables = {t.lower() for t in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][\w.]*)", code, flags=re.I)}
    assert "logs" in tables and tables <= {"logs"} | {c.lower() for c in ctes}, tables
    for col in ("cs_uri_query", "query_masked"):
        assert col not in code, "never select query strings, not even masked ones"


# ---- value tests (the brief's four) ---------------------------------------------------------

def test_alb_lb_vs_target_status_counts_502_without_a_target_response(env):
    rows = run(env, "alb", "lb_vs_target_status")
    none = [r for r in rows if r["origin"] == "no_target_response"]
    assert {r["elb_status_code"] for r in none} == {"502"} and sum(int(r["requests"]) for r in none) == 5
    assert {r["error_reason"]: int(r["requests"]) for r in none} == {"TargetNotFound": 2, "-": 3}
    assert int(one(rows, elb_status_code="502", origin="target_responded")["requests"]) == 3
    assert all(int(r["elb_status_code"]) >= 500 for r in rows)
    assert not any("lb_generated" in r["origin"] or "target_generated" in r["origin"] for r in rows)


def test_waf_concentration_top_share_and_client_keys(env):
    (r,) = run(env, "waf", "concentration")
    assert r["top1_client"] == gf.IPS[0]
    assert float(r["top1_share"]) == pytest.approx(0.40)
    assert int(r["requests"]) == 100 and int(r["top1_requests"]) == 40
    assert int(r["distinct_clients"]) == 6
    assert int(r["top1_client_keys"]) == 25
    assert int(r["distinct_client_keys"]) == 25


def test_cloudfront_cache_results_three_to_one(env):
    rows = run(env, "cloudfront", "cache_results")
    hit, miss = one(rows, x_edge_result_type="Hit"), one(rows, x_edge_result_type="Miss")
    assert (int(hit["requests"]), int(miss["requests"])) == (24, 8)
    assert float(hit["share"]) == pytest.approx(0.75) and float(miss["share"]) == pytest.approx(0.25)
    assert {r["hit_ratio"] for r in rows} == {"0.75"}


def test_waf_compare_days_per_rule_delta(env):
    rows = run(env, "waf", "compare_days")
    rl = one(rows, rule="example-rate-limit")
    assert (int(rl["requests_a"]), int(rl["requests_b"]), int(rl["delta"])) == (10, 25, 15)
    bot = one(rows, rule="example-bot-control")
    assert (int(bot["requests_a"]), int(bot["requests_b"]), int(bot["delta"])) == (0, 5, 5)
    assert int(one(rows, rule="Default_Action")["delta"]) == 0
    assert rows[0]["rule"] == "example-rate-limit"          # largest absolute change first
    swapped = run(env, "waf", "compare_days", a=DAY_B, b=DAY_A)
    assert int(one(swapped, rule="example-rate-limit")["delta"]) == -15


# ---- more value tests -----------------------------------------------------------------------

def test_cloudfront_summary_and_status_codes(env):
    (s,) = run(env, "cloudfront", "summary")
    assert int(s["requests"]) == 32 and int(s["distinct_clients"]) == 6 and int(s["distinct_objects"]) == 3
    assert (int(s["status_2xx"]), int(s["status_4xx"]), int(s["status_5xx"])) == (29, 2, 1)
    rows = run(env, "cloudfront", "status_codes")
    assert {r["sc_status"]: int(r["requests"]) for r in rows} == {"200": 25, "206": 4, "404": 2, "502": 1}


def test_cloudfront_client_concentration(env):
    (r,) = run(env, "cloudfront", "client_concentration")
    assert r["top1_client"] == gf.IPS[0] and int(r["top1_requests"]) == 11
    assert float(r["top1_share"]) == pytest.approx(11 / 32, abs=1e-3)
    assert int(r["distinct_clients"]) == 6 and int(r["requests"]) == 32


def test_cloudfront_bytes_per_viewer_flags_repeated_downloads(env):
    rows = run(env, "cloudfront", "bytes_per_viewer")
    big = one(rows, cs_uri_stem="/media/big.bin")
    assert int(big["requests"]) == 10 and int(big["distinct_clients"]) == 2
    assert int(big["object_size"]) == 1000000 and int(big["bytes"]) == 8800000
    assert int(big["bytes_per_viewer"]) == 4400000 and big["size_is_estimate"] == "false"
    assert float(big["repeat_factor"]) == pytest.approx(4.4)
    assert rows[0]["cs_uri_stem"] == "/media/big.bin"        # most bytes first
    part = one(rows, cs_uri_stem="/media/part.bin")          # only 206s: size is a lower-bound estimate
    assert part["size_is_estimate"] == "true" and int(part["object_size"]) == 400000


def test_cloudfront_aborted_range_edges_and_object(env):
    ab = run(env, "cloudfront", "aborted")
    big = one(ab, cs_uri_stem="/media/big.bin")
    assert int(big["aborted_requests"]) == 2 and int(big["requests"]) == 10
    # app.js has a HEAD 200 (headers only) and a download whose sc-bytes include header overhead: neither is aborted
    assert all(r["cs_uri_stem"] != "/static/app.js" for r in ab)
    assert [r["cs_uri_stem"] for r in ab] == ["/media/big.bin"]
    rg = one(run(env, "cloudfront", "range_requests"), cs_uri_stem="/media/part.bin")
    assert int(rg["range_requests"]) == 4 and int(float(rg["avg_range_bytes"])) == 100000
    edges = run(env, "cloudfront", "edges")
    assert sum(int(r["requests"]) for r in edges) == 32 and len(edges) == 2
    days = run(env, "cloudfront", "object_by_day")
    assert sum(int(r["requests"]) for r in days) == 10 and {r["day"] for r in days} == {DAY_A}


def test_cloudfront_referers_user_agents_and_top_lists(env):
    hosts = {r["referer_host"]: int(r["requests"]) for r in run(env, "cloudfront", "top_referers")}
    assert hosts == {"www.example.com": 6, "news.example.com": 3}
    pages = {r["referer_page"]: int(r["requests"]) for r in run(env, "cloudfront", "referer_pages")}
    assert pages == {"https://www.example.com/blog/post-1": 6, "https://news.example.com/item/9": 3}
    ua = run(env, "cloudfront", "user_agents")
    assert sum(int(r["requests"]) for r in ua if r["ua_bucket"] == "bot/crawler/spider") == 6
    assert sum(int(r["requests"]) for r in ua if r["ua_bucket"] == "other") == 26
    top = run(env, "cloudfront", "top_objects")
    assert top[0]["cs_uri_stem"] == "/static/app.js" and int(top[0]["requests"]) == 18
    clients = run(env, "cloudfront", "top_clients")
    assert clients[0]["c_ip"] == gf.IPS[0] and float(clients[0]["share"]) == pytest.approx(11 / 32, abs=1e-3)


def test_cloudfront_time_series(env):
    assert [int(r["requests"]) for r in run(env, "cloudfront", "by_day")] == [32]
    hours = run(env, "cloudfront", "by_hour")
    assert len(hours) == 3 and sum(int(r["requests"]) for r in hours) == 32


def test_waf_summary_rules_labels_and_count_rules(env):
    (s,) = run(env, "waf", "summary")
    assert (int(s["requests"]), int(s["allowed"]), int(s["blocked"])) == (100, 50, 50)
    assert int(s["distinct_clients"]) == 6 and int(s["distinct_rules"]) == 4
    rules = {r["terminating_rule_id"]: int(r["requests"]) for r in run(env, "waf", "top_rules")}
    assert rules == {"Default_Action": 50, "example-rate-limit": 35, "example-geo-block": 10,
                     "example-bot-control": 5}
    labels = run(env, "waf", "labels")
    assert [(r["label"], int(r["requests"])) for r in labels] == [("example:rate:limited", 35)]
    cr = one(run(env, "waf", "count_rules"), rule_id="example-count-rule")
    assert cr["rule_action"] == "COUNT" and int(cr["requests"]) == 15       # j % 7 == 0 for j < 100
    days = run(env, "waf", "by_day")
    assert [(r["day"], int(r["requests"])) for r in days] == [(DAY_A, 40), (DAY_B, 60)]
    assert sum(int(r["requests"]) for r in run(env, "waf", "rules_by_minute")) == 100


def test_waf_clients_keys_and_fingerprints_are_aggregated_hashes(env):
    clients = run(env, "waf", "clients")
    assert clients[0]["client_ip"] == gf.IPS[0] and int(clients[0]["requests"]) == 40
    assert float(clients[0]["share"]) == pytest.approx(0.4) and int(clients[0]["distinct_client_keys"]) == 25
    keys = run(env, "waf", "client_keys")
    assert len(keys) == 25
    assert all(re.fullmatch(r"[0-9a-f]{12}", r["client_key"]) for r in keys)       # hashes only
    assert all(int(r["distinct_ips"]) == 1 for r in keys)
    fp = run(env, "waf", "fingerprints")
    assert {(r["ja3"][:1], int(r["requests"])) for r in fp} == {("a", 40), ("b", 60)}


def test_waf_user_agents_asns_uris_countries_header_shape(env):
    ua = run(env, "waf", "user_agents")
    assert sum(int(r["requests"]) for r in ua if r["ua_bucket"] == "bot/crawler/spider") == 10
    assert {r["asn"]: int(r["requests"]) for r in run(env, "waf", "asns")} == {"64500": 40, "64501": 60}
    assert sum(int(r["requests"]) for r in run(env, "waf", "uris")) == 100
    assert sum(int(r["requests"]) for r in run(env, "waf", "countries")) == 100
    shapes = {r["header_shape"]: int(r["requests"]) for r in run(env, "waf", "header_shape")}
    assert shapes == {"host,user-agent": 10, "host,user-agent,accept": 50,
                      "host,user-agent,accept,cookie": 40}               # names only, never a value


def test_waf_matched_data_never_shows_the_value(env):
    cp = sqlq(env, DS["waf"], "--run", RUN, "matched_data")
    assert cp.returncode == 0 and gf.SQLI_VALUE not in cp.stdout
    (r,) = list(csv.DictReader(io.StringIO(cp.stdout)))
    assert r["terminating_rule_id"] == "example-bot-control"
    assert (r["matched_field"], r["match_type"], int(r["requests"])) == ("QUERY_STRING", "SQL_INJECTION", 5)
    assert int(r["distinct_matched_values"]) == 1


def test_waf_by_minute_still_works(env):
    assert sum(int(r["requests"]) for r in run(env, "waf", "by_minute")) == 100
    assert sum(int(r["requests"]) for r in run(env, "waf", "by_minute", action="BLOCK")) == 50


def test_alb_summary_minute_and_targets(env):
    (s,) = run(env, "alb", "summary")
    assert int(s["requests"]) == 34 and int(s["distinct_clients"]) == 6
    assert (int(s["status_2xx"]), int(s["status_4xx"]), int(s["status_5xx"])) == (22, 4, 8)
    assert int(s["no_target_5xx"]) == 5 and int(s["no_target_time_requests"]) == 5
    assert s["p95_target_seconds"] == "0.9"
    assert "lb_generated_5xx" not in s
    mins = run(env, "alb", "by_minute")
    assert sum(int(r["requests"]) for r in mins) == 34 and sum(int(r["no_target_5xx"]) for r in mins) == 5
    assert sum(int(r["no_target_time_requests"]) for r in mins) == 5
    # six 10-second-spaced minutes; 0.098/0.158/0.2175 interpolate between neighbours (tolerance for the last digit)
    assert [float(r["p95_target_seconds"]) for r in mins] == pytest.approx(
        [0.9, 0.9, 0.098, 0.158, 0.2175, 0.005], abs=1e-3)
    st = run(env, "alb", "status_by_target")
    none = one(st, target_ip="-")
    assert int(none["requests"]) == 5 and int(none["no_target_response"]) == 5 and int(none["elb_5xx"]) == 5
    assert none["target_port"] == "NULL"
    assert sum(int(r["requests"]) for r in st) == 34
    assert {(r["target_ip"], r["target_port"]) for r in st} == {
        ("-", "NULL"), ("198.51.100.10", "8080"), ("198.51.100.11", "8080")}
    lat = run(env, "alb", "target_latency_pct")
    allrow = one(lat, target_ip="ALL")
    assert lat[0]["target_ip"] == "ALL"
    # 29 timed requests: 4 x 0.005, 0.01 .. 0.22, 3 x 0.9; the 5 without a target time are counted, not hidden
    assert (int(allrow["requests"]), int(allrow["timed_requests"]), int(allrow["no_target_time_requests"])) == (34, 29, 5)
    assert [allrow[k] for k in ("p50_s", "p90_s", "p95_s", "p99_s", "max_s")] == ["0.11", "0.356", "0.9", "0.9", "0.9"]
    dash = one(lat, target_ip="-")
    assert (int(dash["timed_requests"]), int(dash["no_target_time_requests"]), dash["p95_s"]) == (0, 5, "NULL")


def test_alb_paths_and_clients(env):
    paths_5xx = run(env, "alb", "top_paths_5xx")
    assert all("?" not in r["path"] and r["path"].startswith("/") for r in paths_5xx)
    r = one(paths_5xx, path="/api/orders", elb_status_code="502")
    assert int(r["requests"]) == 8 and int(r["no_target_response"]) == 5
    clients = run(env, "alb", "top_clients")
    assert [(c["client_ip"], int(c["requests"]), float(c["share"]), int(c["status_5xx"])) for c in clients] == [
        ("192.0.2.10", 9, pytest.approx(0.2647), 5), ("198.51.100.23", 8, pytest.approx(0.2353), 0),
        ("192.0.2.77", 7, pytest.approx(0.2059), 3), ("198.51.100.7", 4, pytest.approx(0.1176), 0),
        ("203.0.113.5", 3, pytest.approx(0.0882), 0), ("203.0.113.99", 3, pytest.approx(0.0882), 0)]


# ---- privacy and bounds on larger data ------------------------------------------------------

_RUN_SEQ = itertools.count(1)


def _wide_dataset(env, ds, select_sql, run_id=None):
    run_id = run_id or "w%d-prod-20261030-1200" % next(_RUN_SEQ)
    d = paths.state_root() / "data" / run_id / ds
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(str(d), 0o700)
    target = d / "part-000001.parquet"
    duck = shutil.which("duckdb")
    subprocess.run([duck, ":memory:", "-c", "COPY (%s) TO '%s' (FORMAT parquet)" % (select_sql, target)],
                   check=True, capture_output=True)
    os.chmod(str(target), 0o444)
    os.chmod(str(d), 0o555)
    return run_id


def test_client_lists_never_exceed_50_rows(env):
    cdn = ("SELECT '10.0.' || (i / 250)::VARCHAR || '.' || (i % 250)::VARCHAR AS c_ip, 1 AS sc_bytes FROM range(0, 400) t(i)")
    waf = ("SELECT '10.0.' || (i / 250)::VARCHAR || '.' || (i % 250)::VARCHAR AS client_ip, 'ALLOW' AS action, "
           "NULL::VARCHAR AS client_key FROM range(0, 400) t(i)")
    alb = ("SELECT '10.0.' || (i / 250)::VARCHAR || '.' || (i % 250)::VARCHAR AS client_ip, "
           "200 AS elb_status_code FROM range(0, 400) t(i)")
    for ds, sql, name in (("cdn1", cdn, "top_clients"), ("waf1", waf, "clients"), ("alb1", alb, "top_clients")):
        rid = _wide_dataset(env, ds, sql, run_id="wide-prod-20261030-1200")
        cp = sqlq(env, ds, "--run", rid, name)
        assert cp.returncode == 0, cp.stderr
        assert len(list(csv.reader(io.StringIO(cp.stdout)))) - 1 == 50, (ds, name)


# ---- query correctness on purpose-built data ------------------------------------------------

def _csv(cp):
    return list(csv.DictReader(io.StringIO(cp.stdout)))


def test_bytes_per_viewer_ranks_by_bytes_not_ratio_and_handles_206_only_and_no_clients(env):
    # 60 tiny popular objects (huge repeat factor, few bytes), one bandwidth burner (1 viewer, low ratio),
    # one object seen only through 206s, one with no client address at all.
    sql = ("SELECT '/tiny/' || (i % 60)::VARCHAR AS cs_uri_stem, '192.0.2.' || (i % 3)::VARCHAR AS c_ip, "
           "10::BIGINT AS sc_bytes, 200 AS sc_status, 10::BIGINT AS sc_content_len, NULL::BIGINT AS sc_range_end "
           "FROM range(0, 600) t(i) "
           "UNION ALL SELECT '/burner.bin', '198.51.100.7', 1000000, 200, 1000000, NULL FROM range(0, 5) "
           "UNION ALL SELECT '/ranged.bin', '203.0.113.5', 100, 206, 100, 99999 FROM range(0, 2) "
           "UNION ALL SELECT '/anon.bin', NULL, 50, 200, 50, NULL")
    rid = _wide_dataset(env, "cdn1", sql)
    cp = sqlq(env, "cdn1", "--run", rid, "bytes_per_viewer")
    assert cp.returncode == 0, cp.stderr
    rows = _csv(cp)
    assert len(rows) == 50 and rows[0]["cs_uri_stem"] == "/burner.bin"
    assert int(rows[0]["bytes"]) == 5000000 and float(rows[0]["repeat_factor"]) == pytest.approx(5.0)
    assert rows[0]["size_is_estimate"] == "false"
    # the 206-only object is not in the top 50 by bytes; check it with its own dataset below
    sql2 = ("SELECT '/ranged.bin' AS cs_uri_stem, '203.0.113.5' AS c_ip, 100::BIGINT AS sc_bytes, 206 AS sc_status, "
            "100::BIGINT AS sc_content_len, 99999::BIGINT AS sc_range_end FROM range(0, 2) "
            "UNION ALL SELECT '/anon.bin', NULL, 50, 200, 50, NULL")
    rid2 = _wide_dataset(env, "cdn1", sql2)
    rows2 = _csv(sqlq(env, "cdn1", "--run", rid2, "bytes_per_viewer"))
    rg = one(rows2, cs_uri_stem="/ranged.bin")
    assert rg["size_is_estimate"] == "true" and int(rg["object_size"]) == 100000
    anon = one(rows2, cs_uri_stem="/anon.bin")                        # no distinct clients: no division error
    assert anon["bytes_per_viewer"] == "NULL" and anon["repeat_factor"] == "NULL"


def test_aborted_follows_the_documented_definition_and_skips_head(env):
    base = ("SELECT '/o' AS cs_uri_stem, '192.0.2.1' AS c_ip, %s AS cs_method, %s AS sc_status, %d::BIGINT AS sc_bytes, "
            "%d::BIGINT AS sc_content_len, %s AS x_edge_result_type, %s AS x_edge_detailed_result_type")
    parts = [
        base % ("'GET'", 200, 1000, 1000, "'Hit'", "'Hit'"),                   # complete
        base % ("'GET'", 200, 1000, 5000, "'Hit'", "'Hit'"),                   # short body: aborted
        base % ("'GET'", 200, 5000, 5000, "'Error'", "'Error'"),               # documented: GET, 200, result Error
        base % ("'GET'", 200, 5000, 5000, "'Hit'", "'ClientCommError'"),       # client comm error
        base % ("'HEAD'", 200, 300, 5000, "'Hit'", "'Hit'"),                   # HEAD: headers only, not aborted
        base % ("'HEAD'", 200, 5000, 5000, "'Error'", "'Error'"),              # HEAD with Error is not the documented case
        base % ("'GET'", 206, 100, 5000, "'Hit'", "'Hit'"),                    # 206 partials are not covered
        base % ("'GET'", 404, 100, 5000, "'Error'", "'Error'"),                # not a 200
    ]
    rid = _wide_dataset(env, "cdn1", " UNION ALL ".join(parts))
    (r,) = _csv(sqlq(env, "cdn1", "--run", rid, "aborted"))
    assert (int(r["aborted_requests"]), int(r["requests"])) == (3, 8)


@pytest.mark.parametrize("kind,name,given,missing", [
    ("waf", "compare_days", {"b": DAY_B}, "a"),
    ("waf", "compare_days", {"a": DAY_A}, "b"),
    ("waf", "compare_days", {}, "a"),
    ("cloudfront", "object_by_day", {}, "object"),
    ("cloudfront", "by_object", {}, "object"),
])
def test_required_param_missing_is_an_error_not_an_empty_result(env, kind, name, given, missing):
    args = [DS[kind], "--run", RUN, name] + [x for k, v in given.items() for x in ("--param", "%s=%s" % (k, v))]
    cp = sqlq(env, *args)
    assert cp.returncode == 4 and cp.stdout == "", cp.stdout
    assert "param %s is required" % missing in cp.stderr
    # a misspelled name is the same as a missing one
    cp = sqlq(env, DS[kind], "--run", RUN, name, "--param", "objekt=/x", "--param", "aa=%s" % DAY_A)
    assert cp.returncode == 4 and "is required" in cp.stderr


def test_sampling_notes_are_per_query_not_blanket():
    for kind, name in ALL:
        first = (SQL_DIR / kind / (name + ".sql")).read_text().split("\n", 1)[0]
        assert "multiply counts by the factor sqlq prints" not in first, (kind, name)
        assert "If sampled:" in first or "UNRELIABLE if sampled" in first, (kind, name)
    bpv = (SQL_DIR / "cloudfront" / "bytes_per_viewer.sql").read_text().split("\n", 1)[0]
    assert "UNRELIABLE if sampled" in bpv and "do not use" in bpv
    for kind, name in ALL:
        first = (SQL_DIR / kind / (name + ".sql")).read_text().split("\n", 1)[0]
        if "share" in first.split("If sampled:")[-1] and name != "bytes_per_viewer":
            assert "do not scale" in first, (kind, name)
        if "distinct_" in first.split("If sampled:")[-1]:
            assert "lower bound" in first, (kind, name)


def test_purpose_lines_say_what_the_numbers_do_not_cover():
    def purpose(kind, name):
        return (SQL_DIR / kind / (name + ".sql")).read_text().split("\n", 1)[0]
    assert "top-level" in purpose("waf", "count_rules") and "rule_group_matches" in purpose("waf", "count_rules")
    lb = purpose("alb", "lb_vs_target_status")
    assert "timed out" in lb and "refused" in lb and "no_target_response" in lb
    ab = purpose("cloudfront", "aborted")
    assert "206" in ab and "HEAD" in ab
    assert "cache-statistics" in (SQL_DIR / "cloudfront" / "cache_results.sql").read_text()
