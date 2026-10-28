---
id: 2026-10-20-orders-api-prod-n-plus-one-list
date: 2026-10-20
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-20T12:30:00Z/2026-10-20T15:30:00Z
symptoms: [latency]
cause_category: deploy
cause: release v2.15.0 (PR #2211) loads order items with one query per order in GET /orders (N+1)
deps: [orders-db]
label: Confirmed
mode: deep
time_to_cause_min: 13
run: runs/orders-api-prod-20261020-1530
---

# orders-api GET /orders slow after v2.15.0

What happened: from 13:08 UTC GET /orders p95 rose from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) on all 3 replicas, about 3 minutes after Helm revision 24 rolled v2.15.0. Other routes were flat. Ongoing at 15:30 UTC.

Causal chain: trigger = PR #2211 replaced one joined query with a per-order list_items loop (Confirmed); mechanism = up to 50 serial SELECT order_items per request, descendant spans p50 41 against 3, database operations x10.4, each statement still about 4 ms (Confirmed); symptom = duration about 90 ms + 6 ms per statement, r = 0.97 (Confirmed).

What found it: per-route p95 isolating GET /orders, then database operations per second stepping at the same sample while the call rate was flat, then the structural trace search and one trace per window.

What did not help: the database span p95 being flat (it looked like the database was fine; the statement count was the signal); alert history and the 14-day pull (unreadable); Kubernetes events (expired); the Loki stream app="orders" (not tied to the service); a past pool-exhaustion incident (2026-08-14), checked and not the cause.

Follow-ups raised: restore a single-query read path for the list; N+1 statement-count test; progressive rollout with a per-route latency gate; export CPU limits and throttling; keep traces of the slowest requests; deploy markers in Grafana.
