# Ledger: orders-api prod 20261020-1530

Mode: Deep (the operator asked for Deep)
Budget used (after Phase 4 merge): 35 / 60 queries · 0.05 / 10 log GB (Loki 0.048; Tempo inspected about 11.4 GB, not part of the log budget) · 7 / 500 CloudWatch metric requests · wave 1 has 21 queries in 6 calls, more than ten, because its fixed legs (three windows, latency extras, 14 d recurrence pull, saturation, change events) need them · counted = data-backend queries (Prometheus, Loki, Tempo, Grafana, CloudWatch metrics); IAM, kubectl, helm, git, ls/cat reads are logged but not counted (free describe/list calls). environment.md has no `budgets.deep`, so the template defaults apply (60 queries, 10 GB, 500 metric requests, window caps as in the template); its own rule "Loki: ask before a query expected to process more than 20 GB" also applies.

## Problem

| Field | Value |
|---|---|
| What | Reporter: "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing." Measurable restatement: p95 latency of `GET /orders` (service `orders-api`, prod) is above its normal level since early afternoon UTC on 2026-10-20 and the alert on it is firing. |
| Where | orders-api, prod, EKS cluster `prod`, namespace `orders` (3 replicas). No region, shard or tenant siblings. |
| When | Reported: "early this afternoon UTC" (no clock time). True onset 13:08 UTC (first elevated p95 sample, W1-Q5; last normal sample 13:06). Helm upgrade to v2.15.0 at 13:04:50 UTC (W1-Q4). |
| Who is affected | Callers of `GET /orders` (order history, a core flow in environment.md). Share of users unknown. |
| Trigger | "the p95 alert": name, rule and link not given. |
| Mitigations already applied | none known (the operator named none) |
| Assumptions made at intake | (0) At checkpoint #1 the operator replied "Agreed, go on.": window accepted, no unseen change named. (1) "Today" is 2026-10-20, the date every telemetry reply carries; `date -u` printed nothing in this environment, so the run start is taken as 15:30 UTC, the newest data point returned. (2) "early this afternoon UTC" carries an explicit zone (rule 1): anchor set to 13:00 UTC, window 12:30 to now (15:30 UTC) because the incident is ongoing. Local zone for display: Australia/Brisbane (UTC+10, from environment.md). (3) Budgets: see the line above. (4) Everything the operator did not name (alert name, SLO) is left unset, not guessed. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md `prod`), role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | 7 of the 10 fixed write actions came back `implicitDeny` (none `allowed`); 3 of the 10 returned no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack). The reply also held 3 rows for actions not on the fixed list (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy), all `implicitDeny`, ignored for the count. Not a full proof; boxed warning not shown. | session valid; `GRAFANA_SERVICE_ACCOUNT_TOKEN` present; `agentbox-env` not found (nothing said) |
| arn:aws:eks:us-east-1:111122223333:cluster/prod | user = assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, group `eks-readonly` | no write verbs in orders (the three `create` rows on selfsubject*reviews are the excluded access-review APIs; everything else is `get list watch`) | current context equals the context in environment.md |
| Grafana datasource proxy: prom-prod, loki-prod, tempo-prod | token `GRAFANA_SERVICE_ACCOUNT_TOKEN` | not applicable | set |

## Impact

Source order: the SLO or error-budget burn named in `environment.md` (none), then load-balancer or APM request/error/duration metrics against the baseline, then `Assumed`.

| Field | Value |
|---|---|
| Symptom | `GET /orders` p95 0.712 s against 0.180 s before and 0.181 s seven days earlier (x3.9); p50 0.311 s against 0.092 s (x3.4). Only this endpoint: POST /orders 0.142 against 0.139, GET /orders/{id} 0.064 against 0.061, PATCH 0.088 against 0.091, /healthz 0.003 (W1-Q5..Q13). |
| Affected | prod orders-api, all 3 replicas (CPU level across pods, W1-Q18); order history (`GET /orders`) is a core flow. Customer-facing. Error rate and number of users not measured. |
| Since / ongoing | 13:08 UTC (23:08 local, Australia/Brisbane); ongoing, no recovery up to 15:30 UTC |
| Suggested severity | SEV2 because a core flow is significantly degraded (about 4x) and nobody reported it as down |
| Basis | W1-Q5, W1-Q6, W1-Q7, W1-Q8, W1-Q11, W1-Q12, W1-Q13, W1-Q14 · label: Confirmed for the latency figures; share of users affected is Assumed (no SLO, no error or per-user data) |
| Third party in the path | none (database is RDS orders-db in the same account); the run cannot contact vendors anyway |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-20 12:30 | 2026-10-20 15:30 |
| Baseline (previous) | 2026-10-20 09:30 | 2026-10-20 12:30 |
| Baseline (−7d) | 2026-10-13 12:30 | 2026-10-13 15:30 |

Re-anchored: no. The onset (13:08 UTC, W1-Q5) is 8 minutes after the assumed 13:00 anchor and inside the incident window. Coverage note: Prometheus replies start at 10:00 UTC, so the previous window (09:30-12:30) is covered from 10:00 only.

## Recurrence

Classify before blaming a change. Classes: `scheduled`, `chronic`, `recurring`, `sudden`, `unclassified`. Shapes seen in the signal: `step`, `ramp`, `periodic`, `ceiling`, `volume`.

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none available: the alert is unnamed and the `ALERTS` search for namespace orders returned an empty matrix (W0-Q13). No CloudWatch alarm is involved, so no sibling alarms. |
| Signal, 14d at 1h resolution | latency cannot be pulled (a 14 d `histogram_quantile` over raw buckets exceeds the 12 h `prom_quantile_range` cap and no recording rule is known): gap. Proxy pulled instead: `increase(http_server_request_duration_seconds_count{route="/orders"}[1h])` (counter, `increase`). It returned 10:00 to 15:30 on 2026-10-20 only: hourly 202.8k, 204.3k, 203.0k, 203.6k (13:00 hour = the onset hour), 202.2k, 107.1k (half hour). Median of complete hours 203.0k, max 204.3k; the onset hour is level with the others. This is volume, not latency, and 5.5 h of 336 h. |
| Coverage | alarm history: none. Prometheus: 2026-10-20 10:00-15:30 and, for `offset 7d` rows, 2026-10-13 10:00-15:30. Nothing else was returned. |
| Class | `unclassified` · shape: `step` (p50 and p95 both jump at 13:08 and stay; endpoint call rate flat, DB statements/s x10.4 at the same sample) |
| Reason | no rule can be tested: scheduled needs three occurrences, chronic needs alarm or 14 d latency history, recurring needs another occurrence in 30 d, sudden needs a 30 d alarm history with no other transition. Observed: the same clock window 7 days earlier was normal (W1-Q6, W1-Q8, W1-Q13, W1-Q16) and 10:00-13:06 today was normal (W1-Q5). Gap recorded. |
| Label and queries | Assumed (class cannot be derived) · W0-Q13, W1-Q19, W1-Q5, W1-Q6 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-07 09:40:12 | Helm revision 23 deployed, app v2.14.0, chart orders-api-4.2.0 (zone not printed; read as UTC, see W1-Q4) | helm | W1-Q4 |
| 2026-10-19 (time not shown) | commits merged in v2.15.0 vs v2.14.0: a4c1e9b "orders: load items per order in list handler (#2211)", 7be20d4 "return shipment ETA on order detail (#2208)"; 3f9d6a1 "bump structlog (#2203)" is dated 2026-10-16 | git | W2-Q8 |
| 2026-10-20 about 13:05 | ReplicaSet `orders-api-7c9b6d8f5d` created (age 145 min at 15:30) | kubectl | W1-Q2 |
| 2026-10-20 13:04:50 | Helm revision 24 deployed: app v2.15.0, chart orders-api-4.2.0 (same chart as revision 23) | helm | W1-Q4 |
| 13:06 | last normal GET /orders p95 0.163 s, p50 0.082 s | Prometheus | W1-Q5, W1-Q7, W3-Q1 |
| 13:08 | first elevated sample: p95 0.716 s, p50 0.295 s; DB statements/s 4,031 (was about 380); endpoint call rate unchanged | Prometheus | W1-Q5, W1-Q7, W1-Q15, W1-Q14 |
| 13:08-15:30 | p95 stays 0.66-0.76 s, no recovery; pool `pending_requests` 0; RDS CPU 37-44% | Prometheus, CloudWatch | W1-Q5, W1-Q17, W1-Q21 |
| 14:30:18-15:27:50 | trace sample: GET /orders requests make 9-52 descendant spans (p50 41), against 2-4 (p50 3) in the 11:00:09-11:57:36 sample; added root time per request matches the added DB statement time | Tempo | W3-Q4, W3-Q5, W3-Q6, W3-Q7 |
| 15:18:08-15:19:49 | 8 log lines `GET /orders` 286-751 ms (stream not tied to the service: lead only) | Loki | W3-Q9 |
| (time unknown) | "the p95 alert keeps firing" | reporter, not from a query | operator line 1 |
| (n/a) | no schedule, scaling action, RDS event or AWS write found near 13:08 (CronJobs, EventBridge rules, Scheduler, RDS events, CloudTrail) | kubectl, aws | W2-Q1..Q6 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The v2.15.0 rollout (Helm revision 24 at 13:04:50 UTC; commit a4c1e9b #2211 on the GET /orders handler) triggered the step: latency rose as the new revision took traffic, and the changed code sits on the failing path | no elevated sample before 13:04:50; elevation within minutes; only the handler's endpoint moves; the diff touches that handler | first elevated sample earlier than the rollout start, or old pods equally slow (per-pod/per-revision split of GET /orders p95, 12:50-13:20) | default | Confirmed |
| H2 | GET /orders now makes many more DB statements per request (one order_items query per order), each about as fast as before, and that accounts for the added latency | spans per request up sharply against the pre-deploy window; per-statement duration unchanged; duration grows with span count | spans per request, incident (14:30-15:30) against baseline (11:00-12:00), at least 20 traces each; equal counts refute | default | Confirmed |
| H3 | orders-db became slower per statement (CPU, locks, I/O) | per-statement latency up, DB CPU high, lock/queue metrics up at the onset | per-statement DB latency and DB CPU/lock/queue metrics at baseline refute | strong | Ruled out |
| H6 | A traffic spike or heavy clients raised load on GET /orders | request count above the previous window and -7d | request rate equal to the previous window and -7d | default | Ruled out |
| H5 | Pod capacity: CPU limits or throttling, HPA at max, or fewer replicas slowed the pods | ready < desired, throttling, all routes on the pods slower | ready = desired, no throttling, other routes on the same pods unchanged | default | Ruled out |
| H4 | DB connection exhaustion or a pool cap: requests wait for a connection | `pending_requests` above 0, `used` pinned at the pool maximum, pool-wait errors | `pending_requests` 0 throughout, `used` not pinned, no pool-wait errors | default | Ruled out |
| from-history:2026-08-14-orders-api.md | (lead, overlaps H4) the orders-db connection pool is exhausted and requests queue: `pending_requests` stays elevated for the window, possibly after a pool-size configuration change | `pending_requests` above 0 for the window; `used` pinned; slowdown on every DB-backed route | `pending_requests` at 0 across the incident window | default | Ruled out |

- `H1` status: supported · evidence: W1-Q4, W1-Q5, W3-Q1, W3-Q2, W3-Q3, W2-Q9, W1-Q15 · note: default tier, no escalation; the tie rests on timing and the diff on the failing path (no pod label for an old-versus-new split)
- `H2` status: supported · evidence: W3-Q4, W3-Q5, W3-Q6, W3-Q7, W1-Q15, W1-Q20 · note: default tier; direct proof (span counts both windows n=24, fetched trace)
- `H3` status: refuted · evidence: W1-Q20, W1-Q21, W1-Q15, W3-Q8 · note: started on the strong tier (conflicting signals); lock-wait metrics unavailable
- `H6` status: refuted · evidence: W1-Q14, W1-Q19, W3-Q12 · note: default tier; -7d call rate unusable
- `H5` status: refuted · evidence: W1-Q2, W0-Q20, W1-Q11..Q13, W1-Q18, W3-Q10, W3-Q11 · note: default tier; ruled out by unchanged sibling routes on the same pods, direct limit/HPA/throttling not readable
- `H4` status: refuted · evidence: W1-Q17, W1-Q21, W3-Q9 · note: default tier
- `from-history:2026-08-14-orders-api.md` status: refuted · evidence: W1-Q17, W1-Q11..Q13 (reused) · note: default tier; no new query; overlaps H4; history stayed a lead, the verdict comes from this run's rows

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (clone `~/src/orders-api`, read by ref) | not read | not read (no fetch or rev-parse allowed or run) | unknown; environment.md says tags v2.14.0 and v2.15.0 are fetched | revision 24: image/tag `v2.15.0` (commits a4c1e9b, 7be20d4, 3f9d6a1 since v2.14.0); revision 23: `v2.14.0`. The tag's own SHA was not resolved; the range was read as `v2.14.0..v2.15.0` (W2-Q8) |

## Query log

Raw pulls: in this simulation the replies are the canned world files; nothing was copied under `raw/`, so the `Raw:` and `link:` pointers into `raw/` name where the real run would have saved them.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | n/a (`date -u` printed nothing) | `git rev-parse --show-toplevel` | n/a | free | printed nothing; the case directory is used as repo root |
| W0-Q2 | n/a | `git check-ignore -q .culiops/sre-investigate` | n/a | free | exit 0: `.culiops/` is ignored by git |
| W0-Q3 | n/a | `ls .culiops/sre-investigate` | n/a | free | `environment.md`, `incidents`; no `profiles/`, no `lessons.md` |
| W0-Q4 | n/a | `cat .culiops/sre-investigate/environment.md` | n/a | free | timezone Australia/Brisbane; one AWS profile `prod-read`; one kube context; Grafana proxy for Prometheus, Loki, Tempo; repo example-org/orders-api; core flows GET /orders and POST /orders |
| W0-Q5 | n/a | `command -v agentbox-env` | n/a | free | exit 1: nothing said about Culibox |
| W0-Q6 | n/a | `aws sts get-caller-identity --profile prod-read` | n/a | free | account 111122223333 = environment.md; role AWSReservedSSO_ReadOnly_… |
| W0-Q7 | n/a | `aws iam get-role` (role name taken from W0-Q6) | n/a | free | role path /aws-reserved/sso.amazonaws.com/, role ARN resolved |
| W0-Q8 | n/a | `aws iam simulate-principal-policy` (fixed list of 10) | n/a | free | 7 of 10 `implicitDeny`, 3 missing rows (gap), 3 unlisted extra rows ignored |
| W0-Q9 | n/a | `kubectl auth whoami --context …/cluster/prod` | n/a | free | assumed role ReadOnly, group eks-readonly |
| W0-Q10 | n/a | `kubectl config current-context` | n/a | free | the environment.md context |
| W0-Q11 | n/a | `kubectl auth can-i --list --context …/cluster/prod --namespace orders` | n/a | free | no write verbs in orders |
| W0-Q12 | n/a | token presence `GRAFANA_SERVICE_ACCOUNT_TOKEN` | n/a | free | set |
| W0-Q13 | n/a | prom-prod `max_over_time(ALERTS{alertstate="firing", namespace="orders"}[1h])` (alert name unknown) | 2026-10-06 15:30 to 2026-10-20 15:30, step 3600 | 1 query | empty matrix: no alert history found; selector unverified (gap) |
| W0-Q14..Q19 | n/a | helper PROFILE discovery: Loki labels / label app / label namespace / label container; Prometheus `label/__name__/values`; Tempo `search/tags` | last hour | 6 queries | see Phase 0 notes in the run log; labels and metric names listed, no stream data |
| W0-Q20 | n/a | `kubectl get pods -n orders` (helper) | now | free | 3 pods orders-api-7c9b6d8f5d-{4kq2m,9vx7t,tz5wp} Running, 0 restarts, age 145m / 144m / 144m |
| W0-Q21 | n/a | `kubectl get deployments,services,ingresses,hpa -n orders` (helper) | now | free | no output (not read as "none") |
| W0-Q22 | n/a | `aws rds describe-db-instances` (helper) | now | free | `orders-db` postgres 16.6, db.r6g.2xlarge, Multi-AZ, Performance Insights off |
| W0-Q23 | n/a | Grafana dashboard search `orders-api` (helper) | now | 1 query | empty object: no dashboards found |
| W0-Q24 | n/a | loki-prod `index/stats` `{namespace="orders"}` | 15:15 to 15:30 | 1 query | empty object: no size estimate available (gap); the Loki ask-above-20-GB rule is met by keeping every log query inside the window caps and one stream |
| W1-Q1 | n/a | kubectl `rollout history deployment/orders-api` (ns orders) | now | free | revisions 23 (image v2.14.0) and 24 (image v2.15.0), chart orders-api-4.2.0 both · Confirmed |
| W1-Q2 | n/a | kubectl `get rs -n orders --sort-by=.metadata.creationTimestamp` | now | free | `orders-api-5f8d9c7b6a` 0 replicas age 13d; `orders-api-7c9b6d8f5d` 3/3 ready age 145m · Confirmed |
| W1-Q3 | n/a | kubectl `get events -n orders --sort-by=.lastTimestamp` | now | free | "No resources found" — events expire after about 1 h; rollout events (13:05) not available: gap, not "no events" |
| W1-Q4 | n/a | `helm history orders-api -n orders --max 10` | now | free | rev 23 Oct 7 09:40:12 superseded v2.14.0; rev 24 Oct 20 13:04:50 deployed v2.15.0; zone not printed, read as UTC because RS age agrees · Confirmed |
| W1-Q5 | n/a | prom-prod `histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))` (service, route labels verified by this reply) | 09:30-15:30, step 120 s (points from 10:00) | 1 query | 10:00-12:28 median 0.180 (max 0.200); 13:06 = 0.163; 13:08 = 0.716; 13:08-15:30 median 0.712 (0.661-0.755) · Confirmed. Raw: `raw/m-p95-orders.json` |
| W1-Q6 | n/a | same, `offset 7d` | 12:30-15:30 (10-13 data), step 120 s | 1 query | median 0.181 (0.161-0.200) · Confirmed |
| W1-Q7 | n/a | prom-prod p50 of the same histogram | 09:30-15:30, step 120 s | 1 query | 10:00-12:28 median 0.092; 13:06 = 0.082; 13:08 = 0.295; 13:08-15:30 median 0.311 (0.281-0.339) · Confirmed |
| W1-Q8 | n/a | same, `offset 7d` | 12:30-15:30 | 1 query | median 0.088 · Confirmed |
| W1-Q9 | n/a | prom-prod p90 of the same histogram | 09:30-15:30 | 1 query | empty matrix although W1-Q5 (same selectors) returned data: unexplained; gap |
| W1-Q10 | n/a | prom-prod p99 of the same histogram | 09:30-15:30 | 1 query | empty matrix: gap |
| W1-Q11 | n/a | prom-prod per-endpoint p95 `sum by (le, method, route)` instant | at 15:30 | 1 query | GET /orders 0.712; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; GET /healthz 0.003 |
| W1-Q12 | n/a | same instant | at 12:30 (previous window end) | 1 query | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q13 | n/a | same instant, `offset 7d` | at 15:30 | 1 query | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q14 | n/a | prom-prod `sum by (route, method) (rate(http_server_request_duration_seconds_count{service="orders-api"}[5m]))` | 09:30-15:30, step 120 s | 1 query | reply holds only the GET /orders series; 10:00-12:28 median 56.5 req/s, 13:08-15:30 median 56.25: flat. Other routes absent from the reply (not zero) |
| W1-Q15 | n/a | prom-prod `sum by (service, db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))` | 09:30-15:30, step 120 s | 1 query | 10:00-12:28 median 381/s; 13:06 = 365.5; 13:08 = 4,031; 13:08-15:30 median 3,962/s (x10.4) · Confirmed (service-wide, not per endpoint) |
| W1-Q16 | n/a | same, `offset 7d` | 12:30-15:30 | 1 query | median 379/s (355-404) · Confirmed |
| W1-Q17 | n/a | prom-prod `db_client_connections_usage{service="orders-api"}` (reply also carried `pending_requests`) | 09:30-15:30, step 120 s | 1 query | `used` median 16 (14-19) before, 21 (17-24) after; `pending_requests` 0 at every point · Confirmed. Pool maximum not exposed by any metric seen |
| W1-Q18 | n/a | prom-prod `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[5m]))` | 12:30-15:30, step 600 s (points only from 13:08) | 1 query | per pod 0.52-0.64 cores, medians 0.576 / 0.584 / 0.604; no pre-onset baseline returned; no CPU limit known |
| W1-Q19 | n/a | prom-prod `sum(increase(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[1h]))` | 14 d, step 3600 (returned 10:00-15:30 only) | 1 query | hourly 202.8k, 204.3k, 203.0k, 203.6k, 202.2k, 107.1k (half hour); coverage gap |
| W1-Q20 | n/a | tempo-prod TraceQL metrics `{ resource.service.name = "orders-api" && span.db.system =~ ".+" } \| quantile_over_time(duration, .95)` (service name verified by this reply) | 09:30-15:30, step 900 s | 1 query; Tempo inspected 6.6 GB | `span.db.system=postgresql`: p95 median 4.19 ms before (3.9-4.36), 4.04 ms after (3.9-4.22): flat · Confirmed. Does not clear the database: the statement count is the question |
| W1-Q21 | n/a | cloudwatch `get-metric-data` AWS/RDS `orders-db`: CPUUtilization (Avg), ReadLatency (Avg), DatabaseConnections (Max), Period 300 | 09:30-15:30 (points from 10:00) | 3 metric requests | CPU median 24.9% before (21.2-26.9), 40.8% after (37.1-44.0); ReadLatency 0.6 ms before and after; connections max 42 before, 47 after (43-48) · Confirmed |
| W2-Q1 | n/a | kubectl `get cronjobs -A` | now | free | no output: none listed |
| W2-Q2 | n/a | `aws events list-rules --query 'Rules[?ScheduleExpression]…'` | now | free | `{}`: none returned |
| W2-Q3 | n/a | `aws scheduler list-schedules` | now | free | `{}`: none returned |
| W2-Q4 | n/a | `aws rds describe-events --source-type db-instance --source-identifier orders-db` | 11:08-14:08 | free | `{}`: no events |
| W2-Q5 | n/a | `aws cloudtrail lookup-events` ReadOnly=false, resource name contains `orders` | 11:08-13:23 | free | `{}`: none |
| W2-Q6 | n/a | `aws cloudtrail lookup-events` ReadOnly=false, no resource filter | 12:58-13:23 | free | `{}`: none. CloudTrail does not log the Kubernetes API, so this covers AWS writes only |
| W2-Q7 | n/a | `git -C ~/src/orders-api tag` | n/a | free | v2.12.0 … v2.15.0; tag rule `v<semver>` = image tag · Confirmed |
| W2-Q8 | n/a | `git -C ~/src/orders-api log --format='%h %cs %s' v2.14.0..v2.15.0` | n/a | free | a4c1e9b (2026-10-19, #2211, list handler loads items per order), 7be20d4 (#2208, shipment ETA on order detail), 3f9d6a1 (2026-10-16, #2203, structlog bump) · Confirmed |
| W2-Q9 | n/a | `git -C ~/src/orders-api diff v2.14.0 v2.15.0` | n/a | free | `orders_api/handlers/list_orders.py` (GET /orders handler): single joined call replaced by `repo.list_orders` + per-order `repo.list_items(order.id)`; `order_detail.py` adds shipment_eta; `pyproject.toml` structlog 25.3.0 to 25.4.0 · Confirmed (file diff, on the failing path) |
| W3-Q1 (was H1-Q1) | n/a | prom-prod `histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))` | 12:50-13:20, step 120 s | 1 query | one series, no `pod` label, identical to W1-Q5: no per-pod/per-revision split exists; 13:06 = 0.163, 13:08 = 0.716 · Confirmed (timing). Raw: `raw/H1/m-p95-by-pod.json` |
| W3-Q2 (was H1-Q2) | n/a | `git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py` | n/a | free | lines 15-18: `repo.list_orders` then `for order in orders: order.items = repo.list_items(order.id)`; limit capped at 50 · Confirmed |
| W3-Q3 (was H1-Q3) | n/a | `git -C ~/src/orders-api show v2.15.0:orders_api/repository.py` | n/a | free | `list_items` = one query per call (lines 44-47); the one-round-trip join `list_orders_with_items` (lines 38-42, "used by the list handler up to v2.14.0") still exists · Confirmed |
| W3-Q4 (was H2-Q1) | n/a | tempo-prod search `{ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }` limit 30 | 14:30-15:30 | 1 query; Tempo inspected 2.41 GB | 24 traces; descendant spans per request p50 41, p95 52, max 52, min 9; durationMs median 340.5 (128-431) · Confirmed |
| W3-Q5 (was H2-Q2) | n/a | same | 11:00-12:00 | 1 query; Tempo inspected 2.35 GB | 24 traces; descendant spans p50 3, p95 4, max 4, min 2; durationMs median 110 (78-165) · Confirmed |
| W3-Q6 (was H2-Q3) | n/a | tempo-prod trace by ID e3ea7a3906419b466a28541306cc5ee1, padded window | 13:30-16:30 | 1 query | 15 spans: root 152 ms; 1 `SELECT orders` 3.05 ms; 12 `SELECT order_items` (median 3.74, max 4.52, total 44.8 ms); 1 `GET auth-api /verify` 3.4 ms; no version or pod attribute · Confirmed |
| W3-Q7 (was H2-Q4) | n/a | tempo-prod trace by ID 65345f5f8176033524bc88af3bd43f6f, padded window | 10:00-13:00 | 1 query | 3 spans: root 109 ms; 1 `SELECT orders JOIN order_items` 3.05 ms; `GET auth-api /verify` 3.77 ms · Confirmed |
| W3-Q8 (was H3-Q1) | n/a | cloudwatch get-metric-data AWS/RDS `orders-db`: WriteLatency, DiskQueueDepth, Deadlocks, FreeableMemory, Period 300 | 09:30-15:30 | 4 metric requests | no data points for any of the four (not zero); Performance Insights off · gap |
| W3-Q9 (was H4-Q1) | n/a | loki-prod `{namespace="orders", app="orders", container="api"}` forward, limit 100 (no filter) | 15:00-15:30 | estimate unavailable (W0-Q24); actual 0.048 GB | 8 `request completed` lines 15:18:08-15:19:49, status 200, page_size 50, duration_ms 286-751; no pod name, no trace ID, no pool text; stream stays (unverified) · lead only |
| W3-Q10 (was H5-Q1) | n/a | kubectl `get hpa -n orders` | now | free | no output (not read as "no HPA") |
| W3-Q11 (was H5-Q2) | n/a | prom-prod throttled/total CFS periods ratio by pod | 12:30-15:30, step 600 s | 1 query | empty matrix; metric names absent from W0-Q18: gap |
| W3-Q12 (was H6-Q1) | n/a | prom-prod `sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[5m] offset 7d))` | 12:30-15:30, step 120 s | 1 query | identical to W1-Q14 to the decimal: `offset 7d` not applied; unusable |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| The p95 alert is unnamed and its state history returned nothing (W0-Q13) | recurrence cannot be taken from alarm history; the alert's threshold and first firing time are unknown | name of the Grafana or Prometheus alert rule, or an export of its state history |
| Write-check: 3 of the 10 fixed actions returned no row (W0-Q8) | "no broad write found" is stated for 7 of 10 actions only | a human re-runs the simulation for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack |
| Loki index stats returned an empty object (W0-Q24) | no size estimate before log queries | Loki stats endpoint enabled for the datasource |
| `kubectl get deployments,services,ingresses,hpa` printed nothing (W0-Q21) | HPA, limits and ingress are unknown | confirm with the owner whether an HPA exists |
| `p90` and `p99` of the endpoint returned empty matrices (W1-Q9, W1-Q10) | ceiling-versus-slow-calls check rests on p50 versus p95 only | the Prometheus histogram exposes the data (p50, p95 returned), so ask the metrics owner why those quantile queries return nothing |
| 14-day latency pull not run (cap `prom_quantile_range` 12 h, no recording rule); the volume proxy returned 5.5 h only (W1-Q19) | recurrence class `unclassified`; "first time or not" for this symptom cannot be settled from metrics | add a p95 recording rule for GET /orders, or point the run at one; or name the alert so its state history can be read |
| Kubernetes events are gone (W1-Q3) | rollout events for 13:05 (probe failures, restarts, FailedScheduling) cannot be read | none (expired); restarts are 0 in `get pods` (W0-Q20) |
| Helm prints times without a zone (W1-Q4) | the 13:04:50 deploy time is read as UTC on the strength of the ReplicaSet age (W1-Q2), not on the printed text | none needed unless the ReplicaSet creationTimestamp is read in a later wave |
| Pod CPU reply has no point before 13:08 and no CPU limit is known (W1-Q18) | no before/after for pod CPU and no headroom figure | a human reads the Deployment's resources and any HPA |
| No IaC or chart-values repo in environment.md; chart `orders-api-4.2.0` is the same in Helm revisions 23 and 24 and values are unreadable by design (W1-Q4) | a values or config-only change inside the same upgrade cannot be excluded; "only the image changed" is Assumed | add the chart/values repo to environment.md `code:`, or a human diffs the values files at the two refs |
| Local clone freshness unknown (no fetch allowed); tags v2.14.0 and v2.15.0 are present (W2-Q7) | the diff is exact for the two tags; whether other commits reached the running image is Assumed (image tag = tag, W1-Q1) | `gh` read access to confirm the tag's commit |
| AWS list/describe calls in wave 2 returned empty objects (W2-Q2..Q6) | read as "none returned"; an empty object cannot be told from a filtered or hidden result | none needed unless a schedule is suspected later |
| Latency histogram has no `pod`/version label; Kubernetes events expired; traces carry no `service.version` or pod (W3-Q1, W1-Q3, W3-Q6) | no direct "new pods slow, old pods fine" split; the deploy tie rests on timing at 2-minute resolution plus the diff on the failing path (H1 stays Confirmed on those two of the three Phase 2 tie options) | add a version/pod label to the histogram or `service.version` to spans; or read the rollout events from a log store |
| RDS lock-wait, deadlock, disk-queue, write-latency and memory metrics returned no data; Performance Insights off (W3-Q8, W0-Q22) | H3's lock arm is excluded only through flat per-statement latency | enable Performance Insights on orders-db |
| CPU limits, HPA and throttling not readable (W3-Q10, W3-Q11) | H5 is ruled out by unchanged sibling routes on the same pods, not by a headroom figure | read the Deployment resources and HPA |
| Pool maximum and DB connection limit unknown (no metric, no config read) | H4 and the history lead are ruled out on zero waiters, with no numeric headroom | read the pool setting from the chart values at the deployed ref |
| No usable -7d call rate for GET /orders (W3-Q12) | H6 rests on the previous window and the 5.5 h hourly pull | shift start/end instead of `offset` |
| Only two traces fetched by ID; neither is typical of the 41-span median (W3-Q6 has 14 descendants) | full time accounting is shown for a short request; the long ones rest on the regression across 24 durations | a human opens a 50-order request trace in Tempo |
| `auth-api` client span in every fetched trace was not tested as a hypothesis | open lead, Assumed | span-metrics p95 for `GET auth-api /verify` over the window |
| Loki stream `app="orders"` not tied to orders-api (W3-Q9) | no log-derived claim is used as evidence | a human confirms the label or adds a pod/trace ID to log lines |
| Run clock unavailable (`date -u` printed nothing) | no wall-clock Start column, no time-to-cause in minutes | none (environment property) |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: `lessons.md` does not exist under the output root (W0-Q3) |
| Re-verified this run | none |
| History lookup | after the ranked list existed: `ls .culiops/sre-investigate/incidents` and `grep -rnE '^(service\|deps\|symptoms):.*(orders-api\|orders-db\|latency\|p95\|GET /orders)' .culiops/sre-investigate/incidents`. Matched file: `2026-08-14-orders-api.md` (fields: service, deps, symptoms). Not matched: `2026-09-30-catalog-api.md`. No `lessons.md`, so no failure-mode lines. Entered as `from-history:2026-08-14-orders-api.md`. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | loki | `index/stats` returned an empty object for `{namespace="orders"}`; no size estimate is available, so narrow by window and stream instead | W0-Q24 |
| process | prometheus | `histogram_quantile` with 0.9 and 0.99 returned empty matrices while 0.5 and 0.95 returned data for the same histogram and selectors; only p50 and p95 are usable for orders-api | W1-Q9 |
| identifier | prometheus | `http_server_request_duration_seconds_*` carries only service, method, route: no pod or version label, so no per-pod or per-revision split from this metric | W3-Q1 |
| process | tempo | Search `matched` counts all descendants of the server span (DB statements plus the auth-api client span) and span names in search previews can differ from the by-ID trace: take counts from `matched`, names and durations from a by-ID fetch | W3-Q5 |
| identifier | tempo | orders-api traces carry resource attributes service.name and k8s.namespace.name only (no service.version, no pod); GET /orders traces include a client span `GET auth-api /verify` and DB spans named SELECT orders / SELECT order_items / SELECT orders JOIN order_items with db.system=postgresql | W3-Q6 |
| process | cloudwatch | for `orders-db` only CPUUtilization, ReadLatency and DatabaseConnections return data; WriteLatency, DiskQueueDepth, Deadlocks and FreeableMemory returned none and Performance Insights is off | W3-Q8 |
| identifier | loki | request-completed lines for `{namespace="orders", app="orders", container="api"}` carry no pod name or trace ID, so the stream cannot be tied to orders-api from its lines alone; keep it (unverified) | W3-Q9 |
| process | prometheus | `container_cpu_cfs_throttled_periods_total` returned an empty matrix and is absent from the metric-name list: an empty throttling series is not evidence of no throttling | W3-Q11 |
| process | prometheus | `offset 7d` on `http_server_request_duration_seconds_count` returned the unshifted series (identical to the decimal); for -7d call rates shift start and end instead | W3-Q12 |
| process | prometheus | `container_cpu_usage_seconds_total` for namespace orders returned points only from 13:08 although the range started 12:30; do not read the missing earlier points as zero | W1-Q18 |
