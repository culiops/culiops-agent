# Investigation: orders-api prod: GET /orders slow since 13:08 UTC

Run: orders-api-prod-20261020-1530 · Mode: Deep · Window: 2026-10-20 12:30-15:30 UTC (22:30-01:30 Brisbane, 2026-10-20/21)
Access:
- prod-read (account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b): write capability only partly checked (gap). 7 of the 10 simulated actions came back implicitDeny. No row came back for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack. Three unrequested rows (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) were also implicitDeny. No action was `allowed`, so no boxed warning.
- arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace orders: no write verbs in orders (only get, list and watch, plus the excluded self-review creates).
- Grafana datasources: GRAFANA_SERVICE_ACCOUNT_TOKEN is set.

## TL;DR

| Field | Value |
|---|---|
| Cause | Release v2.15.0 (PR #2211, "load items per order in list handler") made GET /orders run one database statement per order (up to 50) instead of one joined statement. That is about 36 extra statements per request at roughly 6 ms each. · label: Confirmed |
| Weakest link | Mechanism to symptom rests on one 24-trace sample per window (duration = 90 ms + 6.05 ms per statement, r = 0.97). The metrics agree at the same 13:08 sample (database operations x10.4, p50 x3.4, call rate flat). Label: Confirmed. Two numbers are not reproduced and are carried as open items, not links: the absolute p95 (0.712 s, above the slowest sampled trace at 431 ms) and 64 against 36 extra operations per call. |
| Impact | GET /orders p95 0.18 s to 0.71 s (about 3.9x) and p50 0.09 s to 0.31 s from 13:08 UTC (23:08 Brisbane), on all 3 replicas. Ongoing at 15:30 UTC. Other routes and checkout are flat. Error rate not measured. |
| Severity | SEV2 (suggested) because one core-flow endpoint is significantly degraded while the rest of the service is healthy. The incident owner decides. |
| Pattern | unclassified · the alert's history is unreadable and the 14-day pull returned 3 of 336 points · Assumed |
| Recommended action | A human should consider restoring a single-query read path for the order list. Either roll back to v2.14.0, or fix forward so the items of the whole page load in one query. Check it with `pre-flight` first. A rollback also drops the other two changes in v2.15.0 (shipment ETA on order detail, structlog bump). A fix-forward costs a release cycle while the slowness continues. This run changed nothing. |
| Time to cause | about 8 min to the first Likely (after the diff and code read, wave 3); about 13 min to Confirmed (trace evidence, round 1) |
| Similar past incidents | `2026-08-14-orders-api.md`: same service and symptom words (latency, p95, GET /orders), but the cause was db-connection-pool. This run's pool metric shows no waiters, so this is not a repeat of that cause. No earlier occurrence of this cause is on record. |

## Impact

- **Symptom.** GET /orders p95 is 0.712 s at 15:30 against 0.181 s at 12:30 and 0.181 s at the same time 7 days earlier. p50 is 0.311 s against 0.092 s. (W1-Q5, W1-Q6, W1-Q7, W1-Q8, W1-Q9, W2-Q10, W2-Q11)
- **Affected.**
  - prod orders-api, order history (GET /orders, a core flow, customer-facing), all three replicas.
  - Flat routes: GET /orders/{id} p95 0.064 s, POST /orders (checkout) 0.142 s against 0.139 s, PATCH /orders/{id} 0.088 s. (W1-Q7, W1-Q8)
  - Failure rate was not measured, so SEV1 cannot be excluded on failures.
- **Onset.** 13:08 UTC. The last good sample is 13:06 (p95 0.163 s). Ongoing at 15:30. (W1-Q5)
- **Basis.** Request metrics against baseline; no SLO is named in environment.md. Label: Confirmed for the measurement.
- **Third party in the path.** None known. orders-db is AWS RDS in the same account.

## Recurrence

| Source | Window | Occurrences | When (UTC) | Normal vs incident |
|---|---|---|---|---|
| p95 alert (name and source not given) | 30d | not readable (Prometheus ALERTS empty, Grafana alert annotations empty) | n/a | not applicable |
| sibling alarms | 30d | none known | n/a | not applicable |
| database operations per second, whole-hour rate | 14d at 1h | 3 of 336 hourly points returned (10:30, 11:30, 12:30 on 2026-10-20) | n/a | baseline about 371-376 /s (3 points, so median, p95 and max are not meaningful); incident peak 4,089 /s, median 3,961 /s |

Class: `unclassified`. No rule can be applied honestly. The same clock window on 2026-10-13 is flat at baseline (W1-Q9, W1-Q17, W2-Q10, W2-Q11), and so is 2026-10-20 10:00-13:06. That is a weak negative, not a classification. (W0-Q8, W1-Q20, W1-Q23)

## Timeline

| Time (local, Brisbane) | Time (UTC) | Event | Evidence |
|---|---|---|---|
| (dates only) | 2026-10-16 / 2026-10-19 | Commits in v2.14.0..v2.15.0: #2203 structlog bump, #2208 shipment ETA on order detail, #2211 load items per order in list handler | W2-Q1 |
| 2026-10-20 23:04:50 | 13:04:50 (Helm prints no zone; ReplicaSet age agrees) | Helm revision 24: chart orders-api-4.2.0 unchanged, image v2.14.0 to v2.15.0 | W1-Q4, W1-Q1 |
| about 23:05-23:06 | about 13:05-13:06 | New ReplicaSet `orders-api-7c9b6d8f5d`: 3 pods, ages 145/144/144 min at 15:30. Old ReplicaSet at 0. | W1-Q2, PB-Q10 |
| 23:06 | 13:06 | Last good sample: p95 0.163 s, p50 0.082 s, database operations 365 /s | W1-Q5, W1-Q6, W1-Q16 |
| 23:08 | 13:08 | First bad sample: p95 0.716 s, p50 0.295 s, database operations 4,031 /s (x10.6), call rate unchanged (59.5 /s) | W1-Q5, W1-Q6, W1-Q16, W1-Q14 |
| 23:10 | 13:10 | orders-db CPU bucket 41.3% (the 13:05 bucket was 23.9%); ReadLatency flat at about 0.6 ms | W4-Q5 |
| 23:08-01:30 | 13:08-15:30 | p95 stays 0.66-0.76 s; database span p95 stays about 4 ms; pool used 17-24, pending 0 | W1-Q5, W1-Q21, W1-Q18 |
| 01:30 (10-21) | 15:30 | Still elevated | W1-Q7 |

## Causal chain

1. Trigger: Helm revision 24 rolled v2.15.0 at 13:04:50 (ReplicaSet about 13:05). It contains PR #2211 (commit a4c1e9b), which replaces `repo.list_orders_with_items(...)` with `repo.list_orders(...)` plus one `repo.list_items(order.id)` per order, in `orders_api/handlers/list_orders.py`. · Confirmed · W1-Q4, W1-Q1, W1-Q2, W2-Q2, W3-Q1, W3-Q2
2. Mechanism: each GET /orders now issues one `SELECT order_items` per order (up to 50). · Confirmed · W4-Q1 to W4-Q4, W1-Q16, W1-Q21
   - Descendant spans per request: p50 41 against 3 (n=24 each).
   - The fetched incident trace has 12 serial item selects. The baseline trace has one joined select.
   - Database operations rose x10.4 at the same sample.
   - Per-statement time is unchanged at about 3-4.5 ms.
3. Symptom: GET /orders p50 0.092 to 0.311 s and p95 0.181 to 0.712 s from 13:08. · Confirmed · W1-Q5 to W1-Q9, W4-Q1
   - In the incident sample, duration = 89.8 ms + 6.05 ms per descendant span (r = 0.966).
   - 35.8 extra spans x 6.05 ms = 217 ms, against +219 ms observed at p50.
   - Other routes are flat.

Timing leg: Helm 13:04:50, first bad sample 13:08, last good sample 13:06, and the -7d window flat. The 2-minute metric step and Helm's unzoned clock limit the precision to about a minute or two.

Why it became an incident:
- The rollout reached all 3 pods and scaled the old ReplicaSet to 0, so there was no mixed fleet to compare. (Confirmed, W1-Q2)
- No deploy marker exists in Grafana. (W1-Q24)
- orders-db had headroom (CPU 41%), so the extra work showed as latency only, with no errors or saturation to stop anything. (Confirmed for the headroom, W4-Q5; Assumed that no other alert exists.)
- When the p95 alert first fired is unknown, because its history is unreadable. (G2)

## Evidence

- **Deploy and diff.**
  - W1-Q4 and W1-Q1: Helm revision 24 at 13:04:50, image v2.14.0 to v2.15.0.
  - W1-Q2 and PB-Q10: ReplicaSet and pods about 145 min old at 15:30.
  - W2-Q2 and W3-Q1: handler change.
  - W3-Q2: `list_items` takes its own pool connection per call; the joined `list_orders_with_items` still exists, unused.
- **Step.**
  - W1-Q5: p95 0.163 s at 13:06, 0.716 s at 13:08, median 0.712 s afterwards.
  - W1-Q6: p50 median 0.092 s before, 0.311 s after.
  - W1-Q14: call rate flat at about 56 /s.
  - W1-Q16: database operations 381 /s to 3,961 /s.
  - W1-Q17, W2-Q10, W2-Q11: the same window a week earlier is flat.
- **Per-statement cost unchanged.** W1-Q21: database span p95 3.9-4.4 ms in every sample. W4-Q3: item selects 2.9-4.5 ms against 3.05 ms for the joined baseline select.
- **Traces.**
  - W4-Q1 and W4-Q2: 24 traces per window (at least 20), with per-request descendant-span counts and the latency fit above.
  - W4-Q3: trace `e3ea7a3906419b466a28541306cc5ee1`, 152 ms, 12 serial `SELECT order_items`.
  - W4-Q4: trace `65345f5f8176033524bc88af3bd43f6f`, 109 ms, one `SELECT orders JOIN order_items`.
  - `matched` counts all descendant spans, including one constant auth-api call per request.
- **Database consequence.** W4-Q5: CPU 24.9% to 40.6% median (max 44%), starting in the 13:10 bucket. Connections 42 to 47. ReadLatency flat.
- **Open numbers.**
  - The histogram p95 (0.712 s) is above the slowest sampled incident trace (431 ms; sample p95 422 ms).
  - Metrics imply about 64 extra operations per call; traces imply about 36 on average, and at most 50.

## Ruled out

| Hypothesis | Why | Query |
|---|---|---|
| H2: orders-db saturated or contended, independent of statement count | CPU peaked at 44% and rose only after the application step. ReadLatency flat at about 0.6 ms. Database span p95 flat at about 4 ms. Lock waits excluded only indirectly (Performance Insights off, other RDS metrics had no data). | W4-Q5, W4-Q6, W1-Q21 |
| H3: connection pool or engine connection cap reached | `pending_requests` was 0 in every sample; pool used max 24; DatabaseConnections 41-48 with no ceiling. A past incident (2026-08-14) was a lead only and was not shown to the worker. Caveats: pool size and `max_connections` are unreadable, and the gauge is sampled at 60 s. | W1-Q18, W4-Q7, W4-Q8 |
| H5: a non-database downstream got slower | Request duration is fully proportional to statement count. The fit intercept (90 ms) is at or below the baseline median (110 ms; range 78-165). The only non-database client span in the two fetched traces, auth-api verify, took 3.4 ms and 3.8 ms. Basis: sample fit (default tier inconclusive, escalated tier), no direct auth-api latency series. | W4-Q1 to W4-Q4, W4-Q12 to W4-Q14 |
| H6: traffic spike or bot | GET /orders call rate 56.2 /s against 56.5 /s before. The -7d call rate was not usable (G5). | W1-Q14 |
| H7: another commit in the release (#2208, #2203) | Only GET /orders moved. GET /orders/{id} is 0.064 against 0.061. POST and PATCH are flat. | W1-Q7, W1-Q8, W1-Q9, W2-Q2 |
| H8: image pull or scheduling failure, crash loop, OOM | 3 desired, 3 ready; 0 restarts. Events had expired. | W1-Q2, PB-Q10 |

## Open hypotheses

| Hypothesis | Label | What would settle it |
|---|---|---|
| H4: the 3 new pods are CPU-throttled or at their CPU limit, contributing to the latency tail | Assumed | No CPU limit and no throttling series exist in Prometheus or kubectl (W4-Q9 to W4-Q11). The 24-trace sample does not contain the tail (431 ms against a histogram p95 of 0.712 s). In the two fetched traces, in-process gaps are 1.0-1.7 ms against 1.5 ms, so no stretch is seen there. Settling it needs the container's CPU limit from the chart values, a throttling panel for 13:00-15:30, and the latency histogram's bucket boundaries. |
| Tail size: why p95 is 0.712 s while sampled traces top out at 431 ms | Assumed | A wider trace sample that includes the slowest requests, and the histogram's bucket layout (interpolation could inflate the p95). It does not change the cause. The median and p95 moved together, and the p95/p50 ratio is 2.3 against 2.0 before. |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1: AWS write capability only partly checked (3 of 10 actions had no row) | None on the cause. The report cannot call prod-read read-only. | Re-run the simulation for those three actions, or confirm prod-read is a read-only role. |
| G2/G3: the p95 alert's name and history are unknown (ALERTS series empty, alert annotations `{}`). The 14-day pull returned 3 of 336 points. | Recurrence stays `unclassified`. A chronic or flapping alert is not excluded. When the alert first fired is unknown. | The alert's name, source and state history from its owner. Confirm Prometheus retention and any p95 recording rule. |
| G4: p90 and p99 returned empty | The ceiling check rests on p50 against p95 only. | Confirm whether p90/p99 are scraped. |
| G5: the -7d call rate was not usable (offset query returned current-day timestamps) | Volume against work-per-request is judged against the previous window only. | None needed unless a -7d call rate is wanted. |
| G6: Kubernetes events had expired (one-hour retention; rollout 145 min old) | No Unhealthy, BackOff or scheduling events can be read. | None (expired). Ship events to a log store for future incidents. |
| G7/G16: CPU limit, requests and throttling are not readable; CPU samples start at 13:08 | H4 stays open. | Read the container resources from the chart values at v2.15.0 and the throttling panel. |
| G9/G11: Services, ingresses, HPAs, upstream callers, the IaC or values repo and the repo's default branch are unknown | Merged-versus-applied cannot be checked. The upstream path is unknown. | Name the repo and the ingress. Run `service-discovery` after the incident. |
| G10: Helm prints times without a zone | The 13:04:50 deploy time is approximate against UTC. The ReplicaSet age corroborates about 13:05. | Read the ReplicaSet `creationTimestamp` (UTC). |
| G12: no SLO and no business counter named for the core flows | Impact basis is request metrics, not SLO burn. | Name them in environment.md. |
| G13: schedule listings, CloudTrail and RDS events returned no items (11:08-14:08). RDS windows were not in the reply. | A schedule or control-plane change near 13:08 is not proven absent. Coverage is us-east-1 under prod-read. | A human with wider access lists schedules and maintenance windows. |
| G14/G15: histogram p95 above the sampled maximum; 64 against 36 extra operations per call | Quantity only. | Read the histogram bucket boundaries. Ask the metric owner whether `db_client_operation_duration_seconds_count` counts commits. |
| G17/G18: pool maximum and engine `max_connections` unreadable; no lock-wait data (Performance Insights disabled) | H3 "well below the limit" is not shown. H2 lock contention is excluded only through flat statement latency. | Read pool size from the chart values and `max_connections` from the parameter group. Enable Performance Insights. |
| G19: auth-api seen in traces, no latency series | H5 rests on the fit intercept. | Name the dependency owner and read its latency. |

Open items need your input.

## To confirm, a human would…

1. Read the live pod image string and confirm it is v2.15.0. The traces already show the new query pattern, so this closes the last "running code" doubt.
2. Read the container CPU request and limit from the chart values at v2.15.0, and the throttling panel for the three pods between 13:00 and 15:30 UTC. A throttling share near zero would close H4.
3. Read the latency histogram's bucket boundaries around 0.5 s and 1 s, to see how much of the 0.712 s p95 is interpolation. A trace sample that includes the slowest requests would settle the same question.
4. Ask the owner of `db_client_operation_duration_seconds_count` what an "operation" is (statements only, or commits as well). It would explain 64 against 36 extra operations per call.
5. Ask the owner of the p95 alert for its name, threshold and state history. The history would settle the recurrence class and show when it first fired.
6. Ask the owner of auth-api for its latency over 12:30-15:30 UTC. It would close the sub-20 ms case under H5.
7. Re-run the write-capability simulation for the three actions without a row, or confirm that prod-read is a read-only role.
8. Replay a representative list request against a staging copy to measure per-statement cost. This was not done here, because it would send requests to the service.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Consider restoring a single-query read path for the order list. Options: roll back to v2.14.0, or change the handler so one query (or one batched query) loads the items of the whole page instead of one per order. A rollback drops the shipment ETA change and the structlog bump until they are re-released. A fix-forward needs a release while the slowness continues. Check either with `pre-flight` and hand it to a separate session (`iac-change-execution`), with this report as context. |
| Prevention | Add a test that counts database statements for the order-list endpoint, so a per-item query fails in review. Add a progressive rollout with a per-route p95 gate and an automatic stop. Consider a per-route latency alert and a database-operations-per-request ratio alert. |
| Observability gap | Export CPU limits and throttling (cAdvisor and kube-state series are absent). Keep traces of the slowest requests in the sample, and add a p95 recording rule so the 14-day recurrence can be computed. Write Grafana deploy markers. Keep Kubernetes events beyond one hour. Enable Performance Insights on orders-db. Keep alert state history readable. Record the IaC or values repo in the profile and run `service-discovery` for the dependency map. |

The history match (2026-08-14) is not a repeat, so there is no repeat count and no alert-tuning item.

## Cost

53 queries · 0.096 GB of logs · 7 CloudWatch metric requests · Tempo inspected about 16.2 GB (not a budgeted unit) · negligible metered charges (7 GetMetricData metrics; see the CloudWatch pricing page)

