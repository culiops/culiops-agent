# Investigation log: orders-api prod, GET /orders slow (simulated run)

Conventions used in this log
- `CASE` = the case directory (simulated team repo)
- `OUT` = CASE/out ; run directory `OUT/runs/orders-api-prod-20261020-1530/` ; output root (simulated) = `OUT/`
- World files are named as in `CASE/world/` (for example `prom-03.json`). `_default` = `_default.txt` (`{}`), `_empty` = `_empty.txt` (no output).
- Grafana base `GRAFANA_URL=https://grafana.example.com`; `PROM`, `LOKI`, `TEMPO` = `$GRAFANA_URL/api/datasources/proxy/uid/{prom-prod,loki-prod,tempo-prod}`. Token always referenced as `$GRAFANA_SERVICE_ACCOUNT_TOKEN`, never expanded.
- Operator lines received are marked **OPERATOR**. Messages shown to the operator are marked **MESSAGE** and are verbatim.
- Time anchors: epoch 2026-10-20 00:00 UTC = 1792454400. 09:30 = 1792488600, 12:30 = 1792499400, 13:00 = 1792501200, 15:15 = 1792509300, 15:30 = 1792510200. Same +/-7d: subtract 604800.
- The simulated `date -u` printed nothing (maps to `_empty`), so no real Start times exist; the ledger's Start column says so. "Now" is taken as 2026-10-20 15:30 UTC (newest sample in the backends) and stated to the operator.

---------------------------------------------------------------------------------------------------

## Phase 0: access, mode, intake

**OPERATOR (line 1, opening request):**
`GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing. Deep mode please, I want this one written up properly.`

Skill files read this session before any query: SKILL.md, access/standalone.md, environment.template.md, templates/{ledger,report,profile,incident,lesson}.md, agents/{evidence,helper}.md, playbooks/{metrics,changes,traces,logs,infra-state}.md. Not read (not needed for this incident): playbooks/waf.md (no WAF/403/429 symptom), errors.md (no error tracker in environment.md), external.md (no ticket named), other-backends.md (no Datadog/NewRelic/Elastic).

### Pre-wave housekeeping (setup, not counted as queries)

| # | Command | World file | Key facts |
|---|---|---|---|
| P1 | `echo "${CULIOPS_HOME:-}"` | `_empty` | empty: CULIOPS_HOME unset, so the output root is `.culiops/sre-investigate/` at the repo root |
| P2 | `git rev-parse --show-toplevel` | `_empty` | no output; the case directory stands for the repo, so cwd is taken as the repo root (noted in ledger) |
| P3 | `git check-ignore -q .culiops/sre-investigate` | `_empty` (exit 0) | exit 0 = ignored; I do not touch .gitignore |
| P4 | `ls .culiops/sre-investigate` | `ls-01.txt` | `environment.md`, `incidents`. No `profiles/`, no `lessons.md`, so: no stored profile, no lessons |
| P5 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | tz Australia/Brisbane (UTC+10); account prod 111122223333 us-east-1 profile `prod-read`; kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders`; Grafana datasources prom-prod/loki-prod/tempo-prod, token env `GRAFANA_SERVICE_ACCOUNT_TOKEN`; CloudWatch RDS via `prod-read`; repo `example-org/orders-api`, clone `~/src/orders-api` (tags v2.14.0, v2.15.0); no Logs Insights; Loki ask above 20 GB; default severity scale; core flows checkout `POST /orders`, order history `GET /orders`. No `budgets:` block, no `slo:` |
| P6 | `command -v agentbox-env` | `_empty` (exit 1) | fails, so nothing about Culibox is said |

Budgets: environment.md has no `budgets:` block, so the template's neutral Deep defaults apply (60 queries, 10 GB logs, 500 CloudWatch metric requests, windows: log_stats 48h, log_patterns 2h, log_metric 12h, log_raw 30m, trace_aggregation 24h, trace_samples 1h, prom_quantile_range 12h); Loki ask-above-20GB from environment.md. Counting rule I use and state in the ledger: a "query" counted against the budget is a call to Prometheus, Loki, Tempo, Grafana, CloudWatch/CloudTrail/RDS APIs; identity and write-check calls, kubectl state reads, and local git or gh reads are logged but not counted.

Window decision (SKILL Phase 0 step 6): "since early this afternoon UTC" carries an explicit zone (UTC) but no clock time. I anchor on 13:00 UTC and start 30 minutes earlier. No recovery reported, so the window runs to now. Incident 2026-10-20 12:30-15:30 UTC; previous baseline 09:30-12:30 UTC; same span -7d 2026-10-13 12:30-15:30 UTC.

### MESSAGE 1 (first message)

```text
sre-investigate: Deep mode.
Why Deep: you asked for it and for a proper write-up, even though the p95 alert is still firing. So this is the full RCA path: a ledger, a checkpoint after the change list and another after the hypothesis list, one evidence worker per hypothesis, and the complete report.

Output root: .culiops/sre-investigate/ at the repo root. It is local and is never committed. `git check-ignore -q .culiops/sre-investigate` says it is already ignored, so I am not touching .gitignore.
Run directory: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/

Window and time zone
- You said "early this afternoon UTC". The zone is explicit (UTC) but the clock time is rough, so I anchor on 13:00 UTC and start 30 minutes earlier. No recovery has been reported, so the window runs to now.
- The clock call returned nothing in this session, so I take "now" as 2026-10-20 15:30 UTC, the newest sample the backends hold. Tell me if that is wrong.
- Incident window: 2026-10-20 12:30-15:30 UTC (22:30-01:30 Australia/Brisbane, from environment.md).
- Previous baseline: 09:30-12:30 UTC. Same span a week earlier: 2026-10-13 12:30-15:30 UTC.
- The onset is a guess until the data dates it. All of this is recorded in the ledger.

Budgets: environment.md sets none, so I use the skill defaults for Deep (60 queries, 10 GB of logs, 500 CloudWatch metric requests).
```

Run directory and ledger created (written to `OUT/runs/orders-api-prod-20261020-1530/ledger.md`; first full write after wave 3).

### Wave 0 commands (printed in full, then run)

**MESSAGE 1b (wave 0 plan, shown before running)**

```text
Wave 0: access and intake. Commands, sent together:

C1  date -u +%H:%M:%S ; aws sts get-caller-identity --profile prod-read
C2  arn=$(aws sts get-caller-identity --profile prod-read --query Arn --output text); role=${arn#*:assumed-role/}; role=${role%%/*}; role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text); aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
C3  kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
C4  kubectl config current-context
C5  kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders
C6  [ -n "${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}" ] && echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: set" || echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: unset"
C7  curl -sG "https://grafana.example.com/api/datasources/proxy/uid/loki-prod/loki/api/v1/index/stats" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={namespace="orders"}' --data-urlencode "start=1792509300000000000" --data-urlencode "end=1792510200000000000"
C8  curl -sG "https://grafana.example.com/api/datasources/proxy/uid/prom-prod/api/v1/label/__name__/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
C9  curl -sG "https://grafana.example.com/api/datasources/proxy/uid/prom-prod/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=max_over_time(ALERTS{alertstate="firing"}[1h])' --data-urlencode "start=1789918200" --data-urlencode "end=1792510200" --data-urlencode "step=3600"
C10 curl -sG "https://grafana.example.com/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "type=alert" --data-urlencode "from=1789918200000" --data-urlencode "to=1792510200000" --data-urlencode "limit=100"

Not in this wave, and why: no stored profile exists, so the profile build follows; no lessons.md exists; no ticket was named; no WAF symptom; the trigger alert's name was not given, so C9 and C10 look for its history without guessing a name.
```

### Wave 0 results

| Query ID | Call | World file | Key facts |
|---|---|---|---|
| W0-Q1 | C1 `aws sts get-caller-identity --profile prod-read` (+ `date -u`, which printed nothing: `_empty`) | `sts-01.json` | Account 111122223333 = environment.md account (no mismatch). Role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session part not recorded) |
| W0-Q2 | C2 part 1 `aws iam get-role ...` | `iam-01.json` | path `/aws-reserved/sso.amazonaws.com/`, role resolved |
| W0-Q3 | C2 part 2 `aws iam simulate-principal-policy ...` | `iam-02.json` | 10 rows, all `implicitDeny`, but only 7 of my 10 actions have a row. No row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack. Three rows I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy), also implicitDeny, are not counted. So: nothing allowed; 3 actions unchecked = gap |
| W0-Q4 | C3 `kubectl auth whoami` | `k8s-02.txt` | assumed-role ReadOnly SSO role, group `eks-readonly` (session name not recorded) |
| W0-Q5 | C4 `kubectl config current-context` | `k8s-01.txt` | `arn:aws:eks:us-east-1:111122223333:cluster/prod` = the context in environment.md |
| W0-Q6 | C5 `kubectl auth can-i --list ... --namespace orders` | `k8s-03.txt` | only `[create]` on selfsubjectreviews/selfsubjectaccessreviews/selfsubjectrulesreviews (excluded by rule), `*.*` verbs `[get list watch]`, non-resource GETs. No write verb |
| W0-Q7 | C6 token presence | `env-01.txt` | file content `x`: `GRAFANA_SERVICE_ACCOUNT_TOKEN` is set (the only token var in environment.md) |
| W0-Q8 | C7 Loki index stats probe, `{namespace="orders"}`, 15:15-15:30 | `loki-06.json` | reply is a streams result: `app="orders"` container `api` (GET /orders lines `level=info msg="request completed" method=GET path=/orders status=200 duration_ms=286..751 page_size=50`) and `app="orders-reconcile"` container `worker` ("outbox drained", batch 20-22, pending=0, about every 137 s); `totalBytesProcessed` 48,211,904 (about 0.05 GB), exec 0.41 s. `namespace` label value `orders` returned data: verified |
| W0-Q9 | C8 Prometheus metric names | `prom-09.json` | 11 names: db_client_connections_{pending_requests,usage}, db_client_operation_duration_seconds_{bucket,count,sum}, container_cpu_usage_seconds_total, http_server_request_duration_seconds_{bucket,count,sum}, kube_deployment_status_replicas, up. No `ALERTS`, no `traces_spanmetrics_*`, no CFS throttling series, no ingress or LB series |
| W0-Q10 | C9 ALERTS firing history, 30d at 1h | `prom-10.json` (`anything else`) | empty matrix: no `ALERTS` series (consistent with W0-Q9). Alert history from Prometheus: unavailable |
| W0-Q11 | C10 Grafana annotations type=alert 30d | `_default` | `{}`: no alert annotations returned |

Mode detection: nothing printed about Culibox (P6 failed).

Access results into ledger Access table; gaps recorded (see ledger).

### MESSAGE 2 (after wave 0: write-checks and gaps)

```text
Access results (wave 0)

AWS, profile prod-read (account 111122223333, matches environment.md; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b):
Write check, prod-read: no write action allowed in the 7 rows the simulator returned for my list (all implicitDeny). 3 of my 10 actions came back with no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack), so those are unchecked and recorded as a gap. The reply also held 3 actions I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy), also implicitDeny; I did not count them. This is not a full proof; resource-scoped writes are not covered.

Kubernetes, context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace orders (read as the eks-readonly group):
Write check: no write verbs in orders. The only creates are the self-review APIs, which change nothing.

Token: GRAFANA_SERVICE_ACCOUNT_TOKEN is set (Prometheus, Loki, Tempo all use it).

Gaps found so far
1. The p95 alert's history is unavailable. You did not name it, and neither Prometheus (no ALERTS series) nor Grafana annotations returned anything. Effect: the 30-day alarm history is missing, so the recurrence class is limited to what the metrics themselves hold. To fix: give me the alert rule name or its Grafana rule UID, or point me at where its state history lives.
2. Write check coverage: 3 of 10 actions unchecked (above). Effect: none on the investigation, which stays read-only.
3. No stored profile and no lessons.md: this is the first run for orders-api prod. I am building the profile now.
```

---------------------------------------------------------------------------------------------------

## Build profile (helper, TASK: PROFILE, cheapest tier; simulated inline)

Dispatch note: the helper would be dispatched with an explicit `model` at the cheapest tier. Here it is simulated inline, section labelled `[helper PROFILE, cheapest tier]`. Identifier lessons passed: none (no lessons.md).

`[helper PROFILE, cheapest tier]` one discovery wave (run while the change queries are prepared; not counted against a wave cap):

| Query ID | Call | World file | Result |
|---|---|---|---|
| W0-Q12 | `curl -sG "$LOKI/loki/api/v1/labels" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"` | `loki-01.json` | labels: app, container, namespace, stream |
| W0-Q13 | `curl -sG "$LOKI/loki/api/v1/label/app/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"` | `loki-02.json` | catalog-api, notify-worker, orders, orders-reconcile, payments-worker. The service's own value is `orders`, not `orders-api` |
| W0-Q14 | `curl -sG "$LOKI/loki/api/v1/label/namespace/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"` | `loki-03.json` | catalog, notify, orders, payments |
| W0-Q15 | `curl -sG "$LOKI/loki/api/v1/label/container/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"` | `loki-04.json` | api, worker |
| W0-Q16 | `curl -sG "$TEMPO/api/v2/search/tags" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"` | `tempo-06.json` | resource tags: k8s.namespace.name, k8s.pod.name, service.name, service.version; span tags: db.statement, db.system, http.request.method, http.response.status_code, http.route, server.address |
| W0-Q17 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get deployments,services,ingresses,hpa` | `_empty` | no output (unexpected for a namespace with running pods; the pods list in wave 1 shows otherwise). Read as "unusable result", not as "none exist"; deployment name stays (unverified) until wave 1 |
| W0-Q18 | `curl -sG "$GRAFANA_URL/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=orders-api" --data-urlencode "type=dash-db"` | `_default` | `{}`: no dashboards found |
| W0-Q19 | `ls .culiops/service-discovery` | no row: `No such file or directory` (exit 1) | no service-discovery catalog |

Helper returned the profile below (marks as it would set them: only identifiers that returned data are verified). Written to `OUT/runs/orders-api-prod-20261020-1530/profile.md` and shown to the operator.

### MESSAGE 3 (profile shown, run continues)

```text
Run profile built (first run for orders-api prod; nothing stored yet). Written to .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/profile.md. Corrections welcome; I carry on meanwhile.

- Logs: Loki {namespace="orders", app="orders", container="api"} (verified). Note the app label is "orders", not "orders-api". A sibling worker logs as app="orders-reconcile", container="worker" (verified, same namespace).
- Metrics: Prometheus service="orders-api", route, method on http_server_request_duration_seconds_*; db_client_operation_duration_seconds_* (db_system); db_client_connections_{usage,pending_requests} (pool "orders-db"); container_cpu_usage_seconds_total; kube_deployment_status_replicas. service="orders-api" is (unverified) until a query returns it.
- Traces: Tempo, resource tag service.name (value "orders-api" is (unverified) until a query returns it).
- Compute: namespace orders, Deployment and Helm release orders-api (both (unverified) until wave 1), 3 replicas expected.
- Data store: RDS PostgreSQL orders-db (from environment.md, (unverified) until read).
- Code: example-org/orders-api, local clone ~/src/orders-api, tags v2.14.0 and v2.15.0.
- Not found: dashboards, ingress or load-balancer series, an error tracker, an SLO, a service-discovery catalog.
```

Profile file content is in `OUT/runs/orders-api-prod-20261020-1530/profile.md` (updated after wave 1/2 with verified marks).


---------------------------------------------------------------------------------------------------

## Phase 1: scope, impact, severity (wave 1)

Wave 1 legs (never trimmed): change events (rollout history, ReplicaSets, events, pods, Helm), golden-signal deltas over three windows, latency breakdown (p50/p90/p95/p99, per-endpoint p95 and call rate, slow-downstream aggregation), recurrence pull, saturation (DB pool, CPU), sibling comparison. The rollout detail, p-quantiles and recurrence all sit in this one wave because the symptom is latency (SKILL Phase 1 step 2).

Combined-window choice: for the range queries the incident and the previous window are adjacent and equal, so one range 09:30-15:30 (1792488600-1792510200, step 120) carries both; the -7d window is a second query with `offset 7d`. (The reply timestamps for `offset 7d` rows are on 2026-10-13, the shifted clock window.)

### MESSAGE 4 (wave 1 plan, printed in full before running)

```text
Wave 1: change events, golden signals (three windows), latency breakdown, recurrence pull. Commands, sent together as five shell calls:

CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod

Call A (change events, short-lived first)
date -u +%H:%M:%S
W1-Q1  kubectl --context $CTX -n orders rollout history deployment/orders-api
W1-Q2  kubectl --context $CTX -n orders get rs --sort-by=.metadata.creationTimestamp
W1-Q3  kubectl --context $CTX -n orders get events --sort-by=.lastTimestamp
W1-Q4  kubectl --context $CTX -n orders get pods
W1-Q5  helm history orders-api --kube-context $CTX -n orders --max 10

Call B (per-route p95, three windows, instant)  PROM=https://grafana.example.com/api/datasources/proxy/uid/prom-prod
W1-Q6  curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[30m])))' --data-urlencode "time=1792510200"
W1-Q7  same query, --data-urlencode "time=1792499400"
W1-Q8  curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[30m] offset 7d)))' --data-urlencode "time=1792510200"

Call C (GET /orders quantiles, range, step 120)  every query: curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120" --data-urlencode 'query=<below>'
W1-Q9   histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))
W1-Q10  histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))
W1-Q11  histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m] offset 7d)))
W1-Q12  histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m] offset 7d)))
W1-Q13  histogram_quantile(0.9, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))
W1-Q14  histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))

Call D (call rate, database, saturation, recurrence)  same curl form as Call C
W1-Q15  sum by (route, method) (rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders", method="GET"}[5m]))
W1-Q16  sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))
W1-Q17  sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m] offset 7d))
W1-Q18  sum by (pool, state) (db_client_connections_usage{service="orders-api"})
W1-Q19  sum by (pool, state) (db_client_connections_pending_requests{service="orders-api"})
W1-Q20  sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[10m]))   (step 600)
W1-Q21  recurrence, 14d at 1h: sum by (db_system) (increase(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))   (start=1791289800 end=1792510200 step=3600)

Call E (Tempo, DB client spans; TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod)
W1-Q22  curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.db.system =~ ".+" } | quantile_over_time(duration, .95) by (span.db.system)' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=900"
W1-Q23  same with '| rate() by (span.db.system)'

Why these: p50 and p95 together (and p90/p99) tell a ceiling from general slowness; the call rate beside the database operation rate tells volume from per-call cost; the recurrence pull uses the database operation counter because a 14-day histogram_quantile is past the 12h cap and no recording rule exists (latency recurrence is recorded as a gap).
```

### Wave 1 results

| Query ID | World file | Key facts returned |
|---|---|---|
| W1-Q1 rollout history | `k8s-07.txt` | revision 23 `helm upgrade orders-api (chart orders-api-4.2.0, image v2.14.0)`; revision 24 `... image v2.15.0`. Deployment `orders-api` exists (verified) |
| W1-Q2 get rs | `k8s-06.txt` | `orders-api-5f8d9c7b6a` 0/0/0 age 13d (old); `orders-api-7c9b6d8f5d` 3/3/3 age 145m (new, so created about 13:05 UTC if now = 15:30) |
| W1-Q3 get events | `k8s-05.txt` | `No resources found in orders namespace.` Events expire after about 1 h by default; rollout was about 2 h 25 m ago: "events not available for onset" = a gap, not "no events" |
| W1-Q4 get pods | `k8s-04.txt` | 3 pods of RS 7c9b6d8f5d, all 1/1 Running, 0 restarts, ages 145m/144m/144m |
| W1-Q5 helm history | `helm-01.txt` | rev 23 Wed Oct 7 09:40:12 2026 superseded, v2.14.0; rev 24 Tue Oct 20 13:04:50 2026 deployed, v2.15.0, chart orders-api-4.2.0 (same chart both). Times print without a zone; the 145 m ReplicaSet age corroborates 13:05 UTC |
| W1-Q6 per-route p95, incident (15:30, 30m) | `prom-03.json` | GET /orders 0.712 s; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; GET /healthz 0.003. `service="orders-api"`, `method`, `route` labels verified |
| W1-Q7 per-route p95, previous (12:30) | `prom-04.json` | GET /orders 0.181; /orders/{id} 0.061; POST 0.139; PATCH 0.091; healthz 0.003 |
| W1-Q8 per-route p95, -7d (15:30) | `prom-14.json` | GET /orders 0.181; /orders/{id} 0.061; POST 0.139; PATCH 0.091; healthz 0.003 (reply timestamp 1791905400 = 2026-10-13 15:30) |
| W1-Q9 GET /orders p95 range | `prom-01.json` | coverage starts 10:00 (1792490400); 10:00-13:06: 0.160-0.201 s; first slow sample 13:08 (1792501680) 0.716; 13:08-15:30: 0.661-0.755 s; last 0.663. A step, not a ramp |
| W1-Q10 GET /orders p50 range | `prom-02.json` | 10:00-13:06: 0.080-0.100 s; from 13:08: 0.281-0.339 s (about 3.4x) |
| W1-Q11 p95 -7d | `prom-11.json` | 0.160-0.200 s over the whole -7d window |
| W1-Q12 p50 -7d | `prom-12.json` | 0.080-0.100 s over the whole -7d window |
| W1-Q13 p90 range | `prom-10.json` | empty matrix (no row for this quantile). Same selector returns data for 0.5 and 0.95, so this is an unexplained empty reply, recorded as a gap, not read as zero |
| W1-Q14 p99 range | `prom-10.json` | empty matrix; same gap |
| W1-Q15 GET /orders call rate | `prom-07.json` | 52.0-60.9 req/s from 10:00 to 15:30, no step at 13:08 (about 56 req/s before and after). Volume shape ruled out for this endpoint |
| W1-Q16 DB operations/s | `prom-05.json` | `db_system="postgresql"`: 10:00-13:06 361-401 ops/s; from 13:08 3,820-4,089 ops/s (first 4,031.1): about 10.4x, same minute as the latency step |
| W1-Q17 DB operations/s -7d | `prom-13.json` | 355-404 ops/s over the -7d window |
| W1-Q18 pool used | `prom-06.json` | pool `orders-db` used 14-19 before 13:08; 17-24 after |
| W1-Q19 pool pending | `prom-06.json` | pending_requests 0 at every sample (no pool waits); pool max not exposed |
| W1-Q20 CPU per pod | `prom-08.json` | 3 new pods only; first point 13:08 (series start there), 600 s step; each pod 0.52-0.64 cores, no pod out of line. No points before 13:08 returned, so no baseline: gap |
| W1-Q21 recurrence, DB ops 14d x 1h | `prom-05.json` (same metric) | only points from 2026-10-20 10:00 (5.5 h of the 336 h asked). Coverage gap. Hourly increase read from those samples: about 1.4M per hour (10:00-12:00 hours), about 13M in the 13:00 hour, about 14M per hour after |
| W1-Q22 Tempo DB client span p95 | `tempo-01.json` | `span.db.system="postgresql"`: 3.9-4.4 ms at every 15-min step, before and after 13:08 (flat). `service.name` value `orders-api` verified. 6,633,910,272 bytes inspected (trace aggregation, not log GB) |
| W1-Q23 Tempo DB client span rate | `tempo-08.json` | empty series; recorded as gap |

Derived readings (all from the rows above):
- Shape: step at 13:08 UTC (last normal sample 13:06). p50 and p95 both moved (about 3.4x and about 3.9x), so it is not a ceiling (a timeout wait would leave p50 alone). Call rate flat, so not volume of requests. DB operations per second x10.4 at the same minute while the per-operation DB span p95 stays about 4 ms: more database work per request, each piece as fast as before.
- Siblings: 3 replicas, all on one ReplicaSet; CPU per pod equal. Per-pod latency was not pulled (no `pod` label on the latency histogram).
- Recurrence class: `unclassified`. Reason: no alarm history (W0-Q10, W0-Q11), 14-day metric coverage only 5.5 h (W1-Q21), latency recurrence not pullable under the 12h histogram_quantile cap with no recording rule. What the data does say: nothing like it in the 3 h before onset (p95 max 0.201) nor in the same clock window 7 days earlier (max 0.200), the step is single and persistent (not periodic).

### Impact block (SKILL Phase 1 step 10; shown before Phase 2)

### MESSAGE 5 (impact block)

```text
Impact as of 15:30 UTC (01:30 on 2026-10-21, Australia/Brisbane per environment.md)
Symptom:   GET /orders (order history) is about 4x slower; sampled responses still return 200, and there is no error or status metric to count failures
Affected:  prod, namespace orders, all 3 replicas of orders-api, GET /orders only. p95 0.71 s against 0.18 s (previous window and 7 days earlier), p50 0.31 s against 0.09 s. Other routes flat: GET /orders/{id} p95 0.064 s vs 0.061 s, POST /orders 0.142 vs 0.139, PATCH /orders/{id} 0.088 vs 0.091. GET /orders call rate unchanged at about 56 req/s. Customer-facing: yes (assumed; order history is a listed core flow)
Since:     13:08 UTC (23:08 local), first slow sample; last normal sample 13:06 UTC · ongoing: yes (0.66-0.75 s through 15:30)
Severity:  SEV2 (suggested) because a listed core flow (order history) is significantly degraded while still returning data; nothing shows failing requests, so not SEV1. The incident owner decides.
Basis:     request metrics against baseline (http_server_request_duration_seconds) · W1-Q6..Q12, W1-Q15 · Confirmed for the latency change; "customer-facing" and "no failed requests" are Assumed (no error metric, no load-balancer series)
Third party in the path: none seen (the one dependency found is the in-house RDS database orders-db)
```

Also shown with it, in the same message block: recurrence read ("unclassified: no alarm history and 5.5 h of 14 d of metric coverage; nothing like this in the 3 h before onset or 7 days earlier") and the first shape read ("step at 13:08, p50 and p95 both up, request rate flat, database operations x10 at the same minute").

---------------------------------------------------------------------------------------------------

## Phase 2: change correlation (waves 2 and 3)

Recurrence first (SKILL Phase 2 step 1): the class is `unclassified`, so no schedule can be put ahead of the deploy on recurrence grounds; schedules are therefore listed explicitly (this wave) before any change is blamed. A deploy 3 minutes before a persistent step is a candidate, not a cause.

Profile marks updated after wave 1 (run profile): verified `service="orders-api"` (Prometheus), `service.name="orders-api"` (Tempo), Deployment/Helm release `orders-api`, namespace `orders`, pool `orders-db`, `db_system="postgresql"`.

### MESSAGE 6 (wave 2 plan, printed in full before running)

```text
Wave 2: the slower change sources. Commands, sent together as four shell calls (CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod):

Call F (app code between the two deployed versions, local clone read by ref, no pull or checkout; plus the same through gh)
W2-Q1  git -C ~/src/orders-api tag
W2-Q2  git -C ~/src/orders-api log --oneline --format='%h %cs %s' v2.14.0..v2.15.0
W2-Q3  git -C ~/src/orders-api diff v2.14.0 v2.15.0
W2-Q4  gh api repos/example-org/orders-api/compare/v2.14.0...v2.15.0 --method GET

Call G (CloudTrail writes, two hours before the onset to 15 minutes after, us-east-1)
W2-Q5  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T13:23:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders')]].[EventTime, EventSource, EventName, EventId]" --output text
W2-Q6  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T12:50:00Z --end-time 2026-10-20T13:20:00Z --query "Events[?contains(EventSource, 'eks.amazonaws.com') || contains(EventSource, 'rds.amazonaws.com')].[EventTime, EventSource, EventName, EventId]" --output text

Call H (schedules and platform events)
W2-Q7  kubectl --context $CTX get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'
W2-Q8  aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
W2-Q9  aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text
W2-Q10 aws rds describe-db-instances --profile prod-read --region us-east-1 --db-instance-identifier orders-db
W2-Q11 aws rds describe-events --profile prod-read --region us-east-1 --source-type db-instance --source-identifier orders-db --start-time 2026-10-20T11:08:00Z --end-time 2026-10-20T13:23:00Z --query 'Events[].[Date, Message]' --output text

Call I (Grafana annotations / deploy markers in the window)
W2-Q12 curl -sG "https://grafana.example.com/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "from=1792499400000" --data-urlencode "to=1792510200000" --data-urlencode "limit=100"

Not run, and why: ECS and Auto Scaling (the service runs on EKS), IaC history and `gh run list` (no IaC repo is named in environment.md; the Helm chart repo is unknown, recorded as a gap), a dependency deploy check for orders-db (managed RDS; its events are in W2-Q11).
```

### Wave 2 results

| Query ID | World file | Key facts |
|---|---|---|
| W2-Q1 git tag | `git-03.txt` | v2.12.0, v2.13.0, v2.13.1, v2.14.0, v2.15.0: both deployed tags present. Image tag = git tag (Helm APP VERSION `v2.15.0` = tag `v2.15.0`) |
| W2-Q2 git log v2.14.0..v2.15.0 | `git-01.txt` | 3 commits: `a4c1e9b 2026-10-19 orders: load items per order in list handler (#2211)`, `7be20d4 2026-10-19 orders: return shipment ETA on order detail (#2208)`, `3f9d6a1 2026-10-16 deps: bump structlog to 25.4.0 (#2203)` |
| W2-Q3 git diff v2.14.0 v2.15.0 | `git-02.txt` | `orders_api/handlers/list_orders.py`: `repo.list_orders_with_items(customer_id, limit=limit)` replaced by `repo.list_orders(...)` then `for order in orders: order.items = repo.list_items(order.id)`; `orders_api/handlers/order_detail.py`: adds a `shipment_eta` field; `pyproject.toml`: structlog 25.3.0 to 25.4.0. Three files |
| W2-Q4 gh compare | `gh-01.json` | same 3 commits (ahead_by 3), same 3 files with patches; total_commits 3. Confirms the clone |
| W2-Q5 CloudTrail writes, filter `orders` | `_default` | `{}`: no event rows returned |
| W2-Q6 CloudTrail sweep eks/rds, 12:50-13:20 | `_default` | `{}`: no event rows returned (a Helm upgrade is a Kubernetes API change, not a CloudTrail write; empty replies are not proof of "nothing") |
| W2-Q7 cronjobs | `_empty` | no output: no CronJob rows returned |
| W2-Q8 EventBridge rules | `_default` | `{}`: none returned |
| W2-Q9 Scheduler schedules | `_default` | `{}`: none returned |
| W2-Q10 rds describe-db-instances | `rds-01.json` | `orders-db`, db.r6g.2xlarge, postgres 16.6, Multi-AZ, available, Performance Insights disabled. No backup or maintenance window fields in the reply (recorded as not seen) |
| W2-Q11 rds describe-events | `_default` | `{}`: no RDS events returned for 11:08-13:23 |
| W2-Q12 annotations in window | `_default` | `{}`: no deploy markers or notes |

### MESSAGE 7 (wave 3 plan, app code at the deployed ref)

```text
Wave 3: the code on the failing path, read at the deployed tag, no checkout. (Wave 2 showed #2211 changes the GET /orders handler; the file paths come from that diff.)

W3-Q1  git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py
W3-Q2  git -C ~/src/orders-api show v2.15.0:orders_api/repository.py
```

### Wave 3 results

| Query ID | World file | Key facts |
|---|---|---|
| W3-Q1 | `repo/orders_api/handlers/list_orders.py` | at v2.15.0: `limit = min(int(request.query.get("limit", 50)), 50)`; `orders = repo.list_orders(customer_id, limit=limit)`; then `for order in orders: order.items = repo.list_items(order.id)`; docstring "Each order carries its line items" |
| W3-Q2 | `repo/orders_api/repository.py` | `list_orders` = one SELECT with LIMIT; `list_items(order_id)` = one SELECT per order from `order_items` (each call takes `pool.connection()`); `list_orders_with_items` still exists, docstring: "One round trip: orders plus their items (used by the list handler up to v2.14.0)" |

Reading (code only, a lead until a metric or span count backs it at incident time): each GET /orders request now runs 1 + N queries, N up to 50, where v2.14.0 ran 1. A bound to check later: at about 56 req/s the code adds at most 56 x 50 = 2,800 queries/s; the metric shows +3,570 ops/s (3,950 - 380), about 1.3x that bound. The gap is recorded as an open question for the evidence worker (other callers of the DB, ops counted per connection checkout, or a different request rate than the route-level counter shows).

Change list for the checkpoint (UTC):
| Time (UTC) | Event | Source | Reading |
|---|---|---|---|
| 2026-10-07 09:40 (zone not printed) | Helm rev 23, v2.14.0 | W1-Q5 | previous release; not near the onset |
| 2026-10-16 / 10-19 | commits #2203 structlog, #2208 shipment ETA on detail, #2211 items per order in the list handler merged (commit dates; merged is not deployed) | W2-Q2, W2-Q4 | candidates. #2211 touches the failing path (list_orders.py); #2208 touches /orders/{id} only; #2203 touches every route |
| 2026-10-20 about 13:04:50 | Helm rev 24 v2.15.0 deployed; new ReplicaSet created about 13:05 (age 145m at 15:30) | W1-Q5, W1-Q2 | candidate, ahead of the onset by about 1 to 3 minutes |
| 13:06 | last normal GET /orders p95 sample (0.163 s) | W1-Q9 | |
| 13:08 | first slow sample: p95 0.716 s, DB ops 4,031/s, pool used 22 | W1-Q9, W1-Q16, W1-Q18 | onset (derived series lag their source by a minute or two) |
| 13:08-15:30 | persistent: p95 0.66-0.75 s | W1-Q9 | ongoing |
| not found | CloudTrail writes, EventBridge rules, Scheduler schedules, CronJobs, RDS events, deploy annotations: all returned nothing | W2-Q5..Q9, Q11, Q12 | no schedule or platform event near the onset; Kubernetes events expired (gap) |

### Checkpoint #1 (Deep)

### MESSAGE 8 (checkpoint #1)

```text
Checkpoint #1: window, blast radius, recurrence, changes, profile

Windows (UTC, local Australia/Brisbane beside): incident 12:30-15:30 (22:30-01:30); previous 09:30-12:30; same span a week earlier 2026-10-13 12:30-15:30. Onset dated by the data: 13:08 UTC (23:08 local), last normal sample 13:06.

Blast radius: prod, orders-api, GET /orders only, all 3 replicas moving together. Other routes and the request rate are flat.

Recurrence: unclassified. There is no alarm history (you did not name the alert, and neither Prometheus nor Grafana returned any) and the metrics hold only 5.5 hours of the 14 days I asked for. What I can say: nothing like this in the 3 hours before the onset or in the same window a week earlier, and the step is a single persistent shift, not periodic.

Changes found near the onset
1. Helm revision 24 (orders-api chart 4.2.0, image v2.15.0) deployed at about 13:05 UTC (printed 13:04:50 with no zone; the ReplicaSet and pod ages of about 145 minutes agree). The previous release v2.14.0 had run since 2026-10-07.
2. v2.15.0 holds three commits: #2211 (the GET /orders handler now loads each order's items with a separate query), #2208 (shipment ETA on order detail), #2203 (structlog bump). Only #2211 sits on the failing path.
3. No CloudTrail writes, schedules (EventBridge, Scheduler, CronJobs), RDS events or deploy annotations came back. Kubernetes events had already expired, so the rollout's own events are a gap.
At this point the deploy is a candidate with a mechanism on the code path, not yet a cause: it needs old-versus-new evidence from the traces and the database signals.

Run profile: shown earlier (Message 3). Verified since: service="orders-api" in Prometheus and Tempo, Deployment and Helm release orders-api, namespace orders, connection pool "orders-db". Still (unverified): RDS identifier orders-db details beyond the description, the Helm chart's source repo, replicas' limits and HPA.

Gaps so far: no alert history; metric coverage 5.5 h of 14 d; no CPU baseline (the CPU series start at 13:08); p90 and p99 queries returned nothing even though p50 and p95 with the same selector work; no error or status metric and no load-balancer series, so "no failed requests" is assumed; Kubernetes events expired; 3 of 10 write-check actions unchecked.

Two questions, then I go on:
1. Is the window right (onset 13:08 UTC, still ongoing)?
2. Did anything change that I cannot see from here: a manual action, a feature flag, a database change, a traffic shift, a vendor issue?
```

**OPERATOR (line 2, at checkpoint #1):** `Agreed, go on.`


---------------------------------------------------------------------------------------------------

## Phase 3: hypotheses

Inputs: impact and shape (step at 13:08, p50 and p95 both up, call rate flat, DB ops/s x10, per-op DB span p95 flat), change list (v2.15.0 with #2211 on the path), dependency map (profile: RDS PostgreSQL orders-db, sibling worker orders-reconcile; no service-discovery catalog).

Own ranking first (written before any history was read), in rank order by fit to onset, shape and blast radius:
1. H1 release v2.15.0 / #2211 turns GET /orders into 1 + N queries (N+1)
2. H3 the other v2.15.0 changes (structlog bump, ETA field)
3. H2 orders-db slow on its own (CPU, I/O, locks)
4. H4 pod CPU saturation or throttling
5. H6 neighbouring worker (orders-reconcile) contending for the database
6. H5 traffic spike or bot
(No `sched:` hypotheses: the class is not `scheduled` and W2-Q7..Q9 returned no schedules.)

History lookup (only now that the ranked list exists; SKILL Phase 3 "History after ranking"):

| Cmd | Command | World file | Result |
|---|---|---|---|
| G1 | `ls .culiops/sre-investigate/incidents` | `ls-02.txt` | 2026-08-14-orders-api.md, 2026-09-30-catalog-api.md |
| G2 | `grep -rn -E '^(service\|deps\|symptoms\|cause_category\|cause):.*(orders-api\|orders-db\|postgres\|latency\|p95)' .culiops/sre-investigate/incidents` | applied to both files in `incidents/` | matches only in 2026-08-14-orders-api.md: line 3 `service: orders-api`, line 5 `symptoms: [latency, p95, "GET /orders", "POST /orders"]`, line 7 `deps: [orders-db]`. Nothing in the catalog-api file (service catalog-api, deps search-cluster, symptoms errors/5xx). |
| G3 | `cat .culiops/sre-investigate/incidents/2026-08-14-orders-api.md` | `incidents/2026-08-14-orders-api.md` | past cause: DB connection pool exhausted after a config change lowered the pool size; `pending_requests` above 30 for 40 minutes; label Confirmed in that run |
| G4 | lessons.md `failure-mode` lines | n/a | no lessons.md exists |

A past cause that is not on my list becomes a lead: `from-history:2026-08-14-orders-api.md` (H7). It is a lead, never evidence, and is NOT passed to its worker (the worker gets a neutral statement). Wiki/runbook search: no read-only wiki access is configured in environment.md, so none done.

Models: H1 `strong` (stronger tier): three signals must be correlated (rollout timing, spans per request, ops/s) and the evidence is expected to conflict (observed +3,570 ops/s against a code bound of about 2,800). All others `default` (default tier).

Budget split: counted queries so far = 35 of 60 (wave 0 data 4, profile build 6, wave 1: 18, wave 2: 7). Remaining 25: 3 per worker x 7 = 21, 4 held back for at most one escalation. Logs 0.05 of 10 GB used (about 1 GB per worker); CloudWatch metric requests 0 of 500 used (70 per worker). Not all workers will use their share.

### MESSAGE 9 (checkpoint #2)

```text
Checkpoint #2: hypotheses, each with the query that would disprove it. Ranked by fit to the onset, the shape and the blast radius.

1. H1 (model: strong). Release v2.15.0, commit #2211, changed GET /orders from one joined query to one items query per order, so each request makes up to 51 database queries instead of 1. Expected if true: the step starts as the new pods take traffic (about 13:05, not before); database client spans per GET /orders trace are about 51 against about 1 earlier; the p50 rise is close to 50 x the per-query time (about 4 ms, so about 0.2 s); per-query latency and request rate stay flat. Disproved by: spans per request equal between the incident hour and the hour before the rollout (at least 20 traces each).
2. H3 (default). The other changes in v2.15.0 slowed requests: the structlog bump (every route) or the shipment ETA field (order detail). Disproved by: p95 of the other routes flat across the rollout.
3. H2 (default). The orders-db RDS instance got slower on its own (CPU, read latency, locks). Disproved by: RDS CPU and read latency at baseline across 13:08, together with a flat per-query time. A flat per-query time alone would not clear the database, because the query count per request is the thing H1 says moved.
4. H7 (default), added from history (past incident 2026-08-14 on this service: a database connection pool exhausted after a pool-size change; a lead only). Requests wait for a database connection because the pool is capped or exhausted. Disproved by: pool pending requests at zero and used connections well below the cap, and database connections far below the engine limit.
5. H4 (default). Pod CPU saturation or throttling on the three replicas. Disproved by: CPU headroom against limits, no throttling, autoscaler not at max.
6. H6 (default). The orders-reconcile worker in the same namespace started contending for the database around 13:08. Disproved by: its drain cadence and batch size unchanged across 13:08.
7. H5 (default). A traffic spike or bot raised the GET /orders load. Disproved by: GET /orders call rate unchanged against the previous window and a week earlier.

Already on the ledger before any worker starts (reused, not repeated): the call rate is flat (W1-Q15, which weighs on H5); the other routes are flat (W1-Q6, Q7, Q8, which weighs on H3); the pool shows no pending requests (W1-Q19, which weighs on H7); the per-query database time is flat (W1-Q22, which weighs on H2 but does not clear it). Workers still run for all seven, so each verdict is written against its own falsification query.

Budget: 35 of 60 queries used. Each worker gets 3 of the remaining 25, with 4 held back for at most one escalation.

Add, drop or re-rank anything before I spend the expensive queries?
```

**OPERATOR (line 3, at checkpoint #2):** `Fine, continue.`


---------------------------------------------------------------------------------------------------

## Phase 4: evidence (Deep: one worker per hypothesis, all dispatched in one message)

Dispatch (simulated inline; each section below is labelled with the tier it would run on). Every dispatch passes `model` explicitly:

| Worker | `model` passed | Tier | Query share | Lessons sent |
|---|---|---|---|---|
| H1 | stronger tier | strong | 3 | none (no lessons.md) |
| H2 | default tier | default | 3 | none |
| H3 | default tier | default | 3 | none |
| H4 | default tier | default | 3 | none |
| H5 | default tier | default | 3 | none |
| H6 | default tier | default | 3 | none |
| H7 | default tier | default | 3 | none (the worker is told the neutral statement only, never the past incident) |

Each prompt is the fenced prompt of agents/evidence.md with HYPOTHESIS, EXPECTED IF TRUE, FALSIFICATION QUERY, RUN=`<run directory>/raw/<ID>`, the three UTC windows, the budget share (3 queries, 1 GB logs, 70 CloudWatch metric requests, 3 waves), PREVIOUS VERDICT none, and the ledger/profile paths. Workers read the ledger's Query log first and reuse rows (`reused W1-Qn`) instead of repeating them.

----------------------------------------------------------------------------------------------

### [evidence H1, strong tier]

HYPOTHESIS: H1, release v2.15.0 (#2211) made GET /orders issue one items query per order (1 + N).
EXPECTED IF TRUE: step as the new pods take traffic; db spans per GET /orders trace about 51 vs about 1; per-query time flat; request rate flat; other routes flat.
FALSIFICATION QUERY (run first): db spans per request, incident hour vs the hour before the rollout; equal counts refute.
Reused from the ledger (not repeated): W1-Q15 (rate flat), W1-Q16/Q17 (ops/s x10.4, -7d normal), W1-Q22 (per-query span p95 flat 3.9-4.4 ms), W1-Q6..Q8 (other routes flat), W3-Q1/Q2 (code), W1-Q2/Q5 (rollout).

Wave 1 (falsification first; two searches are independent of each other, run together):

| ID | Command | Window (UTC) | World file | Result |
|---|---|---|---|---|
| H1-Q1 | `curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = server && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span.db.system =~ ".+" }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=30"` | incident 14:30-15:30 | `tempo-02.json` | 24 traces (>= 20). `matched` (db spans per trace): min 9, p50 41, p95 52, max 52, mean 38.9. Root duration 128-431 ms, p50 342 ms. 18,342 traces / 2.41 GB inspected |
| H1-Q2 | same query, `start=1792494000`, `end=1792497600` | baseline 11:00-12:00 (v2.14.0, before the rollout) | `tempo-03.json` | 24 traces (>= 20). `matched`: min 2, p50 3, p95 4, max 4, mean 3.08. Root duration 78-165 ms, p50 110 ms. 17,905 traces / 2.35 GB inspected |

The falsification did not hold: counts are not equal (median 3 to 41, max 4 to 52). The two windows are far apart in count, with no overlap of ranges beyond the low tail (incident min 9 > baseline max 4). The cap of 52 = 2 to 4 baseline-type spans + at most 50 per-order item queries, matching `limit` min(..., 50) in W3-Q1.

Wave 2 (confirming, a single trace waterfall from the incident window):

| ID | Command | World file | Result |
|---|---|---|---|
| H1-Q3 | `curl -sG "$TEMPO/api/v2/traces/e3ea7a3906419b466a28541306cc5ee1" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792503000" --data-urlencode "end=1792513800"` (start/end padded one hour each side) | `tempo-09.json` | root `GET /orders` 152 ms, status 200, route `/orders`, GET. Children, all `SPAN_KIND_CLIENT`: `GET auth-api /verify` (about 3.4 ms, server.address auth-api.auth.svc.cluster.local), one `SELECT orders` (about 3.0 ms), then 12 sequential `SELECT order_items` spans each about 3-4.5 ms with about 1.3-1.5 ms between them, ending about 70 ms after the root starts. 13 db spans in the fetched trace (the search reported matched = 14: one span fewer in the fetch, unexplained). About 82 ms of the 152 ms is not covered by any child span |

Analysis (local arithmetic on the rows above):
- Spans per request: p50 3 to 41 (x13.7), mean 3.08 to 38.9 (x12.6); sample sizes 24 and 24.
- Per-query time unchanged: db span durations 2.9-4.6 ms in both windows (W4 search rows; W1-Q22 p95 flat about 4 ms).
- Added latency is consistent with the added queries: root duration p50 110 to 342 ms (+232 ms); metric p50 0.09 to 0.31 s (W1-Q10); trace durations grow with span count (9 spans 128 ms, 22 spans 252 ms, 52 spans 399-431 ms): about 6-7 ms per extra query (about 4 ms of SELECT plus about 1.4 ms between spans plus unattributed time). (41 - 3) x 6.7 ms is about 255 ms against +232 ms observed.
- Conflict noted (the reason for the strong tier): the metric says database operations rose by about +3,570/s (W1-Q16: about 380 to about 3,960). At 56 req/s (W1-Q15) the sampled traces explain +35.8 spans x 56 = about +2,000/s. So about 1,570 ops/s (about 44% of the rise) is not explained by the sampled GET /orders SELECT spans. Possible readings, none checked: the ops metric counts operations that are not spans (for example one commit per pooled connection checkout, which `with self.pool.connection()` in each `list_items` call would add), the 24-trace mean is off, or another caller. It does not change the finding that the mechanism is directly exhibited in GET /orders traces, but the claim "the whole x10 in ops/s is this N+1" stays at `Likely`.
- Timing: the rollout was created about 13:05 (W1-Q2, W1-Q4, W1-Q5), the last normal GET /orders p95 sample is 13:06 and the first slow one 13:08 (W1-Q9, 120 s samples, 5 min rate window), DB ops/s jump on the same sample (W1-Q16). Helm prints 13:04:50 with no zone; the 145-minute ReplicaSet age and the Prometheus epoch step agree.

```text
VERDICT: H1 | Confirmed
summary: Release v2.15.0 (commit a4c1e9b, #2211) replaced one joined query in GET /orders with one items query per order. Traces show 3 db spans per request before the rollout (p50, max 4) and 41 (p50, max 52) after, with unchanged per-query time and request rate, and the latency step lands 3 minutes after the new pods were created.
weakest_link: timing alignment, the rollout (about 13:05, Helm prints no zone, corroborated by ReplicaSet and pod ages) against the first slow 120 s sample at 13:08 (Confirmed); separate open item: the metric's ops/s rise (+3,570/s) is about 1.8x what the sampled GET /orders spans explain (Likely that it is the same mechanism, not proven)

evidence:
- 24 vs 24 traces: db spans per GET /orders request p50 3 -> 41, max 4 -> 52 [tempo, H1-Q1/H1-Q2, 14:30-15:30 vs 11:00-12:00 on 2026-10-20] https://grafana.example.com/explore (datasource tempo-prod, the two queries above)
- One trace waterfall: 1 SELECT orders then 12 sequential SELECT order_items, 152 ms root [tempo, H1-Q3, trace e3ea7a3906419b466a28541306cc5ee1]
- Code at the deployed tag: for order in orders: order.items = repo.list_items(order.id) [git, reused W3-Q1/W3-Q2]
- Per-query span p95 flat about 4 ms, ops/s x10.4 at the same minute, request rate flat [reused W1-Q22, W1-Q16, W1-Q15]

timeline:
- 13:05 (about) — new ReplicaSet orders-api-7c9b6d8f5d created, Helm revision 24, v2.15.0 — reused W1-Q2, W1-Q5
- 13:06 — last normal p95 sample (0.163 s) — reused W1-Q9
- 13:08 — first slow sample (0.716 s), ops/s 4,031 — reused W1-Q9, W1-Q16

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H1-Q1 | tempo-prod | structural search GET /orders >> db spans, limit 30 | 14:30-15:30 | trace_samples cap 1h; actual 2.41 GB inspected | 24 traces, matched p50 41, max 52 |
| H1-Q2 | tempo-prod | same | 11:00-12:00 | 1h; actual 2.35 GB inspected | 24 traces, matched p50 3, max 4 |
| H1-Q3 | tempo-prod | trace e3ea7a39... by ID | padded 14:30-15:30 | 1 trace | 13 db spans, 12 sequential order_items |

gaps:
- Baseline is the hour before the rollout on the same day (11:00-12:00) because the code did not change in the previous release window; the -7d window would show the same v2.14.0 code but was not queried — no effect on the verdict.
- The fetched trace holds 13 db spans where the search said 14, and 82 ms of its 152 ms is not covered by child spans — effect: the per-request cost split (SELECT time vs other time) is approximate.
- ops/s residual (above) — effect: caps the claim "all of the x10 ops/s is this mechanism" at Likely.

untrusted_text:
- none seen

to_confirm_by_human:
- Ask the orders team whether the per-order items query was intended for a reason other than showing per-item status, and whether the pool's connection checkout in each items call also issues a commit that the database metric counts but traces do not show. Reproducing the slow request, or timing it on a staging copy, would confirm the added cost per request; this run may not do it.

lesson_candidates:
- failure-mode (tempo) Latency step on a list endpoint right after a release: count db spans per trace with a structural search (`route >> { span.db.system =~ ".+" }`) for the hour after vs the hour before; `matched` per trace goes from 3 to 41 for an N+1 — H1-Q1
- identifier (tempo) orders-api: resource.service.name "orders-api"; db spans carry span.db.system="postgresql"; routes are span.http.route with span.http.request.method; use `limit=30` and a 1 h window — H1-Q1
- noise (tempo) The structural search's `matched` can exceed the db spans in the fetched trace by one (14 vs 13); do not quote matched as an exact span count — H1-Q3

cost: 3 queries, 0.0 GB of logs (4.76 GB of traces inspected, Tempo bytes, not log GB), 0 CloudWatch metric requests
```

----------------------------------------------------------------------------------------------

### [evidence H2, default tier]

HYPOTHESIS: H2, orders-db slowed on its own (CPU, read latency, locks, connections), independent of the release.
EXPECTED IF TRUE: RDS CPUUtilization high, ReadLatency up, DatabaseConnections near the limit, per-query span time up, starting before or without the app change.
FALSIFICATION QUERY (first): RDS CPUUtilization and ReadLatency for orders-db across 13:08; at baseline refutes, together with a flat per-query time (reused W1-Q22) — a flat per-query time alone would not clear the database.

| ID | Command | World file | Result |
|---|---|---|---|
| H2-Q1 | `aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/q-rds-cpu-read.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json` with `q-rds-cpu-read.json` = two entries, namespace AWS/RDS, dimension DBInstanceIdentifier=orders-db, `CPUUtilization` and `ReadLatency`, Period 300, Stat Average | `cw-01.json` (reply timestamps newest first, UTC) | 67 points per metric, StatusCode Complete. CPUUtilization: 21.2-26.9 % up to the 13:05 bucket (23.87 at 13:05), then 37.1-44.0 % from the 13:10 bucket (41.29) to 15:30. ReadLatency: 0.52-0.67 ms throughout, no step. The reply also carried a DatabaseConnections series that H2 did not request and did not use (H7 owns it) |

(Note: `cw-01` holds three series for the one mapped call; H2 reads only `cpu` and `readlat`. CloudWatch metric requests charged: 2.)

Reading:
- ReadLatency flat (0.5-0.7 ms before and after) and per-query span time flat (reused W1-Q22: 3.9-4.4 ms). A database that slowed on its own would show queries getting slower. They did not.
- CPUUtilization did rise, from about 24 % to about 41 % (+17 points), but the first elevated 5-minute bucket is 13:10, after the application-side step (first slow app sample 13:08, ops/s x10.4 at the same sample). It rose as the query count rose and leaves about 59 % headroom; it did not come first and did not slow the queries.
- The per-request query count is NOT flat (that is H1), so the database is not "cleared" as a whole: the database is doing about 10x the operations. The hypothesis as written (slow on its own, independent of the release) is what is refuted.

```text
VERDICT: H2 | Ruled out
summary: orders-db did not slow down on its own. Read latency stays at 0.5-0.7 ms and per-query span time at about 4 ms across 13:08. CPU rose from about 24 % to about 41 % starting with the 13:10 bucket, after the application step, as a consequence of about 10x more database operations, with about 59 % headroom left.
weakest_link: CloudWatch 5-minute buckets against the 120 s application samples: the order of the 13:08 application step and the 13:10 CPU bucket rests on bucket boundaries (Likely for the order, Confirmed for "no read-latency change")

evidence:
- ReadLatency 0.52-0.67 ms at every 5-minute bucket from 10:00 to 15:30, no step [cloudwatch AWS/RDS orders-db, H2-Q1, 10:00-15:30]
- CPUUtilization 21-27 % to the 13:05 bucket, 37-44 % from the 13:10 bucket [cloudwatch, H2-Q1]
- Per-query db span p95 about 4 ms before and after [reused W1-Q22]

timeline:
- 13:05 bucket — CPUUtilization 23.87 % (still baseline) — cloudwatch
- 13:10 bucket — CPUUtilization 41.29 % (first elevated) — cloudwatch

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H2-Q1 | cloudwatch prod-read us-east-1 | AWS/RDS CPUUtilization + ReadLatency, orders-db, 300 s | 10:00-15:30 | 2 metric requests; actual 2 | CPU 24 -> 41 %, ReadLatency flat; link: CloudWatch console, RDS orders-db metrics |

gaps:
- Lock waits, deadlocks, IOPS, burst credits and Performance Insights were not read: Performance Insights is disabled (W2-Q10) and the other RDS metrics returned nothing in this setup (the reply held only the three series above) — effect: lock contention is not directly excluded, but a lock wait would show as slower queries, which the span and ReadLatency data do not show.
- The engine's max_connections was not read (parameter group not listed in the instance reply) — effect: none for this verdict; used by H7.

untrusted_text:
- none seen

to_confirm_by_human:
- A database administrator could open Performance Insights equivalents or the slow-query view for 13:00-13:20 to confirm the extra load is the per-order item selects. This run may not enable features or open sessions.

lesson_candidates:
- process (cloudwatch) RDS CloudWatch replies list timestamps newest first and in UTC; the 5-minute bucket is labelled by its start, so a 13:10 bucket does not describe 13:08 — H2-Q1

cost: 1 query, 0.0 GB of logs, 2 CloudWatch metric requests
```

----------------------------------------------------------------------------------------------

### [evidence H3, default tier]

HYPOTHESIS: H3, the other changes in v2.15.0 (structlog 25.3.0 to 25.4.0 for every route; shipment_eta on order detail) slowed requests.
EXPECTED IF TRUE: structlog: all routes slow after the rollout; ETA: GET /orders/{id} slower.
FALSIFICATION QUERY: per-route p95 across the rollout; flat on the other routes refutes. This is already in the ledger, so no new query is run (reused, not repeated).

Reused rows (instant p95 over 30 m, route and method as labels):

| Route | Previous window (12:30, W1-Q7) | -7d (W1-Q8) | Incident (15:30, W1-Q6) |
|---|---|---|---|
| GET /orders/{id} (order detail, touched by #2208) | 0.061 s | 0.061 s | 0.064 s |
| POST /orders | 0.139 s | 0.139 s | 0.142 s |
| PATCH /orders/{id} | 0.091 s | 0.091 s | 0.088 s |
| GET /healthz | 0.003 s | 0.003 s | 0.003 s |
| GET /orders (for contrast) | 0.181 s | 0.181 s | 0.712 s |

Reading: the structlog bump runs in the same process for every route; a logging slowdown would move POST /orders, PATCH, detail and healthz, and none moved (largest change +0.003 s). The ETA field lives on GET /orders/{id}, whose p95 is 0.064 s against 0.061 s. Only GET /orders (the route #2211 changed) moved.

```text
VERDICT: H3 | Ruled out
summary: Neither the structlog bump nor the shipment ETA field slowed requests. Every route other than GET /orders has the same p95 after the rollout as before it and as a week earlier (largest difference 0.003 s).
weakest_link: the instant p95 uses a 30-minute rate window at one point in time per window (Confirmed that no route other than GET /orders is slower at those points; an intra-window blip would not show)

evidence:
- p95 per route, three windows, all flat except GET /orders [prometheus, reused W1-Q6, W1-Q7, W1-Q8]
- Diff: structlog is a one-line dependency bump, order_detail adds one field [git, reused W2-Q3]

timeline:
- 13:05 — v2.15.0 rollout (all three commits go live together) — reused W1-Q5

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | — | reused W1-Q6, W1-Q7, W1-Q8 | 12:30, 15:30, -7d | 0 | other routes flat |

gaps:
- none

untrusted_text:
- none seen

to_confirm_by_human:
- none beyond H1's

lesson_candidates:
- none

cost: 0 queries, 0.0 GB of logs, 0 CloudWatch metric requests
```

----------------------------------------------------------------------------------------------

### [evidence H4, default tier]

HYPOTHESIS: H4, CPU saturation or throttling on the three replicas (capacity).
EXPECTED IF TRUE: CPU near its limit or throttling, autoscaler at max or replicas short, latency following load.
FALSIFICATION QUERY: CPU headroom against limits, no throttling, autoscaler not at max; headroom throughout refutes it.

The playbook's throttling query needs `container_cpu_cfs_throttled_periods_total`; that name is not in the metric list (W0-Q9), so it is not queried (identifiers are discovered, never guessed) and recorded as a gap. The three reads below are kubectl state reads (free, not counted):

| ID | Command | World file | Result |
|---|---|---|---|
| H4-Q1 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get deployment orders-api -o json` piped to `jq '.spec.template.spec.containers[] \| {name, resources, env: [.env[]?.name]}'` | `_empty` | no output: container requests and limits not readable |
| H4-Q2 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get hpa` | `_empty` | no output: not read as "no HPA" (a namespace this size normally prints at least a header); autoscaler state unknown |
| H4-Q3 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders top pod` | `_empty` | no output: current usage not readable |

Reused: W1-Q20 (CPU per pod 0.52-0.64 cores, three pods equal, series start 13:08, no earlier points); W1-Q2/Q4 (3 replicas Ready, 0 restarts); W1-Q15 (request rate flat).

Reading: there is no limit to compare CPU against, no throttling series, no autoscaler state and no CPU before 13:08. Circumstantial points only: load is flat while latency stepped at the rollout; the three pods use about the same CPU; the 82 ms of the sampled 152 ms request that no child span covers (H1-Q3) could be CPU time or pool waits, and cannot be told apart from here. CPU pressure caused by the heavier request path (a consequence of H1) is not excluded either.

```text
VERDICT: H4 | inconclusive
summary: Whether the pods are CPU-limited or throttled cannot be read: the container limits, the throttling series, the autoscaler and any CPU history before 13:08 are not available. The three pods use 0.52-0.64 cores each and the request rate is flat.
weakest_link: no CPU limit and no pre-rollout CPU baseline (Assumed)

evidence:
- CPU per pod 0.52-0.64 cores, equal across the three pods, from 13:08 only [prometheus, reused W1-Q20]
- Three kubectl reads (limits, HPA, top) returned no output [kubectl, H4-Q1..Q3]

timeline:
- 13:08 — first CPU point of the new pods — prometheus

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H4-Q1 | kubectl | get deployment orders-api, resources | now | free | no output |
| H4-Q2 | kubectl | get hpa | now | free | no output |
| H4-Q3 | kubectl | top pod | now | free | no output |

gaps:
- container requests/limits unreadable; HPA unreadable; no throttling series exposed; no CPU before 13:08 — effect: cannot confirm or exclude a capacity contribution; this verdict stays open

untrusted_text:
- none seen

to_confirm_by_human:
- Read the Deployment's CPU limit and the pods' throttling from the platform side, and compare CPU before and after the rollout from the old pods' history if it exists.

lesson_candidates:
- process (kubectl) In this setup `get deployments,services,ingresses,hpa`, `get deployment -o json`, `get hpa` and `top pod` print nothing, while `get pods`, `get rs`, `rollout history` and `helm history` work; use the latter for identifiers — H4-Q1
- process (prometheus) No CFS throttling series and no CPU series for replaced pods exist; container_cpu_usage_seconds_total starts at the new pods' creation — W1-Q20

cost: 3 queries (kubectl, not counted), 0.0 GB of logs, 0 CloudWatch metric requests
```

Dispatcher decision for H4: default tier, `inconclusive`, so it is escalated once to the strong tier with the previous verdict and its full query table in PREVIOUS VERDICT (after the others are merged; see below).

----------------------------------------------------------------------------------------------

### [evidence H5, default tier]

HYPOTHESIS: H5, a traffic spike or bot raised the GET /orders load.
EXPECTED IF TRUE: request count up against the previous window and -7d; volume shape.
FALSIFICATION QUERY: GET /orders call rate vs the previous window and a week earlier; no rise refutes it. Already in the ledger: W1-Q15 (no new query).

Reused: W1-Q15: 52.0-60.9 req/s at every 120 s sample from 10:00 to 15:30 (about 56 before 13:06, about 56 after 13:08), no step. W1-Q8 side check: the -7d p95 matches, and the -7d request-rate series was not pulled (the same metric with `offset 7d` was not requested in wave 1).

```text
VERDICT: H5 | Ruled out
summary: The GET /orders call rate did not change at the onset: about 56 req/s before 13:06 and after 13:08. Latency moved while load stayed flat, so this is not a traffic spike.
weakest_link: the rate is the route total over a 5-minute window; a change in who calls (clients, not volume) is not covered (Confirmed for volume)

evidence:
- GET /orders request rate 52.0-60.9 req/s throughout 10:00-15:30 [prometheus, reused W1-Q15]

timeline:
- 13:08 — latency step; no rate step — reused W1-Q9, W1-Q15

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | — | reused W1-Q15 | 09:30-15:30 (data from 10:00) | 0 | rate flat |

gaps:
- the same-time -7d request-rate series was not pulled in wave 1 — effect: the comparison is against the previous 3 hours, not a week earlier; the rate was flat across the onset itself, which is the part that matters

untrusted_text:
- none seen

to_confirm_by_human:
- none

lesson_candidates:
- none

cost: 0 queries, 0.0 GB of logs, 0 CloudWatch metric requests
```

----------------------------------------------------------------------------------------------

### [evidence H6, default tier]

HYPOTHESIS: H6, the orders-reconcile worker (same namespace) started contending for the database around 13:08.
EXPECTED IF TRUE: its drain cadence or batch size changes around 13:08, and orders-api queries wait on the database (per-query time up).
FALSIFICATION QUERY: its drain cadence and batch size unchanged across 13:08.

| ID | Command | Window (UTC) | World file | Result |
|---|---|---|---|---|
| H6-Q1 | `curl -sG "$LOKI/loki/api/v1/index/stats" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={namespace="orders", app="orders-reconcile"}' --data-urlencode "start=1792499400000000000" --data-urlencode "end=1792510200000000000"` | 12:30-15:30 | `loki-10.json` | stream `orders-reconcile` / `worker`: only 3 lines in the reply, all post-onset (15:00:00, 15:02:17, 15:04:34), `outbox drained batch=20/21/22 pending=0`, spacing 137 s, 1.05 MB processed. Nothing earlier than 15:00 returned |
| H6-Q2 | `curl -sG "$LOKI/loki/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={namespace="orders", app="orders-reconcile"} \|= "outbox drained"' --data-urlencode "start=1792501080000000000" --data-urlencode "end=1792502280000000000" --data-urlencode "direction=forward" --data-urlencode "limit=100"` (onset 13:08 minus 10 min to plus 10 min) | 12:58-13:18 | `loki-10.json` (same selector; the file's lines lie outside this window, so none are returned) | zero lines. For a worker that logs every 137 s about 9 lines were expected in 20 minutes: no log lines for it around the onset, so the cadence comparison across 13:08 cannot be made |

Reading: the stated falsification (cadence unchanged across 13:08) could not be run, because Loki returns no worker lines before 15:00. What the data does show: after the onset the worker drains on a steady 137 s cadence with `pending=0` (no backlog, nothing growing). The other half of the hypothesis's expectation, orders-api queries waiting on the database, is contradicted by results already in scope: per-query span time flat at 3.9-4.4 ms across 13:08 (reused W1-Q22), the pool shows no pending requests (reused W1-Q19), and the slow requests' own trace shows the added time is 12 sequential items queries of normal duration (it is the API's own work, not waits). The worker's own database use is not visible from here (its logs say "outbox drained", the query count is not exposed).

```text
VERDICT: H6 | Ruled out
summary: Contention from the reconcile worker would show as slower orders-api database calls, and they are not slower (about 4 ms per query before and after, no pool waits). The worker's own pre-onset cadence could not be compared: Loki returns no lines for it before 15:00. After the onset it drains steadily every 137 s with nothing pending.
weakest_link: the worker's cadence across 13:08 is not visible (no log lines before 15:00); the verdict rests on the orders-api side being unaffected (Confirmed for the API side, Assumed for the worker side)

evidence:
- Worker lines at 15:00:00, 15:02:17, 15:04:34: batch 20/21/22, pending=0 [loki, H6-Q1]
- No worker lines in 12:58-13:18 [loki, H6-Q2]
- Per-query db span p95 flat; pool pending 0 [reused W1-Q22, W1-Q19]

timeline:
- 15:00-15:05 — three drains at 137 s spacing, pending=0 — loki

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H6-Q1 | loki-prod | index stats / selector {namespace="orders", app="orders-reconcile"} | 12:30-15:30 | log_stats cap 48h; actual 1.05 MB | 3 lines, all after 15:00 |
| H6-Q2 | loki-prod | same selector, |= "outbox drained", forward, limit 100 | 12:58-13:18 | log_raw cap 30m; actual about 0 | 0 lines |

gaps:
- no worker log lines before 15:00 (log shipping gap or retention for that stream is unknown) — effect: cadence before/after the onset cannot be compared; the verdict relies on the API-side evidence

untrusted_text:
- none seen

to_confirm_by_human:
- Ask the owner of orders-reconcile whether its logs are shipped in full and whether it changed on 2026-10-20; its database query rate is not visible to this run.

lesson_candidates:
- noise (loki) orders-reconcile logs `outbox drained batch=N pending=0` about every 137 s; pending=0 is its normal state — H6-Q1
- process (loki) Loki returns no orders-reconcile lines before 15:00 on 2026-10-20 even for a stream that logs every 137 s: do not read an empty result for this stream as inactivity — H6-Q2

cost: 2 queries, 0.001 GB of logs, 0 CloudWatch metric requests
```

----------------------------------------------------------------------------------------------

### [evidence H7, default tier]  (from-history lead; the worker is given the neutral statement only)

HYPOTHESIS: H7, requests wait for a database connection because the connection pool is capped or exhausted.
EXPECTED IF TRUE: pool pending requests above zero, used connections pinned at a flat ceiling, database connections near the engine limit, pool-wait errors.
FALSIFICATION QUERY: pending requests at zero and used connections not pinned; database connections far below the engine limit.
Reused: W1-Q18 (pool used), W1-Q19 (pending).

| ID | Command | World file | Result |
|---|---|---|---|
| H7-Q1 | `aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/q-rds-conns.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json` with one entry: namespace AWS/RDS, DatabaseConnections, DBInstanceIdentifier=orders-db, Period 300, Stat Average | `cw-01.json` | 67 points, Complete. DatabaseConnections: 40-44 up to the 13:05 bucket, 43-48 from 13:10 (about +10 %). 1 metric request. The reply also carried CPU and ReadLatency, not requested and not used here |

Reading:
- Pool: `pending_requests` is 0 at every one of the 166 samples from 10:00 to 15:30, before and after the onset (reused W1-Q19). `used` goes from 14-19 to 17-24 and is not pinned at a flat ceiling (reused W1-Q18). The pool's configured maximum is not exposed, so "used well below the cap" is not shown; the absence of waiting is.
- Database side: 40-48 connections. The engine's max_connections was not read (the instance reply lists no parameter group, so the name was not discovered and no guess was made), so "far below the limit" is not shown either, but the connection count moved by about 10 % while operations moved by about 1,000 %, which is not what an exhausted connection limit looks like.
- Caveat on the pool signal: `pending_requests` is a sampled gauge (120 s), which can miss short bursts (playbook gotcha); no pool-timeout counter is exposed. H1 runs in parallel, so its trace rows are not in the ledger yet and are not used here. Persistent, uniform slowness at every sample argues against a burst-only effect.

```text
VERDICT: H7 | Ruled out
summary: There is no sign of pool waiting. Pool pending requests are zero at all 166 samples before and after the onset, used connections vary (14-19, then 17-24) instead of sitting on a ceiling, and the database sees 40-48 connections, about 10 % more than before.
weakest_link: the pending-requests gauge is sampled every 120 s and the pool maximum and engine max_connections were not read (Likely that no waiting happened between samples; Confirmed that no waiting appears at any sample)

evidence:
- pending_requests = 0 at every sample 10:00-15:30 [prometheus, reused W1-Q19]
- pool used 14-19 -> 17-24, not pinned [prometheus, reused W1-Q18]
- DatabaseConnections 40-44 -> 43-48 [cloudwatch, H7-Q1]

timeline:
- 13:10 bucket — DatabaseConnections first value 46 (previous 41) — cloudwatch

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H7-Q1 | cloudwatch prod-read us-east-1 | AWS/RDS DatabaseConnections orders-db, 300 s | 10:00-15:30 | 1 metric request; actual 1 | 40-44 -> 43-48 |

gaps:
- pool maximum size not exposed; RDS parameter group not listed, so max_connections unread — effect: "well below the cap" is argued from the absence of waits and the small change, not shown against a number

untrusted_text:
- none seen

to_confirm_by_human:
- Read the application's configured pool size and the engine's max_connections from their configuration and compare them with the observed 22-24 used and 48 database connections.

lesson_candidates:
- identifier (prometheus) Pool gauges: db_client_connections_usage and db_client_connections_pending_requests carry service="orders-api", pool="orders-db"; pending_requests is the wait signal (0 = no waits) — W1-Q19

cost: 1 query, 0.0 GB of logs, 1 CloudWatch metric request
```

----------------------------------------------------------------------------------------------

### H4 escalation (dispatcher rule: a default-tier `inconclusive` is re-dispatched once on the strong tier)

[evidence H4, escalated tier] `model` at the stronger tier, PREVIOUS VERDICT = the H4 block above with its full query table; target: the gap it names (limits, HPA, throttling, pre-rollout CPU). Remaining share: 3 queries (one used here).

| ID | Command | World file | Result |
|---|---|---|---|
| H4-Q4 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get events --sort-by=.lastTimestamp --field-selector involvedObject.kind=HorizontalPodAutoscaler` | `k8s-05.txt` | `No resources found in orders namespace.` Events expire after about 1 h; a rollout 2 h 25 min ago leaves none. Not evidence of "no HPA activity" |

Other options considered and not run, and why: a Prometheus query for `kube_deployment_status_replicas` (the name exists in W0-Q9, but its label set was never discovered, so a selector would be a guess); throttling queries (series not exposed); old pods' CPU (no points before 13:08 returned in W1-Q20, so another query for it would repeat the gap); `kubectl describe hpa <name>` (no HPA name discovered).

Reasoning on what is available: the latency change is a fixed offset (p50 +0.22 s, p95 +0.53 s) that appears with the rollout while request rate and per-pod CPU are flat; queueing from CPU exhaustion would normally grow with load and widen the tail relative to the median. These are consistent with H1's fixed extra work and say nothing about whether CPU is a limit. No data can settle it from here.

```text
VERDICT: H4 | inconclusive
summary: The data needed to test CPU limits, throttling, autoscaler state or CPU before the rollout does not exist in this setup. The shape of the change (a fixed added latency at the rollout, flat load, equal CPU across pods) points away from a capacity cause, but nothing here measures headroom.
weakest_link: no CPU limit, no throttling series and no pre-rollout CPU (Assumed)

evidence:
- CPU per pod 0.52-0.64 cores from 13:08 [prometheus, reused W1-Q20]
- Events for the HPA kind: none, and events older than about 1 h are gone [kubectl, H4-Q4]

timeline:
- (nothing new)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H4-Q4 | kubectl | get events, HPA kind | now | free | No resources found (expired) |

gaps:
- same as the default-tier verdict; plus the events gap

untrusted_text:
- none seen

to_confirm_by_human:
- Same as the default-tier verdict.

lesson_candidates:
- none new

cost: 1 query (kubectl, not counted), 0.0 GB of logs, 0 CloudWatch metric requests
```

Dispatcher result: the strong tier is also `inconclusive`; per the rule, it stays open with its gaps and is recorded in the ledger with the label `Assumed` (nothing supports it, nothing refutes it, the source could not be read), model column `default→strong`.

----------------------------------------------------------------------------------------------

### Merge (main session only)

Query IDs renumbered to wave 4: H1-Q1..Q3 = W4-Q1..Q3; H2-Q1 = W4-Q4; H4-Q1..Q3 = W4-Q5..Q7; H6-Q1..Q2 = W4-Q8..Q9; H7-Q1 = W4-Q10; H4-Q4 (escalation) = W4-Q11. Old IDs kept in the ledger's ID cell.
Untrusted text: none seen from any worker. Lesson candidates copied unchanged to the ledger (see ledger). Labels after the dispatcher rules:

| ID | Statement (short) | Tier | Worker label | Recorded label | Why |
|---|---|---|---|---|---|
| H1 | v2.15.0 / #2211 turns GET /orders into 1 + N queries | strong | Confirmed | Confirmed | cites change (diff, Helm), mechanism (W4-Q1 vs W4-Q2 span counts; W4-Q3 waterfall) and timing (rollout 13:05, step 13:08); the ops/s residual caps one sub-claim only |
| H2 | orders-db slow on its own | default | Ruled out | Ruled out | ReadLatency flat, per-query time flat, CPU rose after the app step |
| H3 | structlog / ETA changes | default | Ruled out | Ruled out | other routes flat (reused W1-Q6..Q8) |
| H4 | pod CPU saturation or throttling | default→strong | inconclusive | Assumed (open) | source unreadable; stays open |
| H5 | traffic spike | default | Ruled out | Ruled out | rate flat (reused W1-Q15) |
| H6 | orders-reconcile contention | default | Ruled out | Ruled out | API-side query time flat; worker cadence unreadable (named as weakest link) |
| H7 | pool cap / exhaustion (from-history) | default | Ruled out | Ruled out | pending 0 at every sample; used not pinned |

Stop-early rule: not applied, because H4 is still open (a single hypothesis `Confirmed` while all other plausible ones are `Ruled out` is not met).

Budget after Phase 4: counted queries = 35 + 7 (W4-Q1..Q3 Tempo, W4-Q4 CW, W4-Q8, Q9 Loki, W4-Q10 CW) = 42 of 60; kubectl reads (W4-Q5..Q7, Q11) not counted. Log GB scanned 0.05 of 10; CloudWatch metric requests 3 of 500; Tempo inspected bytes (4 searches/aggregations): 6.63 GB + 2.41 GB + 2.35 GB = 11.4 GB of trace data (no trace budget set).


---------------------------------------------------------------------------------------------------

## Ledger and profile writes (after the workers merged)

Files written by the main session at this point:
- `OUT/runs/orders-api-prod-20261020-1530/ledger.md` (all template sections, with the merged Query log W0-Q1 ... W4-Q11, Hypotheses with status lines, Gaps G1-G13, Memory, Lesson candidates)
- `OUT/runs/orders-api-prod-20261020-1530/profile.md` (run profile, marks updated)
- `OUT/runs/orders-api-prod-20261020-1530/raw/H1/matched-counts.tsv` (derived span counts per trace from W4-Q1/W4-Q2; the other raw directories `raw/H2..H7` and `raw/helper` were created and hold nothing else, since the replies were read inline)

## Phase 5: conclude

1. Causal chain: trigger (v2.15.0 / #2211, Confirmed), mechanism (1 + N queries per request, Confirmed), symptom (p50 and p95 up, Confirmed). All three legs of the cause are cited: change (diff W2-Q3, W2-Q4, W3-Q1, W3-Q2; Helm W1-Q5; ReplicaSet W1-Q2), mechanism (W4-Q1 vs W4-Q2, waterfall W4-Q3), timing (rollout about 13:05, first slow sample 13:08, W1-Q9, W1-Q16). Weakest link named: timing alignment (Confirmed at about two minutes' resolution); separate Likely sub-claim about the operations-rate residual (+3,570/s observed vs about +2,000/s explained).
2. Third parties and downstreams: none in the path. `auth-api` and `orders-db` are in-house; no vendor claim made.
3. Several hypotheses standing: only H4 (Assumed, open, not competing). Reported in the Open hypotheses table.
4. Deep additions: why it became an incident (no database, pool or error alarm in a position to catch slowness; no visible query-count guard or rollout latency check, Assumed).
5. History: the 2026-08-14 incident matched on service and symptoms but not on cause; named in the TL;DR as not a repeat. No recurrence or chronic follow-up applies.
6. Fixes in Follow-ups as prose with trade-offs; no command, patch or flag; each is a candidate for `pre-flight`.
7. `report.md`: report saved separately (all sections of templates/report.md, Deep mode). `ledger.md` and `profile.md` were written normally.

### MESSAGE 10 (end of Phase 5: TL;DR inline, path, open items, cost line)

```text
TL;DR
Cause: release v2.15.0 (Helm revision 24, about 13:05 UTC) shipped commit #2211, which makes GET /orders run one items query per order instead of one joined query: up to 51 database queries per request instead of 1. Each extra query adds about 6-7 ms, so p50 went from 0.09 s to 0.31 s and p95 from 0.18 s to 0.71 s. Label: Confirmed.
Weakest link: timing. The rollout (about 13:05 UTC; Helm prints 13:04:50 with no zone, backed by the 145-minute-old ReplicaSet and pods) against the first slow 120 s sample at 13:08. Confirmed, at about two minutes of resolution. One sub-claim is weaker: the database operations rate rose by about 3,570/s, about 1.8x what the sampled traces explain (about 2,000/s), so "all of the tenfold rise is this mechanism" is Likely, not proven. It does not lower the cause.
Impact: GET /orders (order history, a core flow) about 4x slower on all 3 replicas since 13:08 UTC (23:08 local), still ongoing at 15:30 UTC. Other routes and the request rate (about 56 req/s) unchanged. No sign of failed requests (Assumed: there is no error metric).
Severity: SEV2 (suggested) because a core flow is significantly degraded while still returning data. You decide.
Pattern: unclassified (reads as sudden, but the alarm history is missing and only 5.5 h of the 14 days of metrics came back). Assumed.
Recommended action: have the orders team choose between rolling the release back to v2.14.0 and shipping a fix that loads the items for all listed orders in one round trip again. A rollback is faster but also removes the shipment ETA field (#2208) and the structlog bump until they are re-released. Assess the chosen change with pre-flight and apply it in a separate session.
Ruled out: other v2.15.0 changes (every other route is flat), the database slowing on its own (read latency flat, CPU rose only after the application step), a connection-pool cap (pending requests zero at every sample), the orders-reconcile worker (query time unaffected), a traffic spike (call rate flat). One hypothesis stays open and is not a competing cause: CPU limits or throttling on the pods (Assumed; the data to test it does not exist here).
Similar past incidents: 2026-08-14-orders-api (same service and symptom, different cause: a pool-size change). Not a repeat.

Report: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/report.md. The ledger is complete at .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/ledger.md and the profile at .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/profile.md.

open items need your input

Cost: 42 queries (plus 28 access, kubectl, helm, git, gh and local reads not counted) · 0.05 GB of logs scanned · 3 CloudWatch metric requests · 11.4 GB of trace data inspected by Tempo (no budget set) · under $0.001 in metered charges
```

Open items for the operator (listed in the ledger Gaps G1-G13 and in the report): the p95 alert's name or rule UID (G1); the 7-day metric coverage and missing p99 (G3, G4); CPU limits and throttling (G5); the release's Helm values diff (G11); where error and load-balancer metrics live (G7).

---------------------------------------------------------------------------------------------------

## Phase 6: record

Proposed additions, built only from the ledger's Lesson candidates table and the run (incident per templates/incident.md, lessons per templates/lesson.md, profile merge). Nothing is written before the operator replies.

### MESSAGE 11 (record-phase diff)

```text
Record phase: proposed additions to .culiops/sre-investigate/. Nothing is written until you reply. Accept, edit or skip each item.

1. NEW incidents/2026-10-20-orders-api.md (run named a cause, Confirmed)
+ ---
+ id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
+ date: 2026-10-20
+ service: orders-api
+ env: prod
+ siblings: [all]
+ window_utc: 2026-10-20T13:08Z/ongoing
+ symptoms: [latency]
+ cause_category: deploy
+ cause: v2.15.0 (#2211) changed GET /orders to one items query per order (N+1), up to 51 queries per request instead of 1
+ deps: [orders-db]
+ label: Confirmed
+ mode: deep
+ time_to_cause_min: null
+ run: runs/orders-api-prod-20261020-1530
+ ---
+ 
+ # orders-api: GET /orders slow after v2.15.0
+ 
+ What happened: GET /orders p95 went from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) as a step at 13:08 UTC on 2026-10-20, three minutes after Helm revision 24 (v2.15.0) went live. Other routes and the request rate did not move. Still ongoing at 15:30 UTC.
+ Causal chain: trigger: commit #2211 replaced the joined query with one items query per order (Confirmed). Mechanism: database spans per GET /orders request went from a median of 3 to a median of 41 (max 52), per-query time unchanged at about 4 ms (Confirmed). Symptom: p50 and p95 up by about 6-7 ms per extra query (Confirmed). Weakest link: timing at about two minutes' resolution; the tenfold rise in database operations is about 1.8x what the sampled traces explain (Likely).
+ What found it: the structural trace search `route >> { span.db.system =~ ".+" }` for the incident hour against the hour before the rollout, with the code diff of the release.
+ What did not help: CPU and pool metrics (the pool showed no waits; database CPU rose only after the application step); a 14-day recurrence pull (the metrics returned 5.5 h); p90 and p99 queries (empty); Kubernetes events (expired).
+ Follow-ups raised: restore a single round trip for the order list or roll back; a query-count test for list endpoints; a rollout latency gate; error, load-balancer, throttling and p99 metrics; make the alert's history queryable.

2. NEW lessons.md (10 lines, each backed by a query of this run)
+ - type: identifier | service: orders-api | source: loki | statement: The Loki app label value for orders-api is orders (container api), not orders-api; the sibling worker is app orders-reconcile (container worker) in namespace orders | run: orders-api-prod-20261020-1530 | query_id: W0-Q13 | re-verify: no
+ - type: identifier | service: orders-api | source: tempo | statement: Trace service name is orders-api; db spans carry span.db.system=postgresql; route and method are span.http.route and span.http.request.method; use limit 30 and a 1 h window per search | run: orders-api-prod-20261020-1530 | query_id: W4-Q1 | re-verify: no
+ - type: identifier | service: orders-api | source: prometheus | statement: Pool gauges db_client_connections_usage and db_client_connections_pending_requests carry service=orders-api and pool=orders-db; pending_requests above 0 is the wait signal | run: orders-api-prod-20261020-1530 | query_id: W1-Q19 | re-verify: no
+ - type: process | service: orders-api | source: prometheus | statement: histogram_quantile for 0.90 and 0.99 on http_server_request_duration_seconds_bucket returned an empty matrix while 0.5 and 0.95 returned data; compare p50 with p95 instead and check the quantile exists first | run: orders-api-prod-20261020-1530 | query_id: W1-Q13 | re-verify: yes
+ - type: process | service: orders-api | source: prometheus | statement: A 14-day request returned only 5.5 h of data and container CPU series for replaced pods are absent before the new pods start; check coverage with a short query before planning a recurrence pull | run: orders-api-prod-20261020-1530 | query_id: W1-Q21 | re-verify: yes
+ - type: process | service: orders-api | source: kubectl | statement: In this cluster get deployments,services,ingresses,hpa, get hpa, top pod and get cronjobs -A print nothing while get pods, get rs, rollout history and helm history work; events are gone after about 1 hour, so read them in the first wave | run: orders-api-prod-20261020-1530 | query_id: W0-Q17 | re-verify: yes
+ - type: process | service: any | source: cloudwatch | statement: RDS get-metric-data replies list timestamps newest first and in UTC, and a 5-minute bucket is labelled by its start; a 13:10 bucket does not describe 13:08 | run: orders-api-prod-20261020-1530 | query_id: W4-Q4 | re-verify: no
+ - type: noise | service: orders-api | source: loki | statement: orders-reconcile logs outbox drained batch=N pending=0 about every 137 s; pending=0 is its normal state | run: orders-api-prod-20261020-1530 | query_id: W4-Q8 | re-verify: no
+ - type: process | service: orders-api | source: loki | statement: Loki returned no orders-reconcile lines before 15:00 on 2026-10-20 for a stream that logs every 137 s; do not read an empty result for this stream as inactivity | run: orders-api-prod-20261020-1530 | query_id: W4-Q9 | re-verify: yes
+ - type: failure-mode | service: orders-api | source: tempo | statement: Latency step on a list endpoint right after a release: structural search route >> { span.db.system =~ ".+" } for the hour after vs the hour before; matched per trace going from about 3 to about 41 is an N+1 (one items query per row) | run: orders-api-prod-20261020-1530 | query_id: W4-Q1 | re-verify: no
(No existing lessons, so no confirm, re-verify, contradict or drop updates.)

3. NEW profiles/orders-api-prod.md = this run's profile.md (first run for the service), identifiers added: Loki {namespace="orders", app="orders", container="api"}; Tempo service orders-api and its span attributes; Prometheus labels and pool gauges; Deployment and Helm release orders-api; RDS orders-db; dependency auth-api (new, seen in one trace); sibling worker orders-reconcile; image tag to git tag rule (v2.15.0 = v2.15.0). Still (unverified): default branch, HPA, ingress, error tracker. Stale identifiers: none.

Candidates for the skill itself (not written now, to be proposed in a normal session): (a) the traces playbook's N+1 section could use the structural search's per-trace `matched` count as a one-call first check before fetching traces by ID; (b) the changes playbook could note that `helm history` prints dates with no zone, so a deploy time needs a second source.
```

**OPERATOR (line 4, shown the record-phase diff):** `Yes, write them.`

### After the operator's reply (line 4): files written

All three items accepted as proposed. Written under the simulated output root `OUT/`:
- `OUT/incidents/2026-10-20-orders-api.md` (front matter + body as shown in MESSAGE 11)
- `OUT/lessons.md` (the 10 lines as shown; no pipe character inside any statement)
- `OUT/profiles/orders-api-prod.md` (copy of the run's `profile.md`)

### MESSAGE 12 (after writing)

```text
Written: incidents/2026-10-20-orders-api.md, lessons.md (10 lines), profiles/orders-api-prod.md, all under .culiops/sre-investigate/. Nothing else was changed, and nothing was committed. The two candidates for the skill itself were not written; they are noted for a normal session.
```

---------------------------------------------------------------------------------------------------

## Summary of files written in this run (all under OUT = CASE/out)

| File | What |
|---|---|
| `runs/orders-api-prod-20261020-1530/ledger.md` | working record, all sections |
| `runs/orders-api-prod-20261020-1530/profile.md` | run profile |
| `runs/orders-api-prod-20261020-1530/raw/H1/matched-counts.tsv` | derived span counts from W4-Q1/W4-Q2 |
| `runs/orders-api-prod-20261020-1530/raw/{H2,H3,H4,H5,H6,H7,helper}/` | created, empty |
| `incidents/2026-10-20-orders-api.md` | record phase, after the reply |
| `lessons.md` | record phase, after the reply |
| `profiles/orders-api-prod.md` | record phase, after the reply |
| `run-log.md` | this log |
| `runs/orders-api-prod-20261020-1530/report.md` | report saved separately |

## World files opened (each mapped by a command above)

environment.md, ls-01.txt, env-01.txt, sts-01.json, iam-01.json, iam-02.json, k8s-01.txt, k8s-02.txt, k8s-03.txt, prom-09.json, prom-10.json, loki-06.json, _default.txt, loki-01.json, loki-02.json, loki-03.json, loki-04.json, tempo-06.json, k8s-07.txt, k8s-06.txt, k8s-05.txt, k8s-04.txt, helm-01.txt, prom-03.json, prom-04.json, prom-14.json, prom-01.json, prom-02.json, prom-11.json, prom-12.json, prom-07.json, prom-05.json, prom-13.json, prom-06.json, prom-08.json, tempo-01.json, tempo-08.json, git-03.txt, git-01.txt, git-02.txt, gh-01.json, rds-01.json, repo/orders_api/handlers/list_orders.py, repo/orders_api/repository.py, ls-02.txt, incidents/2026-08-14-orders-api.md and incidents/2026-09-30-catalog-api.md (both read as the files the front-matter grep ran over), tempo-02.json, tempo-03.json, tempo-09.json, cw-01.json, loki-10.json, _empty.txt.

Never opened, because no command of mine mapped to them: tempo-04.json, tempo-05.json, tempo-07.json, tempo-10.json, loki-05.json, loki-07.json, loki-08.json, loki-09.json, loki-11.json, loki-12.json, loki-13.json.

Notes on world behaviour worth knowing (recorded as lessons or gaps, not as findings about the estate): the simulated simulator returned rows for 3 actions I did not ask for and omitted 3 I did; p90/p99 queries returned empty; the 14-day recurrence pull and the CPU series returned only partial coverage; kubectl reads for deployments, hpa, top and cronjobs returned nothing; Loki returned no worker lines before 15:00.
