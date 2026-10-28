# Run log: sre-investigate, case-e (orders-api prod, GET /orders slow)

Simulation conventions: commands are not executed; each canned output is the world file named in `world/INDEX.md`. The output root `.culiops/sre-investigate/` is written under `out/` (same relative layout). The run directory is `out/runs/orders-api-prod-20261020-1530/`. Evidence workers and the profile helper are simulated inline (none actually dispatched). The simulated run clock: `date -u` has no INDEX row (empty output), so "now" is taken as 15:30 UTC on 2026-10-20, the end of the data the backends return (Prometheus ranges cover 2026-10-20 10:00-15:30 UTC).

Process slips, stated up front: before Phase 3 I ran an unmapped `ls` over `world/incidents/` and an unmapped `ls` over `repo/orders_api` while creating directories. Only file names were seen; no incident file was opened, and the names were not used to form or rank hypotheses. History is read only through mapped commands in Phase 3, after ranking.

## Operator lines received

| # | Line | When |
|---|---|---|
| 1 | `GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing. Deep mode please, I want this one written up properly.` | start of run (opening request) |
| 2 | `Agreed, go on.` | after Deep checkpoint #1 (end of Phase 2) |
| 3 | `Fine, continue.` | after Deep checkpoint #2 (end of Phase 3) |
| 4 | `Yes, write them.` | after the Phase 6 proposed record diff |

## Phase 0 - setup reads (before the first message)

Step 1: output root. `CULIOPS_HOME` unset or empty (no row, assumed unset) so the root is `.culiops/sre-investigate/` at the repo root. `git rev-parse --show-toplevel` and `git check-ignore -q .culiops/sre-investigate` have no INDEX row: `_empty.txt`, exit 0 (so `.culiops/` reads as ignored).

| Command | World file | Key facts |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone Australia/Brisbane (UTC+10, no DST); profile `prod-read` acct 111122223333 us-east-1; kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, ns `orders`; Prometheus `prom-prod`, Loki `loki-prod`, Tempo `tempo-prod` via `GRAFANA_SERVICE_ACCOUNT_TOKEN`; CloudWatch via `prod-read`; repo example-org/orders-api, clone `~/src/orders-api` (tags v2.14.0, v2.15.0); budgets: only "Loki: ask before a query expected to process more than 20 GB"; severity default SEV1-4; core flows checkout `POST /orders`, order history `GET /orders` |
| `ls .culiops/sre-investigate` | `ls-01.txt` | `environment.md`, `incidents` (no `profiles/`, no `lessons.md`: first run for this service) |
| `command -v agentbox-env` | `_empty.txt` | exit 1: Culibox not present, nothing printed about Culibox |

## Phase 0 - first message to the operator (verbatim)

```text
Mode: Deep (RCA). You asked for Deep and a proper write-up, so I run the full flow: phases 0-3 myself, one evidence worker per hypothesis in phase 4, and I stop for your reply at two checkpoints. The p95 alert is still firing, so the impact block will say ongoing: yes.

Output root: .culiops/sre-investigate/ at the repo root. Everything this run writes goes under it. It is local and is never committed (git check-ignore says .culiops/sre-investigate is ignored). I will not edit .gitignore or offer a commit.

Environment: found .culiops/sre-investigate/environment.md. Timezone Australia/Brisbane (UTC+10). AWS profile prod-read, kube context arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace orders), Grafana datasources prom-prod / loki-prod / tempo-prod (token variable GRAFANA_SERVICE_ACCOUNT_TOKEN), local clone ~/src/orders-api.
Its Budgets section only sets a Loki ask threshold (20 GB). For everything else I use the template defaults for Deep: 60 queries, 10 GB of logs, 500 CloudWatch metric requests; window caps 2h patterns, 30m raw log lines, 1h trace samples, 12h raw histogram_quantile.

Window: "early this afternoon UTC" carries an explicit zone, so I use it as UTC with no conversion. I take the anchor as 13:00 UTC. You gave no date, so I take today, 2026-10-20, and now = 15:30 UTC. Incident window 12:30-15:30 UTC (22:30 to 01:30 next day Brisbane). Baselines: previous 09:30-12:30 UTC, and minus 7 days 2026-10-13 12:30-15:30 UTC. Tell me if the anchor or the date is off; the true onset will come from the metrics.

Run directory: orders-api-prod-20261020-1530. Starting wave 0 (access and intake).
```

Actions at this point: run directory `out/runs/orders-api-prod-20261020-1530/` created, ledger created from `templates/ledger.md` (Mode: Deep), `RUN` = `<run directory>/raw`. Problem table filled: What = "GET /orders on orders-api in prod slow since early afternoon UTC, p95 alert firing" restated as "p95 latency of GET /orders above baseline since about 13:00 UTC (to be dated by metrics)"; Where = orders-api, prod, ns orders, no named siblings yet; Trigger = "p95 alert" (name and link not given); Mitigations = none known; Assumptions = anchor 13:00 UTC, date 2026-10-20, now 15:30 UTC, template-default budgets.

## Wave 0 - access and intake

Printed to the operator, then run (the first shell call starts with `date -u +%H:%M:%S`; no INDEX row, empty output, so Start column uses the run clock beginning 15:30:00):

```bash
# W0-Q1 identity (AWS)
date -u +%H:%M:%S
aws sts get-caller-identity --profile prod-read

# W0-Q2/Q3 AWS write-check (resolve the role, then simulate the fixed list of ten)
arn=$(aws sts get-caller-identity --profile prod-read --query Arn --output text)
role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)
aws iam simulate-principal-policy --profile prod-read \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text

# W0-Q4/Q5 identity (Kubernetes)
kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl config current-context

# W0-Q6 Kubernetes write-check
kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders

# W0-Q7 token presence (name only)
[ -n "${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}" ] && echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: set" || echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: unset"

# W0-Q8 trigger-alert history: Prometheus ALERTS series, 30 days, hourly (the alert name is not known yet)
GRAFANA_URL=https://grafana.example.com
curl -sG "$GRAFANA_URL/api/datasources/proxy/uid/prom-prod/api/v1/query_range" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=sum by (alertname) (max_over_time(ALERTS{alertstate="firing"}[1h]))' \
  --data-urlencode "start=2026-09-20T15:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=3600"
```

Not run in wave 0, with the reason: no stored profile (`ls` showed no `profiles/`), so nothing to copy; no `lessons.md`; no ticket named; no error-tracker project; not a WAF/403/429 report; the log probe waits for the profile build (first run against a label-based log backend); the request names a "p95 alert" but no CloudWatch alarm, so no `describe-alarm-history`.

### Wave 0 results

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q1 | `aws sts get-caller-identity` | `sts-01.json` | Account 111122223333 (matches `prod-read` in environment.md); role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded) |
| W0-Q2 | `aws iam get-role` | `iam-01.json` | role path `/aws-reserved/sso.amazonaws.com/`, resolved to the full role ARN (not recorded in the box) |
| W0-Q3 | `aws iam simulate-principal-policy` | `iam-02.json` | 10 rows returned, all `implicitDeny`; BUT the rows do not match the 10 requested actions: no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack; three rows I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy), all implicitDeny. 7 of 10 requested actions answered |
| W0-Q4 | `kubectl auth whoami` | `k8s-02.txt` | principal = the same assumed ReadOnly role, group `eks-readonly` (session part not recorded) |
| W0-Q5 | `kubectl config current-context` | `k8s-01.txt` | `arn:aws:eks:us-east-1:111122223333:cluster/prod` (is the context in use) |
| W0-Q6 | `kubectl auth can-i --list` | `k8s-03.txt` | only `[create]` on selfsubjectreviews / selfsubjectaccessreviews / selfsubjectrulesreviews (excluded list); `*.*` `[get list watch]`; non-resource URLs `[get]` |
| W0-Q7 | token presence | `env-01.txt` | `x`: GRAFANA_SERVICE_ACCOUNT_TOKEN is set |
| W0-Q8 | Prometheus `ALERTS` 30d hourly | `prom-10.json` | matrix, empty result: no `ALERTS` series for any alertname in the readable range |

### Wave 0 message to the operator (verbatim)

```text
Wave 0 done. Access:
- AWS prod-read: account 111122223333 matches environment.md, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b.
- Write check, prod-read: no requested action came back allowed, but this is NOT the clean "read-only confirmed" result. 7 of the 10 actions I asked about came back implicitDeny. The reply had no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack, and it carried three rows I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; all implicitDeny). So write capability is only partly checked (gap). Not a finding that the credentials can write, and not proof that they cannot; the role name alone proves nothing.
- Kubernetes context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace orders: no write verbs in orders (only get/list/watch, plus the excluded self-review creates).
- Token GRAFANA_SERVICE_ACCOUNT_TOKEN: set. Culibox: not present, nothing to report.

Gaps so far:
1. AWS write-check incomplete for 3 actions (above). Fix: a human re-runs the simulation for those three, or confirms the role is read-only.
2. Trigger alert history: a 30-day Prometheus ALERTS pull returned no series, so the p95 alert is not visible there (Grafana-managed alert, other datasource, or retention). I will try Grafana annotations in wave 1. Which alert is it, and where does it live? That would help but is not blocking.
No stored profile exists for orders-api prod, so I build one next, then wave 1.
```

## Build profile (first run for orders-api prod)

Helper dispatched: `TASK: PROFILE`, explicit `model` at the cheapest tier, identifier lessons "none" (no `lessons.md`). Simulated inline as `[helper PROFILE, cheapest tier]`, one wave, scratch dir `raw/helper`. While it runs, the main session starts the change-correlation queries that need no identifiers (this is the change leg of wave 1, printed first; the signal and recurrence legs follow once the helper returns metric names).

### Helper wave (commands printed in full, then run)

```bash
GRAFANA_URL=https://grafana.example.com
LOKI=$GRAFANA_URL/api/datasources/proxy/uid/loki-prod
TEMPO=$GRAFANA_URL/api/datasources/proxy/uid/tempo-prod
PROM=$GRAFANA_URL/api/datasources/proxy/uid/prom-prod
# PB-Q1..Q4 Loki discovery
curl -sG "$LOKI/loki/api/v1/labels" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/app/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/namespace/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/container/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
# PB-Q5..Q7 Tempo discovery (tags, service-name values, exact-name search limit 5, last hour)
curl -sG "$TEMPO/api/v2/search/tags" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$TEMPO/api/v2/search/tag/resource.service.name/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600" --data-urlencode "end=1792510200"
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=5"
# PB-Q8 Prometheus metric names
curl -sG "$PROM/api/v1/label/__name__/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
# PB-Q9 dashboards whose title contains the service name
curl -sG "$GRAFANA_URL/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=orders" --data-urlencode "type=dash-db"
# PB-Q10/Q11 Kubernetes compute
kubectl get pods --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders
kubectl get deploy,svc,ingress,hpa --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders
# PB-Q12 RDS with a name filter
aws rds describe-db-instances --profile prod-read --region us-east-1 --query "DBInstances[?contains(DBInstanceIdentifier, 'orders')].{id:DBInstanceIdentifier,class:DBInstanceClass,engine:Engine,version:EngineVersion,status:DBInstanceStatus,multiAz:MultiAZ,pi:PerformanceInsightsEnabled}" --output json
# PB-Q13/Q14 code repo: tags in the local clone, default branch through gh
git -C ~/src/orders-api tag
gh api repos/example-org/orders-api --jq .default_branch
```

### Helper results (world files)

| ID | Command | World file | Key facts |
|---|---|---|---|
| PB-Q1 | Loki labels | `loki-01.json` | `app`, `container`, `namespace`, `stream` (no pod label) |
| PB-Q2 | Loki `app` values | `loki-02.json` | catalog-api, notify-worker, orders, orders-reconcile, payments-worker (no `orders-api`) |
| PB-Q3 | Loki `namespace` values | `loki-03.json` | catalog, notify, orders, payments |
| PB-Q4 | Loki `container` values | `loki-04.json` | api, worker |
| PB-Q5 | Tempo `/api/v2/search/tags` | `tempo-06.json` | resource scope tags: k8s.namespace.name, k8s.pod.name, service.name, service.version; span tags: db.statement, db.system, http.request.method, http.response.status_code, http.route, server.address; intrinsic: duration, kind, name, status, statusMessage |
| PB-Q6 | Tempo tag values `resource.service.name` | `_default.txt` | `{}`: nothing usable |
| PB-Q7 | Tempo search `{ resource.service.name = "orders-api" }` limit 5, last hour | `tempo-07.json` | `traces: []`, 0 inspected |
| PB-Q8 | Prometheus `label/__name__/values` | `prom-09.json` | http_server_request_duration_seconds_{bucket,count,sum}, db_client_operation_duration_seconds_{bucket,count,sum}, db_client_connections_{usage,pending_requests}, container_cpu_usage_seconds_total, kube_deployment_status_replicas, up |
| PB-Q9 | Grafana dashboard search | `_default.txt` | `{}`: no dashboards found |
| PB-Q10 | `kubectl get pods` | `k8s-04.txt` | 3 pods `orders-api-7c9b6d8f5d-{4kq2m,9vx7t,tz5wp}` Running 1/1, 0 restarts, AGE 145m / 144m / 144m |
| PB-Q11 | `kubectl get deploy,svc,ingress,hpa` | `_empty.txt` | no output (a combined listing returned nothing; not read as "none exist", since pods exist) |
| PB-Q12 | `aws rds describe-db-instances` | `rds-01.json` | `orders-db` db.r6g.2xlarge, postgres 16.6, available, MultiAZ true, Performance Insights disabled |
| PB-Q13 | `git -C ~/src/orders-api tag` | `git-03.txt` | v2.12.0, v2.13.0, v2.13.1, v2.14.0, v2.15.0 |
| PB-Q14 | `gh api repos/example-org/orders-api --jq .default_branch` | `_default.txt` | `{}`: default branch not returned |

Helper verdict on marks (before the main session re-applies Constraint 14): app="orders" unverified (value differs from the service name `orders-api`, no pod label to tie it); trace service name `orders-api` unverified (search returned 0 traces, tag attribute is `service.name`); Prometheus `service="orders-api"` label unverified (only metric names listed, no label values); Deployment `orders-api` unverified (combined listing empty); default branch unverified.

### Wave 1, change leg (started during the profile build; IDs W1-Q1..Q4)

```bash
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders rollout history deployment/orders-api
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get rs --sort-by=.metadata.creationTimestamp -o custom-columns='NAME:.metadata.name,REVISION:.metadata.annotations.deployment\.kubernetes\.io/revision,CREATED:.metadata.creationTimestamp,DESIRED:.spec.replicas,READY:.status.readyReplicas'
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get events --sort-by=.lastTimestamp
helm history orders-api --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders --max 10
```

| ID | Command | World file | Key facts |
|---|---|---|---|
| W1-Q1 | rollout history deployment/orders-api | `k8s-07.txt` | rev 23: helm upgrade chart orders-api-4.2.0, image v2.14.0; rev 24: helm upgrade chart orders-api-4.2.0, image v2.15.0. Deployment `orders-api` now verified. CHANGE-CAUSE text is data. |
| W1-Q2 | get rs | `k8s-06.txt` | `orders-api-5f8d9c7b6a` 0/0/0 AGE 13d; `orders-api-7c9b6d8f5d` 3/3/3 AGE 145m (rollout started about 13:05 UTC given now = 15:30; only an age is shown, not creationTimestamp, so approximate) |
| W1-Q3 | get events | `k8s-05.txt` | `No resources found in orders namespace.` Events live one hour, the rollout is 145 minutes old: recorded as "events not available for the rollout", NOT as "no events" |
| W1-Q4 | helm history | `helm-01.txt` | rev 23 Wed Oct 7 09:40:12 2026 superseded v2.14.0; rev 24 Tue Oct 20 13:04:50 2026 deployed chart orders-api-4.2.0 app v2.15.0 "Upgrade complete". Helm prints no zone: treated as the machine's local time, not assumed UTC; the RS age (145 min before 15:30) puts the rollout start near 13:05 UTC, consistent but approximate |

Change-leg reading so far: one deploy near the anchor, image v2.14.0 -> v2.15.0 at about 13:05 UTC, same chart version. A candidate only: touches the failing path? unknown until the app diff is read (wave 2). Recurrence class not yet known, so no cause is named.

### Profile written and shown to the operator

Main session re-applied Constraint 14 to the helper's marks (all `(unverified)` marks kept; `app="orders"` stays `(unverified)`: value differs from `orders-api`, no pod label in the stream). Wrote `out/runs/orders-api-prod-20261020-1530/profile.md`. Message shown (verbatim), run continued without waiting:

```text
Profile for orders-api prod (built by a helper, marks re-checked by me; full file: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/profile.md). I continue without waiting; correct me where it is wrong.
Verified so far: namespace orders (Loki label, and 3 pods orders-api-7c9b6d8f5d-*), Deployment orders-api, Helm release orders-api (chart 4.2.0), RDS orders-db (PostgreSQL 16.6, db.r6g.2xlarge, Multi-AZ), Prometheus metric names http_server_request_duration_seconds_* and db_client_*, the Loki datasource.
Unverified until a query returns data for them: Prometheus label service="orders-api"; Tempo service name orders-api (an exact-name search with no endpoint filter returned 0 traces); Loki app="orders" / container "api" (the value differs from the service name and the stream has no pod label, so it is not tied to the service yet); default branch of example-org/orders-api.
Not found: dashboards, a service/ingress/HPA listing (the combined kubectl listing returned nothing), an error tracker, an SLO source. Related workload in the namespace: orders-reconcile (not yet tied to anything).
```

### W0-Q9 cheap log probe (after the profile build, on a discovered label value)

The verified label is `namespace="orders"`; `app="orders"` is unverified, so the probe uses the namespace.

```bash
curl -sG "$GRAFANA_URL/api/datasources/proxy/uid/loki-prod/loki/api/v1/index/stats" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query={namespace="orders"}' \
  --data-urlencode "start=1792509300000000000" --data-urlencode "end=1792510200000000000"
```

Mapped to `loki-06.json` (LogQL selector row, `namespace=orders`), restricted to the requested window 15:15-15:30 UTC: two streams exist (`app="orders"`/`container="api"` and `app="orders-reconcile"`/`container="worker"`); only the api stream has lines inside the window (8 lines of `method=GET path=/orders status=200 duration_ms=286..751 page_size=50`, 15:18-15:19 UTC); `totalBytesProcessed` 48,211,904 (about 0.048 GB), far under the per-query soft limit (1 GB) and the Loki ask threshold (20 GB). Lines look like the service's traffic (a lead only; the api stream is still not tied to the service). No instruction-like text in the lines.

Slip recorded: before running this probe I had opened `loki-05.json` and `loki-06.json` in one read (the probe maps only to loki-06). `loki-05` holds the same api-stream lines as loki-06; the three `orders-reconcile` lines in loki-06 fall at 15:00-15:04 UTC, outside the probe window, so I did not use them (I removed a baseline note about them from the profile).

### Wave 1, signal and recurrence legs (printed in full, then run; IDs W1-Q5 onward)

Wave 1 is larger than ten calls because its fixed legs (change, signals for a latency symptom, recurrence, alert history) all run: 24 calls in total, of which at most two are heavy on Prometheus (W1-Q5, W1-Q6) and two on Tempo (W1-Q21, W1-Q22). The minus-7-day ranges of the two heavy quantile queries are held for wave 2 (heavy limit); their minus-7-day comparison is carried in wave 1 by the instant p95 per route (W1-Q9).

```bash
date -u +%H:%M:%S
GRAFANA_URL=https://grafana.example.com
PROM=$GRAFANA_URL/api/datasources/proxy/uid/prom-prod
TEMPO=$GRAFANA_URL/api/datasources/proxy/uid/tempo-prod
# W1-Q5 p95 GET /orders, previous + incident window, step 120 (heavy 1)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# W1-Q6 p50 GET /orders, same range (heavy 2)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# W1-Q7 p95 per method and route at 15:30 (incident)
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))' --data-urlencode "time=1792510200"
# W1-Q8 same at 12:30 (just before the incident window)
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))' --data-urlencode "time=1792499400"
# W1-Q9 same, offset 7d, evaluated at 15:30
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m] offset 7d)))' --data-urlencode "time=1792510200"
# W1-Q10/Q11 p99 of GET /orders at 15:30 and 12:30
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "time=1792510200"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "time=1792499400"
# W1-Q12/Q13 p90 of GET /orders at 15:30 and 12:30
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.9, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "time=1792510200"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.9, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))' --data-urlencode "time=1792499400"
# W1-Q14/Q15 call rate of GET /orders: incident+previous, and offset 7d
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders", method="GET"}[5m]))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders", method="GET"}[5m] offset 7d))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# W1-Q16/Q17 database operations per second: incident+previous, and offset 7d
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m] offset 7d))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# W1-Q18 connection pool: used and pending requests
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=db_client_connections_usage{service="orders-api"} or db_client_connections_pending_requests{service="orders-api"}' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# W1-Q19 CPU by pod (saturation), step 600
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders"}[5m]))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=600"
# W1-Q20 recurrence pull: database operations per second, whole-hour rate, 14 days ending at the window start, step 3600
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))' --data-urlencode "start=1791289800" --data-urlencode "end=1792499400" --data-urlencode "step=3600"
# W1-Q21 Tempo: p95 duration of database client spans (TraceQL metrics), step 900 (heavy 1)
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.db.system =~ ".+" } | quantile_over_time(duration, .95)' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=900"
# W1-Q22 Tempo: rate of the same database client spans (heavy 2)
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.db.system =~ ".+" } | rate()' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=900"
# W1-Q23/Q24 Grafana annotations: alert state history (30 days) and everything in the window
curl -sG "$GRAFANA_URL/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "type=alert" --data-urlencode "from=1789918200000" --data-urlencode "to=1792510200000" --data-urlencode "limit=100"
curl -sG "$GRAFANA_URL/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "from=1792499400000" --data-urlencode "to=1792510200000" --data-urlencode "limit=100"
```

### Wave 1 signal-leg results

| ID | World file | Key facts |
|---|---|---|
| W1-Q5 | `prom-01.json` | `service="orders-api"` label now verified (series returned). GET /orders p95, 2-min step, 10:00-15:30 (coverage starts 10:00, not 09:30): median 0.180 s before 13:06 (min 0.160, max 0.200); last baseline sample 13:06 = 0.163 s; first bad sample 13:08 = 0.716 s; 13:10-15:30 median 0.712 s (min 0.661, max 0.755), still elevated at 15:30 |
| W1-Q6 | `prom-02.json` | GET /orders p50: median 0.092 s before 13:06; 13:08 = 0.295 s; 13:10-15:30 median 0.311 s (min 0.281, max 0.339). The median moved too, so this is not a ceiling |
| W1-Q7 | `prom-03.json` | p95 at 15:30: GET /orders 0.712; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; GET /healthz 0.003 |
| W1-Q8 | `prom-04.json` | p95 at 12:30: GET /orders 0.181; GET /orders/{id} 0.061; POST /orders 0.139; PATCH /orders/{id} 0.091; GET /healthz 0.003 |
| W1-Q9 | `prom-14.json` | p95 at the same clock time 7 days earlier (2026-10-13 15:30): GET /orders 0.181; /orders/{id} 0.061; POST /orders 0.139; PATCH 0.091; healthz 0.003 |
| W1-Q10 | `prom-10.json` | empty matrix (no series): p99 not available; empty is not zero |
| W1-Q11 | `prom-10.json` | empty matrix: p99 at 12:30 not available |
| W1-Q12 | `prom-10.json` | empty matrix: p90 at 15:30 not available |
| W1-Q13 | `prom-10.json` | empty matrix: p90 at 12:30 not available |
| W1-Q14 | `prom-07.json` | GET /orders call rate, one series: median 56.5 /s before 13:06, 56.2 /s from 13:10 to 15:30 (min 52.1, max 60.6): flat |
| W1-Q15 | `prom-07.json` | the `offset 7d` form returned the same series with 2026-10-20 timestamps (no offset row exists for call rate): not a usable minus-7-day baseline; recorded as a gap, the previous window is the baseline for call rate |
| W1-Q16 | `prom-05.json` | database operations per second (`db_system="postgresql"`): median 381 /s before 13:06 (min 361, max 401); 13:08 = 4,031 /s; 13:10-15:30 median 3,961 /s (min 3,821, max 4,089): about 10.4x, at the same 2-minute sample as the latency step |
| W1-Q17 | `prom-13.json` | same clock window 2026-10-13: median 379 /s (min 355, max 404) for 12:30-15:30: flat at baseline |
| W1-Q18 | `prom-06.json` | pool `orders-db`: used median 16 (max 19) before, median 21 (max 24) 13:10-15:30; pending_requests 0 throughout. No pool wait |
| W1-Q19 | `prom-08.json` | CPU per pod, 13:08-15:30 only (15 points at 600 s): 4kq2m 0.53-0.64, 9vx7t 0.52-0.63, tz5wp 0.56-0.64 cores; the three replicas move together. No pre-13:08 samples and no limit known: no baseline |
| W1-Q20 | `prom-05.json` | 14-day hourly pull: only 3 of 336 points exist (10:30, 11:30, 12:30 on 2026-10-20): 371.0, 375.9, 374.7 /s, all baseline. Coverage far below 14 days |
| W1-Q21 | `tempo-01.json` | database client span p95, 15-min step, `span.db.system="postgresql"`: 3.9-4.4 ms in every sample from 10:00 to 15:30, no change at 13:08. Tempo `resource.service.name = "orders-api"` now verified (series returned). `inspectedBytes` 6.63 GB (Tempo bytes are not in the budget table; noted) |
| W1-Q22 | `tempo-08.json` | `series: []`, nothing inspected: db span rate not available |
| W1-Q23 | `_default.txt` | `{}`: no alert annotations returned |
| W1-Q24 | `_default.txt` | `{}`: no deploy markers or other annotations returned |

Reading: shape = step at 13:08 UTC (first bad sample; last good sample 13:06). Only GET /orders is slow. Its call rate is flat, its p50 and p95 both rose (3.4x and 3.9x), database operations per second rose 10.4x in the same sample, while the p95 of each database call stayed at about 4 ms. That pattern is "more work per request", not volume to the endpoint and not a slower database. The 14-day recurrence pull and the alert history are unusable (see Recurrence).

### Phase 1 conclusions (written to the ledger before use)

Ledger written after wave 1 (Problem, Access, Impact, Windows, Recurrence, Timeline, Query log W0/PB/W1, Gaps G1-G12, Lesson candidates). Shape = step at 13:08; GET /orders only; call rate flat; database operations x10.4 at the same sample; database span p95 flat at about 4 ms; pool pending 0; not a ceiling (p50 moved 3.4x, p95 3.9x). Recurrence = `unclassified` (alarm history unreadable; 14-day pull 3 of 336 points). Phase 1 step 5 core flows: environment.md lists no business counter, so no counter comparison (gap G12); per-route p95 of POST /orders and GET /orders was read instead. Availability cross-check skipped: the symptom is latency, error rate was not queried (stated in the impact basis).

### Impact block, shown to the operator before Phase 2 (verbatim)

```text
Impact as of 15:30 UTC (01:30 Brisbane, 2026-10-21)
Symptom:   GET /orders p95 0.712 s (was 0.181 s, about 3.9x); p50 0.311 s (was 0.092 s). GET /orders/{id}, POST /orders and PATCH /orders/{id} are flat.
Affected:  prod orders-api, order history (GET /orders, a core flow), all three replicas; customer-facing. Checkout (POST /orders) p95 flat at 0.14 s. Error rate not measured.
Since:     13:08 UTC (23:08 Brisbane; last good sample 13:06) · ongoing: yes
Severity:  SEV2 (suggested) because one core-flow endpoint is significantly degraded (about 4x p95) while the rest of the service is healthy; the SEV1 criteria (a core flow down, or more than 5% of requests failing) are not evidenced, but failures were not measured.
Basis:     request metrics against baseline (no SLO named) · W1-Q5, W1-Q6, W1-Q7, W1-Q8, W1-Q9 · Confirmed
Third party in the path: none known
```

## Phase 2 - change correlation

Recurrence class read first: `unclassified`, so no schedule is put ahead of the deploy by pattern; schedules are still listed before blaming anything (changes playbook, Schedules). The wave 1 change leg already holds the service's own deploy record (Helm revision 24 at 13:04:50, image v2.14.0 -> v2.15.0).

### Wave 2 (slow change sources + the held heavy pair), commands printed in full then run

```bash
date -u +%H:%M:%S
# W2-Q1/Q2 app history between the deployed refs, local clone, by tag, no fetch
git -C ~/src/orders-api log --date=iso-strict --format='%h %cI %an %s' v2.14.0..v2.15.0
git -C ~/src/orders-api diff v2.14.0 v2.15.0
# W2-Q3..Q7 schedules (EventBridge rules, Scheduler, SSM maintenance windows, CronJobs, RDS windows)
aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text
aws ssm describe-maintenance-windows --profile prod-read --region us-east-1 --query 'WindowIdentities[].[WindowId, Name, Enabled, Schedule, ScheduleTimezone, Duration, NextExecutionTime]' --output text
kubectl get cronjobs -A --context arn:aws:eks:us-east-1:111122223333:cluster/prod -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'
aws rds describe-db-instances --profile prod-read --region us-east-1 --db-instance-identifier orders-db --query 'DBInstances[0].{backup: PreferredBackupWindow, maintenance: PreferredMaintenanceWindow}'
# W2-Q8 CloudTrail writes naming 'orders', onset-2h to onset+15m
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T13:23:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders')]].[EventTime, EventSource, EventName, Username, EventId]" --output text
# W2-Q9 events of the direct dependency orders-db
aws rds describe-events --profile prod-read --region us-east-1 --source-type db-instance --source-identifier orders-db --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T14:08:00Z --query 'Events[].[Date, Message]' --output text
# W2-Q10/Q11 the held -7d quantile ranges (the two heavy Prometheus queries of this wave)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m] offset 7d)))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m] offset 7d)))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
```

| ID | Command | World file | Key facts |
|---|---|---|---|
| W2-Q1 | git log | `git-01.txt` | a4c1e9b 2026-10-19 "orders: load items per order in list handler (#2211)"; 7be20d4 2026-10-19 "orders: return shipment ETA on order detail (#2208)"; 3f9d6a1 2026-10-16 "deps: bump structlog to 25.4.0 (#2203)" |
| W2-Q2 | git diff | `git-02.txt` | `list_orders.py`: `repo.list_orders_with_items(customer_id, limit=limit)` replaced by `repo.list_orders(...)` + `for order in orders: order.items = repo.list_items(order.id)`; `order_detail.py`: adds `shipment_eta`; `pyproject.toml`: structlog 25.3.0 -> 25.4.0 |
| W2-Q3 | aws events list-rules | `_default.txt` | `{}` no items |
| W2-Q4 | aws scheduler list-schedules | `_default.txt` | `{}` no items |
| W2-Q5 | aws ssm describe-maintenance-windows | `_default.txt` | `{}` no items |
| W2-Q6 | kubectl get cronjobs -A | `_empty.txt` | no output |
| W2-Q7 | aws rds describe-db-instances (windows) | `rds-01.json` | no PreferredBackupWindow / PreferredMaintenanceWindow field in the reply |
| W2-Q8 | aws cloudtrail lookup-events | `_default.txt` | `{}` no items |
| W2-Q9 | aws rds describe-events | `_default.txt` | `{}` no items |
| W2-Q10 | Prometheus p95 offset 7d | `prom-11.json` | 2026-10-13 12:30-15:30 median 0.181 s (0.161-0.200): flat |
| W2-Q11 | Prometheus p50 offset 7d | `prom-12.json` | 2026-10-13 12:30-15:30 median 0.088 s (0.080-0.100): flat |

### Wave 3 (app code at the deployed ref, paths taken from W2-Q2)

```bash
date -u +%H:%M:%S
git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py
git -C ~/src/orders-api show v2.15.0:orders_api/repository.py
```

| ID | World file | Key facts |
|---|---|---|
| W3-Q1 | `repo/orders_api/handlers/list_orders.py` | limit = min(query limit or 50, 50); `repo.list_orders` then one `repo.list_items(order.id)` per order; up to 50 orders per page |
| W3-Q2 | `repo/orders_api/repository.py` | `list_orders`: one SELECT with LIMIT; `list_items`: one SELECT on order_items per call, each with its own `pool.connection()`; `list_orders_with_items` (one SELECT with LEFT JOIN, "used by the list handler up to v2.14.0") still defined and now unused by the handler |

Process slips noted: I ran an unmapped `find` over `repo/orders_api/handlers` before the `cat` of the mapped file; names only, no extra file was opened.

Phase 2 reading (ledger rows, timeline rows, code repo row and gap G13 written before use):
- The deploy at 13:04:50 touches the failing path: commit a4c1e9b / PR #2211, file `orders_api/handlers/list_orders.py`. Candidate -> suspect. Timing: the first bad sample (13:08) is about 3 minutes after the Helm upgrade and the new ReplicaSet (about 13:05). Old pods are gone, so the old-versus-new split by pod is not available; the old-versus-new evidence available is the image diff on the failing path plus the step in database operations per second at the rollout.
- #2208 changes order detail only; GET /orders/{id} p95 is flat (0.064 vs 0.061 vs 0.061): not a suspect. #2203 (structlog bump) would touch every route; the other four routes are flat: not a suspect.
- Ledger arithmetic recorded for the checkpoint: database operations rose by about 3,580 /s (381 -> 3,961) while GET /orders ran at about 56 /s, i.e. about 64 extra operations per call if the other routes are unchanged, against at most 50 extra statements expected from the per-order loop (limit 50). Same order of magnitude; the exact figure is open and goes to the H1 worker.

### Deep checkpoint #1 message (verbatim)

```text
Checkpoint 1 of 2 (Deep). Please confirm or correct before I write hypotheses.

Windows (UTC, Brisbane in brackets)
- Incident 12:30-15:30 (22:30-01:30); true onset 13:08 (23:08), ongoing
- Previous 09:30-12:30 (19:30-22:30); Prometheus only returned data from 10:00
- Minus 7 days: 2026-10-13 12:30-15:30 (22:30-01:30)

Blast radius: GET /orders only (p95 0.18 s to 0.71 s, p50 0.09 s to 0.31 s). GET /orders/{id}, POST /orders (checkout), PATCH /orders/{id} and /healthz are flat. All 3 replicas move together (CPU per pod similar; per-pod latency not available). Database operations per second rose about 10x at the same 2-minute sample as the latency (381 to 3,961 /s) while the GET /orders call rate stayed flat (about 56 /s); each database call is still about 4 ms at p95 and the pool has no waiters. Shape: step.

Recurrence: unclassified. The alert's history is unreadable (no ALERTS series, no alert annotations) and the 14-day pull returned 3 of 336 hourly points, so I cannot count earlier occurrences. What I can see: the same clock window a week earlier is flat at baseline.

Changes near the onset
1. Helm revision 24 at 13:04:50 (Helm prints no zone; the ReplicaSet age agrees within a minute): chart orders-api-4.2.0 unchanged, image v2.14.0 to v2.15.0; 3 pods on the new ReplicaSet, the old one is at 0. The onset is about 3 minutes later.
2. v2.14.0..v2.15.0 has 3 commits. #2211 "load items per order in list handler" rewrites GET /orders (orders_api/handlers/list_orders.py): one joined query becomes one query for the orders plus one query per order (up to 50). It is on the failing path, so it is a suspect, not yet a cause. #2208 changes order detail only (that route is flat). #2203 bumps structlog (every route would be hit; the others are flat).
3. Nothing else found: no scheduled rules, schedules, CronJobs or maintenance windows listed, no CloudTrail writes naming "orders" and no RDS events for orders-db from 11:08 to 13:23 / 14:08. Those replies were empty, which is weak evidence (region us-east-1, prod-read only). Kubernetes events had already expired (one hour retention).

Run profile since I showed it: Prometheus label service="orders-api" and the Tempo service name orders-api are now verified; Loki app="orders" is still not tied to the service; the IaC or values repo and the default branch of example-org/orders-api are unknown.

Two questions
1. Is the window right (onset about 13:08 UTC, ongoing)?
2. Did anything change that I cannot see: a manual action, a config or feature-flag change, an upstream or vendor change, a caller-side traffic change, or another deploy around 13:00 UTC?
I wait for your reply before Phase 3.
```

### Operator line 2 (cue: checkpoint #1)

`Agreed, go on.` Received at checkpoint #1. Recorded in the ledger's intake assumptions: window and onset confirmed by the operator; no unseen manual/vendor change reported (operator gave none).

## Phase 3 - hypotheses

Inputs: impact and shape (Phase 1), change list (Phase 2), profile dependency table (orders-db). service-discovery catalog check: `ls .culiops/service-discovery/` has no INDEX row for a listing of that path, so it prints `No such file or directory` (exit 1): no catalog; suggest `service-discovery` after the incident. Docs: no wiki/runbook route is configured in environment.md, nothing searched.

Own ranked list formed first (H1-H5 open, H6-H8 ruled out from existing data; see ledger Hypotheses table), then the history lookup (mapped commands):

| Command | World file | Key facts |
|---|---|---|
| `ls .culiops/sre-investigate/incidents` | `ls-02.txt` | `2026-08-14-orders-api.md`, `2026-09-30-catalog-api.md` |
| `grep -rn -i -E "orders-api\|orders-db\|latency" .culiops/sre-investigate/incidents` | apply grep to `incidents/` | matches only `2026-08-14-orders-api.md` (service, symptoms, deps lines) |
| `cat .culiops/sre-investigate/incidents/2026-08-14-orders-api.md` | `incidents/2026-08-14-orders-api.md` | 2026-08-14, cause_category db-connection-pool, Confirmed then: pool exhausted after a config change lowered the pool size; pending_requests above 30; p95 0.2 s to 2.4 s on GET and POST /orders for 40 minutes; fixed by restoring the pool size |

Reading: a lead, matched to H3 (pool/connection cap), no separate `from-history:` ID. It is NOT told to any worker. This run's pool metric (pending 0 throughout, W1-Q18) and POST /orders being flat do not look like that mechanism, so the history does not raise any label. The 2026-09-30 catalog-api incident did not match.

Model tiers decided now (Deep): H1 strong, H2 to H5 default. Reason for H1: three signals have to be correlated (code diff, metrics step, trace span counts) and a numeric mismatch is expected (about 64 extra operations per call from metrics against at most 50 from the loop). Ledger Hypotheses table, status lines, Memory table written before the checkpoint.

### Deep checkpoint #2 message (verbatim)

```text
Checkpoint 2 of 2 (Deep). Ranked hypotheses, each with the query that would disprove it. They run next, one evidence worker each, all sent together. Remaining budget: 21 of 60 queries, so 4 per worker.

1. H1 (strong tier) Release v2.15.0, PR #2211: GET /orders now runs one statement per order (up to 50) instead of one joined statement (an N+1). Expected: more statements per request, each as fast as before. Disprove: statements (spans) per GET /orders request, incident 14:30-15:30 against baseline 11:00-12:00, at least 20 traces each; equal counts refute it.
2. H2 (default) orders-db is saturated or contended (CPU, read latency, locks) independent of the statement count. Disprove: RDS CPU, ReadLatency and connections at baseline, together with the database span p95, which is already flat at about 4 ms.
3. H3 (default) Connection pool or engine connection cap reached. Lead from history: an earlier incident on this service (2026-08-14) was a pool exhaustion after a pool-size change. I read it only after ranking; it is a lead, not evidence. Disprove: pool pending_requests at 0 and connections well below the engine limit. Pre-evidence: pending was 0 throughout (W1-Q18).
4. H4 (default) The 3 new pods are CPU-throttled or at their CPU limit. Disprove: throttling near zero and CPU below the limit. Likely to hit a data gap (no limit known, no baseline).
5. H5 (default) A non-database downstream call of GET /orders got slower. Disprove: non-database client spans at baseline p95.

Already ruled out from phase 1 and 2 data, no worker: traffic spike (GET /orders call rate flat, W1-Q14); the other two commits #2208 and #2203 (the other routes are flat, W1-Q7 to W1-Q9); image pull, scheduling failure, crash loop, OOM (3 of 3 ready, 0 restarts, W1-Q2). No schedule hypotheses: nothing scheduled was listed and the pattern class is not "scheduled". Not generated as implausible for a latency-only step with no errors: NAT/egress, DNS, certificate or credential expiry, API throttling, cache.

Add, drop or re-rank anything before I spend the budget? I wait for your reply.
```

### Operator line 3 (cue: checkpoint #2)

`Fine, continue.` Received at checkpoint #2. No change to the list.

## Phase 4 - evidence workers

Five workers dispatched in one message (simulated inline, each following `agents/evidence.md`): H1 on the stronger tier, H2-H5 on the default tier, each with an explicit `model`. Each gets: the whole fenced prompt, the run's `profile.md` (not the stored one: none exists), read-only `ledger.md`, the three windows, its budget share (4 queries, 0 GB logs, CloudWatch metric requests: 3 for H2 and H3 each, at most 3 waves), no PREVIOUS VERDICT, LESSONS "none", and no past incidents or failure-mode lessons. `RUN` = `<run directory>/raw/<ID>`.

Windows given to workers (UTC): incident 2026-10-20 12:30 to 15:30; baseline (previous) 09:30 to 12:30; baseline (-7d) 2026-10-13 12:30 to 15:30.
### Round 1 workers (wave 4 on merge; worker-local IDs shown, renumbered to W4-Q on merge)

Dispatch message (one message, five workers): H1 stronger tier, H2-H5 default tier. Budget share 4 queries each (21 remaining). Workers run in parallel, so H1 and H5 could not see each other's rows; any duplicate read is accepted.

#### [evidence H1, escalated tier] (strong tier from the start under the dispatcher rule for three signals; this is not an escalation)

Falsification first: span count per GET /orders request, incident against baseline; equal counts refute H1. Commands printed then run (wave 1 of the worker):

```bash
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
# H1-Q1 incident 14:30-15:30: GET /orders server spans and all their descendant client spans, limit 30
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span:kind = client }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=30"
# H1-Q2 baseline 11:00-12:00 (before the rollout, same day)
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span:kind = client }' --data-urlencode "start=1792494000" --data-urlencode "end=1792497600" --data-urlencode "limit=30"
# H1-Q3 one incident trace by ID, window padded one hour each side
curl -sG "$TEMPO/api/v2/traces/e3ea7a3906419b466a28541306cc5ee1" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792503000" --data-urlencode "end=1792513800"
# H1-Q4 one baseline trace by ID
curl -sG "$TEMPO/api/v2/traces/65345f5f8176033524bc88af3bd43f6f" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792490400" --data-urlencode "end=1792501200"
```

Mapped: H1-Q1 `tempo-02.json` (24 traces), H1-Q2 `tempo-03.json` (24 traces), H1-Q3 `tempo-09.json`, H1-Q4 `tempo-10.json` (trace IDs taken from the two searches). Both sample sizes are at least 20. Extracts saved under `raw/H1/`.

```text
VERDICT: H1 | Confirmed
summary: GET /orders spans per request jumped after the v2.15.0 rollout and the added latency is proportional to them. Descendant spans per request (all client spans under the server span; each sampled trace also carries one constant non-database client span, GET auth-api /verify, so database statements are one fewer): incident 14:30:18-15:27:50, n=24: p50 41, p95 52, max 52, min 9, mean 38.9; baseline 11:00:09-11:57:36, n=24: p50 3, p95 4, max 4, min 2, mean 3.1. Equal counts would have refuted H1; they differ by about 13x. Max 52 = 1 auth call + 1 SELECT orders + 50 SELECT order_items, which matches the handler's cap of 50 orders per page. In the incident sample, request duration = about 90 ms + 6.05 ms per descendant span, r = 0.966 (n=24); in the baseline sample duration (78-165 ms, median 110) does not depend on span count (3-4 spans). 35.8 extra spans x 6.05 ms = about 217 ms against the observed p50 shift of +219 ms (0.092 s to 0.311 s, W1-Q6). The two fetched traces show the code change itself at runtime: baseline trace = auth-api verify (3.8 ms) + ONE statement "SELECT orders JOIN order_items" (3.05 ms), root 109 ms; incident trace = auth-api verify (3.4 ms) + "SELECT orders" (3.0 ms) + 12 serial "SELECT order_items" spans (2.9-4.5 ms each, about 1.0-1.7 ms apart), root 152 ms. Per-statement time did not change (2.9-4.5 ms against 3.05 ms; database span p95 flat at about 4 ms, W1-Q21): the extra time is the count, not slower statements. Chain, with the other legs from the ledger: change = PR #2211 / commit a4c1e9b replaces list_orders_with_items by list_orders plus one list_items per order (W2-Q2, W3-Q1, W3-Q2); mechanism = the traces above; timing = Helm revision 24 at 13:04:50 and ReplicaSet age about 13:05 (W1-Q4, W1-Q2) against the first bad sample at 13:08 with the 13:06 sample at baseline (W1-Q5, W1-Q16), and the same clock window a week earlier flat (W2-Q10, W1-Q17).
weakest_link: mechanism to symptom rests on one 24-trace sample per window (metrics agree on the step: database operations x10.4 and p50 x3.4 at the same 13:08 sample, W1-Q16, W1-Q6) (Confirmed)

evidence:
- Descendant spans per GET /orders: p50 41 (max 52) against p50 3 (max 4), n=24 each [tempo, H1-Q1 and H1-Q2, 14:30-15:30 and 11:00-12:00] link: Grafana Explore tempo-prod, TraceQL as above
- Incident trace e3ea7a39...: 12 serial SELECT order_items spans under one GET /orders (152 ms) [tempo, H1-Q3, 14:30:18] link: Tempo trace view e3ea7a3906419b466a28541306cc5ee1
- Baseline trace 65345f5f...: one joined SELECT, root 109 ms [tempo, H1-Q4, 11:00:09] link: Tempo trace view 65345f5f8176033524bc88af3bd43f6f
- Duration against span count, incident: slope 6.05 ms, intercept 89.8 ms, r=0.966 (local fit on raw/H1/tr-matched-incident.tsv)

timeline:
- 13:04:50 - Helm revision 24, image v2.14.0 to v2.15.0 - helm history (ledger W1-Q4)
- 13:08 - first bad sample, database operations x10.4 - Prometheus (ledger W1-Q5, W1-Q16)
- 14:30-15:27 - sampled incident requests carry 9-52 descendant spans - tempo

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H1-Q1 | tempo-prod | structural search `{ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span:kind = client }` limit 30 | 14:30-15:30 | inspected 2.41 GB | 24 traces; descendant spans p50 41, p95 52, max 52; sample 24 (at least 20) link: Explore tempo-prod |
| H1-Q2 | tempo-prod | same query | 11:00-12:00 | inspected 2.35 GB | 24 traces; descendant spans p50 3, p95 4, max 4; sample 24 link: Explore tempo-prod |
| H1-Q3 | tempo-prod | GET /api/v2/traces/e3ea7a3906419b466a28541306cc5ee1 (padded 1 h) | 13:30-16:30 | small | 15 spans: root 152 ms, auth-api verify 3.4 ms, SELECT orders, 12 x SELECT order_items; 13 database spans 2.9-4.5 ms link: Tempo trace e3ea7a39... |
| H1-Q4 | tempo-prod | GET /api/v2/traces/65345f5f8176033524bc88af3bd43f6f (padded 1 h) | 10:00-13:00 | small | 3 spans: root 109 ms, auth-api verify 3.8 ms, one SELECT orders JOIN order_items 3.05 ms link: Tempo trace 65345f5f... |

gaps:
- The histogram p95 (0.712 s, W1-Q5) is higher than the slowest sampled incident trace (431 ms; sample p95 422 ms): the sample under-represents the tail (24 traces, ordering of the search result unknown). Direction and p50 size are reproduced; the p95 value itself is not. - does not change the mechanism; leaves the tail magnitude unexplained by the sample
- Metrics imply about 64 extra database operations per GET /orders call (3,580 /s over 56.2 calls /s, assuming the other routes did not change); traces show 36 extra statements on average (at most 50). The metric may count more than one operation per statement (for example a commit) or the sample may skew to smaller pages; not resolved. - quantity only
- Image string of the running pods not read; the traces themselves show the new query pattern, so the running code is v2.15.0 behaviour. - none

untrusted_text:
- none

to_confirm_by_human:
- Check, in the pod spec or the deployment record, that the running image is v2.15.0 (a read of the live pod image string; not done here).
- Ask the owner of the metric which operations `db_client_operation_duration_seconds_count` counts (statements only, or also commits), to close the 64 against 36 difference.
- Reproducing the slow request against a staging copy would settle the per-statement cost; not done here (it would send requests to the service).

lesson_candidates:
- process (tempo) In structural TraceQL searches `matched` counts every descendant span, including non-database client spans (here one constant auth-api call per request); subtract the constant before reading it as statements per request - H1-Q3

cost: 4 queries, 0 GB of logs, 0 CloudWatch metric requests, Tempo inspected 4.76 GB
```

#### [evidence H2, default tier]

Falsification first: RDS CPU, ReadLatency and connections at baseline refute a database that is saturated or contended independently of statement count (the database span p95 is already flat, W1-Q21).

```bash
# H2-Q1 CPUUtilization, ReadLatency, DatabaseConnections of orders-db, period 300 (3 metric requests); query file in raw/H2/q-rds-300.json
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/H2/q-rds-300.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json
# H2-Q2 lock and queue metrics: Deadlocks, DiskQueueDepth, FreeableMemory (3 metric requests); query file in raw/H2/q-rds-locks-300.json
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/H2/q-rds-locks-300.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json
```

Mapped: H2-Q1 `cw-01.json` (67 points per metric, newest first; sorted before use); H2-Q2 `cw-01.json` rule "other RDS metrics: no data" (results empty).

```text
VERDICT: H2 | Ruled out
summary: orders-db is not saturated and read latency did not move. CPUUtilization median 24.9% (max 26.9%) from 10:00 to 13:00, then 41.3% in the 13:10 bucket and a median of 40.6% (37.1-44.0%) from 13:15 to 15:30. ReadLatency flat at about 0.58-0.60 ms (0.52-0.67 ms) in both periods. DatabaseConnections median 42 (max 44) before and 47 (43-48) after. The CPU step starts in the 13:10 five-minute bucket, after the application-side step (13:08), and the 13:05 bucket is still at 23.9%, so the database load rose after the application began issuing more statements; it did not degrade first. Per-statement database span p95 is flat at 3.9-4.4 ms (W1-Q21). A database that was the bottleneck would show statement latency and read latency rising; neither did, and CPU peaked at 44%.
weakest_link: lock contention is not measured directly (Performance Insights disabled, Deadlocks / DiskQueueDepth / FreeableMemory returned no data); it is excluded only indirectly by the flat statement latency (Likely)

evidence:
- CPU 24.9% to 40.6% median, max 44.0%; ReadLatency 0.58 ms to 0.60 ms; connections 42 to 47 [cloudwatch AWS/RDS orders-db, H2-Q1, 10:00-15:30 UTC at 5 min] link: CloudWatch console, AWS/RDS DBInstanceIdentifier=orders-db
- No data for Deadlocks, DiskQueueDepth, FreeableMemory [cloudwatch, H2-Q2, 10:00-15:30]

timeline:
- 13:05 - CPU bucket 23.9% (baseline) - cloudwatch
- 13:10 - CPU bucket 41.3% - cloudwatch

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H2-Q1 | cloudwatch prod-read us-east-1 | get-metric-data CPUUtilization, ReadLatency, DatabaseConnections, AWS/RDS, DBInstanceIdentifier=orders-db, Period 300 | 10:00-15:30 | 3 metric requests | all three complete, 67 points each; CPU 24.9 to 40.6 median; ReadLatency flat; connections 42 to 47 link: CloudWatch console |
| H2-Q2 | cloudwatch prod-read us-east-1 | get-metric-data Deadlocks, DiskQueueDepth, FreeableMemory, same dimension, Period 300 | 10:00-15:30 | 3 metric requests | no data returned for any of the three link: CloudWatch console |

gaps:
- No lock-wait or Performance Insights data (Performance Insights disabled, PB-Q12) - lock waits excluded only through flat statement latency
- CPU credits not applicable to db.r6g (not burstable); not queried - none

untrusted_text:
- none

to_confirm_by_human:
- If lock waits remain a worry, enable Performance Insights on orders-db for future incidents (a change for a human; costs a small amount of overhead).

lesson_candidates:
- process (cloudwatch) `get-metric-data` for RDS returned timestamps newest first; sort before bucketing or comparing with the onset - H2-Q1

cost: 2 queries, 0 GB of logs, 6 CloudWatch metric requests
```

#### [evidence H3, default tier]

Falsification first: pool wait (pending_requests) and connections against the limit. The pool query W1-Q18 is already in the ledger and is reused (not repeated).

```bash
# H3-Q1 DatabaseConnections of orders-db, period 300 (1 metric request); query file raw/H3/q-conns-300.json
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/H3/q-conns-300.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json
# H3-Q2 pool, timeout and refusal lines in the last 15 minutes (selector app="orders" is unverified; the namespace stats estimate W0-Q9 of 0.048 GB covers it)
curl -sG "$GRAFANA_URL/api/datasources/proxy/uid/loki-prod/loki/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={namespace="orders", app="orders"} |~ "(?i)(pool|too many connections|timeout|refused)"' --data-urlencode "start=1792509300000000000" --data-urlencode "end=1792510200000000000" --data-urlencode "limit=100" --data-urlencode "direction=forward"
```

Mapped: H3-Q1 `cw-01.json` (the three metrics came back; only DatabaseConnections used); H3-Q2 `loki-05.json` (selector app=orders and namespace=orders), restricted to 15:15-15:30 and to lines matching the filter: no line matches.

```text
VERDICT: H3 | Ruled out
summary: No sign of pool or connection exhaustion. Pool pending_requests was 0 in every sample from 10:00 to 15:30 (reused W1-Q18), pool used rose from median 16 (max 19) to median 21 (max 24) with no waiters. RDS DatabaseConnections rose only from 42 to 47 (max 48) with no ceiling reached (H3-Q1). No line matching pool, too many connections, timeout or refused in the app="orders" stream from 15:15 to 15:30 (H3-Q2), but that stream is not tied to the service, so this carries little weight.
weakest_link: neither the pool's configured size nor the engine's max_connections could be read (the RDS reply carries no parameter group name, and pool size lives in the app config), so "well below the limit" is not shown; the refutation rests on pending_requests = 0, a 60-second gauge that could miss a burst shorter than a scrape (Likely for transient bursts, Ruled out for sustained exhaustion)

evidence:
- pending_requests 0 in all 166 samples, used max 24 [prometheus, W1-Q18 reused, 10:00-15:30]
- DatabaseConnections 42 to 47, max 48 [cloudwatch, H3-Q1, 10:00-15:30] link: CloudWatch console AWS/RDS orders-db
- 0 matching lines [loki, H3-Q2, 15:15-15:30]

timeline:
- 13:10 - DatabaseConnections 41 to 46 - cloudwatch

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H3-Q1 | cloudwatch prod-read | get-metric-data DatabaseConnections orders-db Period 300 | 10:00-15:30 | 1 metric request | median 42 before, 47 after, max 48 link: CloudWatch console |
| H3-Q2 | loki loki-prod `{namespace="orders", app="orders"} \|~ "(?i)(pool\|too many connections\|timeout\|refused)"` | 15:15-15:30 | est. 0.048 GB (reused W0-Q9 stats), actual 48,211,904 B | 0 matching lines (stream unverified) link: Explore loki-prod |

gaps:
- Pool size and engine max_connections unreadable - "well below the limit" not shown
- No failure or connect-timeout counter for the pool is exported (only the sampled gauges) - transient bursts not excluded

untrusted_text:
- none

to_confirm_by_human:
- Read the pool's configured maximum from the chart values and the engine's max_connections from the DB parameter group, then compare them with pool used (max 24) and DatabaseConnections (max 48).

lesson_candidates:
- process (prometheus) For pool exhaustion read pending_requests first (0 here) before chasing the engine limit; the gauge is sampled at 60 s - H3-Q1

cost: 2 queries (plus one reuse), 0.048 GB of logs, 1 CloudWatch metric request
```

#### [evidence H4, default tier]

Falsification first: CPU throttling share near zero and CPU below the limit refute H4.

```bash
# H4-Q1 CPU throttling share per pod (cAdvisor)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="orders"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="orders"}[5m]))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
# H4-Q2 CPU limit per container (kube-state-metrics)
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=max by (pod, container) (kube_pod_container_resource_limits{namespace="orders", resource="cpu"})' --data-urlencode "time=1792510200"
# H4-Q3 the Deployment's CPU requests and limits, names and quantities only
kubectl get deployment orders-api --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders -o jsonpath='{.spec.template.spec.containers[*].resources}'
```

Mapped: H4-Q1 `prom-10.json` (empty), H4-Q2 `prom-10.json` (empty), H4-Q3 `_empty.txt` (no output).

```text
VERDICT: H4 | inconclusive
summary: The data needed to test CPU throttling does not exist in the readable sources. The cAdvisor throttling ratio and the kube-state CPU limit returned empty results (the metric-name list from the profile build contains neither container_cpu_cfs_* nor kube_pod_container_resource_limits, so they are probably not scraped), and the Deployment's resources read returned no output. Only W1-Q19 exists: the three pods use 0.52-0.64 cores each, equal across pods, from 13:08; with no limit known and no pre-13:08 sample this says nothing about throttling.
weakest_link: no CPU limit and no throttling signal (inconclusive)

evidence:
- CPU per pod 0.52-0.64 cores, equal across the three pods [prometheus, W1-Q19 reused, 13:08-15:30]

timeline:
- none

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H4-Q1 | prom-prod | throttled periods / periods per pod | 12:30-15:30 | light | empty matrix: metric not exported (not zero) link: Explore prom-prod |
| H4-Q2 | prom-prod | kube_pod_container_resource_limits cpu | 15:30 | light | empty: not exported link: Explore prom-prod |
| H4-Q3 | kubectl | get deployment orders-api resources | now | free | no output |

gaps:
- Throttling and limit data unavailable - H4 can be neither supported nor refuted
- No pre-13:08 CPU sample (W1-Q19 starts at 13:08) - no baseline

untrusted_text:
- none

to_confirm_by_human:
- Read the CPU request and limit of the orders-api container from the chart values at v2.15.0 and the throttling panel in the cluster's container dashboards.

lesson_candidates:
- identifier (prometheus) container_cpu_cfs_* and kube_pod_container_resource_limits are not in the metric names of prom-prod; do not query them, read limits from the chart values - H4-Q1

cost: 3 queries, 0 GB of logs, 0 CloudWatch metric requests
```

#### [evidence H5, default tier]

Falsification first: non-database client spans at baseline p95 refute H5.

```bash
# H5-Q1 p95 of client spans that are not database spans, by span name (TraceQL metrics)
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = client && span.db.system = nil } | quantile_over_time(duration, .95) by (span:name)' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=900"
# H5-Q2/Q3 GET /orders root spans, incident and baseline hour, limit 30
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=30"
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" }' --data-urlencode "start=1792494000" --data-urlencode "end=1792497600" --data-urlencode "limit=30"
```

Mapped: H5-Q1 `tempo-08.json` (empty series), H5-Q2 `tempo-04.json` (24 traces), H5-Q3 `tempo-05.json` (24 traces; root spans only).

```text
VERDICT: H5 | inconclusive
summary: The per-downstream breakdown that would test H5 is not available. The TraceQL metrics query for non-database client spans returned no series. The two trace searches return only the root span of each request: root duration median 340 ms (128-431) in the incident hour against 110 ms (78-165) in the baseline hour, 24 traces each, which shows the slowdown but not where the time goes.
weakest_link: no timing for any non-database downstream (inconclusive)

evidence:
- Root durations: incident median 340 ms, p95 422 ms, max 431; baseline median 110 ms, p95 165 [tempo, H5-Q2 and H5-Q3, 14:30-15:30 and 11:00-12:00]

timeline:
- none

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H5-Q1 | tempo-prod | non-database client span p95 by span:name | 12:30-15:30, step 900 | heavy 1 | series [] (no data, not zero) link: Explore tempo-prod |
| H5-Q2 | tempo-prod | GET /orders root spans | 14:30-15:30 | inspected 2.41 GB | 24 traces; root only; median 340 ms link: Explore tempo-prod |
| H5-Q3 | tempo-prod | GET /orders root spans | 11:00-12:00 | inspected 2.35 GB | 24 traces; root only; median 110 ms link: Explore tempo-prod |

gaps:
- No client-span breakdown for non-database dependencies - H5 untested

untrusted_text:
- none

to_confirm_by_human:
- Name the non-database dependencies of GET /orders (the profile lists none; no trace was fetched by this worker) and ask their owners for latency over the window.

lesson_candidates:
- process (tempo) A plain `/api/search` returns only the root span (matched 1); use a structural query to get child spans - H5-Q2

cost: 3 queries, 0 GB of logs, 0 CloudWatch metric requests, Tempo inspected 4.76 GB
```
### Merge of round 1 (main session)

Verdicts applied by the main session alone. Worker query IDs renumbered to wave 4: H1-Q1..Q4 -> W4-Q1..Q4, H2-Q1..Q2 -> W4-Q5..Q6, H3-Q1..Q2 -> W4-Q7..Q8, H4-Q1..Q3 -> W4-Q9..Q11, H5-Q1..Q3 -> W4-Q12..Q14 (old IDs kept in the ledger ID cell). `untrusted_text`: none from any worker. Lesson candidates copied unchanged. Ledger updated before anything below used the results.

Escalation rules applied (at most one per hypothesis, only from the default tier):
- H1: Confirmed, and H1-Q3 itself exhibits the mechanism (12 serial SELECT order_items spans under one GET /orders inside the window), so no escalation. H1 was already on the strong tier.
- H2: Ruled out (default tier), a falsification query came back negative: no escalation.
- H3: Ruled out (default tier) on a reused pool metric plus CloudWatch: no escalation.
- H4: `inconclusive` from the default tier: escalate once to the strong tier.
- H5: `inconclusive` from the default tier: escalate once to the strong tier.

Budget after round 1: 53 of 60 counted queries; 7 left, split 3 + 3 for the two escalated workers (1 spare).

### Round 2 (wave 5): escalated workers, dispatched in one message on the stronger tier

Each gets the whole prompt, the run profile, the ledger (Query log now contains W4-Q1..W4-Q14 and the raw extracts `raw/H1/*.tsv`), the windows, PREVIOUS VERDICT = its default-tier verdict block and full query table, no lessons, no history. Rule 4: do not repeat logged queries; target the named gap.

#### [evidence H5, escalated tier]

Gap named by the previous verdict: no timing for non-database downstream spans. The ledger already holds what can answer it from a different angle, so no new query is needed: W4-Q1 and W4-Q2 (`raw/H1/tr-matched-*.tsv`: duration against descendant-span count per request) and W4-Q3 / W4-Q4 (one full trace per window).

```text
VERDICT: H5 | Ruled out
summary: A slower non-database downstream would add a roughly constant delay to every GET /orders request, whatever its statement count. The incident sample shows none: request duration = 89.8 ms + 6.05 ms per descendant span (r = 0.966, n = 24); the intercept (a request with no extra statements) is 90 ms, at or below the baseline median of 110 ms (baseline range 78-165 ms), and the smallest incident request (9 descendant spans) took 128 ms, inside the baseline range. All of the added latency is proportional to the number of database statements. In the two fetched traces the only non-database client span is GET auth-api /verify: 3.4 ms in the incident trace, 3.8 ms in the baseline trace. A constant extra delay of more than about 20 ms per request from any non-database dependency is contradicted; a smaller one cannot be excluded by a 24-trace sample.
weakest_link: auth-api's own latency distribution is not measured (two fetched traces only); the refutation rests on the regression intercept of a 24-trace sample that may not be random (Likely for delays under about 20 ms, Ruled out above that)

evidence:
- Intercept 89.8 ms against baseline median 110 ms (78-165) [tempo, W4-Q1 and W4-Q2, 14:30-15:30 and 11:00-12:00; local fit on raw/H1/tr-matched-incident.tsv]
- auth-api verify 3.4 ms (incident) and 3.8 ms (baseline) [tempo, W4-Q3 and W4-Q4]

timeline:
- none

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | ledger | reused W4-Q1, W4-Q2, W4-Q3, W4-Q4 | - | 0 | see summary |

gaps:
- No direct latency series for auth-api or any other non-database dependency - small constant delays not excluded

untrusted_text:
- none

to_confirm_by_human:
- Ask the owner of auth-api for its latency over 12:30-15:30 UTC to close the sub-20 ms case.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs, 0 CloudWatch metric requests
```

#### [evidence H4, escalated tier]

Gap named by the previous verdict: no throttling signal and no CPU limit. Those cannot be read from Prometheus or kubectl (W4-Q9 to W4-Q11 came back empty), so the worker uses the logged traces as an indirect check of whether in-process time stretched. No new query.

```text
VERDICT: H4 | inconclusive
summary: The two fetched traces and the sample fit show no sign of stretched in-process time, but the tail, where throttling would show, is not observed and the limit and throttling data do not exist. In the incident trace (W4-Q3) the gaps between consecutive spans are 1.0-1.7 ms (13 gaps) against 1.5 ms in the baseline trace (W4-Q4); the time after the last child span is 81.9 ms against 99.1 ms; the sample intercept is 90 ms against a baseline median of 110 ms. CPU is steady at 0.52-0.64 cores per pod, equal across the three pods (W1-Q19). Against that: the histogram p95 is 0.712 s (W1-Q5) while the slowest of the 24 sampled incident traces took 431 ms, so the slowest requests, which are the ones intermittent CFS throttling would hit, are not in the sample; the histogram's bucket layout is unknown and could by itself inflate an interpolated p95. H4 is neither supported nor refuted.
weakest_link: no CPU limit, no throttling series, and an unobserved tail (inconclusive)

evidence:
- In-process gaps 1.0-1.7 ms (incident) against 1.5 ms (baseline); tail after last child 81.9 ms against 99.1 ms [tempo, W4-Q3 and W4-Q4]
- Slowest sampled incident trace 431 ms against histogram p95 0.712 s [tempo W4-Q1; prometheus W1-Q5]

timeline:
- none

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | ledger | reused W1-Q19, W4-Q1, W4-Q3, W4-Q4, W4-Q9, W4-Q10, W4-Q11 | - | 0 | see summary |

gaps:
- CPU limit and throttling not readable - H4 untestable from here
- Tail of the latency distribution not sampled - a contributing tail effect (throttling, GC, noisy neighbour) cannot be excluded

untrusted_text:
- none

to_confirm_by_human:
- Read the container CPU request and limit from the chart values at v2.15.0, and the throttling panel for the three pods between 13:00 and 15:30 UTC.
- Read the latency histogram's bucket boundaries around 0.5 s and 1 s to see how much of the 0.712 s p95 is interpolation.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs, 0 CloudWatch metric requests
```

### Merge of round 2 (main session)

- H5 escalated verdict `Ruled out` recorded as `Ruled out`, basis stated as sample-based (the regression of W4-Q1 plus two traces), weakest link named; escalated from `default` so the Model column reads `default→strong`.
- H4 escalated verdict `inconclusive` stays open with its gaps; Model `default→strong`; it is reported as an open hypothesis, label `Assumed` (nothing supports it, one weak indirect indication against it, sources unreadable).
- No new queries in round 2; counted budget stays 53 of 60. Raw extracts exist under `raw/H1/` only (the simulation does not save other raw pulls).
- Stop-early rule: H1 is `Confirmed` but H4 is not `Ruled out`, so the early-stop condition is not met; all workers had already finished anyway.

## Phase 5 - conclude

Ledger finalised before the report (hypothesis labels, W4 rows, gaps G14-G19, timeline row for the RDS CPU step, lesson candidates, Memory). Causal chain, each link with its label and queries:
1. Trigger: Helm revision 24 at 13:04:50 (ReplicaSet about 13:05) rolled v2.15.0, which contains PR #2211 (commit a4c1e9b) replacing one joined query with a per-order `list_items` loop in `orders_api/handlers/list_orders.py`. Confirmed (W1-Q4, W1-Q1, W1-Q2, W2-Q2, W3-Q1, W3-Q2).
2. Mechanism: each GET /orders now issues one `SELECT order_items` per order (up to 50): descendant spans p50 41 against 3 (n=24 each), 12 serial item selects in the fetched incident trace against one joined select in the baseline trace; database operations x10.4 at the same sample; per-statement time unchanged. Confirmed (W4-Q1 to W4-Q4, W1-Q16, W1-Q21).
3. Symptom: GET /orders p50 0.092 -> 0.311 s, p95 0.181 -> 0.712 s from 13:08; duration = 90 ms + 6.05 ms per statement (r = 0.966), 35.8 extra spans x 6.05 ms = 217 ms against +219 ms observed at p50; other routes flat. Confirmed (W1-Q5 to W1-Q9, W4-Q1).
Cause label: Confirmed (change = diff + Helm; mechanism = in-window trace; timing = 13:04:50 -> first bad sample 13:08, last good 13:06, -7d flat). Weakest link named in the TL;DR: mechanism to symptom rests on one 24-trace sample per window, with metrics agreeing on the step (Confirmed). Not reproduced and carried as open items rather than links: the absolute p95 (0.712 s against a slowest sampled trace of 431 ms) and 64 against 36 extra operations per call.
Why it became an incident (Deep): the rollout reached all 3 pods and scaled the old ReplicaSet to 0, so there was no mixed fleet to compare (Confirmed, W1-Q2); no deploy marker in Grafana (W1-Q24); the database had headroom (CPU 41%, W4-Q5) so the extra work showed up as latency only, with no errors or saturation alarm to stop the rollout (Assumed: no alert other than the p95 alert is known); when the alert first fired is unknown (alert history unreadable, G2).
Several hypotheses stand? H1 Confirmed; H4 open as an untested possible tail contributor; the rest ruled out.
History: similar past incident 2026-08-14-orders-api (pool exhaustion); not a repeat of this cause.
Report: `report.md`, saved separately. Sections of Deep mode all present; Gaps table kept; cost line last.

### TL;DR printed to the operator (verbatim)

```text
TL;DR (Deep) - run orders-api-prod-20261020-1530
Cause: release v2.15.0 (PR #2211, "load items per order in list handler") made GET /orders run one database statement per order, up to 50, instead of one joined statement. About 36 extra statements per request at roughly 6 ms each. Label: Confirmed.
Weakest link: mechanism to symptom rests on one 24-trace sample per window (duration = 90 ms + 6.05 ms per statement, r = 0.97); the metrics agree at the same 13:08 sample (database operations x10.4, p50 x3.4, call rate flat). Confirmed. Two numbers are not reproduced and are carried as open items, not as links: the absolute p95 (0.712 s, above the slowest sampled trace, 431 ms) and 64 against 36 extra operations per call.
Impact: GET /orders p95 0.18 s to 0.71 s (about 3.9x) and p50 0.09 s to 0.31 s from 13:08 UTC (23:08 Brisbane), all 3 replicas, ongoing at 15:30 UTC. Other routes and checkout (POST /orders) are flat. Error rate not measured.
Severity: SEV2 (suggested) because one core-flow endpoint is significantly degraded while the rest of the service is healthy. The incident owner decides.
Pattern: unclassified (the alert's history is unreadable and the 14-day pull returned 3 of 336 points). Assumed.
Recommended action: a human should consider restoring a single-query read path for the order list, either by rolling back to v2.14.0 or by a fix that loads the items of the whole page in one query, after checking it with pre-flight. A rollback also drops the other two changes in v2.15.0 (shipment ETA on order detail, structlog bump). This run changed nothing.
Similar past incidents: 2026-08-14-orders-api (same service and symptom words, but a connection-pool cause; this run's pool metrics show no waiters, so this is not a repeat).
Still standing: H4 (CPU limits or throttling on the new pods) is open as an untested possible contributor to the tail; database saturation, pool exhaustion and a slow non-database dependency are ruled out.
Report: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/report.md
Open items need your input.
Cost: 53 queries · 0.096 GB of logs · 7 CloudWatch metric requests · Tempo inspected about 16.2 GB · negligible metered charges.
```

## Phase 6 - record (proposed diff shown after the output; nothing written before the reply)

Proposed diff message (verbatim):

```text
Proposed record. Nothing is written until you reply; accept, edit or skip each item.

1. NEW .culiops/sre-investigate/incidents/2026-10-20-orders-api.md
---
id: 2026-10-20-orders-api-prod-n-plus-one-list
date: 2026-10-20
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-20T12:30:00Z/2026-10-20T15:30:00Z
symptoms: [latency]
cause_category: deploy
cause: release v2.15.0 (PR #2211) loads order items with one query per order in GET /orders (N+1)
deps: [orders-db]
label: Confirmed
mode: deep
time_to_cause_min: 13
run: runs/orders-api-prod-20261020-1530
---
# orders-api GET /orders slow after v2.15.0
What happened: from 13:08 UTC GET /orders p95 rose from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) on all 3 replicas, about 3 minutes after Helm revision 24 rolled v2.15.0. Other routes were flat. Ongoing at 15:30 UTC.
Causal chain: trigger = PR #2211 replaced one joined query with a per-order list_items loop (Confirmed); mechanism = up to 50 serial SELECT order_items per request, descendant spans p50 41 against 3, database operations x10.4, each statement still about 4 ms (Confirmed); symptom = duration about 90 ms + 6 ms per statement, r = 0.97 (Confirmed).
What found it: per-route p95 isolating GET /orders, then database operations per second stepping at the same sample while the call rate was flat, then the structural trace search and one trace per window.
What did not help: the database span p95 being flat (it looked like the database was fine; the statement count was the signal); alert history and the 14-day pull (unreadable); Kubernetes events (expired); the Loki stream app="orders" (not tied to the service); a past pool-exhaustion incident (08-14), checked and not the cause.
Follow-ups raised: restore a single-query read path for the list; N+1 statement-count test; progressive rollout with a per-route latency gate; export CPU limits and throttling; keep traces of the slowest requests; deploy markers in Grafana.

2. NEW .culiops/sre-investigate/lessons.md (10 lines, each backed by a query of this run)
- type: process | service: any | source: aws | statement: iam simulate-principal-policy can return rows that do not match the requested actions (here 3 requested actions had no row and 3 unrequested rows came back); compare returned action names with the request before reading "none allowed" | run: orders-api-prod-20261020-1530 | query_id: W0-Q3 | re-verify: no
- type: process | service: orders-api | source: tempo | statement: a bare resource.service.name = "orders-api" search for the last hour returned 0 traces although the name is valid; check the name with a span-filtered query before marking it wrong | run: orders-api-prod-20261020-1530 | query_id: W1-Q21 | re-verify: no
- type: process | service: any | source: prometheus | statement: an offset 7d call-rate query returned current-day timestamps; check the timestamps of an offset reply before using it as a baseline | run: orders-api-prod-20261020-1530 | query_id: W1-Q15 | re-verify: no
- type: process | service: any | source: kubectl | statement: Kubernetes events were gone for a rollout 145 minutes old; read events in the first minutes of a run | run: orders-api-prod-20261020-1530 | query_id: W1-Q3 | re-verify: no
- type: process | service: any | source: tempo | statement: in structural TraceQL searches matched counts every descendant span, including non-database client spans (one constant auth-api call per request here); subtract the constant before reading it as statements per request | run: orders-api-prod-20261020-1530 | query_id: W4-Q3 | re-verify: no
- type: process | service: any | source: cloudwatch | statement: RDS get-metric-data returned timestamps newest first; sort before bucketing or comparing with the onset | run: orders-api-prod-20261020-1530 | query_id: W4-Q5 | re-verify: no
- type: identifier | service: orders-api | source: prometheus | statement: container_cpu_cfs_* and kube_pod_container_resource_limits are not in the metric names of prom-prod; read CPU limits from the chart values instead | run: orders-api-prod-20261020-1530 | query_id: W4-Q9 | re-verify: no
- type: process | service: any | source: tempo | statement: a plain /api/search returns only the root span (matched 1); use a structural query to get child spans | run: orders-api-prod-20261020-1530 | query_id: W4-Q13 | re-verify: no
- type: process | service: orders-api | source: prometheus | statement: for pool exhaustion read db_client_connections_pending_requests first (0 here); it is a 60 s sampled gauge, so a short burst can be missed | run: orders-api-prod-20261020-1530 | query_id: W1-Q18 | re-verify: no
- type: identifier | service: orders-api | source: loki | statement: loki-prod stream {namespace="orders", app="orders", container="api"} carries GET /orders request lines but has no pod label and is not tied to the orders-api pods; app="orders" stays unverified | run: orders-api-prod-20261020-1530 | query_id: W0-Q9 | re-verify: yes
No confirm, re-verify, contradict or drop updates (no lessons existed). Lessons 1, 4, 5 and 6 may hold beyond this estate; I note them as candidates for the skill itself, to be proposed later in a normal session, not now.

3. NEW .culiops/sre-investigate/profiles/orders-api-prod.md, created from this run's profile.md (full file: runs/orders-api-prod-20261020-1530/profile.md). Verified this run: Prometheus label service="orders-api" and routes, Tempo service name orders-api, Deployment/ReplicaSets, Helm release and chart 4.2.0, RDS orders-db, image-tag-to-git-tag rule (v<semver>), pool label orders-db. Kept (unverified): Loki app="orders"/container api, default branch, IaC or values repo, services/ingress/HPA, load balancing, error tracker, SLO. Added: dependency auth-api (client span seen in traces), baseline notes (GET /orders p95 about 0.18 s, p50 about 0.09 s, about 56 req/s, database operations about 380 /s, pool used 14-19, orders-db CPU about 25%), bare Tempo search note under stale identifiers.
```

### Operator line 4 (cue: the proposed record diff)

`Yes, write them.` Received after the diff. All three items accepted as shown.

### Files written after the reply (under `out/`, same layout as the output root)

- `out/incidents/2026-10-20-orders-api.md`
- `out/lessons.md`
- `out/profiles/orders-api-prod.md`

## Summary of the run

- Phases executed: 0 (access, mode, intake, wave 0), Build profile (helper, cheapest tier), 1 (scope, impact, severity), 2 (change correlation, checkpoint #1), 3 (hypotheses, history lookup after ranking, checkpoint #2), 4 (five round-1 workers, two escalations), 5 (conclude), 6 (record).
- Command counts by id: W0 9, PB 14, W1 24, W2 11, W3 2, W4 14 (worker queries), round 2 none new. Counted against the Deep budget: 53 of 60 (counting interpretation recorded in the ledger header).
- World files mapped and read: environment.md, ls-01, _empty, sts-01, iam-01, iam-02, k8s-01..07, env-01, prom-01..14 (prom-10 for all unmatched PromQL), tempo-01..10 (tempo-04/05 plain searches, tempo-08 unmatched TraceQL metrics), loki-01..06, rds-01, cw-01, git-01..03, helm-01, ls-02, incidents/2026-08-14-orders-api.md, _default, repo/orders_api/repository.py and handlers/list_orders.py.
- World files not opened: gh-01.json, loki-07..13, incidents/2026-09-30-catalog-api.md (the grep did not match it).
- Process slips (kept visible): an unmapped ls over world/incidents and over repo/orders_api, and a find over repo/orders_api/handlers (names only; no incident file opened before the mapped cat in Phase 3; the names were not used); loki-05 and loki-06 opened in one read before the probe ran (only loki-06 content for the probe window was used); local python3 -I summaries of world series (equivalent to the jq summaries in the playbooks); one shell heredoc with unquoted backticks failed to write and was stopped, no state was changed.
- Not done on purpose: no Logs Insights query, no raw log lines beyond the 15-minute probe and the filtered Loki query, no kubectl exec/port-forward or request to the service, no fetch/pull/checkout in the clone, no agentbox-env call (command -v failed, nothing said about Culibox).
- Report: saved separately.

## Files written (all under out/, mirroring the output root)

- out/runs/orders-api-prod-20261020-1530/ledger.md (written after wave 1, updated after waves 2/3, Phase 3 and the round-1 merge)
- out/runs/orders-api-prod-20261020-1530/profile.md
- out/runs/orders-api-prod-20261020-1530/raw/H1/tr-matched-incident.tsv, raw/H1/tr-matched-baseline.tsv, raw/H1/README.txt (empty dirs raw/H2 to raw/H5 and raw/helper; no other raw pulls saved in this simulation)
- out/incidents/2026-10-20-orders-api.md, out/lessons.md, out/profiles/orders-api-prod.md (after "Yes, write them.")
- out/run-log.md (this file)
- report.md: saved separately.
- Not written: environment.md (already exists).
