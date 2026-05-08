# Dry-run of `cloud-cost-investigate` against `attribution-gcp-orders`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Detect & Scope

- Reads `operator-question.md`. Heuristic: "what does X cost / break it down by resource" → **attribution mode** (suggested).
- Detects GCP via `gcloud config get-value project` or `GOOGLE_CLOUD_PROJECT` env var (simulated for fixture: project = `acme-prod`).
- Scope: GCP project `acme-prod`. Time range: last completed billing month (2026-04).
- Catalog lookup: finds `.culiops/service-discovery/orders.md`. Skill loads it and reports: "Found service catalog for `orders`: 8 resources across Cloud Run, Cloud SQL, GCS, Pub/Sub, Cloud Tasks."
- Presents scoping summary: mode=attribution, project=acme-prod, service=orders, period=2026-04, catalog=orders.md (8 resources).

**GATE 1:** operator confirms.

## Step 2A — Attribution mode query plan

Skill proposes 3 queries in a single batch:

1. BigQuery: `gcp_billing_export_v1_*` — monthly totals filtered `WHERE labels.service = 'orders'`, months 2026-03 and 2026-04. Returns `cost-by-label.json`.
2. BigQuery: same export — per-resource breakdown for 2026-04, grouped by `resource.global_name`. Returns `cost-by-resource.json`.
3. BigQuery: same export — monthly total for 2026-03 (period comparison). Already covered by query 1 (two-month window).

Effective distinct queries: **2** (queries 1 and 3 are combined into a single two-month window call).

Estimated BigQuery cost: ~$0.014 (2 queries × ~1.4 GB scanned × $5/TB). Negligible.

IAM required: `roles/bigquery.dataViewer` on the billing export dataset; `roles/bigquery.jobUser` on project `acme-prod`.

Note: This is NOT Cost Explorer (AWS). GCP billing export lives in BigQuery. There is no per-call charge structure like AWS CE — BigQuery charges by bytes scanned. The skill notes the estimated bytes-scanned figure and resulting charge ($0.014) in the query plan.

**GATE 2:** operator approves.

## Step 3 — Execute

- Query 1+3 (combined): returns `cost-by-label.json` — 2026-04: $2,847.32, 2026-03: $2,611.84.
- Query 2: returns `cost-by-resource.json` — 8 rows: 7 catalog resources + 1 uncataloged (`shared-nat`).

## Step 4 — Attribution analysis

### 4A: Load catalog

Skill reads `.culiops/service-discovery/orders.md` and builds the resource index:

```
orders-api           Cloud Run     (active)
orders-worker        Cloud Run     (active)
orders-prod-db       Cloud SQL     (active)
orders-dev-db        Cloud SQL     (active — per catalog; to be verified)
orders-events        GCS           (active)
orders-archives      GCS           (active)
orders-fulfillment   Cloud Tasks   (active)
orders.events        Pub/Sub       (active)
```

Total: 8 catalog resources.

### 4B: Cross-reference billing rows against catalog

Skill iterates all rows in `cost-by-resource.json` and checks each `resource_name` against the catalog index:

| Billing row | Cost | Catalog match? |
|-------------|------|----------------|
| `orders-api` | $680.42 | yes |
| `orders-worker` | $420.17 | yes |
| `orders-prod-db` | $890.55 | yes |
| `orders-events` | $240.33 | yes |
| `orders-archives` | $185.09 | yes |
| `orders.events` | $310.74 | yes |
| `orders-fulfillment` | $122.02 | yes |
| `shared-nat` | $87.15 | **NO — context cost flag** |

Skill checks catalog resources NOT present in any billing row:

| Catalog resource | Billing row found? |
|------------------|--------------------|
| `orders-api` | yes |
| `orders-worker` | yes |
| `orders-prod-db` | yes |
| `orders-dev-db` | **NO — untraced resource flag** |
| `orders-events` | yes |
| `orders-archives` | yes |
| `orders.events` | yes |
| `orders-fulfillment` | yes |

### 4C: Compute service total

Sum of 7 matched catalog resource rows:
```
  680.42  (orders-api)
  420.17  (orders-worker)
  890.55  (orders-prod-db)
  240.33  (orders-events)
  185.09  (orders-archives)
  310.74  (orders.events)
  122.02  (orders-fulfillment)
= 2,849.32
```

Label-level total from query 1: **$2,847.32**.

Discrepancy: $2.00 (~0.07%). Skill notes: "Per-resource sum ($2,849.32) differs from label-level total ($2,847.32) by $2.00. This is within BigQuery export rounding tolerance (fractional cent accumulation across SKUs). Using label-level total as authoritative figure: **$2,847.32**."

### 4D: Flags

**Untraced resource — `orders-dev-db`:**
- In catalog (Cloud SQL, `orders-dev-db`, us-central1, `env=dev`).
- No billing row in 2026-04 export.
- Skill emits: `UNTRACED: orders-dev-db — present in service catalog but no cost recorded for 2026-04. Resource may have been deleted or de-provisioned within the billing period. Action: verify — if intentionally de-provisioned, remove from service catalog.`
- No cost claimed. This is informational, not a savings item.

**Context cost — `shared-nat`:**
- Appears in billing export with `labels_service=shared-infrastructure` and cost $87.15/mo.
- Not present in service catalog for `orders`.
- Skill emits: `CONTEXT COST: shared-nat (Cloud NAT, $87.15/mo) — appears in billing data for this period but is not a cataloged resource of the orders service. This is shared infrastructure cost. EXCLUDED from orders service total. Action: document the cost-split rule for shared-nat so it can be allocated to consuming services.`
- Explicitly excluded from the $2,847.32 service total.

### 4E: Period comparison

- 2026-04: $2,847.32
- 2026-03: $2,611.84
- Delta: +$235.48 (+9.0% MoM)
- Top contributor to MoM growth: Cloud Run (`orders-api` + `orders-worker` combined: $1,100.59 in 2026-04 vs. estimated ~$1,009 in 2026-03 based on label-level allocation). Note: per-resource breakdown for 2026-03 is not in the fixture — skill notes this gap and uses label-level comparison only.

## Step 5 — Compose report

- Writes draft to `.culiops/cloud-cost-investigate/acme-prod-orders-attribution-2026-05-08-HHMM.md`.
- Report sections:

### Service cost summary

> **Orders service — 2026-04**
> Total: **$2,847.32** (authoritative: label-level total from BigQuery export)
> Period comparison: $2,611.84 in 2026-03, +9.0% MoM

### Per-resource breakdown

| # | Resource | Type | Cost (2026-04) | % of total |
|---|----------|------|----------------|------------|
| 1 | `orders-prod-db` | Cloud SQL | $890.55 | 31.3% |
| 2 | `orders-api` | Cloud Run | $680.42 | 23.9% |
| 3 | `orders-worker` | Cloud Run | $420.17 | 14.8% |
| 4 | `orders.events` | Pub/Sub | $310.74 | 10.9% |
| 5 | `orders-events` | GCS | $240.33 | 8.5% |
| 6 | `orders-archives` | GCS | $185.09 | 6.5% |
| 7 | `orders-fulfillment` | Cloud Tasks | $122.02 | 4.3% |

### Untraced / context section

> **Untraced resources (in catalog, no billing row):**
>
> | Resource | Type | Note |
> |----------|------|------|
> | `orders-dev-db` | Cloud SQL | No cost recorded in 2026-04. Resource may be deleted or de-provisioned. Verify — remove from catalog if no longer active. |
>
> **Context costs (in billing data, not in catalog):**
>
> | Resource | Type | Cost | Note |
> |----------|------|------|------|
> | `shared-nat` | Cloud NAT | $87.15/mo | Shared infrastructure; not attributed to orders service. Excluded from service total. Document cost-split rule. |

### Remediation list

Attribution mode produces informational items, not waste/delete actions.

| # | Action | Resource(s) | Est. savings/mo | Source | Confidence | Evidence |
|---|--------|-------------|-----------------|--------|------------|----------|
| 1 | Remove `orders-dev-db` from service catalog if intentionally de-provisioned | `orders-dev-db` | n/a (catalog hygiene) | untraced-resource-flag | informational | No billing row in 2026-04; resource labeled `env=dev` |
| 2 | Document shared NAT cost-split rule | `shared-nat` | n/a (attribution hygiene) | context-cost-flag | informational | $87.15/mo appearing in orders billing data but not in catalog; labeled `shared-infrastructure` |

**Total estimated savings: $0** (attribution mode does not surface waste items in this fixture — both findings are informational).

**GATE 4:** operator approves the report; skill commits to `.culiops/cloud-cost-investigate/`.

## Gaps surfaced

(filled during actual dry-run)

## Fixes applied

(filled during actual dry-run)
