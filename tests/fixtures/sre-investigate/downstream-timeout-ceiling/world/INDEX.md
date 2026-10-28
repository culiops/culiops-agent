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
| `aws logs start-query` … `/eks/prod/catalog-api`, window overlapping 10:05–10:20 UTC | `logs-02.json` | Any query (counts by message or raw lines). |
| `aws logs start-query` … | `logs-03.json` | Any other query or window. |
| `aws logs get-query-results` … `5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` | `logs-12.json` | Message counts. Covers 10:05–10:20 UTC; for another window, counts scale with the minutes after 09:31 inside it (about 1,730 timeout lines per minute, none before 09:31). |
| `aws logs get-query-results` … `0b1c2d3e-4f50-4617-8283-94a5b6c7d8e9` | `logs-13.json` | |
| `aws logs stop-query` … | `_default.txt` | |
