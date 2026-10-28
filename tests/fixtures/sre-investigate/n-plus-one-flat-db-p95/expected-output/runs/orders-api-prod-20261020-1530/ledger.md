# Ledger: orders-api prod 20261020-1530

Mode: Deep
Budget used: 53 / 60 queries (counted = reads of signal and change data: W0-Q8, W0-Q9, W1-Q1 to W1-Q24, W2-Q1 to W2-Q11, W3-Q1, W3-Q2, W4-Q1 to W4-Q14; round-2 escalated workers ran no new query; access checks W0-Q1 to W0-Q7 and the 14 profile-discovery calls PB-Q1 to PB-Q14 are logged below but not counted; environment.md sets no query budget, so the template default of 60 is assumed and that counting rule is my interpretation) · 0.096 / 10 GB log bytes (Loki: W0-Q9 probe 0.048 GB and W4-Q8 0.048 GB; Logs Insights not used) · 7 / 500 CloudWatch metric requests (W4-Q5 3, W4-Q6 3, W4-Q7 1) · other: Tempo inspected 6.63 GB (W1-Q21) + 4.76 GB (W4-Q1, W4-Q2) + 4.76 GB (W4-Q13, W4-Q14) = about 16.2 GB (not a metered unit in the budget table)
Wave 1 exceeded ten calls (24) because its fixed legs all ran: change, golden signals for a latency symptom (p50/p90/p95/p99, per-endpoint p95 and call rate, slow-downstream), recurrence pull, alert history.

## Problem

| Field | Value |
|---|---|
| What | Reported: "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing." Measurable restatement: p95 latency of GET /orders (service="orders-api", route="/orders", method="GET") above its pre-incident level of about 0.18 s |
| Where | orders-api, prod, namespace orders (EKS cluster prod); siblings = 3 replicas `orders-api-7c9b6d8f5d-{4kq2m,9vx7t,tz5wp}`; no regions, shards or tenants |
| When | Reported: "early this afternoon UTC" (taken as about 13:00 UTC on 2026-10-20). True onset: 13:08 UTC, first bad sample at a 2-minute step, last good sample 13:06 (W1-Q5); ongoing at 15:30 |
| Who is affected | Callers of GET /orders (order history, a core flow). POST /orders (checkout) p95 flat at 0.14 s (W1-Q7, W1-Q8). Failure rate not measured |
| Trigger | "the p95 alert" named by the operator; alert name, source and link not given; no state history readable (W0-Q8, W1-Q23) |
| Mitigations already applied | none known |
| Assumptions made at intake | Operator confirmed at checkpoint #1 ("Agreed, go on."): the window and onset as shown, and reported no change the run cannot see; the window anchor 13:00 UTC (the request carries an explicit zone, UTC, so no conversion); no date given, date taken as 2026-10-20; run clock "now" = 15:30 UTC (the `date -u` call had no usable output); local zone Australia/Brisbane (UTC+10) from environment.md; budgets: environment.md sets only the Loki ask threshold (20 GB), template defaults used for everything else; the 'queries' counting rule above |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read (AWS, account 111122223333, us-east-1) | role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b (W0-Q1, W0-Q2) | write capability only partly checked (gap): 7 of the 10 simulated actions returned implicitDeny; no row came back for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack; three unrequested rows (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) also implicitDeny (W0-Q3). No action `allowed`, so no boxed warning | session valid; account matches environment.md |
| arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace orders) | same assumed ReadOnly role, group eks-readonly (W0-Q4); it is the current context (W0-Q5) | no write verbs in orders (only get/list/watch and the excluded self-review creates, W0-Q6) | - |
| Grafana datasources prom-prod, loki-prod, tempo-prod | token variable GRAFANA_SERVICE_ACCOUNT_TOKEN | not applicable | variable set (W0-Q7). Culibox not present (nothing printed) |

## Impact

Source order: the SLO or error-budget burn named in `environment.md` (none), then load-balancer or APM request/error/duration metrics against the baseline, then `Assumed`.

| Field | Value |
|---|---|
| Symptom | GET /orders p95 0.712 s at 15:30 against 0.181 s at 12:30 and 0.181 s at the same time 7 days earlier (about 3.9x); p50 0.311 s against 0.092 s (about 3.4x) |
| Affected | prod orders-api, order history (GET /orders, a core flow), all three replicas (CPU per pod similar; per-pod latency not available). GET /orders/{id}, POST /orders, PATCH /orders/{id}, /healthz p95 flat (W1-Q7, W1-Q8, W1-Q9). Customer-facing. Error rate not measured |
| Since / ongoing | 13:08 UTC (23:08 Brisbane) · ongoing at 15:30 UTC (01:30 Brisbane, 2026-10-21) |
| Suggested severity | SEV2 because one core-flow endpoint is significantly degraded (about 4x p95) with the rest of the service healthy; the SEV1 criteria (core flow down or more than 5% of requests failing) are not evidenced, but failures were not measured |
| Basis | request metrics against baseline (no SLO named) · W1-Q5, W1-Q6, W1-Q7, W1-Q8, W1-Q9 · Confirmed (the measurement) |
| Third party in the path | none known (orders-db is AWS RDS inside the same account; the run cannot contact anyone) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-20 12:30 | 2026-10-20 15:30 |
| Baseline (previous) | 2026-10-20 09:30 | 2026-10-20 12:30 |
| Baseline (-7d) | 2026-10-13 12:30 | 2026-10-13 15:30 |

Coverage actually returned by Prometheus ranges: 10:00-15:30 on 2026-10-20 and 10:00-15:30 on 2026-10-13 (the previous window is 10:00-12:30 in practice).

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not available: Prometheus ALERTS 30 d returned no series (W0-Q8); Grafana alert annotations returned `{}` (W1-Q23). No CloudWatch alarm is involved as far as known |
| Signal, 14d at 1h resolution | database operations per second, whole-hour rate (the p95 itself cannot be pulled over 14 d: raw histogram_quantile over 14 d exceeds the 12 h cap and no recording rule is known) · 3 of 336 points returned (10:30, 11:30, 12:30 on 2026-10-20: 371.0, 375.9, 374.7 /s) · median 375 · p95 and max over 3 points are not meaningful · incident peak 4,089 /s (about 10.9x the 3-point maximum) |
| Coverage | alarm history none; Prometheus 14 d pull 3 of 336 points; the same clock window on 2026-10-13 exists (166 points per series, 10:00-15:30) and is flat at baseline (W1-Q9, W1-Q17) |
| Class | unclassified · shape: step (at 13:08), with the dependency call count (database operations) stepping while the endpoint call count stays flat |
| Reason | no alarm history and 3 usable hourly points, so no rule can be applied honestly. What the readable data shows: the signal was at baseline for the whole of 10-13 10:00-15:30 and for 10-20 10:00-13:06, so no earlier occurrence at this clock time is visible (a weak negative, not a classification). Recorded as a coverage gap |
| Label and queries | Assumed (class) · W0-Q8, W1-Q17, W1-Q20, W1-Q23 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-16 / 2026-10-19 (dates only) | commits in v2.14.0..v2.15.0: 3f9d6a1 deps: bump structlog to 25.4.0 (#2203); 7be20d4 orders: return shipment ETA on order detail (#2208); a4c1e9b orders: load items per order in list handler (#2211) | git log | W2-Q1 |
| 2026-10-07 09:40:12 (printed without a zone) | Helm revision 23: chart orders-api-4.2.0, image v2.14.0 | helm history | W1-Q4 |
| 13:04:50 (printed without a zone, treated as local time of the machine) | Helm revision 24: upgrade orders-api, chart unchanged, image v2.14.0 to v2.15.0 | helm history; consistent with ReplicaSet age | W1-Q4, W1-Q1 |
| about 13:05-13:06 | new ReplicaSet orders-api-7c9b6d8f5d created, 3 pods running (ages 145, 144, 144 min at 15:30; approximate) | kubectl | W1-Q2, PB-Q10 |
| 11:08-13:23 | CloudTrail write events naming 'orders', RDS events for orders-db, schedule listings (EventBridge rules, Scheduler, SSM windows, CronJobs): all returned no items | AWS, kubectl | W2-Q3 to W2-Q9 |
| 13:06 | last good sample: GET /orders p95 0.163 s, p50 0.082 s, database operations 365 /s | Prometheus | W1-Q5, W1-Q6, W1-Q16 |
| 13:08 | first bad sample: p95 0.716 s, p50 0.295 s, database operations 4,031 /s (about 10.6x), call rate unchanged (59.5 /s) | Prometheus | W1-Q5, W1-Q6, W1-Q16, W1-Q14 |
| 13:05 / 13:10 | RDS orders-db CPU bucket 23.9% (13:05, baseline) then 41.3% (13:10); ReadLatency flat at about 0.6 ms: the database load rose after the application step | CloudWatch | W4-Q5 |
| 13:08 to 15:30 | p95 stays 0.66-0.76 s, database operations 3.8-4.1 k /s, database span p95 stays about 4 ms, pool used 17-24, pending 0 | Prometheus, Tempo | W1-Q5, W1-Q16, W1-Q21, W1-Q18 |
| 15:30 | still elevated (ongoing) | Prometheus | W1-Q7 |

## Hypotheses

Ranked by fit to onset (13:08, about 3 minutes after the 13:04:50 rollout), shape (step), blast radius (GET /orders only). Formed before the history lookup.

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Release v2.15.0 (PR #2211, commit a4c1e9b, `orders_api/handlers/list_orders.py`) turned GET /orders into an N+1: one statement per order (up to 50) instead of one joined statement, so each request spends several times longer in the database layer | database statements (spans) per GET /orders request well above baseline, each statement as fast as before (about 4 ms); database operations per second stepping at the rollout (seen: x10.4 at 13:08); onset after the rollout start | span count per GET /orders request, incident (14:30-15:30) against baseline (11:00-12:00), at least 20 traces each; equal counts refute it. Onset before 13:04:50 would also refute it (the 13:06 sample is baseline) | strong (three signals to correlate: diff, metrics, traces; a numeric mismatch is expected) | Confirmed |
| H2 | orders-db is saturated or contended (CPU, read latency, locks) and slows GET /orders independently of the number of statements | per-call database latency up; RDS CPU or ReadLatency rising at about 13:08 beyond what extra statements explain | RDS CPUUtilization, ReadLatency, DatabaseConnections at baseline, with the database span p95 at baseline (already flat at about 4 ms, W1-Q21); note the statement count is not flat, so this refutes "database as the bottleneck", not "database load" | default | Ruled out |
| H3 | The connection pool or the engine connection cap is reached (lead from history: `from-history:2026-08-14-orders-api.md`, a pool exhaustion after a pool-size change; matched to this hypothesis, no separate ID) | pool pending_requests above 0 and used pinned at the cap; DatabaseConnections near the engine limit; pool-wait errors | pool pending_requests at 0 throughout (seen: W1-Q18) and DatabaseConnections well below the engine limit refute it | default | Ruled out |
| H4 | The 3 new pods are CPU-throttled or at their CPU limit (extra per-request work exhausting CPU) | CPU throttling share high; CPU at the limit; replicas pinned | throttling near zero and CPU below the limit refute it | default→strong | open: inconclusive (Assumed) |
| H5 | A non-database downstream call of GET /orders (HTTP or cache client span) got slower | non-database client spans with higher p95 inside the incident window | non-database client span p95 at baseline refutes it | default→strong | Ruled out |
| H6 | Traffic spike or bot on GET /orders | volume shape; call rate up against the previous window | call rate against the previous window; no rise refutes it | main | Ruled out (W1-Q14: 56.2 /s against 56.5 /s; the -7d call rate was not usable, G5) |
| H7 | A different commit of the release (#2208 order detail, #2203 structlog bump) caused the latency | the other routes slow too, or GET /orders/{id} slow | per-route p95 against previous and -7d windows; flat routes refute it | main | Ruled out (W1-Q7, W1-Q8, W1-Q9, W2-Q2: only GET /orders moved; /orders/{id} 0.064 against 0.061) |
| H8 | Image pull or scheduling failure, crash loop or OOM on the new pods | pods Pending, restarts, OOMKilled | running count equals desired and restarts at 0 refute it | main | Ruled out (W1-Q2: 3 desired, 3 ready; PB-Q10: 0 restarts; events unavailable, G6) |

- H1 status: supported (Confirmed) · evidence: W1-Q5, W1-Q6, W1-Q14, W1-Q16, W1-Q21, W2-Q2, W3-Q1, W3-Q2, W4-Q1, W4-Q2, W4-Q3, W4-Q4 · note: strong tier from the start (dispatcher rule: three signals to correlate); descendant spans per GET /orders p50 41 against 3 (n=24 each); duration = 90 ms + 6.05 ms per span (r = 0.966); open quantities: p95 0.712 s above the slowest sampled trace (431 ms), and about 64 extra operations per call from metrics against 36 extra statements on average from traces.
- H2 status: refuted (Ruled out) · evidence: W4-Q5, W4-Q6, W1-Q21 · note: default tier; DB CPU 24.9% to 40.6% (max 44%) after the application step, read latency flat at about 0.6 ms; lock waits only excluded indirectly.
- H3 status: refuted (Ruled out, sustained exhaustion) · evidence: W1-Q18, W4-Q7, W4-Q8 · note: default tier; history lead matched here, not shown to the worker; pool size and engine max_connections unreadable; transient bursts not excluded.
- H4 status: open (inconclusive, Assumed) · evidence: W1-Q19, W4-Q9, W4-Q10, W4-Q11, W4-Q3, W4-Q4 · note: default→strong; no CPU limit or throttling series exist; the latency tail is not in the 24-trace sample.
- H5 status: refuted (Ruled out) · evidence: W4-Q1, W4-Q2, W4-Q3, W4-Q4, W4-Q12 to W4-Q14 · note: default→strong; basis is the latency-against-span-count fit (intercept 90 ms against baseline median 110 ms), auth-api's own latency not measured.
- H6, H7, H8 status: refuted in the main session from Phase 1 and 2 data; no worker dispatched.
- Not generated: `sched:` hypotheses (class is not `scheduled` and no schedule was listed, W2-Q3 to W2-Q6); NAT/egress, DNS, certificate or credential expiry, API throttling, cache (no errors, step shape, no such component in the profile).

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (local clone ~/src/orders-api, read by tag, no fetch) | unknown (gh returned `{}`); newest-on-default-branch not used | not resolved | clone age not verified (environment.md says tags v2.14.0 and v2.15.0 are fetched; both resolved by `log`/`diff`/`show`) | v2.15.0 for Helm revision 24 (APP VERSION and CHANGE-CAUSE, W1-Q4, W1-Q1; the pod image string itself was not read, so "v2.15.0 is running" is Likely); v2.14.0 for revision 23. Commit SHA of the tag not resolved |

## Query log

Start times are the run clock (simulated), UTC. Identifiers marked (verified) returned data in this run; the rest are (unverified).

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 15:30:00 | AWS prod-read: `aws sts get-caller-identity --profile prod-read` | n/a | free | account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b; matches environment.md |
| W0-Q2 | 15:30:00 | AWS prod-read: `aws iam get-role --role-name <ReadOnly role>` | n/a | free | role path `/aws-reserved/sso.amazonaws.com/`; full role ARN resolved |
| W0-Q3 | 15:30:00 | AWS prod-read: `aws iam simulate-principal-policy` (fixed list of ten) | n/a | free | 10 rows, all implicitDeny, but 3 requested actions have no row and 3 unrequested rows came back; gap G1 |
| W0-Q4 | 15:30:00 | kubectl: `auth whoami --context arn:...:cluster/prod` | n/a | free | assumed ReadOnly role, group eks-readonly |
| W0-Q5 | 15:30:00 | kubectl: `config current-context` | n/a | free | arn:aws:eks:us-east-1:111122223333:cluster/prod |
| W0-Q6 | 15:30:00 | kubectl: `auth can-i --list --context ... --namespace orders` | n/a | free | no write verbs; self-review creates excluded |
| W0-Q7 | 15:30:00 | env: token presence of GRAFANA_SERVICE_ACCOUNT_TOKEN | n/a | free | set |
| W0-Q8 | 15:30:00 | Prometheus prom-prod: `sum by (alertname) (max_over_time(ALERTS{alertstate="firing"}[1h]))` | 2026-09-20 15:30 to 2026-10-20 15:30, step 3600 | light | empty matrix: no ALERTS series; gap G2. link: Grafana Explore prom-prod, same expression |
| PB-Q1 | 15:31:00 | Loki loki-prod: label names | last hour | free | app, container, namespace, stream |
| PB-Q2 | 15:31:00 | Loki: values of `app` | last hour | free | catalog-api, notify-worker, orders, orders-reconcile, payments-worker |
| PB-Q3 | 15:31:00 | Loki: values of `namespace` | last hour | free | catalog, notify, orders (verified), payments |
| PB-Q4 | 15:31:00 | Loki: values of `container` | last hour | free | api, worker |
| PB-Q5 | 15:31:00 | Tempo tempo-prod: `/api/v2/search/tags` | n/a | free | resource tag `service.name`; span tags db.system, http.route, http.request.method, ... |
| PB-Q6 | 15:31:00 | Tempo: tag values of `resource.service.name` | 14:30-15:30 | free | `{}`, nothing usable |
| PB-Q7 | 15:31:00 | Tempo: `{ resource.service.name = "orders-api" }` limit 5 | 14:30-15:30 | free | 0 traces (the name is later seen to return data with a db-span filter, W1-Q21) |
| PB-Q8 | 15:31:00 | Prometheus: `label/__name__/values` | n/a | free | http_server_request_duration_seconds_{bucket,count,sum}, db_client_operation_duration_seconds_*, db_client_connections_{usage,pending_requests}, container_cpu_usage_seconds_total, kube_deployment_status_replicas, up |
| PB-Q9 | 15:31:00 | Grafana: dashboard search "orders" | n/a | free | `{}`: none found |
| PB-Q10 | 15:31:00 | kubectl: `get pods -n orders` | now | free | 3 pods orders-api-7c9b6d8f5d-*, Running, 0 restarts, ages 145/144/144 min |
| PB-Q11 | 15:31:00 | kubectl: `get deploy,svc,ingress,hpa -n orders` | now | free | no output (not read as "none exist") |
| PB-Q12 | 15:31:00 | AWS prod-read: `rds describe-db-instances` filtered "orders" | now | free | orders-db, db.r6g.2xlarge, postgres 16.6, available, Multi-AZ, Performance Insights disabled |
| PB-Q13 | 15:31:00 | git: `git -C ~/src/orders-api tag` | n/a | free | v2.12.0, v2.13.0, v2.13.1, v2.14.0, v2.15.0 |
| PB-Q14 | 15:31:00 | gh: `repos/example-org/orders-api` default branch | n/a | free | `{}`: not returned; default branch (unverified) |
| W0-Q9 | 15:31:10 | Loki loki-prod: index stats `{namespace="orders"}` (namespace verified) | 15:15-15:30 | est. 0.048 GB; actual `totalBytesProcessed` 48,211,904 B | two streams (app="orders"/container="api", app="orders-reconcile"/container="worker"); only the api stream has lines in the window (8 lines, GET /orders 286-751 ms, page_size=50); api stream not tied to the service (unverified) |
| W1-Q1 | 15:31:20 | kubectl: `rollout history deployment/orders-api -n orders` | n/a | free | rev 23 image v2.14.0 chart 4.2.0; rev 24 image v2.15.0 chart 4.2.0. Deployment name (verified) |
| W1-Q2 | 15:31:20 | kubectl: `get rs -n orders` sorted by creation | now | free | orders-api-5f8d9c7b6a 0/0/0 age 13d; orders-api-7c9b6d8f5d 3/3/3 age 145m |
| W1-Q3 | 15:31:20 | kubectl: `get events -n orders` | last hour retention | free | none in the namespace. Events live one hour and the rollout is 145 min old: events not available for the rollout (gap G6), not "no events" |
| W1-Q4 | 15:31:20 | helm: `history orders-api -n orders --max 10` | n/a | free | rev 24 Tue Oct 20 13:04:50 2026 deployed, app v2.15.0; rev 23 Wed Oct 7 09:40:12 2026 superseded, v2.14.0; no zone printed (G10) |
| W1-Q5 | 15:33:05 | Prometheus prom-prod: p95 of GET /orders (`histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))`) | 09:30-15:30, step 120 (returned 10:00-15:30) | heavy 1 | median 0.180 s before 13:06; 13:06 = 0.163; 13:08 = 0.716; 13:10-15:30 median 0.712 (0.661-0.755). `service="orders-api"` (verified). Confirmed (measurement) |
| W1-Q6 | 15:33:05 | Prometheus: p50 of GET /orders (same selectors, quantile 0.5) | same | heavy 2 | median 0.092 before; 13:08 = 0.295; 13:10-15:30 median 0.311 (0.281-0.339). Confirmed (measurement) |
| W1-Q7 | 15:33:05 | Prometheus: p95 `by (le, method, route)` of service orders-api, instant | 15:30 | light | GET /orders 0.712; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; GET /healthz 0.003 |
| W1-Q8 | 15:33:05 | Prometheus: same, instant | 12:30 | light | GET /orders 0.181; /orders/{id} 0.061; POST 0.139; PATCH 0.091; healthz 0.003 |
| W1-Q9 | 15:33:05 | Prometheus: same with `offset 7d`, instant | 2026-10-13 15:30 | light | GET /orders 0.181; /orders/{id} 0.061; POST 0.139; PATCH 0.091; healthz 0.003 |
| W1-Q10 | 15:33:05 | Prometheus: p99 of GET /orders, instant | 15:30 | light | empty (no series); not zero; gap G4 |
| W1-Q11 | 15:33:05 | Prometheus: p99 of GET /orders, instant | 12:30 | light | empty; gap G4 |
| W1-Q12 | 15:33:05 | Prometheus: p90 of GET /orders, instant | 15:30 | light | empty; gap G4 |
| W1-Q13 | 15:33:05 | Prometheus: p90 of GET /orders, instant | 12:30 | light | empty; gap G4 |
| W1-Q14 | 15:33:05 | Prometheus: `sum(rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders", method="GET"}[5m]))` | 09:30-15:30, step 120 | light | 56.5 /s before 13:06; 56.2 /s from 13:10 (52.1-60.6); flat |
| W1-Q15 | 15:33:05 | Prometheus: same with `offset 7d` | 12:30-15:30 | light | reply carries 2026-10-20 timestamps, not 2026-10-13: not a usable -7d baseline; gap G5 |
| W1-Q16 | 15:33:05 | Prometheus: `sum(rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))` | 09:30-15:30, step 120 | light | 381 /s before 13:06 (361-401); 13:08 = 4,031; 13:10-15:30 median 3,961 (3,821-4,089); about 10.4x. label `db_system="postgresql"` |
| W1-Q17 | 15:33:05 | Prometheus: same with `offset 7d` | 12:30-15:30 | light | 2026-10-13: median 379 (355-404): flat |
| W1-Q18 | 15:33:05 | Prometheus: `db_client_connections_usage{service="orders-api"} or db_client_connections_pending_requests{service="orders-api"}` | 09:30-15:30, step 120 | light | pool orders-db used: median 16 (max 19) before, median 21 (max 24) after 13:10; pending_requests 0 throughout |
| W1-Q19 | 15:33:05 | Prometheus: `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders"}[5m]))` | 09:30-15:30, step 600 (returned 13:08-15:30, 15 points) | light | 4kq2m 0.53-0.64, 9vx7t 0.52-0.63, tz5wp 0.56-0.64 cores; replicas move together; no baseline, no limit known (G7) |
| W1-Q20 | 15:33:05 | Prometheus: `sum(rate(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))` | 2026-10-06 12:30 to 2026-10-20 12:30, step 3600 | light | 3 of 336 points (371.0, 375.9, 374.7 /s); gap G3 |
| W1-Q21 | 15:33:05 | Tempo tempo-prod: `{ resource.service.name = "orders-api" && span.db.system =~ ".+" } \| quantile_over_time(duration, .95)` | 09:30-15:30, step 900 | heavy 1; inspected 6.63 GB | database span p95 3.9-4.4 ms in every sample, no change at 13:08. Trace service name `orders-api` (verified) |
| W1-Q22 | 15:33:05 | Tempo: same selector `\| rate()` | 09:30-15:30, step 900 | heavy 2 | `series: []`; db span rate not available (G8) |
| W1-Q23 | 15:33:05 | Grafana annotations, type=alert | 2026-09-20 15:30 to 2026-10-20 15:30, limit 100 | free | `{}`: nothing returned; gap G2 |
| W1-Q24 | 15:33:05 | Grafana annotations, all types | 12:30-15:30, limit 100 | free | `{}`: no deploy markers or notes returned |
| W2-Q1 | 15:36:00 | git: `git -C ~/src/orders-api log --date=iso-strict --format='%h %cI %an %s' v2.14.0..v2.15.0` | tags | free | 3 commits: a4c1e9b (2026-10-19) orders: load items per order in list handler (#2211); 7be20d4 (2026-10-19) return shipment ETA on order detail (#2208); 3f9d6a1 (2026-10-16) bump structlog to 25.4.0 (#2203). Reply showed date and subject only |
| W2-Q2 | 15:36:00 | git: `git -C ~/src/orders-api diff v2.14.0 v2.15.0` | tags | free | 3 files: `orders_api/handlers/list_orders.py` (one query `repo.list_orders_with_items(...)` replaced by `repo.list_orders(...)` plus a per-order loop `repo.list_items(order.id)`), `orders_api/handlers/order_detail.py` (adds shipment_eta to the response), `pyproject.toml` (structlog 25.3.0 to 25.4.0) |
| W2-Q3 | 15:36:00 | AWS prod-read: `aws events list-rules --region us-east-1` scheduled rules | now | free | `{}`: no items returned |
| W2-Q4 | 15:36:00 | AWS prod-read: `aws scheduler list-schedules --region us-east-1` | now | free | `{}`: no items returned |
| W2-Q5 | 15:36:00 | AWS prod-read: `aws ssm describe-maintenance-windows --region us-east-1` | now | free | `{}`: no items returned |
| W2-Q6 | 15:36:00 | kubectl: `get cronjobs -A` (custom columns) | now | free | no output |
| W2-Q7 | 15:36:00 | AWS prod-read: `aws rds describe-db-instances` backup and maintenance windows of orders-db | now | free | reply (same as PB-Q12) carries no PreferredBackupWindow or PreferredMaintenanceWindow fields: windows not known |
| W2-Q8 | 15:36:00 | AWS prod-read: `TZ=UTC aws cloudtrail lookup-events` ReadOnly=false, resource name containing 'orders' | 11:08-13:23 | free | `{}`: no events returned (CloudTrail sees AWS control-plane writes, not Helm deploys inside the cluster) |
| W2-Q9 | 15:36:00 | AWS prod-read: `aws rds describe-events --source-type db-instance --source-identifier orders-db` | 11:08-14:08 | free | `{}`: no events returned |
| W2-Q10 | 15:36:00 | Prometheus: p95 of GET /orders with `offset 7d` (same selectors as W1-Q5) | 12:30-15:30 evaluated, step 120 | heavy 1 | 2026-10-13 12:30-15:30 median 0.181 s (0.161-0.200); 13:00-13:20 median 0.172: flat. Confirms the -7d baseline across the whole window |
| W2-Q11 | 15:36:00 | Prometheus: p50 of GET /orders with `offset 7d` | same | heavy 2 | 2026-10-13 median 0.088 s (0.080-0.100): flat |
| W3-Q1 | 15:38:00 | git: `git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py` | tag v2.15.0 | free | `limit = min(int(request.query.get("limit", 50)), 50)`; `orders = repo.list_orders(customer_id, limit=limit)`; then `for order in orders: order.items = repo.list_items(order.id)`; up to 50 orders per page, one `list_items` call per order |
| W3-Q2 | 15:38:00 | git: `git -C ~/src/orders-api show v2.15.0:orders_api/repository.py` | tag v2.15.0 | free | `list_orders` runs one SELECT with LIMIT; `list_items` runs one SELECT on order_items per call and takes its own connection from the pool; `list_orders_with_items` (one SELECT with a LEFT JOIN, "used by the list handler up to v2.14.0") still exists, unused by the handler in v2.15.0 |
| W4-Q1 (was H1-Q1) | 15:42:00 | Tempo tempo-prod: `{ resource.service.name = "orders-api" && span.http.route = "/orders" && span.http.request.method = "GET" } >> { span:kind = client }` limit 30 | 14:30-15:30 | inspected 2.41 GB | 24 traces (at least 20); descendant spans per request p50 41, p95 52, max 52, min 9, mean 38.9; duration = 89.8 ms + 6.05 ms per span, r = 0.966. raw/H1/tr-matched-incident.tsv. link: Explore tempo-prod |
| W4-Q2 (was H1-Q2) | 15:42:00 | Tempo: same query | 11:00-12:00 | inspected 2.35 GB | 24 traces; descendant spans p50 3, p95 4, max 4, min 2, mean 3.1; durations 78-165 ms (median 110) not related to span count. raw/H1/tr-matched-baseline.tsv. link: Explore tempo-prod |
| W4-Q3 (was H1-Q3) | 15:42:00 | Tempo: `GET /api/v2/traces/e3ea7a3906419b466a28541306cc5ee1` (window padded 1 h) | 13:30-16:30 | small | 15 spans: root GET /orders 152 ms, GET auth-api /verify 3.4 ms, SELECT orders 3.0 ms, 12 x SELECT order_items 2.9-4.5 ms, serial, 1.0-1.7 ms apart; tail after last child 81.9 ms. link: Tempo trace e3ea7a39... |
| W4-Q4 (was H1-Q4) | 15:42:00 | Tempo: `GET /api/v2/traces/65345f5f8176033524bc88af3bd43f6f` (padded 1 h) | 10:00-13:00 | small | 3 spans: root 109 ms, auth-api verify 3.8 ms, one `SELECT orders JOIN order_items` 3.05 ms; tail after last child 99.1 ms. link: Tempo trace 65345f5f... |
| W4-Q5 (was H2-Q1) | 15:42:00 | CloudWatch prod-read us-east-1: get-metric-data CPUUtilization, ReadLatency, DatabaseConnections, AWS/RDS orders-db, Period 300 | 10:00-15:30 | 3 metric requests | CPU median 24.9% (max 26.9) until 13:05 bucket, 41.3% in the 13:10 bucket, median 40.6% (37.1-44.0) from 13:15; ReadLatency 0.58-0.60 ms flat; connections median 42 to 47 (max 48). 67 points per metric, newest first. link: CloudWatch console |
| W4-Q6 (was H2-Q2) | 15:42:00 | CloudWatch: get-metric-data Deadlocks, DiskQueueDepth, FreeableMemory, orders-db, Period 300 | 10:00-15:30 | 3 metric requests | no data for any of the three (gap G18) |
| W4-Q7 (was H3-Q1) | 15:42:00 | CloudWatch: get-metric-data DatabaseConnections, orders-db, Period 300 | 10:00-15:30 | 1 metric request | same series as W4-Q5: 42 to 47, max 48 (duplicate read of a parallel worker) |
| W4-Q8 (was H3-Q2) | 15:42:00 | Loki loki-prod: `{namespace="orders", app="orders"} \|~ "(?i)(pool\|too many connections\|timeout\|refused)"` | 15:15-15:30 | est. 0.048 GB (reused W0-Q9); actual 48,211,904 B | 0 matching lines (stream not tied to the service, unverified) |
| W4-Q9 (was H4-Q1) | 15:42:00 | Prometheus: throttled periods / periods per pod, namespace orders | 12:30-15:30 | light | empty matrix: metric not exported (not zero); gap G16 |
| W4-Q10 (was H4-Q2) | 15:42:00 | Prometheus: `kube_pod_container_resource_limits{namespace="orders", resource="cpu"}` | 15:30 | light | empty; gap G16 |
| W4-Q11 (was H4-Q3) | 15:42:00 | kubectl: get deployment orders-api resources (jsonpath) | now | free | no output; gap G16 |
| W4-Q12 (was H5-Q1) | 15:42:00 | Tempo: non-database client span p95 by span:name (TraceQL metrics) | 12:30-15:30, step 900 | heavy | `series: []` (no data, not zero) |
| W4-Q13 (was H5-Q2) | 15:42:00 | Tempo: GET /orders root spans, limit 30 | 14:30-15:30 | inspected 2.41 GB | 24 traces, root only; duration median 340 ms, p95 422, max 431 |
| W4-Q14 (was H5-Q3) | 15:42:00 | Tempo: GET /orders root spans, limit 30 | 11:00-12:00 | inspected 2.35 GB | 24 traces, root only; median 110 ms, p95 165 |
## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1: AWS write capability only partly checked: no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (W0-Q3) | none on the cause; the report cannot say the profile is read-only | a human re-runs the simulation for those three actions, or confirms prod-read is a read-only role |
| G2: trigger alert history and name unknown; ALERTS series empty, alert annotations empty (W0-Q8, W1-Q23) | recurrence class cannot be computed; chronic or flapping alert not excluded; alert threshold not known | the alert's name, source (Grafana-managed or other) and its state history from whoever owns the alert |
| G3: 14-day hourly pull returned 3 of 336 points (W1-Q20); readable Prometheus data is 10:00-15:30 on 10-13 and 10-20 only | recurrence label `unclassified` stays `Assumed`; prior occurrences may exist outside the readable range | confirm Prometheus retention and any recording rule for p95 with the platform owner |
| G4: p90 and p99 returned empty (W1-Q10 to W1-Q13) | the ceiling check rests on p50 versus p95 only | the platform owner confirms whether p90/p99 are scraped; or use a recording rule |
| G5: -7d call rate not usable (W1-Q15) | volume versus work-per-request is judged against the previous window only | none needed unless a -7d call rate is wanted |
| G6: Kubernetes events not available for the rollout (events live one hour; rollout 145 min old) (W1-Q3) | no Unhealthy, BackOff or scheduling events can be read; probe and pull hypotheses rest on pod state and metrics | none (expired); a human can read the event history if the cluster ships events to a log store |
| G7: CPU only from 13:08, no limit or request known (W1-Q19) | CPU saturation cannot be ruled out or in against a baseline | read the Deployment's resource requests and limits from the chart values at the deployed ref |
| G8: Tempo db span rate empty (W1-Q22) | span counts must come from sampled traces | none |
| G9: Services, ingresses, HPAs not listed; no load balancer or upstream identified (PB-Q11) | upstream path and autoscaling cannot be reasoned about | a human lists them or points to the chart values |
| G10: Helm prints the revision times without a zone (W1-Q4) | the 13:04:50 deploy time is approximate against UTC (consistent with ReplicaSet age at about 13:05) | read the ReplicaSet creationTimestamp (RFC 3339, UTC) in a follow-up read |
| G11: IaC repo/values repo and the default branch of example-org/orders-api unknown (PB-Q14) | IaC history (merged versus applied) cannot be checked | name the repo |
| G14: histogram p95 0.712 s (W1-Q5) is above the slowest sampled incident trace (431 ms, sample p95 422 ms) (W4-Q1, W4-Q13) | the absolute p95 value is not reproduced by the trace sample; direction and p50 size are (r = 0.966). The histogram bucket layout is unknown and could inflate an interpolated p95 | a human reads the bucket boundaries of the latency histogram and the tail of the real latency distribution |
| G15: metrics imply about 64 extra database operations per GET /orders call, traces about 36 extra statements on average (at most 50) | quantity only; does not affect the mechanism | the metric owner says whether `db_client_operation_duration_seconds_count` counts commits or other operations besides statements |
| G16: CPU limit, requests and throttling not readable (W4-Q9 to W4-Q11; W1-Q19 has no baseline) | H4 stays open | read the container resources from the chart values at v2.15.0 and the throttling panel |
| G17: pool maximum size and engine max_connections unreadable | "well below the limit" is not shown for H3; refutation rests on pool waiters = 0 (sampled gauge) | read pool size from the chart values and max_connections from the DB parameter group |
| G18: no lock-wait data (Performance Insights disabled; Deadlocks, DiskQueueDepth, FreeableMemory returned no data, W4-Q6) | H2 lock contention excluded only through flat statement latency | enable Performance Insights for future incidents |
| G19: non-database dependencies of GET /orders not listed in the profile; auth-api seen in traces (client span GET auth-api /verify) with no latency series | H5 refuted only through the regression intercept | name the dependencies and read their latency |
| G13: schedule listings, CloudTrail and RDS events returned no items (W2-Q3 to W2-Q9); RDS backup and maintenance windows not in the reply | a schedule, a control-plane change or a maintenance window near 13:08 cannot be ruled out by an empty reply alone; coverage is region us-east-1 under prod-read | a human with other access (or a different region/account scope) lists the schedules and the maintenance windows |
| G12: no SLO and no business counter named for the core flows | impact basis is request metrics, not SLO burn | name the SLO or the checkout/order-history counters in environment.md |

## Untrusted text

none seen. (Helm/rollout CHANGE-CAUSE text "helm upgrade orders-api (chart orders-api-4.2.0, image v2.15.0)" and the Loki api lines were read as data; neither contains an instruction.)

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: no `lessons.md` exists |
| Re-verified this run | none (no lessons existed) |
| History lookup | run after H1-H8 were ranked: `ls .culiops/sre-investigate/incidents` (2 files: 2026-08-14-orders-api.md, 2026-09-30-catalog-api.md); `grep -rn -i -E "orders-api|orders-db|latency" .culiops/sre-investigate/incidents` matched only 2026-08-14-orders-api.md (service orders-api, deps orders-db, symptoms latency, "GET /orders"). Read it: cause_category db-connection-pool, Confirmed then, pool exhausted after a pool-size change, pending_requests above 30. It matches H3, noted against H3 as a lead. Not given to any worker. 2026-09-30-catalog-api.md did not match. service-discovery catalog: none (`ls .culiops/service-discovery/` returns no such directory) |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | `iam simulate-principal-policy` on this account returned rows that did not match the requested action list (3 missing, 3 unrequested); check the returned action names against the request before reading "none allowed" | W0-Q3 |
| process | tempo | A bare `resource.service.name = "orders-api"` search for the last hour returned 0 traces, yet a TraceQL metrics query with `span.db.system =~ ".+"` returned the service; do not mark the service name wrong after one empty bare search | W1-Q21 |
| process | prometheus | An `offset 7d` query on the HTTP call rate returned current-day timestamps; check the timestamps of an offset reply before using it as a baseline | W1-Q15 |
| process | kubectl | Kubernetes events were gone for a rollout 145 minutes old; read events in the first minutes of a run or accept "events not available" | W1-Q3 |
| process | tempo | In structural TraceQL searches `matched` counts every descendant span, including non-database client spans (one constant auth-api call per request here); subtract the constant before reading it as statements per request | W4-Q3 |
| process | cloudwatch | `get-metric-data` for RDS returned timestamps newest first; sort before bucketing or comparing with the onset | W4-Q5 |
| identifier | prometheus | `container_cpu_cfs_*` and `kube_pod_container_resource_limits` are not in the metric names of prom-prod; do not query them, read limits from the chart values | W4-Q9 |
| process | tempo | A plain `/api/search` returns only the root span (`matched` 1); use a structural query to get child spans | W4-Q13 |
| process | prometheus | For pool exhaustion read `db_client_connections_pending_requests` first (0 here); the gauge is sampled at 60 s, so a short burst can be missed | W1-Q18 |
| identifier | loki | In loki-prod, `{namespace="orders", app="orders", container="api"}` carries `GET /orders` request lines (no pod label); it is not tied to the orders-api pods (no shared pod name or trace ID), so `app="orders"` stays unverified | W0-Q9 |
