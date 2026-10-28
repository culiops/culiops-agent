# Ledger: orders-api prod 20261020-1530

Run directory: `.culiops/sre-investigate/runs/orders-api-prod-20261020-1530/` (simulated under `out/`). Times are UTC.

Mode: Deep
Budget used: 42 of 60 counted queries (a counted query is a call to Prometheus, Loki, Tempo, Grafana, CloudWatch, CloudTrail, EventBridge, Scheduler or RDS; identity and write-check calls, kubectl/helm state reads, and local git/gh reads are logged but not counted; environment.md has no `budgets:` block, so the template's Deep defaults apply) · 0.05 of 10 GB log bytes (Loki: 48.2 MB probe + 1.05 MB) · 3 of 500 CloudWatch metric requests · other metered units: Tempo inspected 11.4 GB across 4 aggregation/search calls (no trace budget set)

## Problem

| Field | Value |
|---|---|
| What | Reporter's words: "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing." Measurable restatement: GET /orders p95 0.71 s against 0.18 s baseline (about 3.9x) and p50 0.31 s against 0.09 s (about 3.4x), as a step at 13:08 UTC on 2026-10-20, still present at 15:30 UTC (W1-Q6..Q12) |
| Where | orders-api, prod, EKS cluster `prod`, namespace `orders`, Deployment/Helm release `orders-api`, 3 replicas (one ReplicaSet). Siblings in scope: the 3 replicas (no regions, shards or tenants). Route in scope: GET /orders |
| When | Reported: "since early this afternoon UTC" (rough, from the reporter). True onset 13:08 UTC (first slow sample; last normal sample 13:06; derived series, 120 s samples, 5 min rate window). Deploy about 13:05 UTC (Helm revision 24 printed 13:04:50 without a zone; ReplicaSet and pods 145/144 minutes old at 15:30) |
| Who is affected | Callers of GET /orders (order history, a listed core flow). Customer-facing: assumed (no load-balancer or error metric to size users). Other routes unaffected |
| Trigger | "the p95 alert" on GET /orders; alert name, rule UID and link not given; no ticket named |
| Mitigations already applied | none known (none reported) |
| Assumptions made at intake | (1) "early this afternoon UTC": explicit zone UTC, rough time, anchored at 13:00 UTC, window starts 30 minutes earlier (12:30). (2) `date -u` printed nothing in the session, so "now" = 2026-10-20 15:30 UTC (newest sample in the backends), told to the operator. (3) User zone = Australia/Brisbane (UTC+10) from environment.md, used only for the local column. (4) git rev-parse printed nothing, so the working directory is treated as the repo root; `.culiops/sre-investigate` is git-ignored (check-ignore exit 0). (5) No `budgets:` block, so template Deep defaults. (6) Customer-facing impact and "no failed requests" are Assumed |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| `prod-read` (account 111122223333, us-east-1) | assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded); account matches environment.md | no write allowed in the 7 simulator rows that match the fixed list (all implicitDeny); 3 actions got no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) = unchecked, a gap; 3 extra rows returned for actions not asked (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy), also implicitDeny, not counted. Not a full proof | session valid; boxed warning not shown (nothing allowed) |
| kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders` | assumed-role ReadOnly SSO principal, group `eks-readonly` (session name not recorded); current context = this context | no write verbs in `orders`: only `[create]` on selfsubjectreviews / selfsubjectaccessreviews / selfsubjectrulesreviews (excluded by rule) and `*.*` `[get list watch]` | RBAC list complete (no incompleteness notice) |
| Grafana datasources `prom-prod`, `loki-prod`, `tempo-prod` (token `GRAFANA_SERVICE_ACCOUNT_TOKEN`) | service account, privileges not inspectable | not applicable (read-only API use) | token variable set (name only); all three answered. CloudWatch (RDS) uses `prod-read`. Culibox: `command -v agentbox-env` failed, nothing printed |

## Impact

| Field | Value |
|---|---|
| Symptom | GET /orders (order history) about 4x slower; sampled responses and traces return 200; no error or status metric exists to count failures |
| Affected | prod, namespace orders, all 3 replicas, GET /orders only. p95 0.712 s vs 0.181 s (previous window and -7d), p50 about 0.31 s vs about 0.09 s. Other routes flat (GET /orders/{id} 0.064 vs 0.061 s, POST /orders 0.142 vs 0.139, PATCH /orders/{id} 0.088 vs 0.091). GET /orders call rate unchanged at about 56 req/s. Core flow: order history (listed in environment.md) |
| Since / ongoing | 13:08 UTC (23:08 Australia/Brisbane) / ongoing at 15:30 UTC (p95 0.66-0.75 s throughout) |
| Suggested severity | SEV2 because a listed core flow is significantly degraded while still returning data; not SEV1 (no sign of failing requests, not down). The incident owner decides |
| Basis | W1-Q6, W1-Q7, W1-Q8, W1-Q9, W1-Q10, W1-Q11, W1-Q12, W1-Q15 · label: Confirmed for the latency change; "customer-facing" and "no failed requests" are Assumed (no SLO, no load-balancer, no error metric) |
| Third party in the path | none seen. Dependencies found: RDS PostgreSQL `orders-db` (in-house) and `auth-api` (in-cluster, seen as a 3.4 ms client span in one trace, W4-Q3) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-20 12:30:00 | 2026-10-20 15:30:00 |
| Baseline (previous) | 2026-10-20 09:30:00 | 2026-10-20 12:30:00 |
| Baseline (−7d) | 2026-10-13 12:30:00 | 2026-10-13 15:30:00 |

Data coverage actually returned: Prometheus from 2026-10-20 10:00 (so the previous window is covered only from 10:00); CloudWatch RDS from 10:00; trace baseline window used for spans-per-request: 2026-10-20 11:00-12:00 (same version v2.14.0, before the rollout); trace incident sample: 14:30-15:30.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | unavailable: alert name not given; Prometheus has no `ALERTS` series (W0-Q9, W0-Q10); Grafana alert annotations returned `{}` (W0-Q11). Sibling alarms: none known |
| Signal, 14d at 1h resolution | statistic: `increase(db_client_operation_duration_seconds_count[1h])` (counter, as the playbook table prescribes); latency itself not pulled (a 14-day histogram_quantile exceeds the 12h cap and no recording rule exists). Data returned covers only 2026-10-20 10:00-15:30 (5.5 h of 336 h): hourly increase about 1.4M in the 10:00-12:00 hours, about 13M in the 13:00 hour, about 14M per hour after. Median/p95/max of a 14-day baseline cannot be computed |
| Coverage | alarm history: none. Metrics: first sample 2026-10-20 10:00 UTC (W1-Q21), 5.5 h of the 14 days asked. Same clock window 2026-10-13: p95 max 0.200 s, p50 max 0.100 s, DB ops/s 355-404 (W1-Q11, W1-Q12, W1-Q17): normal |
| Class | `unclassified` · shape: `step` |
| Reason | The class rules need the 30-day alarm history and 14 days of signal; neither was returned. What is known: before the onset the previous 3 h p95 never exceeded 0.201 s and the same clock window a week earlier never exceeded 0.200 s (a level 3.7x higher now); the change is one persistent step at 13:08, not periodic; no schedule found (W2-Q7..Q9). This points to `sudden` but the class is not assigned from coverage this short. Shape: step (p50 and p95 both moved so not a ceiling; call rate flat so not volume) |
| Label and queries | Assumed (class) · W0-Q10, W0-Q11, W1-Q9, W1-Q11, W1-Q21; shape: Confirmed · W1-Q9, W1-Q10, W1-Q15, W1-Q16 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-07 09:40 (zone not printed) | Helm revision 23 deployed, v2.14.0 (later superseded) | helm history | W1-Q5 |
| 2026-10-16 | commit 3f9d6a1 "deps: bump structlog to 25.4.0 (#2203)" (commit date; merged is not deployed) | git | W2-Q2, W2-Q4 |
| 2026-10-19 | commits 7be20d4 "return shipment ETA on order detail (#2208)" and a4c1e9b "load items per order in list handler (#2211)" (commit dates) | git | W2-Q2, W2-Q4 |
| 2026-10-20 about 13:04:50 (Helm, no zone; 13:05 from ReplicaSet age) | Helm revision 24 deployed: chart orders-api-4.2.0, image v2.15.0; new ReplicaSet orders-api-7c9b6d8f5d created (3 pods, ages 145/144/144 min at 15:30) | helm history; kubectl | W1-Q5, W1-Q2, W1-Q4 |
| 13:06 | last normal GET /orders p95 sample: 0.163 s | prometheus | W1-Q9 |
| 13:08 | first slow sample: p95 0.716 s, p50 0.295 s; DB ops/s 4,031 (from about 365); pool used 22 (from 14); latency step = onset | prometheus | W1-Q9, W1-Q10, W1-Q16, W1-Q18 |
| 13:05 bucket / 13:10 bucket | RDS CPUUtilization 23.9 % then 41.3 % (first elevated 5-minute bucket is 13:10); DatabaseConnections 41 then 46 | cloudwatch | W4-Q4, W4-Q10 |
| 13:08-15:30 | p95 stays 0.66-0.75 s; ops/s 3,820-4,089; no recovery | prometheus | W1-Q9, W1-Q16 |
| 14:30-15:30 | trace sample: db spans per GET /orders 9-52 (p50 41), root duration p50 342 ms | tempo | W4-Q1 |
| not seen | CloudTrail writes, EventBridge rules, Scheduler schedules, CronJobs, RDS events, deploy annotations: empty replies. Kubernetes events: expired | various | W2-Q5..Q9, Q11, Q12; W1-Q3 |
| 15:00-15:05 | orders-reconcile drains every 137 s, pending=0 (no earlier lines returned) | loki | W4-Q8 |

Rows from the reporter, not from a query: "since early this afternoon" and "the p95 alert keeps firing".

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Release v2.15.0 (#2211) changed GET /orders from one joined query to one items query per order, so each request makes up to 51 DB queries instead of 1 | step as the new pods take traffic; db spans per GET /orders trace about 51 vs about 1; p50 rise about 50 x per-query time; per-query time and request rate flat | db spans per request, incident hour vs the hour before the rollout (>= 20 traces each); equal counts refute | strong | Confirmed |
| H3 | The other v2.15.0 changes (structlog bump on every route, shipment ETA on order detail) slowed requests | other routes slower after the rollout | per-route p95 across the rollout; flat refutes | default | Ruled out |
| H2 | orders-db became slow on its own (CPU, read latency, locks) | RDS CPU up and read latency up before/without the app change; per-query time up | RDS CPUUtilization and ReadLatency across 13:08, with flat per-query time (not sufficient alone) | default | Ruled out |
| H7 (from-history:2026-08-14-orders-api.md) | Requests wait for a DB connection because the pool is capped or exhausted | pending requests > 0; used pinned at a ceiling; DB connections near the engine limit | pending at zero and used not pinned; DB connections far below the limit | default | Ruled out |
| H4 | Pod CPU saturation or throttling on the three replicas | CPU near limit or throttling; autoscaler at max; latency following load | CPU headroom against limits; no throttling; autoscaler not at max | default→strong | Assumed |
| H6 | The orders-reconcile worker started contending for the database around 13:08 | its cadence or batch changes at 13:08; orders-api queries wait | its drain cadence and batch unchanged across 13:08 | default | Ruled out |
| H5 | A traffic spike or bot raised the GET /orders load | request count up vs previous window and -7d | call rate unchanged vs previous window | default | Ruled out |

- `H1` status: supported · evidence: W4-Q1, W4-Q2, W4-Q3 (spans per request 3 -> 41, waterfall), W3-Q1, W3-Q2, W2-Q3, W2-Q4 (code), W1-Q2, W1-Q5 (rollout), W1-Q9, W1-Q10 (step), W1-Q15, W1-Q16, W1-Q22 (rate flat, ops x10.4, per-query flat) · note: strong tier because three signals must be correlated and the ops/s rise (+3,570/s) is about 1.8x the +2,000/s the sampled spans explain; verdict Confirmed, worker's cited query itself exhibits the mechanism; open sub-claim "all of the x10 ops/s is this mechanism" = Likely.
- `H3` status: refuted · evidence: reused W1-Q6, W1-Q7, W1-Q8 (no new query) · note: default tier; every other route flat, largest difference 0.003 s.
- `H2` status: refuted · evidence: W4-Q4 (CPU 24 -> 41 % from the 13:10 bucket, ReadLatency 0.5-0.7 ms flat), reused W1-Q22 · note: default tier; CPU rise follows the app step and is a consequence of H1.
- `H7` status: refuted · evidence: reused W1-Q18, W1-Q19 (pending 0 at 166 of 166 samples; used 14-19 -> 17-24, not pinned), W4-Q10 (DB connections 40-44 -> 43-48) · note: seeded from history (`from-history:2026-08-14-orders-api.md`), a lead only; the worker got the neutral statement; weakest point: sampled gauge, pool maximum and engine max_connections not read.
- `H4` status: testing, left open · evidence: W4-Q5, W4-Q6, W4-Q7 (empty outputs), W4-Q11 (events expired), reused W1-Q20 · note: default tier returned inconclusive, escalated once to strong, still inconclusive; recorded Assumed (open) with gaps G5.
- `H6` status: refuted · evidence: W4-Q8, W4-Q9 (no worker lines before 15:00), reused W1-Q22, W1-Q19 · note: refuted through the API side (per-query time flat, no pool waits); the worker's own cadence across 13:08 not visible (gap G8).
- `H5` status: refuted · evidence: reused W1-Q15 (no new query) · note: -7d request-rate series not pulled; the rate was flat across the onset.
- `from-history` seeding: only H7 (see Memory).

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (local clone `~/src/orders-api`, read by ref; `gh` compare as cross-check) | not read (unverified) | not read | not read; tags v2.14.0 and v2.15.0 present locally (W2-Q1), so the clone holds both deployed refs | prod now: tag v2.15.0 = image v2.15.0 (Helm revision 24); top commit of v2.14.0..v2.15.0 is a4c1e9b (W2-Q2), taken as the tag's commit (inferred). Previous: v2.14.0 (Helm revision 23). Image tag to ref rule: Helm APP VERSION `v2.15.0` equals git tag `v2.15.0` |

## Query log

Deeplink rule: for Prometheus, Loki and Tempo rows the human deeplink is `https://grafana.example.com/explore` with the datasource UID shown, the expression in the Source cell and the window in the Range cell (no token in any link); for kubectl, helm, aws, git and gh rows the read-only command shown is the deeplink. Start (UTC) is `n/a`: the session's `date -u +%H:%M:%S` printed nothing. Rows marked (not counted) are logged but not counted against the budget. Identifiers: all marked verified unless stated.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | n/a | aws sts get-caller-identity --profile prod-read | now | free (not counted) | account 111122223333 matches; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b · label Confirmed · link: cmd |
| W0-Q2 | n/a | aws iam get-role (role name from W0-Q1) | now | free (not counted) | role path /aws-reserved/sso.amazonaws.com/ resolved · link: cmd |
| W0-Q3 | n/a | aws iam simulate-principal-policy, fixed 10 actions | now | free (not counted) | 7 requested actions implicitDeny; 3 requested actions no row (gap); 3 unrequested rows implicitDeny · link: cmd |
| W0-Q4 | n/a | kubectl auth whoami --context $CTX | now | free (not counted) | ReadOnly SSO role, group eks-readonly · link: cmd |
| W0-Q5 | n/a | kubectl config current-context | now | free (not counted) | = $CTX · link: cmd |
| W0-Q6 | n/a | kubectl auth can-i --list --context $CTX --namespace orders | now | free (not counted) | no write verbs · link: cmd |
| W0-Q7 | n/a | token presence for GRAFANA_SERVICE_ACCOUNT_TOKEN (`${VAR:+x}`) | now | free (not counted) | set · link: cmd |
| W0-Q8 | n/a | loki-prod index stats probe `{namespace="orders"}` | 15:15-15:30 | est. small; actual 48.2 MB | streams for app=orders and app=orders-reconcile; label namespace=orders verified · link: explore loki-prod |
| W0-Q9 | n/a | prom-prod label __name__ values | now | free | 11 metric names; no ALERTS, no spanmetrics, no CFS throttling · link: explore prom-prod |
| W0-Q10 | n/a | prom-prod `max_over_time(ALERTS{alertstate="firing"}[1h])` step 3600 | 2026-09-20 15:30 - 2026-10-20 15:30 | small; actual empty | empty matrix: no ALERTS series (alert history gap G1) · link: explore prom-prod |
| W0-Q11 | n/a | grafana /api/annotations type=alert limit=100 | 30 d to 15:30 | free | `{}` (no alert annotations) · link: grafana annotations |
| W0-Q12 | n/a | loki-prod labels (helper) | now | free | app, container, namespace, stream · link: explore loki-prod |
| W0-Q13 | n/a | loki-prod label app values (helper) | now | free | catalog-api, notify-worker, orders, orders-reconcile, payments-worker; app=`orders` verified, `orders-api` is not an app value · link: explore loki-prod |
| W0-Q14 | n/a | loki-prod label namespace values (helper) | now | free | catalog, notify, orders, payments · link: explore loki-prod |
| W0-Q15 | n/a | loki-prod label container values (helper) | now | free | api, worker · link: explore loki-prod |
| W0-Q16 | n/a | tempo-prod /api/v2/search/tags (helper) | now | free | resource: service.name, service.version, k8s.*; span: db.system, http.route, http.request.method, ... · link: explore tempo-prod |
| W0-Q17 | n/a | kubectl get deployments,services,ingresses,hpa -n orders (helper) | now | free (not counted) | no output (unusable; not read as "none exist") · link: cmd |
| W0-Q18 | n/a | grafana /api/search?query=orders-api&type=dash-db (helper) | now | free | `{}` (no dashboards) · link: grafana search |
| W0-Q19 | n/a | ls .culiops/service-discovery (helper) | now | local (not counted) | No such file or directory (no catalog) |
| W1-Q1 | n/a | kubectl rollout history deployment/orders-api -n orders | now | free (not counted) | revisions 23 (v2.14.0) and 24 (v2.15.0), chart 4.2.0 both · link: cmd |
| W1-Q2 | n/a | kubectl get rs -n orders --sort-by=.metadata.creationTimestamp | now | free (not counted) | old RS 5f8d9c7b6a 0/0/0 age 13d; new RS 7c9b6d8f5d 3/3/3 age 145m · link: cmd |
| W1-Q3 | n/a | kubectl get events -n orders --sort-by=.lastTimestamp | now | free (not counted) | No resources found (events expire about 1 h; gap G6) · link: cmd |
| W1-Q4 | n/a | kubectl get pods -n orders | now | free (not counted) | 3 pods Running 1/1, 0 restarts, ages 145/144/144 min · link: cmd |
| W1-Q5 | n/a | helm history orders-api -n orders --max 10 | now | free (not counted) | rev 23 Oct 7 09:40:12 v2.14.0 superseded; rev 24 Oct 20 13:04:50 v2.15.0 deployed (no zone printed) · link: cmd |
| W1-Q6 | n/a | prom-prod `histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[30m])))` instant | at 15:30 (incident) | small | GET /orders 0.712; /orders/{id} 0.064; POST 0.142; PATCH 0.088; healthz 0.003; service label verified · link: explore prom-prod |
| W1-Q7 | n/a | same expression, instant | at 12:30 (previous) | small | 0.181; 0.061; 0.139; 0.091; 0.003 · link: explore prom-prod |
| W1-Q8 | n/a | same expression with `offset 7d`, instant | 15:30, -7d | small | 0.181; 0.061; 0.139; 0.091; 0.003 (reply stamped 2026-10-13 15:30) · link: explore prom-prod |
| W1-Q9 | n/a | prom-prod `histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))` | 09:30-15:30 step 120 (data from 10:00) | within 12h cap | 0.160-0.201 s to 13:06; 0.716 at 13:08; 0.661-0.755 to 15:30: a step · link: explore prom-prod |
| W1-Q10 | n/a | same with quantile 0.5 | 09:30-15:30 step 120 | within cap | 0.080-0.100 s to 13:06; 0.281-0.339 s from 13:08 · link: explore prom-prod |
| W1-Q11 | n/a | Q9 expression with `offset 7d` | 09:30-15:30, -7d | within cap | 0.160-0.200 s throughout (reply stamped 2026-10-13) · link: explore prom-prod |
| W1-Q12 | n/a | Q10 expression with `offset 7d` | 09:30-15:30, -7d | within cap | 0.080-0.100 s throughout · link: explore prom-prod |
| W1-Q13 | n/a | same with quantile 0.9 | 09:30-15:30 step 120 | within cap | empty matrix (unexplained; gap G4) · link: explore prom-prod |
| W1-Q14 | n/a | same with quantile 0.99 | 09:30-15:30 step 120 | within cap | empty matrix (gap G4) · link: explore prom-prod |
| W1-Q15 | n/a | prom-prod `sum by (route, method) (rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders", method="GET"}[5m]))` | 09:30-15:30 step 120 | small | 52.0-60.9 req/s throughout, no step · label Confirmed · link: explore prom-prod |
| W1-Q16 | n/a | prom-prod `sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))` | 09:30-15:30 step 120 | small | 361-401 ops/s to 13:06; 3,820-4,089 from 13:08 (x10.4) · link: explore prom-prod |
| W1-Q17 | n/a | same with `offset 7d` | 09:30-15:30, -7d | small | 355-404 ops/s throughout · link: explore prom-prod |
| W1-Q18 | n/a | prom-prod `sum by (pool, state) (db_client_connections_usage{service="orders-api"})` | 09:30-15:30 step 120 | small | pool orders-db used 14-19 then 17-24 · link: explore prom-prod |
| W1-Q19 | n/a | prom-prod `sum by (pool, state) (db_client_connections_pending_requests{service="orders-api"})` | 09:30-15:30 step 120 | small | pending 0 at all 166 samples · link: explore prom-prod |
| W1-Q20 | n/a | prom-prod `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[10m]))` | 12:30-15:30 step 600 | small | 3 new pods only, first point 13:08, 0.52-0.64 cores each, nothing earlier (gap G5) · link: explore prom-prod |
| W1-Q21 | n/a | prom-prod `sum by (db_system) (increase(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))` step 3600 (recurrence) | 14 d to 15:30 | small | data only from 2026-10-20 10:00 (5.5 h of 336 h; gap G3) · link: explore prom-prod |
| W1-Q22 | n/a | tempo-prod TraceQL metrics `{ resource.service.name = "orders-api" && span.db.system =~ ".+" } \| quantile_over_time(duration, .95) by (span.db.system)` | 09:30-15:30 step 900 | within 24h cap; actual 6.63 GB inspected | postgresql db span p95 3.9-4.4 ms at every step, flat across 13:08; service name verified · link: explore tempo-prod |
| W1-Q23 | n/a | tempo-prod same with `\| rate() by (span.db.system)` | 09:30-15:30 step 900 | within cap; 0 bytes | empty series (gap) · link: explore tempo-prod |
| W2-Q1 | n/a | git -C ~/src/orders-api tag | local | free (not counted) | v2.12.0 ... v2.15.0 · link: cmd |
| W2-Q2 | n/a | git -C ~/src/orders-api log --oneline --format='%h %cs %s' v2.14.0..v2.15.0 | local | free (not counted) | a4c1e9b (#2211), 7be20d4 (#2208), 3f9d6a1 (#2203) · link: cmd |
| W2-Q3 | n/a | git -C ~/src/orders-api diff v2.14.0 v2.15.0 | local | free (not counted) | list_orders.py: joined query -> list_orders + list_items per order; order_detail.py adds shipment_eta; pyproject structlog 25.3.0 -> 25.4.0 · link: cmd |
| W2-Q4 | n/a | gh api repos/example-org/orders-api/compare/v2.14.0...v2.15.0 --method GET | n/a | free (not counted) | same 3 commits, 3 files · link: cmd |
| W2-Q5 | n/a | cloudtrail lookup-events ReadOnly=false, resource filter `orders` | 11:08-13:23 | free | `{}` (no rows) · link: cmd |
| W2-Q6 | n/a | cloudtrail lookup-events ReadOnly=false, eks/rds sources | 12:50-13:20 | free | `{}` (no rows; Helm is not a CloudTrail write) · link: cmd |
| W2-Q7 | n/a | kubectl get cronjobs -A | now | free (not counted) | no output · link: cmd |
| W2-Q8 | n/a | aws events list-rules (scheduled) | now | free | `{}` · link: cmd |
| W2-Q9 | n/a | aws scheduler list-schedules | now | free | `{}` · link: cmd |
| W2-Q10 | n/a | aws rds describe-db-instances orders-db | now | free | db.r6g.2xlarge, postgres 16.6, Multi-AZ, available, Performance Insights off; no windows/param group in reply · link: cmd |
| W2-Q11 | n/a | aws rds describe-events db-instance orders-db | 11:08-13:23 | free | `{}` · link: cmd |
| W2-Q12 | n/a | grafana /api/annotations (no type) limit=100 | 12:30-15:30 | free | `{}` (no deploy markers) · link: grafana annotations |
| W3-Q1 | n/a | git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py | local | free (not counted) | `orders = repo.list_orders(...)`; `for order in orders: order.items = repo.list_items(order.id)` (lines 15-18) · link: cmd |
| W3-Q2 | n/a | git -C ~/src/orders-api show v2.15.0:orders_api/repository.py | local | free (not counted) | list_items = one SELECT per call with its own pool.connection(); list_orders_with_items kept ("used up to v2.14.0") · link: cmd |
| W3-Q3 (= G1) | n/a | ls .culiops/sre-investigate/incidents (after ranking) | local | local (not counted) | 2 files |
| W3-Q4 (= G2) | n/a | grep -rn front matter for orders-api, orders-db, postgres, latency, p95 | local | local (not counted) | matches only in 2026-08-14-orders-api.md |
| W3-Q5 (= G3) | n/a | cat incidents/2026-08-14-orders-api.md | local | local (not counted) | past cause: DB pool exhausted after pool-size change (lead only) |
| W4-Q1 (was H1-Q1) | n/a | tempo-prod structural search `{ resource.service.name = "orders-api" && span:kind = server && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span.db.system =~ ".+" }` limit 30 | 14:30-15:30 | within 1h sample cap; 2.41 GB inspected | 24 traces; db spans per request min 9, p50 41, p95 52, max 52; root duration p50 342 ms · label Confirmed (mechanism) · link: explore tempo-prod |
| W4-Q2 (was H1-Q2) | n/a | same query | 11:00-12:00 (v2.14.0) | within cap; 2.35 GB inspected | 24 traces; db spans per request min 2, p50 3, p95 4, max 4; root duration p50 110 ms · link: explore tempo-prod |
| W4-Q3 (was H1-Q3) | n/a | tempo-prod trace e3ea7a3906419b466a28541306cc5ee1 by ID | padded 14:30-15:30 | 1 trace | root 152 ms; 1 SELECT orders then 12 sequential SELECT order_items (13 db spans; search said 14); auth-api client span 3.4 ms; about 82 ms not covered by child spans · link: explore tempo-prod |
| W4-Q4 (was H2-Q1) | n/a | cloudwatch get-metric-data AWS/RDS orders-db CPUUtilization + ReadLatency, 300 s | 10:00-15:30 | 2 metric requests; actual 2 | CPU 21-27 % to the 13:05 bucket, 37-44 % from 13:10; ReadLatency 0.52-0.67 ms flat · link: cloudwatch console RDS orders-db |
| W4-Q5 (was H4-Q1) | n/a | kubectl get deployment orders-api -o json (resources) | now | free (not counted) | no output · link: cmd |
| W4-Q6 (was H4-Q2) | n/a | kubectl get hpa -n orders | now | free (not counted) | no output · link: cmd |
| W4-Q7 (was H4-Q3) | n/a | kubectl top pod -n orders | now | free (not counted) | no output · link: cmd |
| W4-Q8 (was H6-Q1) | n/a | loki-prod index stats `{namespace="orders", app="orders-reconcile"}` | 12:30-15:30 | log_stats within 48h; actual 1.05 MB | 3 lines, all 15:00-15:05; batch 20-22, pending=0, 137 s spacing · link: explore loki-prod |
| W4-Q9 (was H6-Q2) | n/a | loki-prod `{namespace="orders", app="orders-reconcile"} \|= "outbox drained"` forward limit 100 | 12:58-13:18 | log_raw within 30m | 0 lines (gap G8) · link: explore loki-prod |
| W4-Q10 (was H7-Q1) | n/a | cloudwatch get-metric-data AWS/RDS orders-db DatabaseConnections, 300 s | 10:00-15:30 | 1 metric request; actual 1 | 40-44 to the 13:05 bucket, 43-48 from 13:10 · link: cloudwatch console RDS orders-db |
| W4-Q11 (was H4-Q4) | n/a | kubectl get events, HPA kind | now | free (not counted) | No resources found (expired) · link: cmd |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1. Alert history unavailable: the p95 alert's name was not given; no `ALERTS` series; Grafana annotations `{}` (W0-Q10, W0-Q11) | recurrence class cannot use alarm history (class `unclassified`); detection time (how long the alert took to fire) not stated | give the alert rule name or Grafana rule UID, or the place its state history lives |
| G2. Write-check: 3 of the 10 listed actions returned no simulator row (W0-Q3) | none on the investigation (read-only throughout); the "read-only" statement is limited to the 7 returned rows | rerun the simulation after the role's policy view is checked by a person; no change to the run needed |
| G3. Metric coverage: 5.5 h of the 14 days asked (W1-Q21); latency recurrence not pulled (12h histogram cap, no recording rule) | recurrence class `unclassified`; "sudden" is a reading, not a class | confirm Prometheus retention for these series, or add a latency recording rule; then rerun the recurrence pull |
| G4. p90 and p99 queries returned empty matrices while p50 and p95 with the same selector return data (W1-Q13, W1-Q14) | ceiling-versus-slowness read rests on p50 vs p95 (both moved), not on p99 | ask the metrics owner whether those quantiles are exposed; query p99 once they are |
| G5. No CPU limits, throttling series, HPA state or pre-13:08 CPU readable (W1-Q20, W4-Q5..Q7, W4-Q11) | H4 stays `Assumed` (open); a capacity contribution to the extra latency is neither shown nor excluded | read the Deployment's CPU limit and throttling from the platform side; expose `container_cpu_cfs_throttled_periods_total` |
| G6. Kubernetes events expired (W1-Q3); rollout events not available | the rollout's own events (probe failures, restarts at the switch) are unseen; pods show 0 restarts | none for this incident; read events within an hour of the next rollout |
| G7. No error/status metric, no load-balancer series, no SLO | "no failed requests" and "customer-facing" are Assumed; user impact not sized | point to the ingress or load-balancer metric and the SLO, if they exist |
| G8. No orders-reconcile log lines before 15:00 (W4-Q8, W4-Q9) | H6's cadence-across-13:08 comparison impossible; H6 rests on the API side (Ruled out with that named as weakest link) | check whether that stream's logs are shipped and retained in full |
| G9. Helm printed its times without a zone; `date -u` printed nothing | the deploy time (about 13:05 UTC) rests on ReplicaSet/pod ages relative to the assumed "now" 15:30 and on the epoch-stamped step at 13:08 | none needed if "now" is right; the operator can confirm the time from the release record |
| G10. DB operations rise (+3,570/s) is about 1.8x what the sampled GET /orders traces explain (+2,000/s) (W1-Q16, W4-Q1, W1-Q15) | caps the sub-claim "all of the x10 ops/s is this mechanism" at Likely; does not change H1's Confirmed mechanism | ask the orders team whether the database metric also counts per-checkout commits or another caller; compare with the database's own statement counters |
| G11. Helm values for revision 24 not compared with revision 23 (values are not read: `helm get values` is not run; chart repo not named; chart version the same 4.2.0) | a values change bundled with the image bump (pool size, limits) is not excluded as an additional factor | have the owning team diff the release's values files in git between the two revisions |
| G12. Empty replies from CloudTrail, EventBridge, Scheduler, CronJobs, RDS events, annotations (W2-Q5..Q9, Q11, Q12); RDS backup/maintenance windows not shown in the instance reply | "nothing changed besides the release" is "nothing returned", not proof; a Helm or kubectl change is not a CloudTrail write | check CloudTrail data events and change tickets for the window; read the RDS windows from the console |
| G13. The -7d request-rate series was not pulled (W1-Q15 covers the previous window only) | the call-rate comparison is against the previous 3 h; a week-earlier comparison exists for latency and DB ops only | rerun W1-Q15 with a seven-day shift if wanted |

## Untrusted text

none seen (checked: log lines in W0-Q8, trace and span names in W4-Q1..Q3, commit messages and diffs in W2-Q2..Q4, code comments in W3-Q1/Q2, and the past-incident file in W3-Q5)

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: no `lessons.md` exists yet |
| Re-verified this run | none (no lessons marked re-verify) |
| History lookup | run after the ranked list existed (Phase 3): `ls .culiops/sre-investigate/incidents` -> 2 files; grep of front matter for orders-api, orders-db, postgres, latency, p95 -> match only in `2026-08-14-orders-api.md` (service orders-api, symptoms latency/p95, deps orders-db; past cause: DB connection pool exhausted after a pool-size change, label Confirmed there). Became `H7` with ID note `from-history:2026-08-14-orders-api.md`; it is a lead, was not passed to the worker, and was refuted by this run's own queries (W1-Q18, W1-Q19, W4-Q10). This run has the same service and symptom words but a different cause, so it is not a repeat of that incident. `2026-09-30-catalog-api.md` did not match |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| identifier | loki | For orders-api the Loki app label value is `orders` (container `api`), not `orders-api`; the sibling worker is app `orders-reconcile` (container `worker`) in namespace `orders` | W0-Q13 |
| identifier | tempo | Trace service name is `orders-api`; db spans carry span.db.system=postgresql; route and method are span.http.route and span.http.request.method; use limit 30 and a 1 h window per search | W4-Q1 |
| identifier | prometheus | Pool gauges db_client_connections_usage and db_client_connections_pending_requests carry service=orders-api and pool=orders-db; pending_requests above 0 is the wait signal | W1-Q19 |
| process | prometheus | histogram_quantile for 0.90 and 0.99 on http_server_request_duration_seconds_bucket returned an empty matrix while 0.5 and 0.95 returned data; compare p50 with p95 instead and check the quantile exists first | W1-Q13 |
| process | prometheus | A 14-day request returned only 5.5 h of data and container CPU series for replaced pods are absent before the new pods start; check coverage with a short query before planning a recurrence pull | W1-Q21 |
| process | kubectl | In this cluster `get deployments,services,ingresses,hpa`, `get hpa`, `top pod` and `get cronjobs -A` print nothing while `get pods`, `get rs`, `rollout history` and `helm history` work; Kubernetes events are gone after about 1 hour, so read them in the first wave | W0-Q17 |
| process | cloudwatch | RDS get-metric-data replies list timestamps newest first and in UTC, and a 5-minute bucket is labelled by its start; a 13:10 bucket does not describe 13:08 | W4-Q4 |
| noise | loki | orders-reconcile logs `outbox drained batch=N pending=0` about every 137 s; pending=0 is its normal state | W4-Q8 |
| process | loki | Loki returned no orders-reconcile lines before 15:00 on 2026-10-20 for a stream that logs every 137 s; do not read an empty result for this stream as inactivity | W4-Q9 |
| failure-mode | tempo | Latency step on a list endpoint right after a release: structural search `route >> { span.db.system =~ ".+" }` for the hour after vs the hour before; `matched` per trace going from about 3 to about 41 is an N+1 (one items query per row) | W4-Q1 |
