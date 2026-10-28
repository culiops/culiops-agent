# Run log: sre-investigate, case-e (orders-api prod, GET /orders slow)

Run directory: `orders-api-prod-20261020-1530`
Simulation conventions used in this log:
- Output root `.culiops/sre-investigate/` is mapped to `out/` (same relative layout). The world files `environment.md` and `incidents/` stand for the files already present under the real root.
- `date -u +%H:%M:%S` has no row in `world/INDEX.md`, so it printed nothing (rule 7). Wall-clock times of waves are therefore unknown. "Now" is taken as 15:30 UTC on 2026-10-20 (the newest point in every telemetry reply, and 145 min after the ReplicaSet creation).
- `git rev-parse --show-toplevel` and the other text commands without a row also printed nothing.
- Query-log counting: only data-backend queries (Prometheus, Loki, Tempo, Grafana, CloudWatch metrics) count against `budgets.deep` (environment.md has none, so the template defaults 60 queries / 10 GB / 500 metric requests apply). IAM, kubectl, helm, git and file reads are logged but not counted.
- Evidence workers and the profile helper were simulated inline. A worker read only: environment.md, the playbooks, the run's profile.md, and the ledger's Windows, Query log and Gaps sections plus its own hypothesis row.
- Operator lines are quoted exactly as scripted, at the moment their cue happened.

## Operator line 1 (opening request)

> GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing. Deep mode please, I want this one written up properly.

## Phase 0, steps 1-6: output root, environment, mode, run directory, problem statement, window

Read before querying: SKILL.md, access/standalone.md, environment.template.md, templates (ledger, report, profile, incident, lesson), agents (evidence, helper), playbooks metrics, changes, traces, logs. (waf, errors, external, infra-state, other-backends were not needed: no WAF/403 symptom, no error tracker named, no ticket named, no infra drift question, no Datadog/NR/Elastic.)

Setup reads (printed in full, then run):

```bash
git rev-parse --show-toplevel
git check-ignore -q .culiops/sre-investigate
echo "${CULIOPS_HOME:+set}"
ls .culiops/sre-investigate
cat .culiops/sre-investigate/environment.md
command -v agentbox-env
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W0-Q1 | `git rev-parse --show-toplevel` | `_empty.txt` | nothing printed; case directory used as repo root |
| W0-Q2 | `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` | no output, exit 0 = ignored |
| (none) | `echo "${CULIOPS_HOME:+set}"` | `_empty.txt` | nothing: `CULIOPS_HOME` unset, so the output root is `.culiops/sre-investigate/` |
| W0-Q3 | `ls .culiops/sre-investigate` | `ls-01.txt` | `environment.md`, `incidents` (no `profiles/`, no `lessons.md`) |
| W0-Q4 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone Australia/Brisbane (UTC+10); account 111122223333 profile `prod-read` us-east-1; context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders`; Prometheus `prom-prod`, Loki `loki-prod`, Tempo `tempo-prod` via Grafana proxy `https://grafana.example.com`, token env `GRAFANA_SERVICE_ACCOUNT_TOKEN`; CloudWatch RDS via `prod-read`; repo example-org/orders-api, clone `~/src/orders-api`; budgets: only "Loki: ask before > 20 GB"; core flows `POST /orders`, `GET /orders`; default severity scale |
| W0-Q5 | `command -v agentbox-env` | `_empty.txt` | exit 1: Culibox absent, so nothing is said about Culibox |

Note on the incident listing: while preparing this simulation I also listed the file names in `world/incidents/` (`2026-08-14-orders-api.md`, `2026-09-30-catalog-api.md`). Only the names were seen; no incident content was read and none of it was used until Phase 3 after the ranked list existed.

Mode decision: Deep. The request says "Deep mode please, I want this one written up properly" and the symptom is ongoing; the operator's explicit request wins over the "ongoing means Fast" default.

Run directory created at `.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/` (written under `out/runs/orders-api-prod-20261020-1530/`), ledger copied from the template, `RUN=<run directory>/raw`.

Window rule applied: rule 1 (the time carries an explicit zone, "UTC"), no clock time given, so the anchor is an assumption.

### Message to operator 1 (verbatim)

```text
sre-investigate: Deep mode, because you asked for it ("Deep mode please, I want this one written up properly"). The alert is still firing, so I will stop at two checkpoints for you (after the change list, and after the ranked hypotheses) and send one evidence worker per hypothesis.

Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is not set). Everything this run writes goes there. It is local and is never committed. git already ignores .culiops/, so I am not touching .gitignore.

Window: "early this afternoon UTC" carries an explicit zone, so I use it as UTC. You gave no clock time, so I assume the anchor is 13:00 UTC and look from 30 minutes before it to now:
  incident            2026-10-20 12:30 to 15:30 UTC  (22:30 to 01:30 on 10-21, Australia/Brisbane, UTC+10)
  previous baseline   2026-10-20 09:30 to 12:30 UTC
  same window -7d     2026-10-13 12:30 to 15:30 UTC
If the real start was earlier or later than that I will re-anchor on the onset the metrics show.
Assumption to check: "today" is 2026-10-20 (the date every telemetry reply carries; my clock call printed nothing).
```

## Phase 0, step 7: wave 0 (access and intake)

Printed in full, then run. Ledger Access and Gaps written afterwards (see "Files written").

```bash
# call A
date -u +%H:%M:%S
aws sts get-caller-identity --profile prod-read
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

# call B
kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl config current-context
kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders

# call C
[ -n "${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}" ] && echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: set" || echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: unset"

# call D  (trigger is a Prometheus/Grafana alert whose name was not given: look for any firing alert in the service namespace)
curl -sG "https://grafana.example.com/api/datasources/proxy/uid/prom-prod/api/v1/query_range" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=max_over_time(ALERTS{alertstate="firing", namespace="orders"}[1h])' \
  --data-urlencode "start=2026-10-06T15:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" \
  --data-urlencode "step=3600"
```

Stored profile and lessons: `ls` (W0-Q3) shows neither exists, so nothing to copy and no lessons to load. No error-tracker project and no ticket named. No WAF symptom. No CloudWatch alarm is the trigger, so no alarm history or sibling alarms.

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W0-Q6 | `aws sts get-caller-identity --profile prod-read` | `sts-01.json` | Account 111122223333 (= environment.md), assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded) |
| W0-Q7 | `aws iam get-role ...` | `iam-01.json` | path `/aws-reserved/sso.amazonaws.com/`, role ARN resolved |
| W0-Q8 | `aws iam simulate-principal-policy ...` | `iam-02.json` | 10 rows, all `implicitDeny`, but only 7 are on the fixed list; ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack have no row (gap); rows for ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy are not on the fixed list and are ignored |
| W0-Q9 | `kubectl auth whoami` | `k8s-02.txt` | assumed role ReadOnly, groups `eks-readonly`, `system:authenticated` |
| W0-Q10 | `kubectl config current-context` | `k8s-01.txt` | the environment.md context |
| W0-Q11 | `kubectl auth can-i --list` | `k8s-03.txt` | `selfsubjectreviews`, `selfsubjectaccessreviews`, `selfsubjectrulesreviews` with `[create]` only (excluded); `*.*` `[get list watch]`; non-resource URLs `get` |
| W0-Q12 | token presence | `env-01.txt` | `x` = `GRAFANA_SERVICE_ACCOUNT_TOKEN` set |
| W0-Q13 | Prometheus `ALERTS` 14 d | `prom-10.json` | empty matrix |

Gaps recorded: alert history empty; 3 write-check rows missing.

### Message to operator 2 (verbatim, after wave 0)

```text
Access results (wave 0):
- prod-read, account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b.
  Write check, prod-read: 7 of the 10 fixed write actions were evaluated and all came back implicitDeny (none allowed). The other 3 (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no row, so that part is a gap and I will not call this "read-only confirmed". Even for the 7 it is not a proof: resource-scoped writes are not covered.
- Kubernetes context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace orders: no write verbs in orders (only the self-review create rows, which change nothing).
- GRAFANA_SERVICE_ACCOUNT_TOKEN: set (Prometheus, Loki and Tempo go through the Grafana proxy).
- Gap: you did not name the p95 alert and my search for a firing alert in namespace orders (14 days) came back empty, so I have no alert history. I will classify recurrence from the metrics and say how weak that is.
- First run for orders-api: there is no stored profile and no lessons file. I am building the profile now with a helper (cheapest model) and will carry on without waiting.
```

## Build profile (helper TASK: PROFILE, cheapest tier, 1 wave)

Dispatch: `TASK: PROFILE`, service orders-api, environment prod, identifier lessons: none. Simulated inline as `[helper PROFILE, cheapest tier]`. While it ran, the main session had no identifier-free change queries to start that were not already in wave 1 (no IaC repo configured; cluster listings are the helper's), so it started nothing else.

```bash
GR=https://grafana.example.com/api/datasources/proxy/uid
curl -sG "$GR/loki-prod/loki/api/v1/labels" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600000000000" --data-urlencode "end=1792510200000000000"
curl -sG "$GR/loki-prod/loki/api/v1/label/app/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600000000000" --data-urlencode "end=1792510200000000000"
curl -sG "$GR/loki-prod/loki/api/v1/label/namespace/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600000000000" --data-urlencode "end=1792510200000000000"
curl -sG "$GR/loki-prod/loki/api/v1/label/container/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600000000000" --data-urlencode "end=1792510200000000000"
curl -sG "$GR/prom-prod/api/v1/label/__name__/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=2026-10-20T14:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z"
curl -sG "$GR/tempo-prod/api/search/tags" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600" --data-urlencode "end=1792510200"
kubectl get pods -n orders --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl get deployments,services,ingresses,hpa -n orders --context arn:aws:eks:us-east-1:111122223333:cluster/prod
aws rds describe-db-instances --profile prod-read --region us-east-1 --db-instance-identifier orders-db --output json
curl -sG "https://grafana.example.com/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=orders-api"
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W0-Q14 | Loki `labels` | `loki-01.json` | `app`, `container`, `namespace`, `stream` |
| W0-Q15 | Loki `label/app/values` | `loki-02.json` | catalog-api, notify-worker, orders, orders-reconcile, payments-worker |
| W0-Q16 | Loki `label/namespace/values` | `loki-03.json` | catalog, notify, orders, payments |
| W0-Q17 | Loki `label/container/values` | `loki-04.json` | api, worker |
| W0-Q18 | Prometheus `label/__name__/values` | `prom-09.json` | `http_server_request_duration_seconds_{bucket,count,sum}`, `db_client_operation_duration_seconds_{bucket,count,sum}`, `db_client_connections_usage`, `db_client_connections_pending_requests`, `container_cpu_usage_seconds_total`, `kube_deployment_status_replicas`, `up` (no throttling or memory metric names listed) |
| W0-Q19 | Tempo `search/tags` | `tempo-06.json` | resource: k8s.namespace.name, k8s.pod.name, service.name, service.version; span: db.statement, db.system, http.request.method, http.response.status_code, http.route, server.address |
| W0-Q20 | `kubectl get pods` | `k8s-04.txt` | 3 pods `orders-api-7c9b6d8f5d-{4kq2m,9vx7t,tz5wp}`, Running, 0 restarts, age 145m/144m/144m |
| W0-Q21 | `kubectl get deployments,services,ingresses,hpa` | `_empty.txt` | no output (helper: recorded as unread, not as "none") |
| W0-Q22 | `aws rds describe-db-instances` | `rds-01.json` | `orders-db`, postgres 16.6, db.r6g.2xlarge, Multi-AZ, Performance Insights off, available |
| W0-Q23 | Grafana dashboard search | `_default.txt` | `{}`: none found |

Helper result applied by the main session: written to the run's `profile.md` with all marks kept. Tie rule re-applied: the Loki `app` value `orders` differs from the service name `orders-api`, and the helper ran only label listings (no stream query), so the log label stays `(unverified)`. The Tempo service name (user-supplied `orders-api`) and the Prometheus `service`/`route` label values were not seen in any discovery reply (the helper listed metric names and tag names only), so they are `(unverified)` until a query returns data. The helper's "Queries" list is the W0-Q14..Q23 rows above.

Log probe (first run on a label-based backend: run right after the profile build, on a discovered label value `namespace="orders"`):

```bash
curl -sG "https://grafana.example.com/api/datasources/proxy/uid/loki-prod/loki/api/v1/index/stats" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query={namespace="orders"}' \
  --data-urlencode "start=1792509300000000000" --data-urlencode "end=1792510200000000000"
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W0-Q24 | Loki `index/stats` `{namespace="orders"}` 15:15-15:30 | `_default.txt` | `{}`: no streams/bytes figures; size cannot be estimated (gap, lesson candidate). Consequence: every Loki query in this run stays inside the window caps and one stream |

### Message to operator 3 (verbatim, profile shown, continue without waiting)

```text
Profile built (working copy .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/profile.md; the stored profile changes only after you reply in the last step):
- orders-api, prod, EKS cluster prod, namespace orders, 3 pods (orders-api-7c9b6d8f5d-4kq2m, -9vx7t, -tz5wp), all Running, 0 restarts, about 145 minutes old.
- Metrics: http_server_request_duration_seconds_* and db_client_* with service="orders-api" (label values not yet seen in a reply: unverified until the first query returns).
- Traces: Tempo service name orders-api (unverified until a query returns it).
- Logs: Loki has namespace=orders, container=api, app="orders". That app value is not the service name, so I mark it (unverified) and will not treat it as orders-api's own log until a query ties it (a shared pod name or a trace ID).
- Database: RDS PostgreSQL orders-db (db.r6g.2xlarge, Multi-AZ, Performance Insights off).
- Not found: dashboards, HPA/ingress listing (empty output, not read as "none"), error tracker, IaC repo (none in environment.md).
- Loki gave no size estimate (stats call returned an empty object), so log queries will stay narrow.
Tell me if any of that is wrong; I am carrying on with the first metric wave.
```

## Phase 1: wave 1 (scope, impact, signals, change events, recurrence)

Wave 1 exceeds ten queries on purpose (stated in the ledger): its fixed legs are the siblings/golden signals in three windows, the latency extras (p50/p90/p95/p99, per-endpoint p95 and call rate, slow-downstream), the 14 d recurrence pull, saturation, and the change events (rollout history, ReplicaSets, events, helm history). Calls of one kind are chained: 6 shell calls, 21 queries. No Logs Insights is used. No heavy log query is in flight (no Loki query in this wave). Core-flow counters: environment.md lists the flows but no counter, so there is nothing to compare for step 5; the per-endpoint call rate stands in. The availability cross-check is skipped (errors are not the symptom).

Printed in full, then run:

```bash
# call A: change events (short-lived evidence first)
date -u +%H:%M:%S
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders rollout history deployment/orders-api
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get rs --sort-by=.metadata.creationTimestamp
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get events --sort-by=.lastTimestamp
helm history orders-api --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders --max 10

# call B: latency of GET /orders, incident+previous in one range, then the -7d range
PROM=https://grafana.example.com/api/datasources/proxy/uid/prom-prod
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p95-orders.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m] offset 7d)))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p95-orders-7d.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p50-orders.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m] offset 7d)))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p50-orders-7d.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.9, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p90-orders.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-p99-orders.json"

# call C: per endpoint, three windows (instant at the end of each window), and call rate
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))' --data-urlencode "time=2026-10-20T15:30:00Z" > "$RUN/m-ep-p95-incident.json"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))' --data-urlencode "time=2026-10-20T12:30:00Z" > "$RUN/m-ep-p95-previous.json"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m] offset 7d)))' --data-urlencode "time=2026-10-20T15:30:00Z" > "$RUN/m-ep-p95-7d.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (route, method) (rate(http_server_request_duration_seconds_count{service="orders-api"}[5m]))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-ep-rate.json"

# call D: dependency and saturation, and the 14-day recurrence pull (request volume; see note)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (service, db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-db-rate.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (service, db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m] offset 7d))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-db-rate-7d.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=db_client_connections_usage{service="orders-api"}' --data-urlencode "start=2026-10-20T09:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-pool.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[5m]))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=600" > "$RUN/m-pod-cpu.json"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(increase(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[1h]))' --data-urlencode "start=2026-10-06T15:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=3600" > "$RUN/m-recur-14d.json"

# call E: slow downstream, database spans of the service (TraceQL metrics), 15-minute step
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.db.system =~ ".+" } | quantile_over_time(duration, .95)' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=900" > "$RUN/tr-db-p95.json"

# call F: RDS metrics (3 metric requests, Period 300)
cat > "$RUN/q-rds-300.json" <<'JSON'
[ {"Id": "cpu",     "MetricStat": {"Period": 300, "Stat": "Average", "Metric": {"Namespace": "AWS/RDS", "MetricName": "CPUUtilization",      "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}},
  {"Id": "readlat", "MetricStat": {"Period": 300, "Stat": "Average", "Metric": {"Namespace": "AWS/RDS", "MetricName": "ReadLatency",         "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}},
  {"Id": "conns",   "MetricStat": {"Period": 300, "Stat": "Maximum", "Metric": {"Namespace": "AWS/RDS", "MetricName": "DatabaseConnections", "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}} ]
JSON
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/q-rds-300.json" --start-time 2026-10-20T09:30:00Z --end-time 2026-10-20T15:30:00Z --output json > "$RUN/m-rds.json"
```

Note on the recurrence pull (D, last curl): the alerting signal is a latency quantile, and a 14-day `histogram_quantile` over raw buckets is far over the 12 h `prom_quantile_range` cap and no recording rule is known, so per the metrics playbook the latency recurrence is recorded as a gap and the pull uses the volume counter (`increase` per hour, a counter, so no cap issue). It is a proxy, not the alerting signal.

Results (world file per query, key facts; all summarised in the ledger before use):

| ID | Query | World file | Key facts returned |
|---|---|---|---|
| W1-Q1 | `kubectl rollout history deployment/orders-api` | `k8s-07.txt` | revision 23 "helm upgrade orders-api (chart orders-api-4.2.0, image v2.14.0)"; revision 24 "helm upgrade orders-api (chart orders-api-4.2.0, image v2.15.0)" |
| W1-Q2 | `kubectl get rs -n orders` | `k8s-06.txt` | `orders-api-5f8d9c7b6a` 0/0/0 age 13d; `orders-api-7c9b6d8f5d` 3/3/3 age 145m (so created about 13:05 UTC) |
| W1-Q3 | `kubectl get events -n orders` | `k8s-05.txt` | "No resources found in orders namespace." Events expire after about an hour; the rollout at 13:05 is 2 h 25 min old: gap, not "no events" |
| W1-Q4 | `helm history orders-api` | `helm-01.txt` | rev 23 "Wed Oct 7 09:40:12 2026" superseded, app v2.14.0; rev 24 "Tue Oct 20 13:04:50 2026" deployed, app v2.15.0; chart `orders-api-4.2.0` in both. Helm printed no zone; read as UTC because the ReplicaSet age (145 min before 15:30 UTC = 13:05) agrees (recorded as an assumption, not taken from an offset) |
| W1-Q5 | p95 GET /orders 09:30-15:30 | `prom-01.json` | series service=orders-api, route=/orders, method=GET (labels now verified). Returned points start 10:00 (nothing for 09:30-10:00). 10:00-12:28 median 0.180 s (max 0.200); 12:30-13:06 median 0.179; last normal sample 13:06 = 0.163; first elevated sample 13:08 = 0.716; 13:08-15:30 median 0.712 (0.661-0.755, 72 points), no recovery |
| W1-Q6 | same, `offset 7d`, 12:30-15:30 | `prom-11.json` | 2026-10-13 same clock window: median 0.181 s (0.161-0.200, 91 points) |
| W1-Q7 | p50 GET /orders 09:30-15:30 | `prom-02.json` | 10:00-12:28 median 0.092 (0.080-0.100); 13:06 = 0.082; 13:08 = 0.295; 13:08-15:30 median 0.311 (0.281-0.339) |
| W1-Q8 | p50, `offset 7d` | `prom-12.json` | median 0.088 (0.080-0.100) |
| W1-Q9 | p90 | `prom-10.json` | empty matrix (unexpected: same selectors as W1-Q5, which returned data). Gap |
| W1-Q10 | p99 | `prom-10.json` | empty matrix. Gap |
| W1-Q11 | per-endpoint p95 at 15:30 | `prom-03.json` | GET /orders 0.712; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; GET /healthz 0.003 |
| W1-Q12 | per-endpoint p95 at 12:30 | `prom-04.json` | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q13 | per-endpoint p95, `offset 7d` | `prom-14.json` | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q14 | per-endpoint call rate 09:30-15:30 | `prom-07.json` | the reply holds ONE series (GET /orders); other routes absent from the reply (not read as zero). 10:00-12:28 median 56.5 req/s (52.0-60.9); 13:08-15:30 median 56.25 (52.1-60.6): no step |
| W1-Q15 | DB statements/s 09:30-15:30 | `prom-05.json` | series service=orders-api, db_system=postgresql. 10:00-12:28 median 381 /s (361-401); 13:06 = 365.5; 13:08 = 4,031; 13:08-15:30 median 3,962 /s (3,821-4,089): x10.4, same sample as the latency step |
| W1-Q16 | same, `offset 7d` | `prom-13.json` | median 379 /s (355-404) on 10-13 12:30-15:30 |
| W1-Q17 | pool `db_client_connections_usage` | `prom-06.json` | the reply carries both series for pool `orders-db`: `used` before onset median 16 (14-19), after median 21 (17-24); `pending_requests` = 0 at every point |
| W1-Q18 | pod CPU 12:30-15:30, step 600 | `prom-08.json` | points only from 13:08 (15 per pod, none before). Per pod 0.52-0.64 cores, medians 0.576 / 0.584 / 0.604; no outlier pod. No pre-onset baseline in the reply |
| W1-Q19 | volume `increase[1h]`, 14 d | `prom-07.json` | coverage: 10:00 to 15:30 on 2026-10-20 only (hourly requests 202.8k, 204.3k, 203.0k, 203.6k, 202.2k, and 107.1k for 15:00-15:30); nothing for the other 13.7 days. No excursion in the hours returned |
| W1-Q20 | TraceQL metrics p95 of DB spans | `tempo-01.json` | series `span.db.system=postgresql` (service name orders-api verified). p95 10:00-13:00 median 4.19 ms (3.9-4.36); 13:15-15:30 median 4.04 ms (3.9-4.22): flat. `inspectedBytes` 6.6 GB (Tempo, not a log scan) |
| W1-Q21 | RDS metrics (3 metric requests) | `cw-01.json` | CPUUtilization before onset median 24.9% (21.2-26.9), after median 40.8% (37.1-44.0); ReadLatency 0.6 ms before and after (0.5-0.7); DatabaseConnections max before 42 (40-44), after 47 (43-48) |

Ledger written after the wave (Query log W1-Q1..Q21, Windows, Recurrence, Impact, Timeline, Gaps) before any of it is used below. Counted queries so far: 9 (wave 0) + 17 (wave 1: 15 Prometheus, 1 Tempo, 1 CloudWatch) = 26 of 60; 3 CloudWatch metric requests of 500; log GB 0.

### Reading wave 1 (Phase 1 steps 1-9)

- Siblings: one deployment, three replicas, no region/shard/tenant members. Per-pod CPU is level across the three pods (W1-Q18). A per-pod latency split was not pulled because no pod label has been seen on the histogram; this is tested later by H1.
- Shape: a step. p50 and p95 both jump at the 13:08 sample (p95 0.163 to 0.716, p50 0.082 to 0.295) and stay there. p50 moved, so it is not a ceiling (a timeout wait would leave p50 alone); p90/p99 returned nothing, so the check rests on p50 versus p95. Only `GET /orders` moved (W1-Q11..Q13); POST /orders, GET /orders/{id}, PATCH and /healthz are within 0.003 s of both baselines. The request rate of the endpoint is flat (W1-Q14) while DB statements/s stepped x10.4 at the same sample (W1-Q15): more work per call, not more calls. Per-statement DB p95 is flat at about 4 ms (W1-Q20), so it is the number of statements, not their speed. (The playbook rule: a flat DB p95 does not clear the database; the statement count is what moved.)
- Recurrence: class `unclassified`. Reason: alarm history empty (W0-Q13), the latency 14 d pull is over the quantile cap (not run), and the proxy volume pull returned only 5.5 h (W1-Q19). What the data does say: the same clock window on 10-13 is normal (W1-Q6, W1-Q8, W1-Q13, W1-Q16) and nothing earlier on 10-20 (10:00-13:06) was elevated. This is below the bar for `sudden` (needs a 30-day alarm history). Recorded as a gap.
- Re-anchor: not needed. The true onset (13:08 UTC) is 8 minutes from the assumed 13:00 anchor and inside the window.
- Known noise: none.
- Impact source order: no SLO named; load-balancer/APM request metrics are the Prometheus histograms (W1-Q5..Q14), so impact is "request metrics against baseline".

### Message to operator 4 (verbatim, impact block, before Phase 2)

```text
Impact as of 15:30 UTC (01:30 on 10-21 local, Australia/Brisbane)
Symptom:   GET /orders is about 4 times slower: p95 0.71 s against 0.18 s, p50 0.31 s against 0.09 s (no failures reported by you; status codes not measured)
Affected:  prod, orders-api, GET /orders only (order history, a core flow in environment.md). All three pods are equally loaded. POST /orders (checkout), GET /orders/{id}, PATCH and /healthz are unchanged. Customer-facing. Error rate and share of users affected not measured.
Since:     13:08 UTC (23:08 local on 10-20), the first elevated sample; the last normal one is 13:06 · ongoing: yes, no recovery in the data up to 15:30
Severity:  SEV2 (suggested) because a core flow (order history) is significantly degraded (about 4x) and nobody reported it as down. The incident owner decides.
Basis:     request metrics against baseline (previous window and the same window 7 days earlier) · W1-Q5..Q8, W1-Q11..Q14 · Confirmed for latency; the share of affected users is Assumed (no SLO, no error or per-user data)
Third party in the path: none (the database is RDS in the same account)
```

## Phase 2: wave 2 (schedules, platform events, CloudTrail, app code at the deployed ref)

Recurrence class is `unclassified`, so no schedule is ranked ahead of the deploy; schedules are still listed (an unclassified class is not an all-clear). Wave 2 holds the slower change sources. The first falsification queries belong to the Deep-mode evidence workers (Phase 4), so none are run here. IaC history: environment.md names no IaC or chart-values repo, so there is nothing to run; recorded as a gap. The ticket behind a change is read only when a commit or PR names one: the commits name PR numbers (#2211, #2208, #2203), not tickets, so no ticket is read. The clone's remote freshness cannot be checked without `fetch` (forbidden), so it is a gap; gh is not needed because both tags are present locally.

Printed in full, then run:

```bash
# call A: schedules and managed-service events
date -u +%H:%M:%S
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'
aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text
aws rds describe-events --profile prod-read --region us-east-1 --source-type db-instance --source-identifier orders-db --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T14:08:00Z --query 'Events[].[Date, Message]' --output text

# call B: CloudTrail writes, 2 h before the onset to 15 min after, then once without the resource filter over a shorter window
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T13:23:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders')]].[EventTime, EventSource, EventName, Username, EventId]" --output text
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T12:58:00Z --end-time 2026-10-20T13:23:00Z --query "Events[].[EventTime, EventSource, EventName, EventId]" --output text

# call C: app code by ref, local clone (no pull, fetch, checkout)
git -C ~/src/orders-api tag
git -C ~/src/orders-api log --format='%h %cs %s' v2.14.0..v2.15.0
git -C ~/src/orders-api diff v2.14.0 v2.15.0
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W2-Q1 | `kubectl get cronjobs -A` | `_empty.txt` | no output: no CronJob listed |
| W2-Q2 | `aws events list-rules` | `_default.txt` | `{}`: no scheduled rules returned |
| W2-Q3 | `aws scheduler list-schedules` | `_default.txt` | `{}`: no schedules returned |
| W2-Q4 | `aws rds describe-events` (orders-db, 11:08-14:08) | `_default.txt` | `{}`: no RDS events in the window |
| W2-Q5 | CloudTrail writes 11:08-13:23, resource name contains `orders` | `_default.txt` | `{}`: none |
| W2-Q6 | CloudTrail writes 12:58-13:23, no resource filter | `_default.txt` | `{}`: none (the helm upgrade goes through the Kubernetes API, which CloudTrail does not log; so "no AWS write" is all this says) |
| W2-Q7 | `git tag` | `git-03.txt` | v2.12.0, v2.13.0, v2.13.1, v2.14.0, v2.15.0 (image tag `v2.15.0` = git tag `v2.15.0`; tag rule verified) |
| W2-Q8 | `git log v2.14.0..v2.15.0` | `git-01.txt` | `a4c1e9b 2026-10-19 orders: load items per order in list handler (#2211)`; `7be20d4 2026-10-19 orders: return shipment ETA on order detail (#2208)`; `3f9d6a1 2026-10-16 deps: bump structlog to 25.4.0 (#2203)` |
| W2-Q9 | `git diff v2.14.0 v2.15.0` | `git-02.txt` | `orders_api/handlers/list_orders.py`: `orders = repo.list_orders_with_items(customer_id, limit=limit)` replaced by `repo.list_orders(...)` plus `for order in orders: order.items = repo.list_items(order.id)`; `orders_api/handlers/order_detail.py`: adds `shipment_eta` to the detail response; `pyproject.toml`: structlog 25.3.0 to 25.4.0. Env var and config values: none in the diff |

Reading the changes:
- The only change near the onset is the Helm upgrade to v2.15.0 at 13:04:50 UTC (W1-Q4); the first elevated sample is 13:08 (W1-Q5), 3 minutes later; the previous sample (13:06) is normal. No schedule, scaling action, RDS event or AWS write fires near the onset (W2-Q1..Q6). Pods have 0 restarts (W0-Q20).
- It touches the failing path: `list_orders.py` is the `GET /orders` handler (commit a4c1e9b, PR #2211). The `order_detail.py` change affects `GET /orders/{id}`, which did not move (W1-Q11..Q13). The structlog bump is on no data path. So the deploy is a SUSPECT, not yet a cause (Phase 2 step 3): old-against-new evidence is tested in Phase 4.
- "Nobody changed anything" is not the situation: there is a change. Schedules, scaling, reclaims were checked first as the skill requires. Upstream deploys of other services and vendor status were not checked: no third party is in the path and the profile lists no upstream, so there is no status page to read.
- A config-only change inside the same chart version cannot be excluded: chart `orders-api-4.2.0` is identical in both Helm revisions and values are unreadable by design (no IaC/values repo configured).

Ledger written after the wave: Code repos row, W2-Q1..Q9, Timeline, Gaps (no IaC/values repo; clone freshness unknown; AWS replies empty objects). Counted queries: still 26 of 60 (wave 2 has no counted query).

### Message to operator 5 (verbatim): Deep checkpoint #1

```text
Checkpoint 1 of 2 (change correlation). Nothing below is a cause yet; labels come later from the evidence workers.

WINDOWS (UTC, local Australia/Brisbane beside)
  incident            2026-10-20 12:30-15:30   (22:30-01:30 on 10-21)
  previous baseline   2026-10-20 09:30-12:30   (19:30-22:30)   Prometheus data starts 10:00
  same window -7d     2026-10-13 12:30-15:30   (22:30-01:30)
  True onset 13:08 UTC (23:08 local), the first elevated sample; last normal sample 13:06. Not re-anchored (8 minutes from the 13:00 anchor).

BLAST RADIUS
  GET /orders only (order history, a core flow): p95 0.71 s against 0.18 s (x3.9), p50 0.31 s against 0.09 s (x3.4), no recovery to 15:30. POST /orders, GET /orders/{id}, PATCH and /healthz are unchanged. All three pods behave alike. Request rate on GET /orders is flat (56 req/s). DB statements per second are x10.4 from the same minute (381 to 3,962 /s); per-statement DB p95 is flat at about 4 ms; pool waits are 0; RDS CPU went 25% to 41%.
  Suggested severity SEV2. Third party in the path: none.

RECURRENCE
  unclassified. No alert history was found (alert not named, ALERTS search empty), the 14-day latency pull is over the quantile cap, and the volume proxy only came back for 5.5 hours. The same clock window a week ago was normal. This is a gap, not a finding of "first time".

CHANGES NEAR THE ONSET (all UTC)
  13:04:50  Helm upgrade orders-api to app v2.15.0 (chart orders-api-4.2.0, same chart as the previous revision 23, v2.14.0 from 10-07). ReplicaSet orders-api-7c9b6d8f5d created about 13:05, 3/3 ready, 0 restarts.
  v2.14.0..v2.15.0 contains three commits: a4c1e9b "load items per order in list handler" (#2211, changes the GET /orders handler: one extra query per order inside a loop instead of one joined query), 7be20d4 "shipment ETA on order detail" (#2208), 3f9d6a1 "bump structlog" (#2203).
  Nothing else: no CronJob, EventBridge rule or Scheduler schedule, no RDS event, no AWS write in CloudTrail near 13:08. Kubernetes events from 13:05 have expired (cannot be read).
  The deploy touches the failing path (list_orders.py), so it is a suspect. It is not yet a cause: that needs old-against-new evidence.

RUN PROFILE (working copy; confirmation requested)
  Compute: namespace orders, Deployment orders-api, 3 pods, ReplicaSet orders-api-7c9b6d8f5d. Image tag v2.15.0 = git tag v2.15.0.
  Metrics: http_server_request_duration_seconds_* (service, route, method labels verified), db_client_* (pool orders-db), container_cpu_usage_seconds_total (pod label). Traces: Tempo service orders-api (verified), DB spans carry db.system=postgresql. Logs: Loki namespace=orders, container=api, app="orders" (UNVERIFIED: value differs from the service name, no tie yet).
  Data store: RDS PostgreSQL orders-db (db.r6g.2xlarge, Multi-AZ, Performance Insights off). No dashboards, HPA/ingress listing, error tracker or IaC repo found.

QUESTIONS FOR YOU
  1. Is the window right (onset 13:08 UTC, still ongoing)?
  2. Did anything change that I cannot see from here: a manual action, a feature flag or config edit that is not in the chart, a vendor or upstream problem, a data import?
Reply when ready and I will form and rank the hypotheses.
```

## Operator line 2 (answer at checkpoint #1)

> Agreed, go on.

(Cue: checkpoint #1 shown. Recorded in the ledger Assumptions: operator confirmed the window and named no unseen change.)

## Phase 3: hypotheses

Inputs: impact and shape (a step on one endpoint, flat call rate, more DB statements, flat per-statement latency), the change list (one deploy, touching the failing path), the dependency map from the profile (orders-db only; the service-discovery catalog `.culiops/service-discovery/orders-api*.md` is not under the output root, so there is none to read), the catalogue in SKILL.md. Recurrence class `unclassified`, so no `sched:` entries are added. No runbook/wiki access is configured, so no `from-docs:` lead.

The run's own ranked list, written BEFORE any past incident was opened (best fit to onset, shape and blast radius first):

| Rank | ID | Statement (specific enough to be wrong) | Expected if true | Falsification query | Tier |
|---|---|---|---|---|---|
| 1 | H1 | The v2.15.0 rollout (Helm revision 24 at 13:04:50 UTC, commit a4c1e9b #2211 on the `GET /orders` handler) triggered the step: latency rose as the new revision took traffic, and the changed code sits on the failing path | no elevated sample before 13:04:50; elevation within minutes of the rollout; only the handler's endpoint moves; the diff touches that handler | onset earlier than the rollout start, or old-revision pods equally slow, refutes it: first-elevated-sample time against the Helm time, plus a per-pod or per-revision split of `GET /orders` p95 around 12:50-13:20 | default |
| 2 | H2 | `GET /orders` now makes many more database statements per request (N+1: one `order_items` query per order), each about as fast as before, and that accounts for the added latency | descendant/DB spans per `GET /orders` request up sharply against the pre-deploy window, per-statement duration unchanged, request duration growing with the span count | spans per request, incident window against the baseline window, at least 20 traces each; equal counts refute it | default |
| 3 | H3 | orders-db became slower per statement (CPU saturation, locks, I/O), which slows every statement `GET /orders` issues | per-statement DB latency up, DB CPU high, lock waits or queue depth up, at the onset | per-statement DB latency and DB CPU/lock/queue metrics at baseline refute it | strong (RDS CPU rose 25% to 41% while ReadLatency and span p95 stayed flat: conflicting signals, three series to correlate) |
| 4 | H6 | A traffic spike or a few heavy clients raised the load on `GET /orders` | request count on the endpoint above the previous window and above -7d | request rate against the previous window and -7d at the same level refutes it | default |
| 5 | H5 | Pod capacity: CPU limits or throttling, an HPA at max, or a drop in running replicas slowed the pods | desired or ready replicas dropped, throttling or CPU at the limit, all routes on the pods slower | ready replicas equal to desired, no throttling, and the other routes on the same pods unchanged refute it | default |
| 6 | H4 | Database connection exhaustion or a pool cap: requests wait for a connection | pool `pending_requests` above zero, `used` pinned at the pool maximum, "too many connections" or pool-wait errors | pool `pending_requests` at 0 throughout and `used` not pinned, no pool-wait errors, refute it | default |

My own wave-1 reading hints that H3, H4, H5 and H6 are contradicted (flat per-statement latency, `pending_requests` 0, other routes unchanged, flat call rate). These are hints to the workers only: Deep mode gives no hypothesis a label before its worker's verdict, and each of these still gets its own worker, citing the existing ledger rows as `reused W1-Qn` as its falsification where they already answer it.

### History lookup (only now that the ranked list exists)

```bash
ls .culiops/sre-investigate/incidents
grep -rnE '^(service|deps|symptoms):.*(orders-api|orders-db|latency|p95|GET /orders)' .culiops/sre-investigate/incidents
```

| Command | World file | Result |
|---|---|---|
| `ls .culiops/sre-investigate/incidents` | `ls-02.txt` | `2026-08-14-orders-api.md`, `2026-09-30-catalog-api.md` |
| `grep -rnE ... incidents` (front-matter lines) | `incidents/` (grep applied to both files) | `2026-08-14-orders-api.md:3:service: orders-api`; `:5:symptoms: [latency, p95, "GET /orders", "POST /orders"]`; `:7:deps: [orders-db]`. Nothing from `2026-09-30-catalog-api.md` (service catalog-api, deps search-cluster, symptoms errors, 5xx, GET /search) |

`lessons.md` does not exist (W0-Q3), so there are no `failure-mode` lines to read.

One match, so one entry. To write its statement, expected evidence and falsification query I read the matched file (`cat .culiops/sre-investigate/incidents/2026-08-14-orders-api.md`, world file `incidents/2026-08-14-orders-api.md`). Its content goes only into the entry below; nothing about it is logged in the ledger's Memory row except file name and matched fields, and the worker will get only the entry text.

| Rank | ID | Statement | Expected if true | Falsification query | Tier |
|---|---|---|---|---|---|
| 7 | from-history:2026-08-14-orders-api.md | (lead from a past incident; overlaps H4) The orders-db connection pool is exhausted, so requests queue for a connection: `pending_requests` on the pool metric stays well above zero for the window, possibly after a pool-size configuration change | `pending_requests` above zero (the past case was above 30) for the whole window; `used` pinned at the pool maximum; slowdown on every route that uses the DB | pool `pending_requests` at 0 across the incident window refutes it | default |

It starts with no label, is a lead and not evidence, and gets its own worker with only these three lines (never the incident file, its body or its label).

Dispatch plan, decided now (Deep mode, Phase 3 note on tiers; `model` is passed explicitly on every dispatch):
- Tier per worker: H1 default, H2 default, H3 stronger (started there per the dispatcher rule), H4 default, H5 default, H6 default, from-history default.
- Remaining budget split evenly across 7 workers: 34 queries left of 60, so 4 queries each (6 held back as the main session's reserve); CloudWatch metric requests: 497 left, 70 each; log GB: 10 left, 1.4 GB each; at most 3 waves each.

### Message to operator 6 (verbatim): Deep checkpoint #2

```text
Checkpoint 2 of 2 (hypotheses). Ranked by how well they fit the onset (13:08), the shape (a step on one endpoint) and the blast radius (GET /orders only). Each gets its own evidence worker and its falsification query runs first.

 1. H1  The v2.15.0 rollout (Helm revision 24, 13:04:50 UTC; commit a4c1e9b changes the GET /orders handler) triggered the step.
        Falsify: first elevated sample earlier than the rollout start, or a per-pod/per-revision split showing old pods equally slow. [default tier]
 2. H2  GET /orders now issues many more DB statements per request (one order_items query per order), each as fast as before, and that explains the added latency.
        Falsify: spans per request, incident window against the pre-deploy window (24 traces each); equal counts refute it. [default tier]
 3. H3  orders-db got slower per statement (CPU, locks, I/O).
        Falsify: per-statement DB latency and DB CPU/lock/queue metrics at baseline. [stronger tier: RDS CPU rose 25% to 41% while per-statement latency stayed flat, so the signals conflict]
 4. H6  Traffic spike or heavy clients on GET /orders.
        Falsify: request rate against the previous window and -7d. [default tier]
 5. H5  Pod capacity (CPU limits/throttling, HPA at max, fewer replicas).
        Falsify: ready replicas = desired, no throttling, other routes on the same pods unchanged. [default tier]
 6. H4  DB connection exhaustion or pool cap.
        Falsify: pool pending_requests at 0 and used not pinned, no pool-wait errors. [default tier]
 7. from-history:2026-08-14-orders-api.md  Past-incident lead (overlaps H4): the orders-db connection pool exhausted, with pending_requests elevated.
        Falsify: pending_requests at 0 across the incident window. [default tier]

My wave-1 numbers already point against H3, H4, H5, H6 and the history lead (flat per-statement latency, pool waits 0, other routes unchanged, flat request rate). That is only a hint for the workers: each still gets a worker and the labels come from their verdicts.
History lookup: one earlier orders-api incident matched on service, dependency (orders-db) and symptom words; it is entry 7. I added nothing else from history.

Budget: 26 of 60 queries used; each worker gets 4 (6 held back), at most 3 waves.
Add, drop or re-rank anything before I send the workers out.
```

## Operator line 3 (answer at checkpoint #2)

> Fine, continue.

(Cue: checkpoint #2 shown. No change to the list.)

## Phase 4: evidence workers (Deep)

All seven workers are dispatched in ONE message, each with `model` passed explicitly: H1, H2, H4, H5, H6 and from-history on the default tier, H3 on the stronger tier. Each gets the full prompt from agents/evidence.md with its own ID, statement, expected evidence and falsification query, `RUN=<run directory>/raw/<ID>`, the three UTC windows, its budget share (4 queries, 70 CloudWatch metric requests, 1.4 GB of logs, 3 waves), the run's `profile.md` (never the stored one), `LESSONS: none` (no lessons file) and `PREVIOUS VERDICT: none`. The from-history worker receives only its three lines. The ledger snapshot every worker reads is the one after Phase 3 (Windows, Query log W0-Q1..W2-Q9, Gaps, own row): so parallel workers cannot see each other's queries, and a rare duplicate is renumbered at merge.

Worker sections below are simulated inline. Each lists what it ran, in full, with the world file each command mapped to, then the verdict block it returns.

---

### [evidence H1, default tier]

Hypothesis H1 (trigger = v2.15.0 rollout). Falsification run first, then confirming evidence. Wave 1 of 1.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H1; mkdir -p "$RUN"
PROM=https://grafana.example.com/api/datasources/proxy/uid/prom-prod
# H1-Q1 (falsification): first elevated sample against the rollout start, split by pod
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))' --data-urlencode "start=2026-10-20T12:50:00Z" --data-urlencode "end=2026-10-20T13:20:00Z" --data-urlencode "step=120" > "$RUN/m-p95-by-pod.json"
# H1-Q2, H1-Q3: the handler and its data access at the deployed ref
git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py
git -C ~/src/orders-api show v2.15.0:orders_api/repository.py
```

| ID | World file | Result |
|---|---|---|
| H1-Q1 | `prom-01.json` (same metric and selectors as W1-Q5) | one series with labels service, route, method (no `pod` label despite `by (pod)`), values identical to W1-Q5 at every shared timestamp: 12:50 0.169, 12:52 0.179, 12:54 0.169, 12:56 0.185, 12:58 0.171, 13:00 0.190, 13:02 0.179, 13:04 0.164, 13:06 0.163, 13:08 0.716, 13:10 0.698, 13:12 0.719, 13:14 0.662, 13:16 0.748, 13:18 0.750, 13:20 0.722 |
| H1-Q2 | `repo/orders_api/handlers/list_orders.py` | lines 15-18: `orders = repo.list_orders(customer_id, limit=limit)` then `for order in orders: order.items = repo.list_items(order.id)`; limit capped at 50 (line 13) |
| H1-Q3 | `repo/orders_api/repository.py` | `list_items` (lines 44-47) runs `ITEMS_SQL` (one query per call, own pooled connection); `list_orders_with_items` (lines 38-42) is the one-round-trip join, docstring "used by the list handler up to v2.14.0" |

Verdict block returned:

```text
VERDICT: H1 | Confirmed
summary: GET /orders was normal through 13:06 (0.163 s) and elevated from 13:08 (0.716 s), 3 minutes after the Helm upgrade to v2.15.0 at 13:04:50 and 2-3 minutes after the new ReplicaSet (created about 13:05, 3/3 ready). No sample between 12:50 and 13:06 is elevated, so the first-elevated-sample-before-rollout refutation is not met. The v2.15.0 handler (list_orders.py lines 15-18) now calls repo.list_items(order.id) once per returned order, up to 50, where v2.14.0 used the one-round-trip repo.list_orders_with_items. Only the endpoint whose handler changed moved (POST /orders, GET /orders/{id}, PATCH, /healthz unchanged, W1-Q11..Q13). Service-wide DB statements/s stepped x10.4 at the same 13:08 sample while the endpoint's call rate stayed flat (W1-Q15, W1-Q14). The per-request statement count is H2's question, not part of this statement.
weakest_link: no old-versus-new latency split by pod or revision exists (the latency histogram has no pod label, H1-Q1; Kubernetes events from 13:05 have expired, W1-Q3), so "the new revision took traffic" rests on the ReplicaSet age and Helm time agreeing with the onset at 2-minute resolution, plus the image diff on the failing path; those are two of the three tie options Phase 2 accepts. (Confirmed)

evidence:
- first elevated sample 13:08 (0.716 s), last normal 13:06 (0.163 s), 12:50-13:06 all 0.163-0.190 [prom-prod, H1-Q1 and reused W1-Q5, 12:50-13:20] link: raw/H1/m-p95-by-pod.json
- Helm revision 24 (app v2.15.0) at 13:04:50; ReplicaSet orders-api-7c9b6d8f5d 3/3 ready, age 145m at 15:30; revision 23 (v2.14.0) superseded [helm, kubectl, reused W1-Q1, W1-Q2, W1-Q4]
- v2.15.0 list_orders.py lines 15-18 loop over orders calling repo.list_items(order.id); v2.14.0 called repo.list_orders_with_items [git, H1-Q2, H1-Q3, reused W2-Q9]
- other routes on the same pods unchanged at 15:30 against 12:30 and -7d [prom-prod, reused W1-Q11, W1-Q12, W1-Q13]
- DB statements/s 365.5 at 13:06, 4,031 at 13:08, endpoint call rate flat [prom-prod, reused W1-Q15, W1-Q14]

timeline:
- 13:04:50 — Helm upgrade to v2.15.0 deployed — helm (W1-Q4)
- about 13:05 — ReplicaSet orders-api-7c9b6d8f5d created — kubectl (W1-Q2)
- 13:06 — last normal p95 0.163 s — prometheus (H1-Q1)
- 13:08 — first elevated p95 0.716 s — prometheus (H1-Q1)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H1-Q1 | prom-prod | histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m]))) | 12:50-13:20, step 120 s | 1 query | one series, no pod label, identical to W1-Q5; onset 13:06 to 13:08; link: raw/H1/m-p95-by-pod.json |
| H1-Q2 | git (clone, ref v2.15.0) | show v2.15.0:orders_api/handlers/list_orders.py | n/a | free | loop with repo.list_items per order, lines 15-18; link: git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py |
| H1-Q3 | git (clone, ref v2.15.0) | show v2.15.0:orders_api/repository.py | n/a | free | list_items one query per call, lines 44-47; join variant lines 38-42; link: git -C ~/src/orders-api show v2.15.0:orders_api/repository.py |

gaps:
- No pod or revision label on the latency histogram — no direct "new pods slow, old pods fine" split; the tie rests on timing and the diff.
- Onset resolution is 120 s (rate window 5 min) against a Helm time to the second — the 13:06 to 13:08 step can place the onset anywhere in that interval.
- Helm values (config) between revisions 23 and 24 are unreadable here (no values repo, helm get values forbidden) — a config-only change in the same upgrade is not excluded by this worker.

untrusted_text:
- none

to_confirm_by_human:
- Compare the Helm values for revisions 23 and 24 (or the values files at the two refs) to rule out a configuration change in the same upgrade.
- Ask the release owner whether the rollout was a rolling update or a recreate, and when the last v2.14.0 pod stopped serving.

lesson_candidates:
- identifier (prometheus) http_server_request_duration_seconds_* carries only service, method, route: no pod or version label, so no per-pod or per-revision split from this metric — H1-Q1

cost: 1 query, 0 GB, 0 CloudWatch metric requests, 2 git reads
```

---

### [evidence H2, default tier]

Hypothesis H2 (N+1). Falsification first: spans per request, incident against baseline, at least 20 traces each; then the single traces. Wave 1 (searches) and wave 2 (two fetches by ID), within the 1 h `trace_samples` cap.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H2; mkdir -p "$RUN"
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
# wave 1: falsification, the same structural search in both windows (up to 30 traces each)
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=30" > "$RUN/tr-search-incident.json"
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }' --data-urlencode "start=1792494000" --data-urlencode "end=1792497600" --data-urlencode "limit=30" > "$RUN/tr-search-baseline.json"
# wave 2: one trace per window by ID, window padded by one hour on each side
curl -sG "$TEMPO/api/v2/traces/e3ea7a3906419b466a28541306cc5ee1" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792503000" --data-urlencode "end=1792513800" > "$RUN/tr-e3ea.json"
curl -sG "$TEMPO/api/v2/traces/65345f5f8176033524bc88af3bd43f6f" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792490400" --data-urlencode "end=1792501200" > "$RUN/tr-65345.json"
```

| ID | World file | Result |
|---|---|---|
| H2-Q1 | `tempo-02.json` | 24 traces, start times 14:30:18-15:27:50. `matched` (descendant spans of the GET /orders server span) sorted: 9, 14, 18, 22, 27, 31, 33, 36, 38, 39, 40, 41, 41, 42, 44, 47, 49, 51, 52 x6: p50 41, p95 52, max 52, min 9. `durationMs`: 128-431, median 340.5. Tempo inspected 18,342 traces / 2.41 GB |
| H2-Q2 | `tempo-03.json` | 24 traces, start times 11:00:09-11:57:36. `matched`: 2, 2, 3 x18, 4 x4: p50 3, p95 4, max 4, min 2. `durationMs`: 78-165, median 110. Tempo inspected 17,905 traces / 2.35 GB |
| H2-Q3 | `tempo-09.json` (trace e3ea…, first listed in H2-Q1) | 15 spans, root `GET /orders` 152 ms; 1 client span `GET auth-api /verify` 3.4 ms (server.address auth-api.auth.svc.cluster.local); 1 `SELECT orders` 3.05 ms; 12 `SELECT order_items` (median 3.74 ms, max 4.52 ms, total 44.8 ms); all DB spans `db.system=postgresql`; resource attributes service.name, k8s.namespace.name only |
| H2-Q4 | `tempo-10.json` (trace 65345…, first listed in H2-Q2) | 3 spans, root `GET /orders` 109 ms; `GET auth-api /verify` 3.77 ms; one `SELECT orders JOIN order_items` 3.05 ms |

Worker's own arithmetic (local, from the saved JSON): across the 24 incident traces, duration against descendant spans fits 89.8 ms + 6.05 ms per span (r = 0.97); incident fetched trace root 152 ms against 109 ms baseline (+43 ms); DB span time 47.9 ms against 3.05 ms (+44.8 ms); the root time not inside any child span is 100.8 ms (incident trace) against 102.2 ms (baseline trace).

Verdict block returned:

```text
VERDICT: H2 | Confirmed
summary: The falsification (equal span counts) fails. Per GET /orders request the server span has p50 41 and p95 52 descendant spans in 14:30-15:30 (24 traces) against p50 3 and p95 4 in the pre-deploy hour 11:00-12:00 (24 traces). Both windows meet the 20-trace minimum. The fetched incident trace shows the pattern directly: one SELECT orders followed by 12 SELECT order_items, each 3.7 ms median (4.5 ms max), where the baseline trace has one SELECT orders JOIN order_items of 3.05 ms: statements are about as fast as before (also W1-Q20: DB span p95 4.19 ms before, 4.04 ms after) but there are more of them. In that trace the extra root time (+43 ms) equals the extra DB span time (+44.8 ms), and the root time outside any child span is the same (100.8 ms against 102.2 ms). Across the 24 incident traces duration grows with span count, about 6 ms per extra span (r = 0.97), which with the baseline intercept reproduces the 110 ms to 340 ms median step. The service-wide metric agrees with the samples: DB statements/s x10.4 at the same 13:08 sample with a flat call rate (W1-Q15, W1-Q14). The matched count includes the auth-api client span that every fetched trace carries (one per trace), so DB statements per request are about the count minus one.
weakest_link: representativeness of the sample: 24 traces per window as returned by the search (not a random draw), one retrievable trace per window by ID, and the first-listed incident trace is a short one (14 descendants against a median of 41). The service-wide statement rate (W1-Q15) agrees, which is why this stays Confirmed. (Confirmed)

evidence:
- spans per request p50 41 / p95 52 / max 52 (incident, n=24) against p50 3 / p95 4 / max 4 (baseline, n=24) [tempo-prod, H2-Q1 and H2-Q2, 14:30-15:30 and 11:00-12:00] link: raw/H2/tr-search-incident.json, raw/H2/tr-search-baseline.json
- incident trace e3ea…: root 152 ms, 1 SELECT orders (3.05 ms) + 12 SELECT order_items (3.74 ms median, 4.52 ms max), 1 auth-api call (3.4 ms) [tempo-prod, H2-Q3, trace start 14:30:18] link: raw/H2/tr-e3ea.json
- baseline trace 65345…: root 109 ms, one SELECT orders JOIN order_items (3.05 ms), 1 auth-api call (3.77 ms) [tempo-prod, H2-Q4, trace start 11:00:09] link: raw/H2/tr-65345.json
- request duration against descendant spans in the incident sample: slope 6.05 ms per span, intercept 89.8 ms, r = 0.97 [local arithmetic over H2-Q1]
- DB span p95 flat 4.19 ms to 4.04 ms; statements/s x10.4; call rate flat [reused W1-Q20, W1-Q15, W1-Q14]
- the repository still has the one-round-trip join the v2.14.0 handler used [git, reused W2-Q9]

timeline:
- 11:00:09-11:57:36 — baseline sample: 2-4 descendant spans per GET /orders — tempo-prod (H2-Q2)
- 14:30:18-15:27:50 — incident sample: 9-52 descendant spans per GET /orders — tempo-prod (H2-Q1)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H2-Q1 | tempo-prod | { resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client } , limit 30 | 14:30-15:30 | 1 query, 2.41 GB inspected | 24 traces, matched p50 41 p95 52; link: raw/H2/tr-search-incident.json |
| H2-Q2 | tempo-prod | same | 11:00-12:00 | 1 query, 2.35 GB inspected | 24 traces, matched p50 3 p95 4; link: raw/H2/tr-search-baseline.json |
| H2-Q3 | tempo-prod | GET /api/v2/traces/e3ea7a3906419b466a28541306cc5ee1 (padded window) | 13:30-16:30 | 1 query | 15 spans, 12 SELECT order_items; link: raw/H2/tr-e3ea.json |
| H2-Q4 | tempo-prod | GET /api/v2/traces/65345f5f8176033524bc88af3bd43f6f (padded window) | 10:00-13:00 | 1 query | 3 spans, one JOIN; link: raw/H2/tr-65345.json |

gaps:
- Only these two traces were fetched; the budget share was 4 queries. Traces with 41-52 descendants were not retrieved, so the full time accounting is shown for a short request only (14 descendants); for the long ones the evidence is the regression across the 24 sampled durations.
- The search listing's span previews (names and durations) disagree with the fetched baseline trace (the preview lists SELECT orders and SELECT order_items spans; the fetched trace has one SELECT orders JOIN order_items), so span names come from the fetched traces and counts from `matched`.
- About 2 ms of each extra statement's 6 ms cost (6.05 ms slope against about 3.7 ms of span time) is time outside any span (pool checkout, row decoding); inferred from the slope only.
- Trace attributes carry no service.version or pod: the baseline-versus-incident comparison is by time window, not by revision.

untrusted_text:
- none

to_confirm_by_human:
- Replay GET /orders for one customer with 50 orders against a non-production copy of v2.14.0 and v2.15.0 with tracing on and compare statement counts and durations (needs an active request, which this run does not make).
- Ask the handler's owners whether the list view needs per-item status for every order, or whether the join can serve it.

lesson_candidates:
- process (tempo) Search `matched` counts all descendants of the server span (DB statements plus the auth-api client span), and span names in the search preview can differ from the by-ID trace: take counts from `matched`, names and durations from a by-ID fetch — H2-Q2
- identifier (tempo) Traces for orders-api carry resource attributes service.name and k8s.namespace.name only; no service.version or pod, so revisions cannot be separated in traces — H2-Q3
- identifier (tempo) GET /orders traces include a client span `GET auth-api /verify` (server.address auth-api.auth.svc.cluster.local) and DB spans named SELECT orders / SELECT order_items / SELECT orders JOIN order_items with db.system=postgresql — H2-Q3

cost: 4 queries, 0 GB of logs (Tempo inspected 4.76 GB), 0 CloudWatch metric requests, 0 other units
```

---

### [evidence H3, escalated tier] (started on the stronger tier by the dispatcher rule, not re-dispatched)

Hypothesis H3 (orders-db slower per statement). The falsification is per-statement latency and DB CPU/lock/queue metrics. The existing rows W1-Q20 and W1-Q21 already hold per-statement latency and CPU, so the worker cites them (`reused`) and spends one query on the metrics the ledger lacks. Wave 1 of 1.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H3; mkdir -p "$RUN"
cat > "$RUN/q-rds-extra-300.json" <<'JSON'
[ {"Id": "wlat",  "MetricStat": {"Period": 300, "Stat": "Average", "Metric": {"Namespace": "AWS/RDS", "MetricName": "WriteLatency",   "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}},
  {"Id": "dq",    "MetricStat": {"Period": 300, "Stat": "Average", "Metric": {"Namespace": "AWS/RDS", "MetricName": "DiskQueueDepth", "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}},
  {"Id": "dead",  "MetricStat": {"Period": 300, "Stat": "Sum",     "Metric": {"Namespace": "AWS/RDS", "MetricName": "Deadlocks",      "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}},
  {"Id": "fmem",  "MetricStat": {"Period": 300, "Stat": "Minimum", "Metric": {"Namespace": "AWS/RDS", "MetricName": "FreeableMemory", "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": "orders-db"}]}}} ]
JSON
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/q-rds-extra-300.json" --start-time 2026-10-20T09:30:00Z --end-time 2026-10-20T15:30:00Z --output json > "$RUN/m-rds-extra.json"
```

CPUCreditBalance is not requested: the instance class (db.r6g.2xlarge, W0-Q22) is not burstable.

| ID | World file | Result |
|---|---|---|
| H3-Q1 | `cw-01.json` (row "aws cloudwatch get-metric-data … AWS/RDS … orders-db"; the world note says other RDS metrics have no data) | the four ids WriteLatency, DiskQueueDepth, Deadlocks, FreeableMemory return no data points (empty Timestamps/Values); not read as zero |

Verdict block returned:

```text
VERDICT: H3 | Ruled out
summary: The hypothesis "each statement got slower" is contradicted. Per-statement DB p95 from traces is 4.19 ms before the onset and 4.04 ms after (W1-Q20); RDS ReadLatency is 0.6 ms before and after (W1-Q21). RDS CPU did rise, from a median of 24.9% to 40.8% (max 44.0%) and connections from 42 to 47 (max 48) (W1-Q21), but that rise coincides with the same 13:08 sample at which service-wide DB statements/s went from about 381 to about 3,962 (x10.4) (W1-Q15), and a CPU of 41% is far from saturation: it is the database doing roughly ten times the statements at the same per-statement speed, a consequence and not a cause. Pool waiters are 0 (W1-Q17). Lock waits, deadlocks, queue depth and write latency could not be read (no data; Performance Insights is off), so the lock arm is excluded indirectly: lock waits would lengthen statement durations, which are flat. This does not clear the database as the place where the extra work lands (H2).
weakest_link: lock-wait, deadlock and queue metrics are unavailable (no data returned, Performance Insights off), so that arm of the hypothesis is excluded only through the flat per-statement latency. (Assumed for that arm; the hypothesis as a whole is Ruled out by W1-Q20 and W1-Q21.)

evidence:
- per-statement DB p95 4.19 ms before, 4.04 ms after [tempo-prod, reused W1-Q20, 09:30-15:30]
- ReadLatency 0.6 ms before and after; CPU 24.9% to 40.8% (max 44.0%); connections 42 to 47 [cloudwatch, reused W1-Q21, 09:30-15:30]
- DB statements/s x10.4 at 13:08 [prometheus, reused W1-Q15]
- WriteLatency, DiskQueueDepth, Deadlocks, FreeableMemory: no data points [cloudwatch, H3-Q1, 09:30-15:30]

timeline:
- 13:08 — RDS CPU and statements/s step together (statements x10.4; CPU +16 points) — cloudwatch, prometheus (W1-Q21, W1-Q15)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H3-Q1 | cloudwatch, profile prod-read | get-metric-data AWS/RDS orders-db WriteLatency, DiskQueueDepth, Deadlocks, FreeableMemory, Period 300 | 09:30-15:30 | 4 metric requests | no data points for any of the four; link: aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/H3/q-rds-extra-300.json |

gaps:
- Lock waits, deadlocks, disk queue depth, write latency and freeable memory: no data (not zero). Performance Insights is off (W0-Q22), which would have shown waits per statement.
- The RDS CPU rise is attributed to the statement increase by timing and size only (both step at 13:08); no per-statement CPU figure exists.

untrusted_text:
- none

to_confirm_by_human:
- Enable Performance Insights (or read it in the console if it is enabled elsewhere) for orders-db to confirm that waits per statement stayed flat while load rose.
- Check the instance's max_connections and the application pool maximum to give the connection headroom a number.

lesson_candidates:
- process (cloudwatch) For `orders-db` only CPUUtilization, ReadLatency and DatabaseConnections return data; WriteLatency, DiskQueueDepth, Deadlocks and FreeableMemory returned none, and Performance Insights is off: lock evidence must come from statement latency — H3-Q1

cost: 1 query, 0 GB of logs, 4 CloudWatch metric requests, 0 other units
```

---

### [evidence H4, default tier]

Hypothesis H4 (connection exhaustion or pool cap). Falsification first: pool waiters and `used` against the pool maximum. Existing row W1-Q17 answers the waiters; one Loki raw-lines query looks for pool-wait errors. Estimate first: the stats call returned an empty object for this datasource (W0-Q24), so the query is kept to one stream, one 30-minute window (the `log_raw` cap), no line filter, limit 100, and the reply's own byte count is recorded.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H4; mkdir -p "$RUN"
curl -sG "https://grafana.example.com/api/datasources/proxy/uid/loki-prod/loki/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={namespace="orders", app="orders", container="api"}' --data-urlencode "start=1792508400000000000" --data-urlencode "end=1792510200000000000" --data-urlencode "direction=forward" --data-urlencode "limit=100" > "$RUN/logs-api-1500-1530.json"
```

| ID | World file | Result |
|---|---|---|
| H4-Q1 | `loki-05.json` (selector app=orders ∩ namespace=orders ∩ container=api) | one stream {app: orders, namespace: orders, container: api}; 8 lines between 15:18:08 and 15:19:49, all `level=info msg="request completed" method=GET path=/orders status=200 page_size=50`, duration_ms 380, 311, 286, 751, 474, 703, 576, 484 (median 479). No pod name, no trace ID, no pool or connection text in any line. Reply stats: 48,211,904 bytes processed (0.048 GB) |

Verdict block returned:

```text
VERDICT: H4 | Ruled out
summary: Pool waiters are zero at every one of the 166 points between 09:30 and 15:30, including the whole incident window (pending_requests 0), and the `used` gauge is 14-19 before the onset and 17-24 after, with no plateau (W1-Q17); a pool whose cap is hit shows waiters, and there are none. RDS connections went 42 to 47 (max 48) (W1-Q21). The 8 log lines returned for 15:00-15:30 contain no pool or connection error; that sample is far too small to count as evidence either way and its stream is unverified (below), so it is not used. The rise in `used` (median 16 to 21) is what ten times more statements per second, each taking a pooled connection, would produce at this per-statement speed (W1-Q15); it never reaches the point of queueing.
weakest_link: the pool maximum and the database connection limit are not exposed by any metric or read from configuration, so "not pinned at its cap" has no numeric ceiling; the absence of waiters is the evidence that carries it. (Confirmed for the waiters; the cap value is a gap)

evidence:
- pool `pending_requests` = 0 at all 166 points; `used` median 16 (14-19) before, 21 (17-24) after [prometheus, reused W1-Q17, 09:30-15:30]
- DatabaseConnections max 42 before, 47 after (43-48) [cloudwatch, reused W1-Q21]
- 8 request-completed lines, duration_ms 286-751, no error text [loki-prod, H4-Q1, 15:18:08-15:19:49] link: raw/H4/logs-api-1500-1530.json

timeline:
- 13:08 — pool `used` median moves from 16 to 21, `pending_requests` stays 0 — prometheus (W1-Q17)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H4-Q1 | loki-prod | {namespace="orders", app="orders", container="api"} direction=forward limit=100 | 15:00-15:30 | estimate unavailable (stats empty, W0-Q24); actual 0.048 GB | 8 lines, no pool text, no pod or trace ID in the lines; link: raw/H4/logs-api-1500-1530.json |

gaps:
- No pool-maximum metric (only `usage` and `pending_requests` exist) and no config read: no numeric headroom.
- The Loki stream app="orders" is not tied to orders-api (its lines carry no pod name or trace ID), so nothing from it is evidence about this service; the application's own pool-wait log messages (if it logs them) were not searched with a filter.

untrusted_text:
- none

to_confirm_by_human:
- Read the application's pool configuration (maximum size and wait timeout) from the chart values or the service's config at v2.15.0 and compare it with the observed `used` maximum of 24.

lesson_candidates:
- identifier (loki) Request-completed lines for `{namespace="orders", app="orders", container="api"}` carry no pod name or trace ID, so the stream cannot be tied to orders-api from its lines alone; keep it (unverified) — H4-Q1

cost: 1 query, 0.048 GB of logs, 0 CloudWatch metric requests, 0 other units
```

---

### [evidence H5, default tier]

Hypothesis H5 (pod capacity). Falsification first: replicas, HPA and throttling; most is already in the ledger (W1-Q2, W0-Q20, W1-Q11..Q13, W1-Q18). Two new reads for the HPA and for CPU throttling. Wave 1 of 1.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H5; mkdir -p "$RUN"
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get hpa
curl -sG "https://grafana.example.com/api/datasources/proxy/uid/prom-prod/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="orders", pod=~"orders-api-.*"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="orders", pod=~"orders-api-.*"}[5m]))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=600" > "$RUN/m-throttle.json"
```

| ID | World file | Result |
|---|---|---|
| H5-Q1 | `_empty.txt` | no output: HPA state unknown (not read as "no HPA") |
| H5-Q2 | `prom-10.json` | empty matrix; neither throttling metric appears in the metric-name list (W0-Q18), so they are probably not scraped: not read as "no throttling" |

Verdict block returned:

```text
VERDICT: H5 | Ruled out
summary: A pod-capacity problem (CPU limit or throttling, a drop in replicas, an HPA at its maximum) would slow every route served by these pods, and it did not. Ready replicas equal desired (3/3, orders-api-7c9b6d8f5d, W1-Q2), the pods have 0 restarts (W0-Q20), and the three pods use the same CPU (0.52-0.64 cores, medians 0.576 / 0.584 / 0.604, no outlier, W1-Q18). During the same window on the same pods POST /orders p95 is 0.142 s against 0.139 s, GET /orders/{id} 0.064 against 0.061, PATCH 0.088 against 0.091, /healthz 0.003 unchanged (W1-Q11, W1-Q12, W1-Q13); only GET /orders moved. The HPA listing printed nothing and the throttling counters returned no data, so the CPU limit, throttling and HPA arms were not read directly.
weakest_link: CPU limit, throttling and HPA state were not readable (empty output, no throttling series), so the capacity arms are excluded by the unchanged sibling routes on the same pods, not by a headroom figure. (Assumed for the direct headroom; the cross-route result is Confirmed)

evidence:
- ready 3/3 = desired, 0 restarts [kubectl, reused W1-Q2, W0-Q20]
- other routes on the same pods unchanged at 15:30 against 12:30 and -7d [prometheus, reused W1-Q11, W1-Q12, W1-Q13]
- per-pod CPU level across the three pods [prometheus, reused W1-Q18, 13:08-15:28]
- kubectl get hpa: no output; throttling ratio: empty matrix [kubectl, prom-prod, H5-Q1, H5-Q2]

timeline:
- none new (13:08 step on GET /orders only, W1-Q5)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H5-Q1 | kubectl | get hpa -n orders | now | free | no output |
| H5-Q2 | prom-prod | sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="orders", pod=~"orders-api-.*"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="orders", pod=~"orders-api-.*"}[5m])) | 12:30-15:30, step 600 s | 1 query | empty matrix (series not present); link: raw/H5/m-throttle.json |

gaps:
- No CPU or memory limit, HPA definition or throttling series could be read; pod CPU has no value before 13:08 in W1-Q18.
- Memory and OOM state were not queried (no memory metric appears in the name list; pods show 0 restarts).

untrusted_text:
- none

to_confirm_by_human:
- Read the Deployment's resource requests/limits and any HPA for orders-api and compare CPU usage (about 0.6 cores per pod) with the limit.

lesson_candidates:
- process (prometheus) container_cpu_cfs_throttled_periods_total and container_cpu_cfs_periods_total returned an empty matrix for namespace orders and are absent from the metric-name list: an empty throttling series is not evidence of no throttling — H5-Q2

cost: 1 query, 0 GB of logs, 0 CloudWatch metric requests, 1 kubectl read
```

---

### [evidence H6, default tier]

Hypothesis H6 (traffic). Falsification: request rate against the previous window and -7d. The previous-window comparison is already in W1-Q14 and W1-Q19; the worker tries the -7d call rate, which no earlier row has. Wave 1 of 1.

```bash
RUN=.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/raw/H6; mkdir -p "$RUN"
curl -sG "https://grafana.example.com/api/datasources/proxy/uid/prom-prod/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[5m] offset 7d))' --data-urlencode "start=2026-10-20T12:30:00Z" --data-urlencode "end=2026-10-20T15:30:00Z" --data-urlencode "step=120" > "$RUN/m-rate-7d.json"
```

| ID | World file | Result |
|---|---|---|
| H6-Q1 | `prom-07.json` | one series, values identical to the decimal to W1-Q14 at every timestamp (e.g. 13:08), although the query asked for `offset 7d`: the backend did not shift it. Not usable as -7d evidence |

Verdict block returned:

```text
VERDICT: H6 | Ruled out
summary: Traffic on GET /orders did not rise. The call rate is 56.5 req/s (median, 10:00-12:28) before and 56.25 req/s (13:08-15:30) after, with no step at 13:08 (W1-Q14); hourly requests are 202.8k, 204.3k, 203.0k, 203.6k (the 13:00 hour) and 202.2k, level across the hours returned (W1-Q19). The -7d comparison is unavailable: the offset query returned the unshifted series (identical to W1-Q14 to the decimal), so it is discarded. A concentration on a few clients cannot be tested (no client dimension on the counter), but the endpoint's total volume is flat, and the latency step is accounted for by statements per request, not requests per second (W1-Q15).
weakest_link: no usable -7d call-rate comparison (the previous window and the hourly pull are the only baselines, and the hourly pull covers 5.5 hours), so "not above -7d" is not shown directly. (Assumed for -7d; the previous-window comparison is Confirmed)

evidence:
- GET /orders rate median 56.5 req/s before, 56.25 after, no step [prometheus, reused W1-Q14, 09:30-15:30]
- hourly requests 202.2k-204.3k, onset hour 203.6k [prometheus, reused W1-Q19, 10:00-15:30]
- offset-7d query returned an unshifted, identical series [prometheus, H6-Q1]

timeline:
- none new

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H6-Q1 | prom-prod | sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[5m] offset 7d)) | 12:30-15:30, step 120 s | 1 query | identical to W1-Q14 at every timestamp: offset not applied; link: raw/H6/m-rate-7d.json |

gaps:
- No -7d call rate for the endpoint.
- No per-client breakdown of requests.

untrusted_text:
- none

to_confirm_by_human:
- Check the load balancer or access logs for the share of GET /orders requests per client or per customer over the incident window (a read in a log tool this run cannot reach).

lesson_candidates:
- process (prometheus) `offset 7d` on http_server_request_duration_seconds_count returned the unshifted series (identical to the decimal to the same query without the offset); for -7d call rates shift start and end instead of using offset — H6-Q1

cost: 1 query, 0 GB of logs, 0 CloudWatch metric requests, 0 other units
```

---

### [evidence from-history:2026-08-14-orders-api.md, default tier]

Entry received (only these three lines): statement, expected evidence, falsification query. The ledger already holds the rows that answer the falsification (W1-Q17), so the worker runs no new query and cites them (`reused`), as Phase 4 allows for an entry the data already seems to contradict.

Verdict block returned:

```text
VERDICT: from-history:2026-08-14-orders-api.md | Ruled out
summary: The falsification (pool pending_requests at 0 across the incident window) holds. pending_requests is 0 at all 166 points from 09:30 to 15:30, which includes the whole incident window 12:30-15:30, so no request waited for a pool connection (W1-Q17). The pool `used` gauge is 14-19 before the onset and 17-24 after, without a plateau at a ceiling. The lead also expects a slowdown on every DB-backed route; here only GET /orders moved while POST /orders, GET /orders/{id} and PATCH stayed at baseline (W1-Q11..Q13). A pool-size configuration change cannot be read (no values repo), but without any waiters the pool is not the bottleneck whatever its size.
weakest_link: the pool maximum and any configuration change are unreadable here (no values repo, no pool-maximum metric); the verdict rests on zero waiters. (Confirmed for the waiters; the configuration arm is a gap)

evidence:
- pool `pending_requests` 0 at all 166 points; `used` 14-19 before, 17-24 after [prometheus, reused W1-Q17, 09:30-15:30]
- other DB-backed routes unchanged [prometheus, reused W1-Q11, W1-Q12, W1-Q13]

timeline:
- none new

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none) | reused W1-Q17, W1-Q11, W1-Q12, W1-Q13 | | | 0 | |

gaps:
- Pool maximum and configuration history unreadable.

untrusted_text:
- none

to_confirm_by_human:
- Read the pool-size setting in the chart values at Helm revisions 23 and 24 (same item as H4).

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs, 0 CloudWatch metric requests, 0 other units
```

---

### Dispatcher review and merge (main session, the only writer of the ledger)

Verdicts, escalation rules applied:

| ID | Tier | Worker label | Direct query exhibiting the point, inside window and scope? | Escalate? | Merged label |
|---|---|---|---|---|---|
| H1 | default | Confirmed | yes for what H1 asserts: the timing is H1-Q1 (W1-Q5 series, 13:06 to 13:08 against Helm 13:04:50), the change on the failing path is the file reads H1-Q2/Q3 at v2.15.0 lines 15-18 and W2-Q9, and the statement step is W1-Q15. The per-request mechanism is H2's, not part of H1's statement | no | Confirmed |
| H2 | default | Confirmed | yes: H2-Q1/Q2 (counts, both windows, n=24 each) and H2-Q3 (a fetched trace showing the pattern) are query results exhibiting the mechanism inside the incident window and scope; W1-Q15 agrees | no | Confirmed |
| H3 | strong | Ruled out | falsification negative: per-statement p95 and ReadLatency flat (W1-Q20, W1-Q21) | no | Ruled out |
| H4 | default | Ruled out | pending_requests 0 (W1-Q17) | no | Ruled out |
| H5 | default | Ruled out | other routes unchanged on the same pods (W1-Q11..Q13); direct headroom unreadable | no | Ruled out (cross-route basis; direct headroom is a gap) |
| H6 | default | Ruled out | rate flat (W1-Q14) | no | Ruled out (-7d is a gap) |
| from-history:2026-08-14-orders-api.md | default | Ruled out | pending_requests 0 (W1-Q17) | no | Ruled out |

No worker returned `inconclusive`, no default-tier verdict claimed `Confirmed` without a direct query, so there are no escalations. The Confirmed verdicts were checked for a query result that itself exhibits the point (table above).

Merge into the ledger (query IDs renumbered, old ID kept): W3-Q1 (was H1-Q1), W3-Q2 (H1-Q2), W3-Q3 (H1-Q3), W3-Q4 (H2-Q1), W3-Q5 (H2-Q2), W3-Q6 (H2-Q3), W3-Q7 (H2-Q4), W3-Q8 (H3-Q1), W3-Q9 (H4-Q1), W3-Q10 (H5-Q1), W3-Q11 (H5-Q2), W3-Q12 (H6-Q1). `lesson_candidates` copied to the ledger; `untrusted_text`: none from any worker, so nothing to flag. Counted queries now: 26 + 9 = 35 of 60; CloudWatch metric requests 7 of 500; log GB 0.05 of 10 (Tempo inspected about 11.4 GB across W1-Q20, W3-Q4, W3-Q5, not part of the log budget).

Auth-api: two fetched traces show a `GET auth-api /verify` client span (3.4 ms and 3.77 ms). It was not on the profile's dependency list and was not a hypothesis in the checkpoint-#2 list, so no worker tested it. It is recorded as an open lead (Assumed, not tested), not as a finding.

## Phase 5: conclude

Causal chain and labels (from the merged verdicts):
1. Trigger: Helm revision 24 (v2.15.0) at 13:04:50 UTC; commit a4c1e9b (#2211) changes `list_orders.py` lines 15-18 to call `repo.list_items(order.id)` per returned order. Confirmed (H1; W1-Q4, W1-Q1, W1-Q2, W2-Q8, W2-Q9, W3-Q2, W3-Q3).
2. Mechanism: GET /orders makes a median of 41 descendant spans (about 40 DB statements) against 3, each statement as fast as before; DB statements/s x10.4 with a flat call rate. Confirmed (H2; W3-Q4..Q7, W1-Q15, W1-Q14, W1-Q20).
3. Symptom: p95 0.18 s to 0.71 s, p50 0.09 s to 0.31 s from the 13:08 sample, 3 minutes after the upgrade. Confirmed (W1-Q5, W1-Q7, W1-Q11..Q13).
Timing leg: first elevated sample 13:08 (last normal 13:06) against Helm 13:04:50, first occurrence of the symptom, not a last-seen age. All three legs (change, mechanism, timing) are cited, so the cause may be `Confirmed`; the weakest link is named in the TL;DR. No third party or vendor in the path. Several hypotheses still standing: none; one open lead (auth-api, not tested, Assumed) is listed under Open hypotheses.
History: one similar past incident (2026-08-14-orders-api.md, matched on service, dependency, symptoms); its pool mechanism was tested as an entry and Ruled out here (W1-Q17), so this is not a repeat of that cause.
Fixes and mitigations are written as prose in Follow-ups (no command, patch or config fragment).

### Message to operator 7 (verbatim): TL;DR, report path, open items, cost line (last)

```text
TL;DR (Deep run orders-api-prod-20261020-1530)
Cause: the v2.15.0 release (Helm revision 24, 13:04:50 UTC) changed the GET /orders handler to run one order_items query per returned order (up to 50) instead of one joined query. A request now makes a median of 41 descendant spans (about 40 DB statements) against 3, each statement as fast as before, and the endpoint is about 4 times slower · Confirmed.
Weakest link: there is no old-versus-new latency split by pod or revision (no pod label on the histogram, rollout events expired), so the tie to the deploy rests on timing at 2-minute resolution plus the diff on the failing path; the per-request counts come from 24 sampled traces per window, backed by the service-wide statement rate x10.4 · Confirmed.
Impact: GET /orders p95 0.71 s against 0.18 s (p50 0.31 s against 0.09 s) since 13:08 UTC (23:08 local), still ongoing at 15:30 UTC; other endpoints unchanged. SEV2 suggested; you decide.
Recommended action: a human should decide on a rollback to v2.14.0 or a fix that restores the single joined query; both are described in prose in the report, with their costs, and should go through pre-flight first.
Ruled out: the database getting slower per statement, pool exhaustion (including the earlier incident's pool theory), pod capacity, a traffic spike.
Pattern: unclassified (no alert history, no 14-day latency data). Similar past incident: 2026-08-14-orders-api.md, but it was a different mechanism (pool), ruled out here.
Report: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/report.md
open items need your input: the unnamed alert, the Helm values diff, pool/CPU limits and HPA, Performance Insights, and the untested auth-api lead (see Gaps and "To confirm").
35 queries · 0.05 GB of logs scanned · 7 CloudWatch metric requests · Tempo inspected about 11.4 GB (not billed as logs) · about $0.00 in metered charges
```

`report.md`: report saved separately.

## Phase 6: record (after the report, never before)

Inputs: the ledger's Lesson candidates table (W0-Q24, W1-Q9, W1-Q18, W3-Q1, W3-Q5, W3-Q6, W3-Q8, W3-Q9, W3-Q11, W3-Q12), the run's `profile.md`, the run's finding. No existing `lessons.md`, so there are no confirm / re-verify / contradict / drop updates. A lesson that would hold beyond this estate is noted for the skill itself, not written here: the Tempo `matched` semantics (descendants of every kind, not only DB) and the search-preview versus by-ID mismatch; and that an empty throttling series is not evidence of no throttling.

### Message to operator 8 (verbatim): proposed record diff

```text
Proposed record, three new files under .culiops/sre-investigate/. Nothing is written until you reply; accept, edit or skip each item.

1. incidents/2026-10-20-orders-api.md (a cause was named at Confirmed)
2. lessons.md (10 lines, each backed by a query of this run; no existing lessons to confirm or drop)
3. profiles/orders-api-prod.md (first stored profile for this service: identifiers verified this run, the Loki label kept (unverified), dependencies orders-db and auth-api, baseline notes)

--- /dev/null
+++ .culiops/sre-investigate/incidents/2026-10-20-orders-api.md
@@ -0,0 +1,43 @@
+---
+id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
+date: 2026-10-20
+service: orders-api
+env: prod
+siblings: [all]
+window_utc: 2026-10-20T13:08Z/ongoing at 2026-10-20T15:30Z
+symptoms: [latency]
+cause_category: deploy
+cause: v2.15.0 list handler loads items with one query per order (N+1): median 41 descendant spans per GET /orders request against 3, p95 0.18 s to 0.71 s
+deps: [orders-db]
+label: Confirmed
+mode: deep
+time_to_cause_min: null
+run: runs/orders-api-prod-20261020-1530
+---
+ 
+# orders-api GET /orders about 4x slower after the v2.15.0 rollout
+ 
+## What happened
+ 
+Helm revision 24 (orders-api v2.15.0) was deployed at 13:04:50 UTC on 2026-10-20. From the 13:08 sample, p95 of `GET /orders` went from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) and stayed there up to 15:30 UTC. No other endpoint moved. The database was not saturated (CPU 25% to 41%, no pool waiters). The p95 alert kept firing.
+ 
+## Causal chain
+ 
+1. Trigger: commit a4c1e9b (#2211) in v2.15.0 changed `list_orders.py` to call `repo.list_items(order.id)` once per returned order (up to 50) instead of one joined query. Confirmed.
+2. Mechanism: each request makes about 1 + N statements (descendant spans p50 41, p95 52 against p50 3, p95 4 before; 24 traces each), each statement as fast as before (about 4 ms); service-wide DB statements per second x10.4 with a flat call rate. Confirmed.
+3. Symptom: GET /orders p95 x3.9, p50 x3.4 from 13:08, three minutes after the upgrade. Confirmed.
+ 
+## What found it
+ 
+The statement rate stepping x10.4 at the same sample as the latency step while the endpoint's call rate and the per-statement DB p95 stayed flat (a flat database p95 did not clear the database), then the span count per request in the incident window against the pre-deploy window.
+ 
+## What did not help
+ 
+- p90 and p99 queries returned nothing; the shape was read from p50 against p95.
+- The Loki stream for the service is labelled app="orders" and its lines carry no pod or trace ID; it could not be tied to the service and was not used as evidence.
+- Kubernetes events for the rollout had expired; the histogram has no pod label, so there was no old-versus-new split by pod.
+- The earlier orders-api latency incident (2026-08-14) pointed at the connection pool; here pool waiters are 0 at every point.
+ 
+## Follow-ups raised
+ 
+Fix or roll back the list handler; a statement-count test and canary gate for list endpoints; pod/version labels and p90/p99 recording rules; Performance Insights on orders-db; name the alert and add the chart values repo to environment.md.

--- /dev/null
+++ .culiops/sre-investigate/lessons.md
@@ -0,0 +1,10 @@
+- type: identifier | service: orders-api | source: loki | statement: logs sit under namespace=orders, container=api, app=orders (not orders-api); the request lines carry no pod name or trace ID, so the stream is unverified until a tie is found | run: orders-api-prod-20261020-1530 | query_id: W3-Q9 | re-verify: yes
+- type: process | service: orders-api | source: loki | statement: index/stats returned an empty object for namespace=orders (no size estimate); keep log queries to one stream and a short window | run: orders-api-prod-20261020-1530 | query_id: W0-Q24 | re-verify: yes
+- type: process | service: orders-api | source: prometheus | statement: histogram_quantile 0.9 and 0.99 on http_server_request_duration_seconds_bucket return empty although 0.5 and 0.95 work; read the shape from p50 against p95 | run: orders-api-prod-20261020-1530 | query_id: W1-Q9 | re-verify: yes
+- type: identifier | service: orders-api | source: prometheus | statement: http_server_request_duration_seconds_* carries only service, method and route (no pod, no version), so no per-pod or per-revision latency split | run: orders-api-prod-20261020-1530 | query_id: W3-Q1 | re-verify: no
+- type: process | service: orders-api | source: prometheus | statement: offset 7d on http_server_request_duration_seconds_count returned the unshifted series; for a -7d call rate shift start and end instead | run: orders-api-prod-20261020-1530 | query_id: W3-Q12 | re-verify: yes
+- type: process | service: orders-api | source: prometheus | statement: container_cpu_usage_seconds_total for namespace orders returned points only from 13:08 although the range began at 12:30; missing points are not zero | run: orders-api-prod-20261020-1530 | query_id: W1-Q18 | re-verify: yes
+- type: process | service: orders-api | source: prometheus | statement: container_cpu_cfs_throttled_periods_total returned an empty matrix and is absent from the metric-name list; an empty throttling series is not evidence of no throttling | run: orders-api-prod-20261020-1530 | query_id: W3-Q11 | re-verify: no
+- type: process | service: orders-api | source: tempo | statement: search `matched` counts all descendants of the server span (DB statements plus the auth-api client span) and search-preview span names can differ from the by-ID trace; take counts from matched, names from a by-ID fetch | run: orders-api-prod-20261020-1530 | query_id: W3-Q5 | re-verify: no
+- type: identifier | service: orders-api | source: tempo | statement: traces carry resource attributes service.name and k8s.namespace.name only (no service.version, no pod); DB spans are named SELECT orders, SELECT order_items, SELECT orders JOIN order_items with db.system=postgresql; the downstream client span is GET auth-api /verify | run: orders-api-prod-20261020-1530 | query_id: W3-Q6 | re-verify: no
+- type: process | service: orders-api | source: cloudwatch | statement: for orders-db only CPUUtilization, ReadLatency and DatabaseConnections return data; WriteLatency, DiskQueueDepth, Deadlocks and FreeableMemory return none and Performance Insights is off | run: orders-api-prod-20261020-1530 | query_id: W3-Q8 | re-verify: no

--- /dev/null
+++ .culiops/sre-investigate/profiles/orders-api-prod.md
@@ -0,0 +1,76 @@
+(the run's profile.md, whole, with the header line above; marks as in the run profile)
```

## Operator line 4 (answer when shown the proposed record diff)

> Yes, write them.

(Cue: the Phase 6 diff was shown. All three items accepted as proposed.)

## Phase 6 writes (after operator line 4)

Written exactly as shown in the diff, under the same relative layout:
- `incidents/2026-10-20-orders-api.md`
- `lessons.md` (10 lines)
- `profiles/orders-api-prod.md` (the run's `profile.md` with the header line updated)

No edits were requested and none were skipped.

## Files written (all under `out/`)

| Path | When | What |
|---|---|---|
| `runs/orders-api-prod-20261020-1530/ledger.md` | created after wave 0 and the profile build; rewritten in place after wave 1 (Query log W1, Windows, Recurrence, Impact, Timeline, Gaps), after wave 2 (Code repos, W2 rows), at Phase 3 (Hypotheses, Memory) and after the Phase 4 merge (W3 rows, labels, gaps, lesson candidates) | the working record; this is the final state |
| `runs/orders-api-prod-20261020-1530/profile.md` | written at the end of the profile build; marks and query IDs updated after Phase 4 (the file on disk is the final version, so it already shows the verified marks and the dependency `auth-api`) | the run's working profile |
| `incidents/2026-10-20-orders-api.md` | after operator line 4 | incident summary |
| `lessons.md` | after operator line 4 | 10 lessons |
| `profiles/orders-api-prod.md` | after operator line 4 | stored profile |
| `run-log.md` | this file | investigation log |

`runs/orders-api-prod-20261020-1530/report.md`: report saved separately. Not created: anything under `raw/` (the replies were the canned world files; the ledger says so).

## Totals

- Counted data-backend queries: 35 of 60 (wave 0: 9, wave 1: 17, workers: 9). CloudWatch metric requests: 7 of 500. Log GB scanned: 0.048 (Loki). Tempo inspected about 11.4 GB (not a log scan).
- Uncounted reads logged: IAM, kubectl, helm, git, ls/cat (the ledger lists them).
- Waves: main session waves 0, 1, 2 (wave 1 over ten queries, stated); Phase 4 workers each in one wave (H2 two waves of searches then fetches within one share); no escalations; no worker returned `inconclusive`.
- Labels: Confirmed H1, H2; Ruled out H3, H4, H5, H6, from-history:2026-08-14-orders-api.md. No `Likely` or `Assumed` hypothesis; the open lead `auth-api` is Assumed and untested.
- Operator lines received: line 1 at the start, line 2 at checkpoint #1, line 3 at checkpoint #2, line 4 at the record diff.
- Boxed write-capable warning: not shown (no allowed write action, no write verb). Culibox notice: not shown (`agentbox-env` absent). Suspected prompt injection: none seen.
- Time-to-cause: not measurable (`date -u` printed nothing). In order of events: the extra-work signal (statements/s x10.4 against a flat call rate) appeared in wave 1, the deploy became a suspect in wave 2, and Confirmed was reached with the Phase 4 verdicts.
