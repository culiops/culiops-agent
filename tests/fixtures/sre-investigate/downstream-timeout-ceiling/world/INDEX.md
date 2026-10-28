# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.

Prometheus range files cover 2026-10-23 04:20–10:20 UTC (or the same clock times one week earlier for `offset 7d`) at a 60 s step; instant files are evaluated at 10:20 UTC (or 7 days earlier) over a 30-minute rate window. Tempo metrics files cover the same windows at a 300 s step.

## Rows

`<…>` in a pattern is a parameter: the value comes from an earlier output, and the row's table (below the main table) gives the file for each value.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `kubectl config current-context` | `k8s-01.txt` | |
| `kubectl auth whoami` | `k8s-02.txt` | |
| `kubectl auth can-i --list` … | `k8s-03.txt` | |
| `kubectl get pods` … `catalog` | `k8s-04.txt` | |
| `kubectl get events` … `catalog` | `k8s-05.txt` | Ages are relative to 10:20 UTC. |
| `kubectl get hpa` … `catalog` | `k8s-06.txt` | |
| `kubectl top pods` … `catalog` | `k8s-07.txt` | |
| `kubectl rollout history` … `catalog-api` | `k8s-08.txt` | |
| `kubectl get rs` … `catalog` | `k8s-09.txt` | |
| `helm history catalog-api` … | `helm-01.txt` | |
| `helm list` … | `_empty.txt` | |
| `GET $PROM_URL/api/v1/alerts` | `prom-12.json` | |
| `GET $PROM_URL/api/v1/label/__name__/values` | `prom-13.json` | |
| PromQL `histogram_quantile(0.95, …http_server_request_duration_seconds_bucket{service="catalog-api"…} … by (le, route))`, `offset 7d` | `prom-10.json` | Instant vector by route. |
| PromQL same, no offset | `prom-09.json` | Instant vector by route. |
| PromQL `histogram_quantile(0.5, …http_server_request_duration_seconds_bucket{service="catalog-api"…})`, `offset 7d` | `prom-04.json` | Range. |
| PromQL `histogram_quantile(0.95, …)` same selector, `offset 7d` | `prom-05.json` | Range. |
| PromQL `histogram_quantile(0.99, …)` same selector, `offset 7d` | `prom-06.json` | Range. |
| PromQL `histogram_quantile(0.5, …)` same selector | `prom-01.json` | Range. |
| PromQL `histogram_quantile(0.95, …)` same selector | `prom-02.json` | Range. |
| PromQL `histogram_quantile(0.99, …)` same selector | `prom-03.json` | Range. |
| PromQL `rate`/`increase` of `http_server_request_duration_seconds_count{service="catalog-api"…}` by `route` | `prom-11.json` | Instant vector, requests per second by route. |
| PromQL ratio or rate of `…_count{service="catalog-api", status=~"5.."…}` | `prom-08.json` | Range, 5xx share of requests. |
| PromQL `rate` of `http_server_request_duration_seconds_count{service="catalog-api"…}` | `prom-07.json` | Range, requests per second. |
| PromQL anything else | `prom-14.json` | |
| `GET $TEMPO_URL/api/v2/search/tags` (or `/api/search/tags`) | `tempo-04.json` | |
| TraceQL metrics `quantile_over_time(duration, …)` over catalog-api client spans `by (span.server.address)`, window one week earlier | `tempo-02.json` | |
| TraceQL metrics `quantile_over_time(duration, …)` over catalog-api client spans `by (span.server.address)` | `tempo-01.json` | Also matches the same query without `kind = client`. |
| TraceQL metrics anything else | `tempo-06.json` | |
| TraceQL search over catalog-api spans, window overlapping 10:00–10:20 UTC, with a `duration >` filter of 1 s or more, or `status = error` | `tempo-03.json` | 5 traces. |
| TraceQL search anything else | `tempo-05.json` | |
| `aws logs describe-log-groups` … | `logs-01.json` | |
| `aws logs start-query` … `<log group from logs-01.json>` … `<query>` | table P1 | |
| `aws logs get-query-results` … `<queryId>` | table P2 | |
| `aws logs stop-query` … | `_default.txt` | |

**P1 — `start-query`**

| Log group | Query | Window | File (queryId) |
|---|---|---|---|
| `/eks/prod/catalog-api` | `stats count(*)` by message, no time bin | 10:05–10:20 UTC (last 15 min) | `logs-02.json` |
| `/eks/prod/catalog-api` | `stats count(*)` by message, no time bin | 09:50–10:20 UTC (last 30 min) | `logs-05.json` |
| `/eks/prod/catalog-api` | `stats count(*)` by message, no time bin | 09:20–10:20 UTC (last 60 min) | `logs-04.json` |
| `/eks/prod/catalog-api` | `stats count(*)` by message, with a time bin; or no bin and any other window overlapping 09:00–10:20 UTC | — | `logs-06.json` |
| `/eks/prod/catalog-api` | no `stats` (fields, filter, sort, limit) | overlapping 10:05–10:20 UTC | `logs-07.json` |
| any | anything else | — | `logs-03.json` |

**P2 — `get-query-results`**

| queryId | File | Shape |
|---|---|---|
| `5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` | `logs-12.json` | Totals per message, 10:05–10:20 UTC. |
| `d5e6f7a8-192a-4b3c-8d4e-5f6a7b8c9d0e` | `logs-16.json` | Totals per message, 09:50–10:20 UTC. |
| `c4d5e6f7-0819-4a2b-9c3d-4e5f6a7b8c9d` | `logs-15.json` | Totals per message, 09:20–10:20 UTC. |
| `e6f7a8b9-2a3b-4c4d-9e5f-6a7b8c9d0e1f` | `logs-14.json` | Rows per minute and message, 09:00–10:20 UTC. For a query without a time bin, sum the rows inside its window. |
| `f7a8b9c0-3b4c-4d5e-8f60-7a8b9c0d1e2f` | `logs-17.json` | Up to 10 lines, 10:05–10:20 UTC. |
| `0b1c2d3e-4f50-4617-8283-94a5b6c7d8e9` | `logs-13.json` | |
