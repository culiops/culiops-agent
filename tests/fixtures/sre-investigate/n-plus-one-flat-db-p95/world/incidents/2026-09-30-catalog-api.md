---
date: 2026-09-30
service: catalog-api
env: prod
symptoms: [errors, 5xx, "GET /search"]
cause_category: dependency-capacity
deps: [search-cluster]
label: Likely
run: runs/catalog-api-prod-20260930-1402
---

# catalog-api search errors

5xx on `GET /search` for 25 minutes while the search cluster was rebalancing shards. Likely: timing and the cluster's own health events; the cluster's internal logs were not available.
