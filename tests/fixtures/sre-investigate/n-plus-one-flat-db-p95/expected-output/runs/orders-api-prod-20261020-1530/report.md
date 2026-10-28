# Investigation: orders-api prod: GET /orders p95 about 4x slower since 13:08 UTC

Run: orders-api-prod-20261020-1530 · Mode: Deep · Window: 2026-10-20 12:30-15:30 UTC (22:30 on 10-20 to 01:30 on 10-21, Australia/Brisbane)
Access: prod-read: 7 of the 10 fixed write actions were evaluated and all came back implicitDeny (none allowed); 3 returned no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack), so this is a gap and not a proof; resource-scoped writes are not covered · arn:aws:eks:us-east-1:111122223333:cluster/prod: no write verbs in orders

## TL;DR

| Field | Value |
|---|---|
| Cause | The v2.15.0 release (Helm revision 24, 13:04:50 UTC) changed the `GET /orders` handler (commit a4c1e9b, PR #2211) to run one `order_items` query per returned order (up to 50) instead of one joined query. A request now makes a median of 41 descendant spans (about 40 DB statements) against 3. Each statement is as fast as before, and the endpoint is about 4x slower · label: Confirmed |
| Weakest link | There is no old-versus-new latency split by pod or revision (the histogram has no pod label and the rollout events have expired). The tie to the deploy therefore rests on timing at 2-minute resolution plus the code diff on the failing path. The per-request counts come from 24 sampled traces per window, backed by the service-wide statement rate (x10.4 against a flat call rate) · Confirmed |
| Impact | `GET /orders` (order history, a core flow) p95 0.71 s against 0.18 s and p50 0.31 s against 0.09 s, from 13:08 UTC (23:08 local). Still ongoing at 15:30 UTC (01:30 local). POST /orders, GET /orders/{id}, PATCH and /healthz are unchanged |
| Severity | SEV2 because a core flow is significantly degraded (about 4x) and nobody reported it as down. The incident owner decides |
| Pattern | unclassified · no alert history was found (alert unnamed), the 14-day latency pull is over the quantile cap, and the volume proxy returned 5.5 hours; the same clock window 7 days earlier was normal · Assumed |
| Recommended action | A human should decide between two options. One is to roll back to v2.14.0, at the cost of also withdrawing the shipment ETA on order detail and the structlog bump until they are re-released. The other is to ship a fix that restores the single joined query the repository still contains. Either should go through `pre-flight` and a separate session first |
| Time to cause | Not measured: the run clock was unavailable (`date -u` printed nothing). In order: the extra-work signal appeared in wave 1, the deploy became a suspect in wave 2, and Confirmed came with the Phase 4 verdicts |
| Similar past incidents | `2026-08-14-orders-api.md` (matched on service, dependency orders-db and symptom words). Its mechanism (connection pool exhaustion) was tested here as `from-history:` and Ruled out (W1-Q17). This is not a repeat of that cause; it is the second orders-api latency incident in about nine weeks |

## Impact

- **Symptom.** `GET /orders` p95 is 0.712 s against 0.180 s before and 0.181 s seven days earlier (x3.9). p50 is 0.311 s against 0.092 s (x3.4). From 13:08 to 15:30 UTC the p95 stays in 0.66-0.76 s, with no recovery. Only this endpoint moved: POST /orders 0.142 against 0.139, GET /orders/{id} 0.064 against 0.061, PATCH 0.088 against 0.091, /healthz 0.003 (W1-Q5..Q13) · Confirmed.
- **Scope.** Prod, orders-api, all three replicas (CPU is level across the pods, W1-Q18). Customer-facing: order history is a core flow named in environment.md.
- **Not measured.** The error rate and the number of users affected were not measured, so that part of the impact is Assumed. There is no SLO, so impact is sized from request metrics against the baseline.
- **Third party.** None in the path. The database is RDS `orders-db` in the same account.

## Recurrence

| Source | Window | Occurrences | When (UTC) | Normal vs incident |
|---|---|---|---|---|
| p95 alert on GET /orders (name not given) | 30d | not available: the `ALERTS` search for namespace orders returned an empty matrix (W0-Q13) | n/a | not applicable |
| sibling alarms | 30d | none: no CloudWatch alarm is involved | n/a | not applicable |
| request volume of GET /orders (proxy; the latency pull is over the 12 h quantile cap) | 14d at 1h | 0 hours above normal, but only 10:00-15:30 on 10-20 was returned (W1-Q19) | none | hourly requests median 203.0k, max 204.3k; onset hour (13:00) 203.6k. This is volume, not latency, and 5.5 h of 336 h |

Class `unclassified`, shape `step`. p50 and p95 both jump at 13:08 and stay. The call rate is flat. DB statements per second step x10.4 at the same sample. No rule can be tested without an alert history or a 14-day latency series. The same clock window on 10-13 was normal (W1-Q6, W1-Q8, W1-Q13, W1-Q16). This is a gap, not a finding of "first time".

## Timeline

| Time (local) | Time (UTC) | Event | Evidence |
|---|---|---|---|
| 10-07 19:40:12 | 2026-10-07 09:40:12 | Helm revision 23 deployed (app v2.14.0, chart orders-api-4.2.0). The printed time has no zone and is read as UTC (see Gaps) | W1-Q4 |
| n/a | 2026-10-19 (time not shown) | Commits for v2.15.0 merged: a4c1e9b "load items per order in list handler" (#2211), 7be20d4 "shipment ETA on order detail" (#2208). 3f9d6a1 "bump structlog" (#2203) is dated 10-16 | W2-Q8 |
| 23:04:50 | 13:04:50 | Helm revision 24 deployed: app v2.15.0, same chart as revision 23 | W1-Q4, W1-Q1 |
| about 23:05 | about 13:05 | ReplicaSet `orders-api-7c9b6d8f5d` created (age 145 min at 15:30), 3/3 ready, 0 restarts | W1-Q2, W0-Q20 |
| 23:06 | 13:06 | Last normal sample: p95 0.163 s, p50 0.082 s | W1-Q5, W1-Q7, W3-Q1 |
| 23:08 | 13:08 | First elevated sample: p95 0.716 s, p50 0.295 s. DB statements/s 4,031 (about 380 before). Endpoint call rate unchanged | W1-Q5, W1-Q7, W1-Q15, W1-Q14 |
| 23:08-01:30 (10-21) | 13:08-15:30 | p95 stays 0.66-0.76 s. Pool `pending_requests` 0. RDS CPU 37-44% | W1-Q5, W1-Q17, W1-Q21 |
| 00:30-01:27 (10-21) | 14:30:18-15:27:50 | Trace sample: GET /orders requests make 9-52 descendant spans (p50 41), against 2-4 (p50 3) in the 11:00-11:57 sample | W3-Q4, W3-Q5, W3-Q6, W3-Q7 |
| n/a | n/a | No CronJob, EventBridge rule, Scheduler schedule, RDS event or AWS write near 13:08 | W2-Q1..Q6 |

## Causal chain

1. Trigger: Helm upgrade of orders-api to v2.15.0 at 13:04:50 UTC. Commit a4c1e9b (#2211) changes `orders_api/handlers/list_orders.py` (lines 15-18 at v2.15.0) to call `repo.list_items(order.id)` once per returned order, with the page capped at 50. v2.14.0 used one joined query, `repo.list_orders_with_items`, which still exists in `repository.py` (lines 38-42) · Confirmed · W1-Q1, W1-Q2, W1-Q4, W2-Q8, W2-Q9, W3-Q2, W3-Q3
2. Mechanism: `GET /orders` now issues one list query plus one `order_items` query per order. Descendant spans per request are p50 41 and p95 52 (24 traces, 14:30-15:30), against p50 3 and p95 4 (24 traces, 11:00-12:00). Each statement takes 3-4.5 ms as before (DB span p95 4.19 ms before, 4.04 ms after). Service-wide DB statements per second are x10.4 from 13:08 while the endpoint's call rate is flat. In the fetched incident trace the added request time (+43 ms) equals the added DB statement time (+44.8 ms) · Confirmed · W3-Q4, W3-Q5, W3-Q6, W3-Q7, W1-Q15, W1-Q14, W1-Q20
3. Symptom: `GET /orders` p95 0.18 s to 0.71 s and p50 0.09 s to 0.31 s from the first sample at 13:08, 3 minutes after the upgrade. The last normal sample is 13:06 and no other endpoint moved. The database is not saturated (RDS CPU 41%, pool waiters 0) · Confirmed · W1-Q5, W1-Q7, W1-Q11, W1-Q12, W1-Q13, W1-Q17, W1-Q21

Timing leg: the first occurrence of the symptom is the 13:08 sample, against a Helm time of 13:04:50. The sample before it (13:06) is normal (W1-Q5, W3-Q1).

**Why it became an incident.**
- The handler's cost scales with page size (up to 50 extra statements per request). No pre-release check on statements per request for list endpoints is visible (Assumed: no CI or review record was read).
- The rollout replaced all three pods within about three minutes. No staged rollout or p95 gate is visible (Assumed: only the rollout history was read).
- The database absorbed ten times the statements (CPU 25% to 41%, pool waits 0). No saturation signal fired, only endpoint latency changed, and the only latency series that answered were p50 and p95 (p90 and p99 returned nothing).
- The alert's definition, threshold and first firing time are unknown (alert not named). Detection delay cannot be stated.

No competing explanation is still standing. The two remaining leads are under Open hypotheses.

## Evidence

- **Deploy.** `kubectl rollout history deployment/orders-api` shows revision 24 with image v2.15.0. `kubectl get rs -n orders` shows `orders-api-7c9b6d8f5d` 3/3 ready, age 145 min, and the old `orders-api-5f8d9c7b6a` at 0. `helm history orders-api` shows revision 24 on "Tue Oct 20 13:04:50 2026", chart orders-api-4.2.0 in both revisions. (W1-Q1, W1-Q2, W1-Q4.) link: read-only `helm history orders-api -n orders --max 10`
- **Change on the failing path.** `git -C ~/src/orders-api diff v2.14.0 v2.15.0` replaces `repo.list_orders_with_items(...)` with `repo.list_orders(...)` plus `for order in orders: order.items = repo.list_items(order.id)`. The same diff touches `order_detail.py` (GET /orders/{id}, which did not move) and the structlog pin (no data path). (W2-Q8, W2-Q9, W3-Q2, W3-Q3.) link: `git -C ~/src/orders-api diff v2.14.0 v2.15.0 -- orders_api/handlers/list_orders.py`
- **Onset.** p95: 12:50-13:06 all 0.163-0.190 s, 13:08 0.716 s, 13:08-15:30 median 0.712 s. p50: 0.082 s at 13:06, 0.295 s at 13:08, median 0.311 s after. Same clock window 7 days earlier: p95 median 0.181 s, p50 0.088 s. (W1-Q5..Q8, W3-Q1.) link: Grafana Explore, prom-prod, `histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}[5m])))`, 2026-10-20 09:30-15:30
- **Only this endpoint.** p95 per route at 15:30 / 12:30 / 7 days earlier: GET /orders 0.712 / 0.181 / 0.181; GET /orders/{id} 0.064 / 0.061 / 0.061; POST /orders 0.142 / 0.139 / 0.139; PATCH /orders/{id} 0.088 / 0.091 / 0.091; /healthz 0.003 throughout. (W1-Q11..Q13.)
- **Not more requests.** GET /orders runs at a median of 56.5 req/s before and 56.25 req/s after. Hourly requests are 202.2k-204.3k, onset hour 203.6k. (W1-Q14, W1-Q19.)
- **More work per request.** DB statements per second: median 381 before, 4,031 at 13:08, median 3,962 after (x10.4); 7 days earlier median 379. (W1-Q15, W1-Q16.)
- **Statements are not slower.** DB span p95 is 4.19 ms before (3.9-4.36) and 4.04 ms after (3.9-4.22). RDS ReadLatency is 0.6 ms before and after. (W1-Q20, W1-Q21.) A flat database p95 did not clear the database; the statement count is what moved.
- **Per-request span counts.** Incident sample: 24 traces, descendant spans p50 41, p95 52, max 52, min 9, request duration median 340.5 ms. Baseline sample: 24 traces, p50 3, p95 4, max 4, request duration median 110 ms. The count includes the one `auth-api` client span each trace carries. (W3-Q4, W3-Q5.) link: Grafana Explore, tempo-prod, `{ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }`, 14:30-15:30 and 11:00-12:00
- **One fetched trace per window.** Trace `e3ea7a39…` (14:30:18): root 152 ms, one `SELECT orders` 3.05 ms, 12 `SELECT order_items` (median 3.74 ms, max 4.52 ms, total 44.8 ms), one `GET auth-api /verify` 3.4 ms. Trace `65345f5f…` (11:00:09): root 109 ms, one `SELECT orders JOIN order_items` 3.05 ms, `auth-api` 3.77 ms. The time outside any child span is the same (100.8 ms and 102.2 ms). Across the 24 incident traces, duration rises about 6 ms per extra span (r = 0.97). (W3-Q6, W3-Q7, local arithmetic over W3-Q4.)
- **Database not saturated.** RDS CPU median 24.9% before and 40.8% after (max 44.0%), connections 42 to 47 (max 48). Pool `pending_requests` is 0 at all 166 points; `used` is 14-19 before and 17-24 after. (W1-Q17, W1-Q21.)
- **No schedule or AWS write near the onset.** No CronJob, EventBridge rule, Scheduler schedule, RDS event or CloudTrail write (the replies were empty objects). (W2-Q1..Q6.) CloudTrail does not log the Kubernetes API, so the Helm upgrade itself is not covered by it.
- **Logs (lead only, not evidence).** Eight `GET /orders` log lines at 15:18-15:19 show duration_ms 286-751 and status 200. The stream (`app="orders"`) could not be tied to the service. (W3-Q9.)

## Ruled out

| Hypothesis | Why | Query |
|---|---|---|
| H3: orders-db became slower per statement (CPU, locks, I/O) | Per-statement p95 4.19 ms before and 4.04 ms after; ReadLatency 0.6 ms before and after. CPU rose only as statements per second rose x10.4, and 41% is far from saturation, so it is a consequence. Lock, queue and write-latency metrics returned no data and Performance Insights is off, so the lock arm is excluded only through the flat statement latency | W1-Q20, W1-Q21, W1-Q15, W3-Q8 |
| H4: connection exhaustion or pool cap | `pending_requests` 0 at every point; `used` 14-24 with no plateau. The pool maximum and the DB connection limit are unknown | W1-Q17, W1-Q21, W3-Q9 |
| from-history 2026-08-14-orders-api.md: pool exhausted with elevated `pending_requests` | `pending_requests` is 0 across the whole incident window, and only one DB-backed route moved | W1-Q17, W1-Q11..Q13 |
| H5: pod capacity (CPU limit, throttling, HPA at max, fewer replicas) | Ready 3/3 = desired, 0 restarts, CPU level across the pods, and every other route on the same pods is unchanged. CPU limits, HPA and throttling could not be read, so the basis is the unchanged sibling routes | W1-Q2, W0-Q20, W1-Q11..Q13, W1-Q18, W3-Q10, W3-Q11 |
| H6: traffic spike or heavy clients | Call rate 56.5 req/s before and 56.25 after, hourly volume level. No usable -7d call rate (the offset query returned the unshifted series) | W1-Q14, W1-Q19, W3-Q12 |

## Open hypotheses

| Hypothesis | Label | What would settle it |
|---|---|---|
| The downstream `GET auth-api /verify` call (seen in every fetched trace) contributed | Assumed | It took 3.4 ms in the incident trace and 3.77 ms in the baseline trace, so it looks flat. It was not on the checkpoint list and no worker tested it. A TraceQL p95 and call rate for that client span, incident against baseline, would settle it |
| A configuration change inside the same Helm upgrade (values, not the image) added to the slowdown | Assumed | A diff of the chart values for revisions 23 and 24. It is unreadable here by design and no values repo is configured. The code change already accounts for the whole step, so this is low priority |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| The p95 alert is unnamed and its state history returned nothing (W0-Q13) | The recurrence class is `unclassified`. The alert's threshold and first firing time are unknown, so detection delay cannot be stated | The name of the alert rule, or an export of its state history |
| 14-day latency pull not run (over the 12 h quantile cap, no recording rule); the volume proxy returned 5.5 h only (W1-Q19) | Whether this symptom happened before cannot be settled from metrics | A p95 recording rule for GET /orders |
| `p90` and `p99` returned empty matrices while p50 and p95 returned data (W1-Q9, W1-Q10) | The ceiling-versus-slower-calls check rests on p50 against p95 only | Ask the metrics owner why those quantile queries return nothing |
| The latency histogram has no `pod` or version label, traces carry no `service.version` or pod, and Kubernetes events from 13:05 have expired (W3-Q1, W3-Q6, W1-Q3) | There is no direct "new pods slow, old pods fine" split. The deploy tie rests on timing at 2-minute resolution plus the diff | Add a version or pod label to the histogram, or `service.version` to spans |
| No IaC or chart-values repo in environment.md; Helm values are unreadable by design; chart orders-api-4.2.0 is identical in both revisions (W1-Q4) | A config-only change in the same upgrade cannot be excluded; "only the image changed" is Assumed | Add the chart or values repo to environment.md, or diff the values files at the two refs |
| Local clone freshness unknown (no fetch allowed) (W2-Q7) | The diff is exact for the two tags. That the running image is the tag's code is Assumed | `gh` read access to confirm the tag's commit |
| Helm prints times without a zone (W1-Q4) | The 13:04:50 deploy time is read as UTC because the ReplicaSet age (145 min before 15:30) agrees. It is not taken from the printed text | Read the ReplicaSet `creationTimestamp` |
| RDS lock-wait, deadlock, disk-queue, write-latency and memory metrics returned no data; Performance Insights is off (W3-Q8) | H3's lock arm is excluded only through flat statement latency | Enable Performance Insights on orders-db |
| CPU limits, HPA and throttling not readable; pod CPU has no point before 13:08 (W3-Q10, W3-Q11, W1-Q18) | H5 is ruled out by unchanged sibling routes, not by a headroom figure | Read the Deployment resources and any HPA |
| Pool maximum and DB connection limit unknown (W1-Q17) | H4 and the history lead are ruled out on zero waiters, with no numeric headroom | Read the pool setting from the chart values at the deployed ref |
| Loki stream `app="orders"` not tied to orders-api; Loki stats returned an empty object (W3-Q9, W0-Q24) | No log-derived claim is used as evidence; the log label stays unverified | Confirm the label, or add a pod or trace ID to the log lines |
| Only two traces fetched by ID; the incident one has 14 descendants against a median of 41 (W3-Q6) | Full time accounting is shown for a short request; for long ones the evidence is the regression over 24 sampled durations | Open a 50-order request trace in Tempo |
| Write-check: 3 of the 10 fixed actions returned no row (W0-Q8) | "No broad write found" holds for 7 of 10 actions only | Re-run the simulation for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack |
| Run clock unavailable (`date -u` printed nothing) | No wall-clock times for the waves and no time-to-cause in minutes | None (environment property) |

Open items need your input.

## To confirm, a human would…

1. Compare the Helm values of revisions 23 and 24, or the values files at the two refs, to rule out a configuration change in the same upgrade. An identical set of values confirms that only the image changed.
2. Replay a `GET /orders` for a customer with 50 orders against a non-production copy of v2.14.0 and of v2.15.0, with tracing on. A statement count of about 3 against about 52 would confirm the mechanism, and equal counts would refute it. This needs an active request, which this run does not make.
3. Open a long incident trace (about 50 descendant spans) in Tempo and check that the time outside spans is about 100 ms plus roughly 2 ms per extra statement, as the 24-trace regression implies.
4. Pull the p95 and call rate of the `GET auth-api /verify` client span for the incident and baseline windows, to close the open auth-api lead.
5. Read the Deployment's resource limits and any HPA, and the pool's maximum size, to put numbers on the capacity and pool headroom that were excluded only indirectly.
6. Enable or open Performance Insights for orders-db and check that waits per statement stayed flat while the load rose tenfold.
7. Ask the alert owner for the alert's name, threshold and first firing time, to judge detection delay and whether this is a first occurrence.

## Follow-ups

Fixes and mitigations are prose for a human. Each is a candidate to be checked with `pre-flight` before it is applied, and an infrastructure or release change goes to `iac-change-execution` in a new session with this report's path as context. This run changed nothing.

| Kind | Item |
|---|---|
| Fix | Restore a single round trip for loading orders with their items in the list handler. The joined query the repository still contains does this, or one statement keyed on the page's order ids. The cost is a larger single result and a small change in how items are grouped. As a quicker mitigation, consider rolling back to v2.14.0, at the cost of also withdrawing the shipment ETA on order detail (7be20d4) and the structlog bump (3f9d6a1) until they are re-released. Because the pool and the database have headroom, nothing else needs to change to recover |
| Prevention | Add a test or CI check that pins the number of database statements the list endpoint makes for a page of 50 orders. Add a staged or canary rollout with a p95 gate on `GET /orders`, at the cost of a slower rollout. Review other list endpoints for per-row queries. Consider an alert on statements per request (DB statements per second divided by requests per second), which would have fired at 13:08 with a clear cause |
| Prevention | The orders-api latency incident of 2026-08-14 had a different cause (the connection pool). Two latency incidents in about nine weeks suggest a latency alert whose threshold and runbook are written down, because the alert is not named in the evidence available here |
| Observability gap | Add a pod or version label to the latency histogram (at the cost of more series), or `service.version` to spans, so an old-versus-new split is possible. Fix the p90 and p99 queries or add recording rules for p50, p90, p95 and p99 so recurrence can be classified from 14 days of latency. Enable Performance Insights on orders-db. Make the Loki label tie-able to the service (a pod or trace ID in the lines, or a label named after the service). Add the chart and values repo to environment.md |

## Cost

35 queries · 0.05 GB of logs scanned (Loki 0.048 GB) · 7 CloudWatch metric requests · Tempo inspected about 11.4 GB in trace searches and metrics (not billed as logs) · about $0.00 in metered charges (7 GetMetricData metrics; no metered charge known for the Grafana-proxied backends)
