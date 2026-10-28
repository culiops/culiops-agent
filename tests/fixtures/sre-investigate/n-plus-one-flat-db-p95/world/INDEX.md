# World index — n-plus-one-flat-db-p95

The first matching row wins; `*` matches any text. A command that matches no row returns `_default.txt` (`{}` for a JSON API, no lines for a text command): no data, never an error.

Prometheus, Loki and Tempo rows match on the query text, whether it is sent through the Grafana datasource proxy (`curl` with the token) or a Grafana MCP tool. "Baseline" means a window that ends at or before 2026-10-20 13:00 UTC, or the same query with `offset`. Prometheus range files cover 10:00–15:30 UTC at a 120 s step.

The output root `.culiops/sre-investigate/` maps to files in this directory: `environment.md` and `incidents/`. There is no `profiles/` and no `lessons.md`.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls * .culiops/sre-investigate/incidents*` | `ls-incidents.txt` | |
| `ls * .culiops/sre-investigate*` | `ls-output-root.txt` | |
| `grep * .culiops/sre-investigate/incidents*` | `incidents-grep.txt` | Any grep of the incident front matter for orders-api, orders-db or latency terms. |
| `cat .culiops/sre-investigate/incidents/2026-08-14-orders-api.md` | `incidents/2026-08-14-orders-api.md` | |
| `cat .culiops/sre-investigate/incidents/2026-09-30-catalog-api.md` | `incidents/2026-09-30-catalog-api.md` | |
| `command -v agentbox-env` | `_default.txt` | No output, exit status 1 (not installed). |
| `*${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}*` | `env-token-present.txt` | The token is set. |
| `aws sts get-caller-identity --profile prod-read*` | `sts-prod-read.json` | |
| `aws iam get-role --profile prod-read *` | `iam-get-role.json` | |
| `aws iam simulate-principal-policy --profile prod-read *` | `iam-simulate-readonly.json` | Every write action `implicitDeny`. |
| `kubectl config current-context*` | `kubectl-current-context.txt` | |
| `kubectl auth whoami*` | `kubectl-auth-whoami.txt` | |
| `kubectl auth can-i --list*` | `kubectl-can-i-list.txt` | Read verbs only. |
| `PromQL *histogram_quantile(0.95*by (*route* (baseline)` | `prom-p95-by-route-baseline.json` | p95 by method and route at 12:30 UTC. |
| `PromQL *histogram_quantile(0.95*by (*route*` | `prom-p95-by-route.json` | p95 by method and route at 15:30 UTC. |
| `PromQL *histogram_quantile(0.95*orders-api*/orders*` | `prom-orders-p95-range.json` | `GET /orders` p95 over time. |
| `PromQL *histogram_quantile(0.5*orders-api*/orders*` | `prom-orders-p50-range.json` | `GET /orders` p50 over time. |
| `PromQL *db_client_operation_duration_seconds_count*` | `prom-db-op-rate.json` | DB operations per second issued by orders-api. |
| `PromQL *db_client_connections*` | `prom-db-pool.json` | Pool `used` and `pending_requests`. |
| `PromQL *container_cpu_usage_seconds_total*orders*` | `prom-pod-cpu.json` | Per-pod CPU since 13:08 UTC. |
| `PromQL *http_server_request_duration_seconds_count*` | `prom-rps.json` | `GET /orders` request rate. |
| `TraceQL metrics *span.db.system*` | `tempo-db-span-p95.json` | DB client-span p95, 10:00–15:30 UTC, 15-minute step. |
| `TraceQL search *orders-api*/orders* >> * (baseline)` | `tempo-spancount-baseline.json` | 24 `GET /orders` traces, 11:00–12:00 UTC; `matched` = client spans in the trace. |
| `TraceQL search *orders-api*/orders* >> *` | `tempo-spancount-incident.json` | 24 `GET /orders` traces, 14:30–15:30 UTC; `matched` = client spans in the trace. |
| `LogQL *app="orders-api"*` | `loki-empty.json` | Also `service_name="orders-api"`: no streams. |
| `GET */loki/api/v1/labels*` | `_default.txt` | |
| `GET */loki/api/v1/label/app/values*` | `loki-label-app-values.json` | Also `logcli labels app`. |
| `LogQL *app="orders"*` | `loki-orders-lines.json` | 8 request lines, 15:18–15:24 UTC. |
| `aws cloudwatch get-metric-data --profile prod-read *` | `cw-rds-orders-db.json` | `orders-db` CPUUtilization, ReadLatency, DatabaseConnections, period 300, 10:00–15:30 UTC. |
| `kubectl rollout history * orders-api*` | `kubectl-rollout-history.txt` | |
| `kubectl get rs -n orders*` | `kubectl-get-rs.txt` | Also `get replicasets`. |
| `kubectl get pods -n orders*` | `kubectl-get-pods.txt` | |
| `kubectl get events -n orders*` | `kubectl-get-events.txt` | Events older than one hour have expired. |
| `helm history orders-api*` | `helm-history.txt` | |
| `git -C ~/src/orders-api log * v2.14.0..v2.15.0*` | `git-log.txt` | |
| `git -C ~/src/orders-api diff v2.14.0* v2.15.0*` | `git-diff.txt` | |
| `git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py` | `../repo/orders_api/handlers/list_orders.py` | |
| `git -C ~/src/orders-api show v2.15.0:orders_api/repository.py` | `../repo/orders_api/repository.py` | |
| `gh api repos/example-org/orders-api/compare/v2.14.0...v2.15.0*` | `gh-compare.json` | Same change set as `git-diff.txt`. |
