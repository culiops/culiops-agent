# World index — downstream-timeout-ceiling

The first matching row wins; `*` matches any text. A command that matches no row returns `_default.txt` (`{}` for a JSON API, no lines for a text command): no data, never an error.

Prometheus and Tempo rows match on the query text, whether it is sent with `curl` to `$PROM_URL` / `$TEMPO_URL` or through a Grafana MCP tool. Prometheus range files cover 2026-10-23 08:50–10:20 UTC at a 60 s step; instant files are evaluated at 10:20 UTC over a 30-minute rate window.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | Per-org facts. |
| `ls * .culiops/sre-investigate*` | `_default.txt` | Only `environment.md` exists. |
| `command -v agentbox-env` | `_default.txt` | No output, exit status 1 (not installed). |
| `aws sts get-caller-identity --profile prod-read*` | `sts-prod-read.json` | |
| `aws iam get-role --profile prod-read *` | `iam-get-role.json` | |
| `aws iam simulate-principal-policy --profile prod-read *` | `iam-simulate-readonly.json` | Every write action `implicitDeny`. |
| `kubectl config current-context*` | `kubectl-current-context.txt` | |
| `kubectl auth whoami*` | `kubectl-auth-whoami.txt` | |
| `kubectl auth can-i --list*` | `kubectl-can-i-list.txt` | Read verbs only (plus the self-review `create` every user has). |
| `GET $PROM_URL/api/v1/alerts*` | `prom-alerts.json` | Firing alert, active since 09:32 UTC. |
| `PromQL *histogram_quantile(0.95*route*offset 7d*` | `prom-p95-by-route-7d.json` | p95 by route, one week earlier. |
| `PromQL *histogram_quantile(0.95*route*` | `prom-p95-by-route.json` | p95 by route, now. |
| `PromQL *histogram_quantile(0.5*offset 7d*` | `prom-p50-7d.json` | |
| `PromQL *histogram_quantile(0.95*offset 7d*` | `prom-p95-7d.json` | |
| `PromQL *histogram_quantile(0.99*offset 7d*` | `prom-p99-7d.json` | |
| `PromQL *histogram_quantile(0.5*` | `prom-p50.json` | Also matches `0.50`. |
| `PromQL *histogram_quantile(0.95*` | `prom-p95.json` | |
| `PromQL *histogram_quantile(0.99*` | `prom-p99.json` | |
| `PromQL *_count*route*` | `prom-rps-by-route.json` | Request rate by route. |
| `PromQL *_count*status*5*` | `prom-5xx-ratio.json` | Any 5xx rate or 5xx ratio for catalog-api. |
| `PromQL *_count*` | `prom-rps.json` | Total request rate. |
| `TraceQL metrics *catalog-api*kind = client*by(span.server.address)* (window before 2026-10-23)` | `tempo-downstream-p95-baseline.json` | Slow-downstream aggregation, one week earlier. |
| `TraceQL metrics *catalog-api*by(span.server.address)*` | `tempo-downstream-p95.json` | Client-span p95 by downstream address, 09:00–10:20 UTC, 5-minute step. Also matches `quantile_over_time` without `kind = client`. |
| `TraceQL search *catalog-api*` | `tempo-search-slow.json` | 5 slow `GET /products/{id}` traces. |
| `kubectl get pods -n catalog*` | `kubectl-get-pods.txt` | |
| `kubectl get events -n catalog*` | `kubectl-get-events.txt` | |
| `kubectl get hpa -n catalog*` | `kubectl-get-hpa.txt` | |
| `kubectl top pods -n catalog*` | `kubectl-top-pods.txt` | |
| `kubectl rollout history * catalog-api*` | `kubectl-rollout-history.txt` | |
| `kubectl get rs -n catalog*` | `kubectl-get-rs.txt` | Also `get replicasets`. |
| `helm history catalog-api*` | `helm-history.txt` | |
| `aws logs describe-log-groups --profile prod-read*` | `logs-describe-log-groups.json` | `storedBytes` 1,693,440,000,000 over 14 days of retention. |
| `aws logs start-query --profile prod-read * /eks/prod/catalog-api*` | `li-start-catalog.json` | Any query on the catalog-api group. |
| `aws logs get-query-results --profile prod-read * 5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9*` | `li-results-catalog.json` | Message counts for 10:05–10:20 UTC. |
| `aws logs stop-query *` | `_default.txt` | |
