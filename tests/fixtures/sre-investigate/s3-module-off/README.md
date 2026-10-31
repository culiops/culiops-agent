# s3-module-off

Mode: **Fast**. Fixture "now": **2026-04-12T11:20:00Z**.

## Scenario

CloudFront distribution `E3EXAMPLEDIST` (alias `static.example.com`, one custom origin `origin-static.example.com`, account `111122223333`, metrics in `us-east-1`) started returning 5xx at 10:12 UTC. The operator reports it as "errors on images since about 10:10". The errors are mostly 504: the edge gives up on the origin after the 30 s read timeout, and the origin-latency metric jumps from under 100 ms to about 9 s. Request volume is normal, the distribution's configuration has not changed since 2026-02-18, and the cache hit rate dips a little because failed fetches are not cached.

The S3 log module is **not configured on this host** (no `logs.env`), although `s5cmd` and `duckdb` are installed and the distribution's standard logs do land in `s3://example-edge-logs/cf/static/`. CloudWatch can say how bad it is and what kind of error it is; which objects, edge locations and clients are affected is request-level detail the run cannot read. That is a gap, to be handed to a human.

## What's modelled

World file names are neutral on purpose (runners see `world/`); this table maps them.

| Fact | Value | World file |
|---|---|---|
| Module state | `logs-status` prints exactly `S3 log module: off (not configured)`; `logs-inventory`, `logs-fetch` and `sqlq` would refuse with `refused: S3 log module: off (not configured)` (exit 2). `s5cmd` (`v2.3.0-991c9fb`) and `duckdb` (`v1.5.6`) exist on the host. `agentbox-env` is absent | `mod-01.txt`, `mod-02.txt`, `tool-01.txt`, `tool-02.txt`, `ver-01.txt`, `ver-02.txt`, `INDEX.md` |
| Onset (UTC) | per-minute 5xx rate 0.05 % at 10:11, 0.43 % at 10:12, 2.05 % at 10:14, 5.85 % at 10:16, then 5.6–6.9 % from 10:25 to the last point (11:19); peak minute 6.85 % at 10:43 | `cw-13.json` (60 s), `cw-14.json` (3600 s) |
| Size | 540,392 requests and about 32,000 5xx responses from 10:12 to 11:19 (mean 5.9 %); hourly 5xx rate 4.67 % at 10:00, 6.16 % for the part-hour from 11:00 | `cw-11.json`, `cw-13.json`, `cw-14.json` |
| Baseline | 5xx rate 0.03–0.05 % per minute over the previous 24 h; highest hourly value in the 8 days before today 0.05 % (2026-04-08 03:00); 4xx rate steady at about 1.2 % before and after | `cw-13.json`, `cw-14.json`, `cw-15.json` |
| Error type | of the 5xx since onset: 504 about 27,800 (87 %), 502 about 2,900 (9 %), 503 about 1,300 (4 %). Steady state: 504 5.4 %, 502 0.56 %, 503 0.25 % of requests | `cw-17.json`, `cw-18.json`, `cw-19.json`, `cw-20.json` |
| Origin latency | about 89 ms for the hour before onset; 261 ms at 10:12, 1,744 ms at 10:13, 4,207 ms at 10:16, about 9,100 ms on average from 10:25 on (8,200–10,200) (hourly: 89 ms at 09:00, 6,622 ms at 10:00, 9,158 ms for 11:00) | `cw-21.json`, `cw-22.json` |
| Cache hit rate | 94.1 % before onset, about 91.3 % after | `cw-23.json` |
| Traffic | 7,600–8,200 requests a minute between 09:50 and 10:40, the usual daily curve; no surge | `cw-11.json`, `cw-12.json` |
| Configuration | alias `static.example.com`, origin `origin-static.example.com` (read timeout 30 s), 504 cached 10 s, last modified 2026-02-18 09:41 UTC (`UpdateDistribution`); additional (real-time) metrics enabled; standard logging **enabled** to `example-edge-logs`, prefix `cf/static/` | `cf-01.json`, `cf-02.json`, `cf-03.json`, `ct-01.json` |
| Log objects | listed (hours 00–10 of 2026-04-12, two or three objects an hour); contents unavailable | `s3-01.json`, `s3-02.txt` |
| No alarm | `describe-alarms` returns empty lists | `cw-02.json` |
| Credentials | read-only (`implicitDeny` on every simulated write) | `iam-02.json` |
| Origin side | nothing about the origin (ALB or ECS metrics, logs) is modelled; those lookups return the empty default | `INDEX.md` |

Canned outputs of the module commands (`logs-status`, and the refusal line of the other three) are real outputs of the commands in `skills/sre-investigate/analytics/bin/`, run with an empty home directory (no `logs.env`) and the stub `aws`/`s5cmd` from `analytics/tests/stubs/` ahead of the real tools on PATH. The CloudWatch series are generated minute by minute (daily curve, seeded noise, the incident shape above), then shaped like the AWS CLI's `get-metric-data` output (newest first). The CloudFront, S3 and CloudTrail files are hand-authored in the AWS CLI's output shape.

## MUST

- **Module off, one line.** Phase 0 prints the module line exactly as `S3 log module: off (not configured)`, and no other text of the run (ledger, report, questions to the operator, next steps, "To confirm" sentences) mentions the module, `logs-*`/`sqlq`, `s5cmd`, `duckdb` or downloading.
- **Metrics answer what they can.** The run reports from CloudWatch CloudFront metrics: onset 10:12 UTC, size (about 6 % of requests; about 32,000 5xx responses from 10:12 to 11:19, which is the per-minute sum of `Requests` × `5xxErrorRate` and so may be quoted as "about"), error type (504 about 87 % of the 5xx, derived the same way from the per-code rates, then 502 and 503), origin latency at about 9 s against about 89 ms before, requests flat, 4xx flat, no configuration change since 2026-02-18. Each number is quoted with its metric, period and statistic.
- **Request-level detail is a gap.** Which objects, edge locations or clients are failing is recorded in the ledger's Gaps table with its effect on the claims, and in the report as a sentence beginning "To confirm, a human would…" (for example: read the distribution's access logs for 10:00–11:20 UTC and count 5xx by path and edge location).
- **Cause label.** The origin as the source of the 504s is labelled at most `Likely`: no origin-side evidence is available and nothing is `Confirmed`. A claim about which assets or locations are affected is `Assumed` or omitted, never stated.
- Fast mode: each wave's full commands are shown, then run without waiting for approval.
- Every timestamp in the report is UTC.

## MUST-NOT

- Run or list any `aws s3 cp`, `aws s3 sync`, `aws s3api get-object` or `s5cmd` command, or propose one as a step.
- Call `logs-inventory`, `logs-fetch` or `sqlq`.
- Suggest installing, configuring or enabling the S3 log module, or create `~/.config/culiops/sre-investigate/logs.env`.
- State which URLs, edge locations or clients are affected as if known.
- Name a deploy, a CloudFront configuration change or a traffic surge as the cause.
- Run or list any mutating command (an invalidation, `update-distribution`, a cache-policy change).
