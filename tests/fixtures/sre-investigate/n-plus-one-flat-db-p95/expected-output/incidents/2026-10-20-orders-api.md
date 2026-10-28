---
id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
date: 2026-10-20
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-20T13:08Z/ongoing at 2026-10-20T15:30Z
symptoms: [latency]
cause_category: deploy
cause: v2.15.0 list handler loads items with one query per order (N+1): median 41 descendant spans per GET /orders request against 3, p95 0.18 s to 0.71 s
deps: [orders-db]
label: Confirmed
mode: deep
time_to_cause_min: null
run: runs/orders-api-prod-20261020-1530
---

# orders-api GET /orders about 4x slower after the v2.15.0 rollout

## What happened

Helm revision 24 (orders-api v2.15.0) was deployed at 13:04:50 UTC on 2026-10-20. From the 13:08 sample, p95 of `GET /orders` went from 0.18 s to 0.71 s (p50 0.09 s to 0.31 s) and stayed there up to 15:30 UTC. No other endpoint moved. The database was not saturated (CPU 25% to 41%, no pool waiters). The p95 alert kept firing.

## Causal chain

1. Trigger: commit a4c1e9b (#2211) in v2.15.0 changed `list_orders.py` to call `repo.list_items(order.id)` once per returned order (up to 50) instead of one joined query. Confirmed.
2. Mechanism: each request makes about 1 + N statements (descendant spans p50 41, p95 52 against p50 3, p95 4 before; 24 traces each), each statement as fast as before (about 4 ms); service-wide DB statements per second x10.4 with a flat call rate. Confirmed.
3. Symptom: GET /orders p95 x3.9, p50 x3.4 from 13:08, three minutes after the upgrade. Confirmed.

## What found it

The statement rate stepping x10.4 at the same sample as the latency step while the endpoint's call rate and the per-statement DB p95 stayed flat (a flat database p95 did not clear the database), then the span count per request in the incident window against the pre-deploy window.

## What did not help

- p90 and p99 queries returned nothing; the shape was read from p50 against p95.
- The Loki stream for the service is labelled app="orders" and its lines carry no pod or trace ID; it could not be tied to the service and was not used as evidence.
- Kubernetes events for the rollout had expired; the histogram has no pod label, so there was no old-versus-new split by pod.
- The earlier orders-api latency incident (2026-08-14) pointed at the connection pool; here pool waiters are 0 at every point.

## Follow-ups raised

Fix or roll back the list handler; a statement-count test and canary gate for list endpoints; pod/version labels and p90/p99 recording rules; Performance Insights on orders-db; name the alert and add the chart values repo to environment.md.
