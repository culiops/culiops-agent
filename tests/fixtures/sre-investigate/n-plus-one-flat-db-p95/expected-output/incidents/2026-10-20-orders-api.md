---
id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
date: 2026-10-20
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-20T13:08Z/ongoing
symptoms: [latency]
cause_category: deploy
cause: v2.15.0 (#2211) changed GET /orders to one items query per order (N+1), up to 51 queries per request instead of 1
deps: [orders-db]
label: Confirmed
mode: deep
time_to_cause_min: null
run: runs/orders-api-prod-20261020-1530
---

# orders-api: GET /orders slow after v2.15.0

What happened: GET /orders p95 went from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) as a step at 13:08 UTC on 2026-10-20, three minutes after Helm revision 24 (v2.15.0) went live. Other routes and the request rate did not move. Still ongoing at 15:30 UTC.

Causal chain: trigger: commit #2211 replaced the joined query with one items query per order (Confirmed). Mechanism: database spans per GET /orders request went from a median of 3 to a median of 41 (max 52), per-query time unchanged at about 4 ms (Confirmed). Symptom: p50 and p95 up by about 6-7 ms per extra query (Confirmed). Weakest link: timing at about two minutes' resolution; the tenfold rise in database operations is about 1.8x what the sampled traces explain (Likely).

What found it: the structural trace search `route >> { span.db.system =~ ".+" }` for the incident hour against the hour before the rollout, together with the code diff of the release.

What did not help: CPU and pool metrics (the pool showed no waits; database CPU rose only after the application step); a 14-day recurrence pull (the metrics returned 5.5 h); p90 and p99 queries (empty); Kubernetes events (expired).

Follow-ups raised: restore a single round trip for the order list or roll back; a query-count test for list endpoints; a rollout latency gate; error, load-balancer, throttling and p99 metrics; make the alert's history queryable.
