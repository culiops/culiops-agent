# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.
8. Plugin commands: `…/analytics/bin/<name>` stands for the plugin's `skills/sre-investigate/analytics/bin/<name>`, called by any path (relative or absolute). Each row gives the combined stdout and stderr of the command and its exit status.

## Rows

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `command -v s5cmd` | `tool-01.txt` | The tools are installed on this host. |
| `command -v duckdb` | `tool-02.txt` | |
| `s5cmd version` | `ver-01.txt` | |
| `duckdb --version` | `ver-02.txt` | |
| `…/analytics/bin/logs-status` | `mod-01.txt` | Exit status 0. |
| `…/analytics/bin/logs-inventory` …, `…/analytics/bin/logs-fetch` …, `…/analytics/bin/sqlq` … (any arguments) | `mod-02.txt` | Exit status 2. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws cloudfront list-distributions` | `cf-01.json` | |
| `aws cloudfront get-distribution` … `E3EXAMPLEDIST` | `cf-02.json` | `get-distribution-config` returns the `DistributionConfig` object of this file, with the `ETag`, and without the wrapper fields. |
| `aws cloudfront get-monitoring-subscription` … `E3EXAMPLEDIST` | `cf-03.json` | |
| `aws cloudwatch list-metrics` … `AWS/CloudFront` | `cw-01.json` | |
| `aws cloudwatch describe-alarms` … | `cw-02.json` | No alarm exists for this distribution. |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `AWS/CloudFront` … | table P1 | Region `us-east-1`, dimensions `DistributionId=E3EXAMPLEDIST`, `Region=Global`. |
| `aws cloudtrail lookup-events` … | `ct-01.json` | Management events for the distribution. Return only events matching the lookup attributes and window; an attribute or window with no event returns `{"Events": []}`. |
| `aws s3api list-objects-v2` … `--bucket example-edge-logs` … `--prefix cf/static/…` | `s3-01.json` | Listing only. Return only the keys whose name starts with the prefix. |
| `aws s3 ls` … `s3://example-edge-logs/cf/static/…` | `s3-02.txt` | Same listing, text form. |
| `aws s3 cp`, `aws s3 sync`, `aws s3api get-object`, `s5cmd` … (anything that reads an object) | `_default.txt` | Object contents are not modelled. |

**P1 — `get-metric-data` / `get-metric-statistics` on `AWS/CloudFront`**

Statistic: `Sum` for `Requests` and `BytesDownloaded`, `Average` for the rest. Rates are percent. `OriginLatency` is milliseconds. A period of 60 to 3599 returns the 60-second file points inside the window; a period of 3600 or more returns the 3600-second file where one exists, otherwise combine the 60-second points (sum for `Sum`, request-weighted mean for `Average`). A request with several queries returns one `MetricDataResults` entry per query.

| Metric | Period | File | Covers |
|---|---|---|---|
| `Requests` | 60 to 3599 | `cw-11.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `Requests` | 3600 or more | `cw-12.json` | 2026-04-04 11:00 – 2026-04-12 11:20 UTC |
| `5xxErrorRate` | 60 to 3599 | `cw-13.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `5xxErrorRate` | 3600 or more | `cw-14.json` | 2026-04-04 11:00 – 2026-04-12 11:20 UTC |
| `4xxErrorRate` | 60 to 3599 | `cw-15.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `TotalErrorRate` | 60 to 3599 | `cw-16.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `502ErrorRate` | 60 to 3599 | `cw-17.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `503ErrorRate` | 60 to 3599 | `cw-18.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `504ErrorRate` | 60 to 3599 | `cw-19.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `504ErrorRate` | 3600 or more | `cw-20.json` | 2026-04-04 11:00 – 2026-04-12 11:20 UTC |
| `OriginLatency` | 60 to 3599 | `cw-21.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `OriginLatency` | 3600 or more | `cw-22.json` | 2026-04-04 11:00 – 2026-04-12 11:20 UTC |
| `CacheHitRate` | 60 to 3599 | `cw-23.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| `BytesDownloaded` | 60 to 3599 | `cw-24.json` | 2026-04-11 11:20 – 2026-04-12 11:20 UTC |
| any other CloudFront metric (`OriginLatency` at p-statistics, `401ErrorRate`, …) or a window outside the covered one | `_default.txt` | |

Statistics blocks, where a file has them, describe the whole covered window.
