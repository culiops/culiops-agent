---
id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
date: 2026-10-20
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-20T13:08Z/2026-10-20T15:30Z
symptoms: [latency]
cause_category: deploy
cause: release v2.15.0 changed the GET /orders list handler to one items query per order (N+1): about 10 times more database operations and p95 0.18 s -> 0.71 s
deps: [orders-db, auth-api]
label: Confirmed
mode: deep
time_to_cause_min: null
run: runs/orders-api-prod-20261020-1530
---

# orders-api GET /orders slow after v2.15.0 (N+1)

## What happened

At 13:08 UTC on 2026-10-20 the p95 of `GET /orders` on orders-api (prod) went from about 0.18 s to about 0.71 s and stayed there; p50 went from about 0.09 s to about 0.31 s. Request rate stayed at about 56/s, other routes were flat, and the window was still open (ongoing) at 15:30 UTC. The p95 alert kept firing; its history could not be read.

## Causal chain

1. Trigger: release v2.15.0 (Helm revision 24, about 13:05 UTC, all 3 pods replaced) contains commit a4c1e9b (#2211), which changes the list handler from one joined query to one items query per order · Confirmed.
2. Mechanism: each request now makes 1 + up to 50 serial database queries (descendant spans per request p50 41, max 52, against p50 3, max 4 before); database operations rose 10.4 times at the same minute; per-query latency stayed at about 4 ms; pool and database had headroom · Confirmed.
3. Symptom: trace duration follows the span count (about 101 ms + 5.8 ms per span), which accounts for the p50 and p95 step · Confirmed.

## What found it

The span count per request, new window against old window (W2-Q8 against W2-Q9), together with the 10.4 times step in database operations at 13:08 with a flat request rate (W1-Q15) and flat per-call database latency (W1-Q17).

## What did not help

Database CPU and pool were dead ends within the first queries (read latency flat, pending requests 0). p90 and p99 returned nothing. The -7d request-rate query came back identical to the unshifted one. The Loki lines carried a label that could not be tied to the pods. Kubernetes events had expired. A bare Tempo search returned no traces although the service name was right. No alert history was available, so detection delay is unknown.

## Follow-ups raised

Restore a single-round-trip read for the list view (or roll back as a stop-gap, which also withdraws the shipment ETA shipped in the same release); add a database-calls-per-request check to tests or rollout analysis; add a status label, a revision label on traces and metrics, a latency recording rule, an alert-history source, and throttling and limit series; reconcile the size of the extra database work with the operations counter; narrow the Kubernetes read grant from all resources to the built-in view role.
