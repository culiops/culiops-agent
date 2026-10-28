---
date: 2026-08-14
service: orders-api
env: prod
symptoms: [latency, p95, "GET /orders", "POST /orders"]
cause_category: db-connection-pool
deps: [orders-db]
label: Confirmed
run: runs/orders-api-prod-20260814-0915
---

# orders-api slow on order reads and writes

p95 on `GET /orders` and `POST /orders` rose from 0.2 s to 2.4 s for 40 minutes. The DB connection pool was exhausted after a config change lowered the pool size; `pending_requests` on the pool metric stayed above 30 for the whole window. Confirmed by the pool metric, the config diff and timing. Fixed by restoring the pool size.
