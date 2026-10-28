# Investigation: orders-api prod: GET /orders p95 about 4x slower since 13:08 UTC
Run: orders-api-prod-20261020-1530 · Mode: Deep · Window: 2026-10-20 12:30-15:30 UTC (22:30 to 01:30 Australia/Brisbane)

## TL;DR
| Field | Value |
|---|---|
| Cause | Release v2.15.0 (Helm revision 24, about 13:05 UTC) shipped commit #2211. It makes GET /orders run one items query per order instead of one joined query, so a request runs up to 51 queries instead of 1 (an N+1). p50 rose from 0.09 s to 0.31 s and p95 from 0.18 s to 0.71 s. **Confirmed** |
| Weakest link | Timing. The rollout (about 13:05; Helm prints 13:04:50 with no zone, backed by 145-minute-old ReplicaSet and pods) against the first slow 120 s sample at 13:08. Confirmed, at about two minutes' resolution. A weaker sub-claim: DB operations rose by about 3,570/s, about 1.8x what the sampled traces explain (about 2,000/s). "All of the tenfold rise is this mechanism" is Likely. This does not lower the cause. |
| Impact | GET /orders (order history, a core flow) is about 4x slower on all 3 replicas since 13:08 UTC and still ongoing at 15:30. Other routes and the request rate (about 56 req/s) are unchanged. No failed requests seen (Assumed; there is no error metric). |
| Severity | SEV2 (suggested). The incident owner decides. |
| Pattern | unclassified, reads as sudden (Assumed). The alarm history is missing and only 5.5 h of the 14 days of metrics came back. |
| Recommended action | The orders team chooses between rolling back to v2.14.0 and a fix that loads all items for the page in one round trip. A rollback also drops the shipment ETA field (#2208) and the structlog bump until they are re-released. Check the chosen change with `pre-flight` and apply it in a separate session. |
| Time to cause | Not measured (no clock in the session). |
| Similar past incidents | `2026-08-14-orders-api` matched on service and symptom. Its cause was a pool-size change, which this run refuted. Not a repeat. |

## Causal chain
1. **Trigger (Confirmed).** #2211 replaces `list_orders_with_items` with `list_orders` plus `list_items` per order (W2-Q3, W3-Q1, W3-Q2). Helm revision 24 and ReplicaSet age date it to about 13:05 (W1-Q5, W1-Q2).
2. **Mechanism (Confirmed).** DB spans per GET /orders request went from median 3 (max 4, 24 traces, 11:00-12:00) to median 41 (max 52, 24 traces, 14:30-15:30) (W4-Q2, W4-Q1). One trace shows `SELECT orders` followed by 12 sequential `SELECT order_items` (W4-Q3). Per-query time stays at about 4 ms and the request rate stays flat (W1-Q22, W1-Q15).
3. **Symptom (Confirmed).** p50 0.09 to 0.31 s, p95 0.18 to 0.71 s from 13:08. Trace duration grows with span count at about 6-7 ms per extra query: (41-3) x 6.7 is about 255 ms against +232 ms observed. Other routes are flat (W1-Q6 to Q8).

**Why it became an incident:** the DB and the pool absorbed 10x the operations without failing, so the effect was slowness, not errors (RDS CPU 24% to 41%, pool pending 0, read latency flat). No query-count guard or rollout latency check was visible to this run (Assumed). The time the alert took to fire is unknown.

## Ruled out
- **H3, other v2.15.0 changes:** every other route is flat (largest change 0.003 s).
- **H2, database slow on its own:** read latency 0.5-0.7 ms and per-query span time about 4 ms are unchanged. CPU rose only from the 13:10 bucket, after the application step, and has about 59% headroom.
- **H7, pool cap (a lead from the 2026-08-14 incident):** pending requests are 0 at all 166 samples and used connections are not pinned.
- **H6, orders-reconcile worker:** orders-api's per-query time is flat and there are no pool waits. No worker log lines before 15:00, so its cadence across 13:08 could not be compared.
- **H5, traffic spike:** call rate flat at 52-61 req/s.

## Open
- **H4, CPU limits or throttling (Assumed):** the Deployment CPU limit, throttling series, autoscaler state and pre-13:08 CPU could not be read. It is not a competing cause. Escalated once to the strong tier, still inconclusive.
- **Operations-rate residual (Likely):** the extra 1,570 ops/s is unexplained. A commit counted per pool checkout, or another caller, are possible readings.

## Gaps (13 in the ledger; main ones)
- The p95 alert's name and history are unavailable.
- Metrics returned 5.5 h of the 14 days asked.
- The p90 and p99 queries returned empty.
- No CPU limits, throttling or HPA data.
- Kubernetes events had expired.
- No error metric, load-balancer series or SLO, so impact is Assumed.
- Helm prints times without a zone, and `date -u` returned nothing, so "now" = 15:30 UTC is an assumption.
- Helm values for revision 24 were not compared with revision 23.
- 3 of the 10 write-check actions got no simulator row.

open items need your input

## To confirm, a human would…
1. Time GET /orders with the old and new handler on a copy of the service. This run may not reproduce it.
2. Ask the orders team whether the DB metric counts a commit per pool checkout, and read the DB's own statement counters for 13:00-13:20, to explain the extra 1,570 ops/s.
3. Read the Deployment's CPU requests and limits and the pods' throttling from the platform side, and compare CPU from before the rollout (H4).
4. Diff the Helm values between revisions 23 and 24 in the chart repository.
5. Confirm the rollout and first alert times from the release and alerting records.
6. Size user impact from load-balancer or real-user metrics.

## Follow-ups
- **Fix:** restore a single round trip for the order list, or roll back first (the cost is above). Assess with `pre-flight` and apply in a separate session.
- **Prevention:** a test that fails when GET /orders exceeds a small number of queries for a page of 50. A rollout gate that compares GET /orders p95 with the previous release, at the cost of slower rollouts and a threshold to maintain.
- **Observability gap:** error/status and load-balancer metrics, p90/p99, CPU throttling series, CPU history for replaced pods, per-pod latency, queryable alert history, complete orders-reconcile log shipping, and kept Kubernetes events.

## Cost
42 queries (plus 28 uncounted access, kubectl, helm, git, gh and local reads) · 0.05 GB of logs · 3 CloudWatch metric requests · 11.4 GB of trace data inspected by Tempo (no budget set) · under $0.001 in metered charges
