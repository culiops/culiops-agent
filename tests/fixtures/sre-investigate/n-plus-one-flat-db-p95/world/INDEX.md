# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.

Prometheus, Loki and Tempo calls go through the Grafana datasource proxy or a Grafana MCP tool; both match the same rows. Prometheus range files cover 2026-10-20 10:00–15:30 UTC at a 120 s step (`offset 7d` rows: the same clock window on 2026-10-13). The output root `.culiops/sre-investigate/` maps to `environment.md` and `incidents/` in this directory; `grep` over it reads those files.

## Rows

`<…>` in a pattern is a parameter: the value comes from an earlier output, and the row's table (below the main table) gives the file for each value.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate/incidents` | `ls-02.txt` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `cat .culiops/sre-investigate/incidents/<file>` | `incidents/<file>` | |
| `grep` … `.culiops/sre-investigate/incidents` | (apply the grep to the files in `incidents/`) | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `echo` … `${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}` | `env-01.txt` | |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `kubectl config current-context` | `k8s-01.txt` | |
| `kubectl auth whoami` | `k8s-02.txt` | |
| `kubectl auth can-i --list` … | `k8s-03.txt` | |
| `kubectl get pods` … `orders` | `k8s-04.txt` | |
| `kubectl get events` … `orders` | `k8s-05.txt` | |
| `kubectl get rs` … `orders` | `k8s-06.txt` | |
| `kubectl rollout history` … `orders-api` | `k8s-07.txt` | |
| `helm history orders-api` … | `helm-01.txt` | |
| `GET …/api/v1/label/__name__/values` (Prometheus) | `prom-09.json` | |
| PromQL `histogram_quantile(0.95, …http_server_request_duration_seconds_bucket{service="orders-api"…} … by (le, method, route))` (or `by (le, route)`), evaluated at or after 13:10 UTC | `prom-03.json` | Instant vector at 15:30 UTC. |
| same, evaluated before 13:00 UTC on 2026-10-20 | `prom-04.json` | Instant vector at 12:30 UTC. |
| same, `offset 7d` | `prom-14.json` | Instant vector at 2026-10-13 15:30 UTC. |
| PromQL `histogram_quantile(0.95, …{service="orders-api", route="/orders"…})`, `offset 7d` | `prom-11.json` | Range. |
| PromQL `histogram_quantile(0.5, …{service="orders-api", route="/orders"…})`, `offset 7d` | `prom-12.json` | Range. |
| PromQL `histogram_quantile(0.95, …{service="orders-api", route="/orders"…})` | `prom-01.json` | Range. Also matches `GET` method filters. |
| PromQL `histogram_quantile(0.5, …{service="orders-api", route="/orders"…})` | `prom-02.json` | Range. |
| PromQL `rate` of `db_client_operation_duration_seconds_count{service="orders-api"…}`, `offset 7d` | `prom-13.json` | Range. |
| PromQL `rate` of `db_client_operation_duration_seconds_count{service="orders-api"…}` | `prom-05.json` | Range, operations per second. |
| PromQL `db_client_connections_usage` or `db_client_connections_pending_requests` for orders-api | `prom-06.json` | Range, both series. |
| PromQL `rate` of `container_cpu_usage_seconds_total{namespace="orders"…}` | `prom-08.json` | Range, 13:08–15:30 UTC, 600 s step. |
| PromQL `rate` of `http_server_request_duration_seconds_count{service="orders-api"…}` | `prom-07.json` | Range. |
| PromQL anything else | `prom-10.json` | |
| `GET …/api/v2/search/tags` (or `/api/search/tags`) (Tempo) | `tempo-06.json` | |
| TraceQL metrics `quantile_over_time(duration, …)` over orders-api spans with `span.db.system` set | `tempo-01.json` | 10:00–15:30 UTC, 900 s step. |
| TraceQL metrics anything else | `tempo-08.json` | |
| TraceQL search with a structural operator (`>>`, `>`, `~`) from orders-api `GET /orders` server spans to their child or descendant spans, window overlapping 14:30–15:30 UTC | `tempo-02.json` | 24 traces; `matched` is the number of matching descendant spans in each trace. |
| same, window overlapping 11:00–12:00 UTC | `tempo-03.json` | 24 traces, same meaning of `matched`. |
| TraceQL search for orders-api `GET /orders` spans, no structural operator, window overlapping 14:30–15:30 UTC | `tempo-04.json` | 24 traces. |
| same, window overlapping 11:00–12:00 UTC | `tempo-05.json` | 24 traces. |
| TraceQL search anything else, or another window | `tempo-07.json` | |
| `GET …/api/traces/<trace ID from a search result>` (or `/api/v2/traces/…`) | table P1 | |
| `GET …/loki/api/v1/labels` | `loki-01.json` | |
| `GET …/loki/api/v1/label/app/values` | `loki-02.json` | Also `logcli labels app`. |
| `GET …/loki/api/v1/label/namespace/values` | `loki-03.json` | |
| `GET …/loki/api/v1/label/container/values` | `loki-04.json` | |
| LogQL `{<label>="<value>"}` (any further matchers or line filters) for a label from `loki-01.json` and a value from that label's values file | table P2 | A regex matcher (`=~`) selects every listed value it matches (union of their streams); several matchers keep only the streams that satisfy all of them. |
| LogQL anything else (including values not in the label-values files) | `loki-07.json` | |
| `aws rds describe-db-instances` … | `rds-01.json` | |
| `aws cloudwatch get-metric-data` … `AWS/RDS` … `orders-db` | `cw-01.json` | CPUUtilization, ReadLatency, DatabaseConnections; period 300; 10:00–15:30 UTC. Other RDS metrics: no data. |
| `git -C ~/src/orders-api tag` … | `git-03.txt` | |
| `git -C ~/src/orders-api log` … `v2.14.0..v2.15.0` | `git-01.txt` | |
| `git -C ~/src/orders-api diff v2.14.0 v2.15.0` … (or `v2.14.0..v2.15.0`) | `git-02.txt` | Path filters return the matching file sections. |
| `git -C ~/src/orders-api show v2.15.0:<path>` | `../repo/<path>` | For the paths under `repo/`. |
| `gh api repos/example-org/orders-api/compare/v2.14.0...v2.15.0` … | `gh-01.json` | |

**P1 — trace by ID**

| Trace ID | File |
|---|---|
| `e3ea7a3906419b466a28541306cc5ee1` | `tempo-09.json` |
| `65345f5f8176033524bc88af3bd43f6f` | `tempo-10.json` |
| any other ID from a search result | `_default.txt` (not retained) |

**P2 — LogQL stream selectors**

| Label | Value | File |
|---|---|---|
| `app` | `catalog-api` | `loki-08.json` |
| `app` | `notify-worker` | `loki-09.json` |
| `app` | `orders` | `loki-05.json` |
| `app` | `orders-reconcile` | `loki-10.json` |
| `app` | `payments-worker` | `loki-11.json` |
| `namespace` | `catalog` | `loki-08.json` |
| `namespace` | `notify` | `loki-09.json` |
| `namespace` | `orders` | `loki-06.json` |
| `namespace` | `payments` | `loki-11.json` |
| `container` | `api` | `loki-12.json` |
| `container` | `worker` | `loki-13.json` |
