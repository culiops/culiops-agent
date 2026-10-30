# Investigation: orders-api prod: GET /orders p95 up from 0.18 s to 0.71 s since 13:08 UTC

Run: orders-api-prod-20261020-1530 · Mode: Deep · Window: 12:30 to 15:30 UTC (22:30 on 2026-10-20 to 01:30 on 2026-10-21, Australia/Brisbane, UTC+10) · Onset: 13:08 UTC (23:08 Australia/Brisbane)
Access: prod-read: write check incomplete: 7 of the 10 broad write actions returned implicitDeny and none was allowed, but there is no result row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack, so write capability is unknown (gap) for those three and the credentials are not claimed read-only; arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace orders): no write verbs in orders

## TL;DR

| Field | Value |
|---|---|
| Cause | Release v2.15.0 (Helm revision 24, rolled out about 13:05 UTC) rewrote the `GET /orders` list handler (commit a4c1e9b, #2211) from one joined query to one items query per order. Each request now makes up to 51 serial database queries instead of one, which adds about 5.8 ms per extra query · label: Confirmed |
| Weakest link | The old and new revisions never ran side by side (all 3 pods were replaced within about a minute), and the rollout start comes from Helm's zone-less time plus pod age, cross-checked to about 3 minutes against the UTC step at 13:08 rather than from a UTC-stamped record · still Confirmed at that resolution. The exact size of the extra database work is also not reconciled with the metrics (see Gaps); that does not touch the cause. |
| Impact | `GET /orders` (order history, a core flow) p95 0.181 s to 0.712 s (3.9 times) and p50 about 0.09 s to about 0.31 s, with request rate unchanged at about 56/s. Other routes are flat and no errors were measured. Since 13:08 UTC, still ongoing at 15:30 UTC (2 h 22 min). |
| Severity | SEV2 (suggested) because a core flow is significantly degraded (about 4 times slower at p95) with no failures measured. The incident owner decides. |
| Pattern | unclassified · no alert history, and the 14-day pull returned 3 of 336 hourly points; the shape is a step · Assumed |
| Recommended action | A human should choose between two options. One is to roll orders-api back to v2.14.0 as a stop-gap; this also withdraws the shipment ETA on order detail (#2208) that shipped in the same release. The other is to ship a fix that loads the items of a page of orders in one round trip again, either by joining as v2.14.0 did or with one batched query. The batched form returns a larger result per request, so test it with a customer who has 50 orders. Check either option with `pre-flight` before applying it. |
| Time to cause | Not measured (no wall clock in this run). The first Likely came after wave 1, when the step lined up with the rollout and a 10.4 times jump in database operations; Confirmed at the Phase 4 merge. |
| Similar past incidents | 2026-08-14-orders-api (matched on service, dependency orders-db and the latency symptom). It was tested here as a lead (`from-history:2026-08-14-orders-api`) and Ruled out, so this is a second latency incident on orders-api in about ten weeks but not a repeat of the same cause. |

## Impact

`GET /orders` is the order-history core flow named in environment.md. Its p95 went from 0.181 s (12:30 UTC) to 0.712 s (15:30 UTC) and its p50 from about 0.09 s to about 0.31 s. The last clean 2-minute sample is 13:06 (p95 0.163 s) and the first elevated one is 13:08 (0.716 s). On the same clock window of 2026-10-13 the p95 stayed between 0.160 and 0.200 s (W1-Q5..Q11). The request rate did not move, at 56.5 req/s before and 56.1 req/s after (PB-Q16). Every caller of the endpoint on all 3 replicas is affected. `POST /orders` (0.139 to 0.142 s), `GET /orders/{id}` (0.061 to 0.064 s), `PATCH /orders/{id}` (0.091 to 0.088 s) and `/healthz` are flat (W1-Q5..Q7).

The impact was sized from request metrics against the baseline because no SLO is named in environment.md. The latency change is Confirmed. Error impact is Assumed: the HTTP histogram has no status label, and two sampled traces returned 200 (W2-Q10, W2-Q11). No third party is in the path. orders-db is the company's own RDS and auth-api is internal.

## Recurrence

| Source | Window | Occurrences | When (UTC) | Normal vs incident |
|---|---|---|---|---|
| p95 alert (name and system not given) | 30d | not available | no alert history: annotations returned nothing (W0-Q8) and there is no `ALERTS` series (PB-Q7) | not applicable |
| sibling alarms | 30d | none known | not applicable | not applicable |
| `GET /orders` p95, same clock window | -7d (2026-10-13) | 0 hours above normal | none | 0.160 to 0.200 s (W1-Q10) vs 0.661 to 0.755 s from 13:08 (W1-Q8) |
| database operations per hour (stand-in for the latency signal, which has no recording rule and cannot be pulled over 14 days within the 12 h cap) | 14d at 1h | 3 of 336 hourly points returned (10:00 to 12:30 today) | none before the incident | median / p95 / max 1.37M / 1.37M / 1.37M per hour vs 14.2M per hour in the 14:00 hour (W1-Q20) |

Class: unclassified. Without alarm history and with 2.5 hours of 14-day signal, none of the rules for `scheduled`, `chronic`, `recurring` or `sudden` can be applied. The step has lasted 2 h 22 min without repeating and no schedule was listed, but that is not a classification. This is a gap, not a finding. Shape: step. p95, p50 and database operations all jump at 13:08. The request rate is flat, so it is not volume, and p50 moved, so it is not a ceiling.

## Timeline

| Time (UTC) | Time (local) | Event | Evidence |
|---|---|---|---|
| 2026-10-16 (date only) | not applicable | commit 3f9d6a1 bumps structlog to 25.4.0 (#2203) | W2-Q1; git log in the local clone |
| 2026-10-19 (date only) | not applicable | commits 7be20d4 (shipment ETA on order detail, #2208) and a4c1e9b (load items per order in the list handler, #2211) | W2-Q1, W2-Q2; git diff v2.14.0..v2.15.0 in the clone |
| 2026-10-07 09:40:12 (zone not printed by Helm) | not applicable | Helm revision 23: chart orders-api-4.2.0, app v2.14.0 | W1-Q4; helm history |
| 13:04:50 (zone not printed by Helm; read as UTC after the cross-check) | 23:04:50 | Helm revision 24: chart 4.2.0 unchanged, app v2.15.0, "Upgrade complete" | W1-Q3, W1-Q4 |
| about 13:05 (derived) | about 23:05 | ReplicaSet orders-api-7c9b6d8f5d created; its 3 pods are 144 to 145 minutes old at about 15:30; the old ReplicaSet is at 0 replicas; 0 restarts | W1-Q2, PB-Q9 |
| 13:06 | 23:06 | last clean samples: p95 0.163 s, p50 0.082 s, database operations 365.5/s | W1-Q8, W1-Q9, W1-Q15; Grafana Explore (prom-prod) |
| 13:08 | 23:08 | first elevated samples: p95 0.716 s, p50 0.295 s, database operations 4031.1/s (10.4 times); request rate unchanged | W1-Q8, W1-Q9, W1-Q15, PB-Q16 |
| 13:10 | 23:10 | RDS CPU 41.3% in the 13:10 five-minute bucket (the 13:05 bucket was 23.9%); read latency flat at about 0.5 ms | W3-Q3; CloudWatch console, AWS/RDS orders-db |
| 15:30 | 01:30 (21 Oct) | still elevated: p95 0.712 s | W1-Q5 |

Rollout dating cross-check: Helm prints `UPDATED` without a zone. Independently, the new pods are 145 minutes old at about 15:30 (W1-Q2), which puts their creation near 13:05, and the UTC-stamped step in Prometheus is at 13:08. These agree to about three minutes. The kubectl output showed only `AGE`, so there is no UTC-stamped creation time.

## Causal chain

1. Trigger: release v2.15.0 replaced all 3 pods at about 13:05 UTC (Helm revision 24, ReplicaSet orders-api-7c9b6d8f5d). It contains commit a4c1e9b, which changes `list_orders` from `repo.list_orders_with_items` (one LEFT JOIN round trip) to `repo.list_orders` followed by `repo.list_items(order.id)` for every order, capped at 50 orders. The other two commits are not on the failing path · Confirmed · W1-Q2, W1-Q3, W1-Q4, W2-Q1, W2-Q2, W3-Q1, W3-Q2
2. Mechanism: each `GET /orders` request now issues 1 orders query plus up to 50 serial item queries.
   - Descendant spans per request: p50 41, p95 52, max 52 (24 traces, 14:30 to 15:30) against p50 3, p95 4, max 4 (24 traces, 11:00 to 12:00).
   - Database operations rose from 380/s to 3,952/s (10.4 times) at 13:08 while the request rate stayed at about 56/s.
   - Each query is as fast as before, p95 3.9 to 4.4 ms. The pool never waited (`pending_requests` 0 in 166 of 166 samples), and RDS had headroom (CPU 24% to 40%, maximum 44%, read latency flat).
   - Confirmed · W2-Q8, W2-Q9, W2-Q10, W2-Q11, W1-Q15, W1-Q17, W1-Q19, W3-Q3
3. Symptom: trace duration follows the span count (about 101 ms + 5.8 ms per span, r = 0.98, 48 traces), which accounts for the p50 move from about 110 ms to about 342 ms. At the metric level p50 and p95 rise together at 13:08 and stay up · Confirmed · W2-Q8, W2-Q9, W1-Q8, W1-Q9

Why it became an incident (Deep mode):
- **Protection missing:** the release reached all 3 pods within about a minute (ages 145, 144 and 144 minutes), so no gradual rollout step is visible · Likely (inferred from pod ages; the rollout strategy was not read). Nothing in the data shows a check on database calls per request before or during the rollout · Assumed.
- **Detection:** the alert's first firing time is unknown because no alert history could be read · Assumed.
- **Capacity:** none was short. The database absorbed ten times the operations and paid in latency, not in errors or pool waits · Confirmed (W3-Q3, W1-Q19).

Standing explanations: H1 (the deploy) and H2 (the per-order query loop) are one chain, trigger and mechanism. Pod CPU capacity (H5) remains open but is not needed to explain any step.

## Evidence

1. **Step at 13:08 in latency.** `GET /orders` p95: 94 samples from 10:00 to 13:06 lie between 0.160 and 0.200 s, and 72 samples from 13:08 to 15:30 lie between 0.661 and 0.755 s. p50: 0.080 to 0.100 s, then 0.281 to 0.339 s. Last clean 13:06, first elevated 13:08. Seven days earlier all 166 samples stayed within 0.160 to 0.200 s (p95) and 0.080 to 0.100 s (p50). [W1-Q8, W1-Q9, W1-Q10, W1-Q11; Grafana Explore, prom-prod, queries as in the ledger]
2. **Only this endpoint, request rate unchanged.** Per-route p95 at 15:30 against 12:30 and -7d: `/orders/{id}` 0.064 vs 0.061, `POST /orders` 0.142 vs 0.139, `PATCH /orders/{id}` 0.088 vs 0.091, `/healthz` 0.003. `GET /orders` call rate 56.5 req/s before and 56.1 after. [W1-Q5, W1-Q6, W1-Q7, PB-Q16; Grafana Explore, prom-prod]
3. **The rollout.** Rollout history shows revision 24 with image v2.15.0 (revision 23 was v2.14.0), and Helm dates revision 24 at 13:04:50 with the chart unchanged. The new ReplicaSet has 3 ready pods that are 144 to 145 minutes old with 0 restarts, and the old ReplicaSet has 0 replicas. [W1-Q2, W1-Q3, W1-Q4, PB-Q9; kubectl and helm history in the cluster]
4. **What the release changed.** Three commits: a4c1e9b (list handler), 7be20d4 (order detail adds `shipment_eta`) and 3f9d6a1 (structlog bump). The list handler at v2.15.0 has a loop at lines 15 to 18 that calls `repo.list_items(order.id)` per order, with `limit` capped at 50 on line 13. `list_items` runs one query per call on its own pool connection (repository.py lines 44 to 47). `list_orders_with_items`, one LEFT JOIN round trip, was used "up to v2.14.0". [W2-Q1, W2-Q2, W3-Q1, W3-Q2; git in the clone]
5. **Old against new, per revision.**
   - New revision (v2.15.0, 13:08 to 15:30): 72 of 72 p95 samples at 0.661 s or more, and 24 of 24 sampled traces with 9 to 52 descendant spans (p50 41).
   - Old revision (v2.14.0, last window before replacement): 0 of 94 p95 samples above 0.200 s, and 24 of 24 traces with 2 to 4 descendants (p50 3).
   - Earlier occurrences while only the old revision ran: none in the covered data (0 of 166 samples above 0.200 s on 2026-10-13).
   - One trace each: the new one (e3ea7a39..., 152 ms) shows auth-api verify, `SELECT orders` and 12 serial `SELECT order_items`. The old one (65345f5f..., 109 ms) shows auth-api verify and one `SELECT orders JOIN order_items`.
   - [W1-Q8, W1-Q10, W2-Q8, W2-Q9, W2-Q10, W2-Q11; Tempo search and trace view]
6. **Mechanism in metrics at the same minute.** Database operations were 365.5/s at 13:06 and 4031.1/s at 13:08 (10.4 times overall). The same hours on 2026-10-13 ran at 355 to 404/s. The per-query span p95 stays at 3.9 to 4.4 ms at all 23 steps, so each call is as fast as before and there are many more of them. [W1-Q15, W1-Q16, W1-Q17; Grafana Explore prom-prod and Tempo metrics query]
7. **Latency follows the span count.** Across the 48 sampled traces, duration is about 100.8 ms + 5.8 ms per descendant span (r = 0.979), with the same fixed part before and after. [W2-Q8, W2-Q9; local fit over the pulled results]
8. **The database is not slow.** RDS CPU averaged 24.5% in the 37 buckets to 13:00, was 23.9% in the 13:05 bucket, and averaged 40.4% (37.1 to 44.0%) from the 13:10 bucket. Read latency was 0.59 ms before and after. Connections moved from 41.7 to 46.1. The CPU rise starts one bucket after the application-side step, so it follows the application. [W3-Q3; CloudWatch console, AWS/RDS orders-db]
9. **Pool not exhausted.** `pending_requests` is 0 in all 166 samples; `used` goes from 14 to 19 before to 17 to 24 after. [W1-Q19; Grafana Explore prom-prod]
10. **No other candidate change.** The order-detail change and the structlog bump sit on routes that stayed flat. No schedules, CloudTrail writes, RDS events, deploy markers or HPA were returned (those replies were `{}` or empty, which does not prove absence), and Kubernetes events had expired. [W2-Q3..Q7, W1-Q21, W1-Q1]

## Ruled out

| Hypothesis | Why | Query |
|---|---|---|
| H3: orders-db itself is slow (CPU, locks, credits) | Read latency is flat at 0.59 ms and per-query span p95 stays at about 4 ms. CPU rises to a maximum of 44% only as a consequence of ten times more queries, one bucket after the application-side step. Lock waits were not measured. | W3-Q3, W1-Q17 |
| H4: connection exhaustion at the pool cap | `pending_requests` is 0 in 166 of 166 samples. The pool maximum is unknown and the gauge is sampled every 2 minutes. | W1-Q19 |
| from-history:2026-08-14-orders-api: a pool-size or configuration change leaves the orders-db pool exhausted | The pool shows no waiting, and the chart version is orders-api-4.2.0 in both revisions. Helm values were not read, so a pool-size change is inferred from the absence of waiting. | W1-Q19, W1-Q4 |
| H6: traffic spike or bot | The request rate has no step at the onset (56.5 to 56.1 req/s). The -7d series was unusable, so the previous window carries the reading. | PB-Q16, W1-Q14 |
| H7: a downstream (orders-db or auth-api) is slow or timing out | No ceiling shape, because p50 moved as much as p95. Per-query database spans are flat at 3.9 to 4.4 ms. auth-api's verify span is 3.4 ms against 3.8 ms in one trace each, and the duration fit leaves the same fixed part (about 101 ms) in both windows. auth-api has no latency series (W3-Q7 returned none). | W1-Q17, W2-Q10, W2-Q11, W3-Q7 |
| The other two commits in v2.15.0 (#2208 order detail, #2203 structlog) as causes | Not on the failing path: the routes they touch are flat. | W1-Q5, W1-Q6, W1-Q7 |

## Open hypotheses

| Hypothesis | Label | What would settle it |
|---|---|---|
| H5: the 3 replicas are CPU-bound or throttled, with no autoscaler seen | Assumed | The Deployment's CPU limit, the container throttling counters and a CPU baseline before 13:08. None is readable here: the deploy spec, HPA listing, throttling series and `kubectl top` all returned nothing (W3-Q4..Q6, W3-Q8), and the CPU series starts at 13:08 (W1-Q18). Replicas are steady at 3 ready with 0 restarts and CPU is 0.52 to 0.64 cores per pod with no ramp, which favours the code cause over a capacity cause, but that is a reading, not a query result. |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| AWS write-check incomplete: no result row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (W0-Q3) | The report cannot call the AWS credentials read-only. | Ask the account owner to confirm the permission set is `ReadOnlyAccess`. |
| No alert history: alert name and system not given, no `ALERTS` series, annotations returned nothing (W0-Q8, PB-Q7) | First firing time, threshold and detection delay unknown; recurrence cannot use alarm history; the "why it became an incident" detection point is Assumed. | Give the alert name and system, or open its state history in Grafana. |
| Recurrence not classifiable: 3 of 336 hourly points (W1-Q20); no latency recording rule and the 14-day subquery exceeds the 12 h cap | Pattern is `unclassified`. | Provide a latency recording rule or longer Prometheus retention for orders-api, or the alert history. |
| p90 and p99 not obtained (W1-Q12, W1-Q13) | A p95/p99 ceiling cannot be read directly; the p50 move excludes it anyway. | Check the histogram buckets and query p90 and p99 in Grafana Explore. |
| -7d request rate unusable: the offset query returned the unshifted series (W1-Q14) | The -7d volume comparison is missing; the flat previous-window rate carries H6. | Open the request-rate panel for 2026-10-13 12:30 to 15:30. |
| Per-pod latency not pulled; no CPU baseline before 13:08; CPU limit, throttling and `top` unreadable (W1-Q18, W3-Q4, W3-Q6, W3-Q8) | H5 stays Assumed; a single-pod latency outlier is not excluded (CPU is the same across pods). | Per-pod p95 in Grafana Explore; the Deployment's CPU limit and a throttling metric. |
| Kubernetes events expired (W1-Q1) | Rollout events (probes, scheduling) are not readable. | None needed unless the owner keeps event history. |
| ReplicaSet creation time not available (only `AGE`, W1-Q2); Helm `UPDATED` has no zone (W1-Q4) | Rollout start is known to about 3 minutes by cross-check, not from a UTC stamp. | Read `creationTimestamp` of ReplicaSet orders-api-7c9b6d8f5d or the CD pipeline's deploy record. |
| No IaC repo in environment.md; Helm values are not read by design | A configuration change shipped in the same rollout would not be visible. | Compare the chart's values files in git at the two releases. |
| Schedule and platform listings returned `{}` or nothing (W2-Q3..Q7, W1-Q21) | "No schedule, CloudTrail write, RDS event or deploy marker found" has unverified coverage. | Ask the owners which schedulers and deploy-marker sources the team uses. |
| Loki label `app="orders"` not tied to the orders-api pods (PB-Q15 has no pod label) | Log lines are a lead only; no claim rests on them. | Add a pod name or trace ID field to the log lines. |
| Deployed commit SHAs, default branch and clone freshness not resolved (W2-Q12, PB-Q13) | Tag names v2.14.0 and v2.15.0 were used as the refs. | Resolve the tags to SHAs in the clone and read the default branch with `gh`. |
| The HTTP histogram has no status label (W1-Q5) | No error rate; error impact is Assumed (two traces returned 200). | Add a status label, or use ingress metrics. |
| Previous window starts at 09:30 but Prometheus has data from 10:00 | 30 minutes of baseline uncovered; the covered part is stable. | None needed. |
| Size of the extra database work not reconciled: +3,572 operations/s at 56.1 req/s is about +64 per request, above the 51 database spans per request that the code and the traces allow (W1-Q15, PB-Q16, W2-Q8). The sampled mean (+35.8 per request) explains about 56% of the increase. | The mechanism is shown directly by spans and code; the exact size is not. | Ask the owning team what `db_client_operation_duration_seconds_count` counts and whether other routes changed. |
| auth-api latency series missing (W3-Q7 returned no series) | auth-api is cleared by indirect evidence only (two traces and the duration fit). | Open auth-api's own latency panel or ask its owning team. |

Open items need your input.

## To confirm, a human would…

1. Date the rollout in UTC from the ReplicaSet's creation time or the CD pipeline's deploy record. A start well after 13:08 would contradict the cause; a start within a few minutes before 13:08 confirms the timing leg to the second.
2. Compare the chart's values files at the two Helm revisions to confirm that no configuration change shipped with the code. A changed pool size or timeout would add a second candidate.
3. In a non-production environment, send one list request for a customer with 50 orders and count the queries issued. About 51 confirms the loop; a very different count would refute the size of the mechanism. This run does not reproduce anything.
4. Ask the orders-api owners what the database operations counter counts (statements only, or also pool checkouts and transaction statements) and whether any other route changed its query count. This reconciles the unexplained +64 per request.
5. Open the alert's state history in Grafana to find when it first fired and its threshold, which settles the detection delay.
6. Read the Deployment's CPU request and limit and the container throttling counters for the last three hours to close H5.
7. Ask the auth-api owners whether their verify latency or error rate moved between 13:00 and 15:30.
8. Ask the AWS account owner to confirm that the prod-read permission set is `ReadOnlyAccess`.
9. If the team wants lock waits closed explicitly, read the database's lock-wait view; Performance Insights is off for this instance, so enabling it is a change for the owner.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Remove the per-order query loop from the list view. Either load the page's items in one round trip again, joining as v2.14.0 did, or fetch the items of all orders on the page with one batched query. A batched fetch returns a larger result per request, so check it with a customer who has 50 orders. A rollback to v2.14.0 is the faster stop-gap, at the cost of delaying the shipment ETA on order detail. Check either option with `pre-flight` first. Any change goes to `iac-change-execution` or the app pipeline in a new session, with this report as context. |
| Fix | Reconcile the operations counter with the span counts, so the next investigation can rely on per-request arithmetic. |
| Prevention | Add a database-calls-per-request check for list endpoints to tests or to rollout analysis, since a flat per-query latency hid this change from latency-only checks. Roll out in steps with a p95 gate, because all 3 pods changed within a minute. The cost is a longer release. |
| Prevention | Replace the cluster read grant on all resources, which includes Secrets, with the built-in view role in `orders`, and confirm the AWS role is read-only. |
| Observability gap | No alert history or alert name, so detection delay and recurrence cannot be measured. Add a source: the state history, or an `ALERTS` series. |
| Observability gap | The HTTP histogram has no status label and there is no service-level error rate; p90 and p99 returned nothing. |
| Observability gap | No revision label: the traces and metrics carry no `service.version`, so old-against-new had to rely on timing and trace shape. |
| Observability gap | No latency recording rule for a 14-day recurrence read, no throttling or CPU-limit series, no per-pod latency, no pod name on Loki lines, and no latency series for auth-api. |

## Cost

43 queries · 0.05 GB of logs · 3 CloudWatch metric requests · no other metered units · about $0.00 in metered charges (a fraction of a cent for the 3 metric requests). 67 calls were logged in all; 24 of them, access checks and profile-discovery lists, are not counted against the ceiling.
