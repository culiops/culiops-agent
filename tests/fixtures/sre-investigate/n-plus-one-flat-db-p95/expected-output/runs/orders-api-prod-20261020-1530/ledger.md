# Ledger: orders-api prod 20261020-1530

(Stage C, final: written after the Phase 4 verdicts were merged. Stages A and B were written after wave 0 and after waves 1 to 2 and Phase 3.)

Mode: Deep
Budget used: 43 / 60 counted queries · 0.05 / 20 GB Loki scanned · 3 / 500 CloudWatch metric requests. Counting rule: environment.md names no query totals, so the template's neutral deep totals (60 queries, 10 GB logs, 500 metric requests) are a self-imposed ceiling. Counted = data reads against Prometheus, Tempo, Loki, kubectl, Helm, AWS, git (W0-Q8..Q9, W1, W2, W3). Not counted but logged: 7 access and permission checks (W0-Q1..Q7) and 17 profile-discovery list reads (PB-Q1..Q17). All logged calls together are 67, which is above 60; I judged IAM/auth checks and discovery lists as unmetered and say so here. Wave 1 had 21 queries in 8 shell calls (above ten, because its fixed legs need it). The 25 queries left after wave 2 were split evenly over 8 workers (3 each); the escalated H5 worker used one query taken from the shares other workers did not use.

## Problem

| Field | Value |
|---|---|
| What | Reporter: "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing." Measurable restatement: p95 of `GET /orders` (service `orders-api`, prod) rose from about 0.18 s to about 0.71 s at 13:08 UTC and is still there; p50 rose from about 0.09 s to about 0.31 s (W1-Q8, W1-Q9). |
| Where | Service orders-api, environment prod, EKS cluster `prod`, namespace `orders`, 3 replicas on one ReplicaSet. Siblings: other routes of the same service (flat), no regions or shards. |
| When | Reported: "early this afternoon UTC". True onset: last clean sample 13:06 UTC, first elevated sample 13:08 UTC (W1-Q8), 23:08 local (UTC+10). Ongoing at 15:30 UTC. |
| Who is affected | Every caller of `GET /orders` (about 56 req/s, PB-Q16); other routes are not slower (W1-Q5, W1-Q6). |
| Trigger | A p95 alert on `GET /orders`; name, system and link not given; no alert history found (W0-Q8). |
| Mitigations already applied | none known |
| Assumptions made at intake | 1. "Early this afternoon UTC" has an explicit zone (UTC) so it is used as given; being rough, anchored at 13:00 UTC, window opened 30 minutes earlier. 2. Window 2026-10-20 12:30 to 15:30 UTC (22:30 to 01:30 Australia/Brisbane, UTC+10, from environment.md). 3. "Now" = 15:30 UTC, the newest Prometheus sample, because `date -u` printed nothing; the Start column of the query log is indicative. 4. Ongoing incident, window runs to now. 5. Helm's `UPDATED` column prints no zone; read as UTC only after the cross-check under Timeline. 6. The Loki `app="orders"` lines are a lead only (log label not tied to the service). |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | write check incomplete: 7 of the 10 fixed actions returned `implicitDeny`, none `allowed`; no result row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack, so "read-only confirmed" is NOT claimed; write capability unknown (gap) for those three. Three extra actions (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) also came back `implicitDeny`; not part of the verdict. | Session valid. Boxed warning not shown (nothing allowed). |
| arn:aws:eks:us-east-1:111122223333:cluster/prod | Kubernetes user = the same SSO ReadOnly role; groups eks-readonly, system:authenticated | no write verbs in orders | Grant is `*.*` get/list/watch, which includes Secrets; Secret objects are never read by this run. |
| Grafana datasources (prom-prod, loki-prod, tempo-prod) | service-account token | not applicable | `GRAFANA_SERVICE_ACCOUNT_TOKEN`: set. |
| Culibox | not detected | | nothing printed |

## Impact

| Field | Value |
|---|---|
| Symptom | `GET /orders` p95 0.181 s (12:30 UTC) to 0.712 s (15:30 UTC), 3.9 times; p50 about 0.09 s to about 0.31 s, 3.4 times; request rate unchanged (56.5 req/s before, 56.1 after). No errors measured: the HTTP histogram has no status label; two sampled traces returned 200. |
| Affected | Order history, a core flow in environment.md, all callers, customer-facing. `POST /orders` (0.139 to 0.142 s), `GET /orders/{id}` (0.061 to 0.064 s), `PATCH /orders/{id}` (0.091 to 0.088 s) and `/healthz` (0.003 s) are flat. |
| Since / ongoing | 13:08 UTC (first elevated sample; last clean 13:06) · ongoing at 15:30 UTC |
| Suggested severity | SEV2 because a core flow (order history) is significantly degraded (about 4 times slower at p95) with no failures measured; the default scale in environment.md has no SLO to burn against. |
| Basis | request metrics against the baseline (W1-Q5..Q11, PB-Q16) · Confirmed for the latency change; error impact Assumed (no status label) |
| Third party in the path | none found (orders-db is the company's own RDS; auth-api is internal) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-20 12:30 | 2026-10-20 15:30 |
| Baseline (previous) | 2026-10-20 09:30 | 2026-10-20 12:30 |
| Baseline (-7d) | 2026-10-13 12:30 | 2026-10-13 15:30 |

Re-anchored: no. The true onset (13:08 UTC, W1-Q8) is 8 minutes from the 13:00 anchor and after the window start, so the windows stay.
Coverage: Prometheus returned samples from 10:00 UTC only, so 09:30 to 10:00 of the previous window is uncovered.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none obtainable: alert name not given, no `ALERTS` series, annotations API returned `{}` (W0-Q8). Sibling alarms: none known. |
| Signal, 14d at 1h resolution | Latency recurrence not pulled: no latency recording rule exists, and the subquery fallback over 14 days exceeds `prom_quantile_range` (12h). Fallback signal: hourly `increase` of DB operations (counter, `increase(x[1h])`), W1-Q20. Median / p95 / max over the hours returned before the incident: 1.37M / 1.37M / 1.37M per hour (3 hourly points, 10:00 to 12:30 today); incident level 14.2M per hour (14:00 hour). |
| Coverage | 3 of 336 hourly points (data starts 10:00 UTC today). Same clock window on 2026-10-13: p95 0.16 to 0.20 s throughout (W1-Q10), DB ops 355 to 404/s (W1-Q16). |
| Class | unclassified · shape: step (p95, p50 and DB operations all step at 13:08 and stay; request rate flat, so not volume; p50 moved, so not a ceiling) |
| Reason | No alarm history and 2.5 hours of 14-day signal coverage: none of the rules for `scheduled`, `chronic`, `recurring` or `sudden` can be applied. The step has lasted 2 h 22 min without repeating, which fits no periodic job, but that is not a classification. |
| Label and queries | shape: Confirmed (W1-Q8, W1-Q9, W1-Q15, PB-Q16) · class: gap, recorded under Gaps |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-16 (date only) | commit 3f9d6a1 "deps: bump structlog to 25.4.0 (#2203)" | git, local clone | W2-Q1 |
| 2026-10-19 (date only) | commits 7be20d4 "return shipment ETA on order detail (#2208)" and a4c1e9b "load items per order in list handler (#2211)" | git, local clone | W2-Q1 |
| 2026-10-07 09:40:12 (zone not printed) | Helm revision 23: orders-api chart 4.2.0, app v2.14.0 (the release that ran until the incident) | helm history | W1-Q4 |
| 13:04:50 (zone not printed by Helm; read as UTC, see assumption 5) | Helm revision 24: chart 4.2.0 unchanged, app v2.15.0, "Upgrade complete" | helm history, rollout history revision 24 | W1-Q4, W1-Q3 |
| about 13:05 (derived) | ReplicaSet orders-api-7c9b6d8f5d created; pods 145, 144, 144 minutes old at about 15:30; old ReplicaSet orders-api-5f8d9c7b6a at 0 replicas; 0 restarts | kubectl | W1-Q2, PB-Q9 |
| 13:06 | last clean `GET /orders` samples: p95 0.163 s, p50 0.082 s, DB ops 365.5/s | Prometheus | W1-Q8, W1-Q9, W1-Q15 |
| 13:08 | first elevated samples: p95 0.716 s, p50 0.295 s, DB ops 4031.1/s (10.4 times); request rate unchanged | Prometheus | W1-Q8, W1-Q9, W1-Q15, PB-Q16 |
| 13:10 | RDS CPU 41.3% in the 13:10 five-minute bucket (the 13:05 bucket was 23.9%); ReadLatency flat at 0.5 ms | CloudWatch | W3-Q3 |
| 15:30 | still elevated: p95 0.712 s | Prometheus | W1-Q5 |

Rollout dating cross-check: Helm prints `UPDATED` without a zone. Independent of it, the new pods are 145 minutes old at about 15:30 (kubectl `AGE`, W1-Q2), which puts creation near 13:05, and the UTC-stamped step in Prometheus is at 13:08. These agree to about three minutes; the run does not have a UTC-stamped creationTimestamp (the kubectl reply shows only `AGE`).

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The v2.15.0 rollout (Helm revision 24) caused the `GET /orders` slowdown: only the new revision is slow | slowdown starts as the new pods take traffic; the old revision was clean before; the diff touches the failing path | old-against-new split of `GET /orders` p95 and spans per revision; an onset before 13:04:50, or the old revision equally slow, refutes it | default | Confirmed |
| H2 | The v2.15.0 list handler loads items with one query per order (N+1), so each request makes many more DB calls | spans per `GET /orders` request up against baseline, each span as fast as before; DB ops/s up while request rate is flat; `limit` caps at 50 | descendant-span count per `GET /orders` request, 24 traces per window, 14:30 to 15:30 against 11:00 to 12:00; equal counts refute it | strong | Confirmed |
| H3 | orders-db itself is slow (CPU, locks, credits) | RDS CPU high, ReadLatency up, per-call DB spans slower | RDS CPUUtilization, ReadLatency, DatabaseConnections at baseline refute it, but only together with a flat per-request query count | default | Ruled out |
| H4 | DB connection exhaustion: the pool cap is reached | pool `used` pinned at its cap, `pending_requests` above zero | `pending_requests` at zero throughout and `used` far from any cap refute it | default | Ruled out |
| from-history:2026-08-14-orders-api | A pool-size or configuration change left the orders-db pool exhausted (a lead from history; overlaps H4) | `pending_requests` above zero for the window; a chart or values change at the onset | `pending_requests` at zero throughout, and the chart version unchanged across the rollout, refute it | default | Ruled out |
| H5 | Pod capacity: the 3 replicas are CPU-bound or throttled, with no autoscaler to add pods | CPU at its limit or throttled, HPA at max, desired above ready | desired = ready = 3 and no throttling refute it; HPA absent or below max refutes the autoscaler part | default→strong | Assumed |
| H6 | A traffic spike or bot raised the load on `GET /orders` | volume shape: call rate up at 13:08 | request count against the previous window and -7d; no rise refutes it | default | Ruled out |
| H7 | A downstream (orders-db or auth-api) is slow or timing out | ceiling shape (p95 and p99 flat together, p50 unchanged), downstream span latency up | downstream span p95 at baseline refutes it | default | Ruled out |

- H1 status: supported · evidence: W1-Q2..Q4, W1-Q8..Q11, W2-Q2, W2-Q8..Q11 (all reused by the worker) · note: default tier. Verdict `Confirmed`, no escalation: W2-Q8 and W2-Q10 show the mechanism inside the incident window.
- H2 status: supported · evidence: W2-Q8..Q11, W3-Q1, W3-Q2, W1-Q15..Q17 · note: stronger tier from the start (three signals to correlate; expected conflict between 35.8 extra spans per request in the sample and +63.7 DB operations per request implied by the metrics). Not an escalation. Verdict `Confirmed`; the size mismatch is a gap.
- H3 status: refuted · evidence: W3-Q3, W1-Q17 · note: default tier. RDS CPU rose to 44% as a consequence of the extra queries and trails the app-side step by one 5-minute bucket; per-call DB latency flat.
- H4 status: refuted · evidence: W1-Q19 · note: default tier; `pending_requests` is 0 in 166 of 166 samples.
- from-history:2026-08-14-orders-api status: refuted · evidence: W1-Q19, W1-Q4 · note: overlaps H4; its worker received only the line written above.
- H5 status: open · evidence: W1-Q2, W1-Q18, PB-Q9, W3-Q4..Q6, W3-Q8 · note: default tier returned inconclusive (limits, HPA and throttling not readable); re-dispatched once on the stronger tier, still inconclusive; stays open with its gaps. Label `Assumed`.
- H6 status: refuted · evidence: PB-Q16 · note: default tier; reused the request-rate rows.
- H7 status: refuted · evidence: W1-Q17, W2-Q10, W2-Q11, W3-Q7 · note: default tier. The auth-api latency series is missing (W3-Q7 empty); the DB side is measured.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (local clone `~/src/orders-api`) | unknown (`gh` lookup printed `{}`, PB-Q13) | not resolved (git printed nothing, W2-Q12) | not known (clone freshness unverified; environment.md says tags v2.14.0 and v2.15.0 are fetched) | revision 23 = tag v2.14.0 (ReplicaSet orders-api-5f8d9c7b6a); revision 24 = tag v2.15.0 (ReplicaSet orders-api-7c9b6d8f5d); SHAs not resolved, tag names used as the refs |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 15:30 (simulated) | AWS STS, profile prod-read: `aws sts get-caller-identity --profile prod-read --output json` | n/a | free | account 111122223333; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b. Confirmed. |
| W0-Q2 | 15:30 | AWS IAM: `aws iam get-role --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b --query Role.Arn --output text` | n/a | free | role ARN resolved. |
| W0-Q3 | 15:30 | AWS IAM: `aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" --action-names <the fixed 10>` | n/a | free | 3 of the 10 fixed actions have no row; the 7 others implicitDeny; 3 foreign actions implicitDeny. Gap. |
| W0-Q4 | 15:30 | kubectl: `kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod` | n/a | free | SSO ReadOnly role; group eks-readonly. |
| W0-Q5 | 15:30 | kubectl: `kubectl config current-context` | n/a | free | equals the environment.md context. |
| W0-Q6 | 15:30 | kubectl: `kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders` | n/a | free | no write verbs. |
| W0-Q7 | 15:30 | shell: token presence, `GRAFANA_SERVICE_ACCOUNT_TOKEN` | n/a | free | set. |
| W0-Q8 | 15:30 | Grafana annotations: `GET https://grafana.example.com/api/annotations?type=alert&from=<2026-09-20 15:30 as ms>&to=<2026-10-20 15:30 as ms>&limit=100` | 30 days | free | `{}`. Gap (no alert history). |
| W0-Q9 | 15:31 | Loki: `GET /loki/api/v1/index/stats?query={app="orders"}` via datasource loki-prod, `app="orders"` (unverified) | 15:15 to 15:30 | estimate | `{}`; no estimate; treated as metered. |
| PB-Q1..Q17 | 15:30 | helper (cheapest tier) discovery reads, see the run log | | list calls | PB-Q15 (Loki, `{app="orders"}`, 8 lines): 48.2 MB processed. PB-Q16 (Prom, `rate(http_server_request_duration_seconds_count{service="orders-api"}[5m])`, 10:00 to 15:30 step 120 s): one series, route /orders method GET, 52 to 61 req/s, mean 56.5 before and 56.1 after 13:08. PB-Q17 (Tempo bare search for orders-api): no traces. PB-Q10 (deploy/svc/ingress/hpa): no output. PB-Q13 (`gh`): `{}`. PB-Q14: no service-discovery catalog. |
| W1-Q1 | 15:32 | kubectl: `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get events --sort-by=.lastTimestamp` | now | free | "No resources found": events older than the 1h TTL are gone. Gap. |
| W1-Q2 | 15:32 | kubectl: `... -n orders get rs --sort-by=.metadata.creationTimestamp -o custom-columns=NAME:.metadata.name,REVISION:.metadata.annotations.deployment\.kubernetes\.io/revision,CREATED:.metadata.creationTimestamp,DESIRED:.spec.replicas,READY:.status.readyReplicas` | now | free | the reply shows NAME, DESIRED, CURRENT, READY, AGE only: orders-api-5f8d9c7b6a 0/0/0 age 13d; orders-api-7c9b6d8f5d 3/3/3 age 145m. No creationTimestamp or revision column. |
| W1-Q3 | 15:32 | kubectl: `... -n orders rollout history deployment/orders-api` | n/a | free | revision 23 = helm upgrade (chart 4.2.0, image v2.14.0); revision 24 = helm upgrade (chart 4.2.0, image v2.15.0). Confirmed. |
| W1-Q4 | 15:32 | helm: `helm history orders-api --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders --max 10` | n/a | free | rev 23 Oct 7 09:40:12; rev 24 Oct 20 13:04:50 (deployed, chart 4.2.0 unchanged). No zone printed. |
| W1-Q5 | 15:32 | Prometheus prom-prod (verified): `histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))` | instant at 15:30 | cheap | GET /orders 0.712 s; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; /healthz 0.003. link: Grafana Explore, prom-prod. |
| W1-Q6 | 15:32 | same expression | instant at 12:30 (previous window end) | cheap | GET /orders 0.181; GET /orders/{id} 0.061; POST 0.139; PATCH 0.091; /healthz 0.003. |
| W1-Q7 | 15:32 | same expression `... [5m] offset 7d` | instant at 15:30 minus 7d | cheap | GET /orders 0.181; GET /orders/{id} 0.061; POST 0.139; PATCH 0.091; /healthz 0.003. |
| W1-Q8 | 15:32 | `histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders", method="GET"}[5m])))` | 09:30 to 15:30, step 120 s (data from 10:00) | cheap | 166 samples. Before 13:08 (94 samples, 10:00 to 13:06): 0.160 to 0.200 s. From 13:08 (72 samples): 0.661 to 0.755 s. Last clean 13:06 (0.163), first elevated 13:08 (0.716). Confirmed. |
| W1-Q9 | 15:32 | same with quantile 0.5 | same | cheap | 94 samples to 13:06: 0.080 to 0.100 s; 72 samples from 13:08: 0.281 to 0.339 s. p50 moved: not a ceiling. Confirmed. |
| W1-Q10 | 15:32 | same as Q8 with `offset 7d` | 2026-10-13 09:30 to 15:30 | cheap | 166 samples, 0.160 to 0.200 s throughout. |
| W1-Q11 | 15:32 | same as Q9 with `offset 7d` | 2026-10-13 09:30 to 15:30 | cheap | 166 samples, 0.080 to 0.100 s throughout. |
| W1-Q12 | 15:32 | quantile 0.90 of the same selector | 09:30 to 15:30 | cheap | no series (empty matrix). Gap: p90 not obtained. |
| W1-Q13 | 15:32 | quantile 0.99 of the same selector | 09:30 to 15:30 | cheap | no series (empty matrix). Gap: p99 not obtained, so a p95/p99 ceiling cannot be read; the p50 move already excludes a ceiling. |
| W1-Q14 | 15:32 | `rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[5m] offset 7d)` | 09:30 to 15:30 | cheap | returned the same 166 points, timestamps and values, as the unshifted PB-Q16: not credible as a -7d series. Treated as unusable. Gap. |
| W1-Q15 | 15:32 | `sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))` | 09:30 to 15:30, step 120 s | cheap | 380/s before 13:08 (361 to 401), 3952/s after (3821 to 4089): 10.4 times, stepping at 13:08 (13:06: 365.5, 13:08: 4031.1). Confirmed. |
| W1-Q16 | 15:32 | same with `offset 7d` | 2026-10-13 09:30 to 15:30 | cheap | 355 to 404/s throughout (mean 379). |
| W1-Q17 | 15:32 | Tempo tempo-prod, TraceQL metrics: `{ resource.service.name = "orders-api" && span.db.system =~ ".+" } \| quantile_over_time(duration, .95)` | 10:00 to 15:30, step 900 s | cheap | series `postgresql`: 3.9 to 4.4 ms at every step, before and after 13:08. DB per-call latency flat. Also verifies the service name `orders-api` in Tempo. |
| W1-Q18 | 15:32 | `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[5m]))` | 12:30 to 15:30, step 600 s | cheap | three pods, 0.52 to 0.64 cores each, mean 0.58 / 0.58 / 0.59; series start 13:08, so no pre-incident baseline. Gap. |
| W1-Q19 | 15:32 | `{__name__=~"db_client_connections_(usage\|pending_requests)", service="orders-api"}` | 09:30 to 15:30, step 120 s | cheap | `used`: 14 to 19 before, 17 to 24 after; `pending_requests`: 0 in all 166 samples. |
| W1-Q20 | 15:32 | `sum by (db_system) (increase(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))` | 2026-10-06 12:30 to 2026-10-20 12:30, step 3600 s | cheap | 3 hourly points only (10:00, 11:00, 12:00 today): 1.37M each. Coverage gap. |
| W1-Q21 | 15:32 | Grafana annotations (deploy markers): `GET /api/annotations?from=<12:30 as ms>&to=<15:30 as ms>&limit=100` | incident window | free | `{}`: no deploy markers. |
| W2-Q1 | 15:36 | git: `git -C ~/src/orders-api log --oneline v2.14.0..v2.15.0` | tags | free | 3 commits: a4c1e9b (2026-10-19, load items per order in list handler, #2211), 7be20d4 (2026-10-19, shipment ETA on order detail, #2208), 3f9d6a1 (2026-10-16, structlog 25.4.0, #2203). |
| W2-Q2 | 15:36 | git: `git -C ~/src/orders-api diff v2.14.0..v2.15.0` | tags | free | list_orders.py: `repo.list_orders_with_items(...)` replaced by `repo.list_orders(...)` plus `for order in orders: order.items = repo.list_items(order.id)`; order_detail.py: adds `shipment_eta`; pyproject.toml: structlog 25.3.0 to 25.4.0. |
| W2-Q3 | 15:36 | kubectl: `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod get cronjobs -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime` | now | free | no output (no CronJobs listed). |
| W2-Q4 | 15:36 | AWS EventBridge: `aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name,State,ScheduleExpression]' --output text` | now | free | `{}`; no rules listed. |
| W2-Q5 | 15:36 | AWS Scheduler: `aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName,Name,State]' --output text` | now | free | `{}`; no schedules listed. |
| W2-Q6 | 15:36 | AWS CloudTrail: `TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T11:05:00Z --end-time 2026-10-20T13:20:00Z --query "Events[].[EventTime,EventSource,EventName]" --output text` | 11:05 to 13:20 | free | `{}`; no write events returned. |
| W2-Q7 | 15:36 | AWS RDS: `aws rds describe-events --profile prod-read --region us-east-1 --source-type db-instance --source-identifier orders-db --start-time 2026-10-20T11:05:00Z --end-time 2026-10-20T13:20:00Z --query 'Events[].[Date,Message]' --output text` | 11:05 to 13:20 | free | `{}`; no events returned. |
| W2-Q8 | 15:36 | Tempo search (`/api/search`, limit 30): `{ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }` | 14:30 to 15:30 | cheap | 24 traces (new revision window). Descendant spans per trace (`matched`): min 9, p50 41, p95 52, max 52. Trace duration p50 342 ms, p95 422 ms. |
| W2-Q9 | 15:36 | same query | 11:00 to 12:00 | cheap | 24 traces (old revision window). Descendants per trace: min 2, p50 3, p95 4, max 4. Trace duration p50 110 ms, p95 165 ms. |
| W2-Q10 | 15:36 | Tempo: `GET /api/v2/traces/e3ea7a3906419b466a28541306cc5ee1?start=<-1h>&end=<+1h>` | trace from 14:30 to 15:30 (new window) | one trace | 152 ms: auth-api verify (3.4 ms), `SELECT orders` (3.05 ms), 12 x `SELECT order_items` (2.9 to 4.5 ms each), all serial children of the server span; status 200. |
| W2-Q11 | 15:36 | Tempo: `GET /api/v2/traces/65345f5f8176033524bc88af3bd43f6f?start=<-1h>&end=<+1h>` | trace from 11:00 to 12:00 (old window) | one trace | 109 ms: auth-api verify (3.8 ms), one `SELECT orders JOIN order_items` (3.05 ms); status 200. |
| W2-Q12 | 15:36 | git: `git -C ~/src/orders-api rev-parse --verify --end-of-options 'v2.15.0^{commit}'` | n/a | free | printed nothing; SHA not resolved. Gap. |
| W3-Q1 (was H2-Q1) | 15:41 | git: `git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py` | tag v2.15.0 | free | line 13 caps `limit` at 50; lines 15 to 18: `repo.list_orders(...)`, then `for order in orders: order.items = repo.list_items(order.id)`. |
| W3-Q2 (was H2-Q2) | 15:41 | git: `git -C ~/src/orders-api show v2.15.0:orders_api/repository.py` | tag v2.15.0 | free | `list_items` (lines 44 to 47) runs ITEMS_SQL (lines 22 to 26) and takes its own pool connection per call; `list_orders_with_items` (lines 38 to 42, SQL lines 11 to 20) is one LEFT JOIN round trip, "used by the list handler up to v2.14.0". |
| W3-Q3 (was H3-Q1) | 15:41 | AWS CloudWatch: `aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/raw/H3/q-rds-300.json --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z` (AWS/RDS, DBInstanceIdentifier=orders-db, Period 300, Average: CPUUtilization, ReadLatency, DatabaseConnections) | 10:00 to 15:30 | 3 metric requests (budget 500) | 67 points each, status Complete. CPU: mean 24.5% (21.2 to 26.9) before, mean 40.4% (37.1 to 44.0) from the 13:10 bucket; ReadLatency 0.59 ms before and after (0.52 to 0.67); connections 41.7 to 46.1. The 13:05 bucket is still at baseline. |
| W3-Q4 (was H5-Q1) | 15:41 | kubectl: `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get deploy orders-api -o json \| jq '[.spec.template.spec.containers[] \| {name, resources}]'` | now | free | no output. Gap: CPU limits not read. |
| W3-Q5 (was H5-Q2) | 15:41 | kubectl: `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders get hpa` | now | free | no output (no HPA listed). |
| W3-Q6 (was H5-Q3) | 15:41 | Prometheus: `sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="orders"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="orders"}[5m]))` | 12:30 to 15:30, step 600 s | cheap | empty matrix; those series are not in the metric-name list (PB-Q7), so they are not exported. Gap. |
| W3-Q7 (was H7-Q1) | 15:41 | Tempo TraceQL metrics: `{ resource.service.name = "orders-api" && span:kind = client && span.server.address = "auth-api.auth.svc.cluster.local" } \| quantile_over_time(duration, .95)` | 10:00 to 15:30, step 900 s | cheap | no series, although W2-Q10 and W2-Q11 show the client span. Gap: auth-api latency series missing. |
| W3-Q8 (was H5-Q4, escalated worker) | 15:44 | kubectl: `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders top pods` | now | free | no output. Gap: no live CPU or limit figures. |

Notes:

- Local summaries (percentiles, regression of trace duration on span count, hourly increases) were computed with `python3 -I -c` over the pulled files; no value or secret left the files.
- The p95/p50 range queries span 5.5 hours, inside the 12-hour `prom_quantile_range`, on a 3-pod service; they were treated as not heavy. No log query beyond PB-Q15 was needed.
- Raw pulls are named in the Result cells; the simulation did not save them.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| AWS write-check incomplete: no result row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (W0-Q3) | The report cannot call the AWS credentials read-only. | Ask the account owner to confirm the permission set is `ReadOnlyAccess`. |
| Alert state history unavailable: no alert name, no `ALERTS` series (PB-Q7), annotations `{}` (W0-Q8) | First firing time, threshold and detection delay unknown; recurrence cannot use alarm history; "why it became an incident" is partly Assumed. | Give the alert name and system, or open its state history in Grafana. |
| Recurrence not classifiable: 14-day signal returned 3 of 336 hourly points (W1-Q20); latency recurrence not pulled (no recording rule, subquery exceeds 12h cap) | Pattern is `unclassified`. | Provide a latency recording rule or longer Prometheus retention for orders-api, or the alert history. |
| p90 and p99 not obtained (W1-Q12, W1-Q13) | No ceiling read from p95/p99; the p50 move excludes it anyway. | Check the histogram exposes the needed buckets; query in Grafana Explore. |
| -7d request rate unusable (W1-Q14 identical to the unshifted series) | -7d volume comparison missing; the previous-window comparison (flat 56 req/s) carries the volume reading (H6). | Open the request-rate panel for the same clock window of 2026-10-13. |
| Per-pod latency not pulled; no pre-incident CPU baseline (W1-Q18 starts 13:08); CPU limits, throttling and `top` unreadable (W3-Q4, W3-Q6, W3-Q8) | H5 (pod capacity) stays `Assumed`; a single-pod outlier is not excluded in latency terms. | Per-pod p95 in Grafana Explore; the Deployment's CPU limit and a throttling metric. |
| Kubernetes events gone (W1-Q1: older than the 1h TTL) | Rollout events (probe failures, scheduling) not readable. | None needed unless the owner has event retention. |
| ReplicaSet creationTimestamp not available (W1-Q2 shows AGE only); Helm `UPDATED` has no zone (W1-Q4) | Rollout start known to about 3 minutes by cross-check, not from a UTC stamp. | Read `creationTimestamp` of ReplicaSet orders-api-7c9b6d8f5d, or the CD pipeline's deploy record. |
| No IaC repo in environment.md; Helm values not read by design | A values or config change shipped in the same rollout would not be visible. | Compare the chart values files in git at the two releases. |
| Schedule and platform listings returned `{}` or nothing (W2-Q3..Q7, W1-Q21) | "No schedule or CloudTrail write found" has unverified coverage: an empty reply is not proof of absence. | Ask the owners which schedulers the team uses. |
| Log label `app="orders"` not tied to the orders-api pods (PB-Q15: no pod label) | Log lines are a lead only; no claim rests on them. | Add a pod or trace ID field to the log lines. |
| Deployed commit SHAs and clone freshness not resolved (W2-Q12, PB-Q13) | Tag names used as refs. | Output of `git -C ~/src/orders-api rev-parse` for the tags and the default branch from `gh`. |
| HTTP histogram has no status label; no error rate (W1-Q5) | Error impact is Assumed (two traces returned 200). | Add a status label or use the ingress metrics. |
| Previous window starts 09:30, Prometheus data from 10:00 | 30 minutes of baseline uncovered. | None needed. |
| DB-operation size not reconciled: +3,572 ops/s at 56.1 req/s is +63.7 per request, above the largest per-request DB-span count seen (51) (W1-Q15, PB-Q16, W2-Q8) | The mechanism is shown directly by spans and code; the exact size of the extra work is not. | Ask the owner what `db_client_operation_duration_seconds_count` counts, and whether other routes also changed. |
| auth-api latency series missing (W3-Q7) | auth-api is cleared by indirect evidence only (trace duration fit, two traces). | Per-dependency latency panel for auth-api, or its owning team. |

## Untrusted text

none seen (log lines, trace names and attributes, git subjects and diffs, and Helm descriptions were read; none read as an instruction)

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no lessons.md under the output root; `ls .culiops/sre-investigate` showed only environment.md and incidents) |
| Re-verified this run | none |
| History lookup | After the ranked list existed: `grep -rn -E '^(service\|deps):.*(orders-api\|orders-db)' .culiops/sre-investigate/incidents` matched 2026-08-14-orders-api.md (fields: service, deps); `grep -rn -E '^symptoms:.*latency' .culiops/sre-investigate/incidents` matched the same file (field: symptoms). The directory listing of incidents/ (file names only) had been printed earlier, together with the output-root listing, before the ranked list existed. 2026-09-30-catalog-api.md did not match. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | tempo | A bare TraceQL search `{ resource.service.name = "orders-api" }` returned no traces, while TraceQL metrics and a structural search on the same name returned data; do not read an empty bare search as a wrong service name. | PB-Q17 |
| process | aws | The IAM simulation for prod-read returned rows for 7 of the 10 fixed actions plus 3 not on the list; a missing row is a gap, not a pass. | W0-Q3 |
| identifier | loki | Loki streams for orders-api are labelled `app="orders"`, `namespace="orders"`, `container="api"`; the stream has no pod label, so the tie to the orders-api pods is unverified. | PB-Q15 |
| process | prometheus | An `offset 7d` rate on the request counter returned the same series as the unshifted query; compare an offset result with the unshifted one before trusting it. | W1-Q14 |
| process | prometheus | 14-day hourly pulls for orders-api returned samples only from 10:00 UTC on the run day, and no latency recording rule exists; plan latency recurrence from alert history. | W1-Q20 |
| process | helm | `helm history` prints `UPDATED` without a zone; confirm the rollout time with the ReplicaSet creationTimestamp, which is UTC. | W1-Q4 |
| failure-mode | tempo | orders-api `GET /orders`: p50 and p95 step together with flat request rate, flat per-call DB latency (about 4 ms) and DB operations/s up about 10 times after a deploy: look for a per-row query loop and count descendant spans per request. | W2-Q8 |
| process | tempo | A structural TraceQL search reports `matched` as every descendant span, including non-DB client spans such as the auth-api verify call; subtract them before reading DB-span counts. | W2-Q8 |
| process | cloudwatch | RDS CPU in 5-minute buckets stepped one bucket (13:10) after the app-side step (13:08); DB-side metrics trail app-side steps, so do not use them to date an onset. | W3-Q3 |
| process | prometheus | No cfs throttling, container-limit or `kubectl top` data is available for namespace orders; capacity hypotheses there cannot be tested with metrics. | W3-Q6 |
| process | tempo | A TraceQL metrics query on the auth-api client spans returned no series although two traces show them; an empty metrics result is not "no calls". | W3-Q7 |
