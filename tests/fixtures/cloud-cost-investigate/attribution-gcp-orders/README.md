# attribution-gcp-orders — cloud-cost-investigate fixture

Attribution-mode fixture exercising catalog consumption, untraced-resource flagging, and context-cost flagging for a GCP service.

## What's modelled

A fictional GCP project `acme-prod` running an `orders` service with 8 cataloged resources. The operator wants a monthly cost breakdown by resource. One cataloged resource (`orders-dev-db`) does not appear in the billing export for the investigation period — it was deleted and stopped billing. One cost line item (`shared-nat`) appears in the billing export but is not in the service catalog — it represents a shared NAT gateway that is not part of the orders service.

## The operator question

> "What does the orders service cost us per month? Break it down by resource."

(See `operator-question.md`.)

## What this fixture exercises

- **Mode detection from question phrasing:** "what does X cost / break it down by resource" → attribution mode (suggested at GATE 1).
- **Catalog consumption:** attribution mode requires a service catalog. Skill loads `.culiops/service-discovery/orders.md` (present in this fixture, simulating a prior service-discovery run). Without a catalog, the skill cannot perform attribution and must ask the operator to supply one or use a tag convention instead.
- **Cost lookup by label:** GCP billing export queried via BigQuery, filtered `WHERE labels.service = 'orders'`. Two calls: one for label-level total, one for resource-level breakdown.
- **Untraced resource flag:** `orders-dev-db` is listed in the service catalog but does NOT appear in the billing export for 2026-04. The skill flags it as "untraced — deleted or de-provisioned within billing period; verify" and does NOT claim $0 cost for it (absence of a billing row is not confirmed zero spend).
- **Context cost flag:** `shared-nat` (a shared Cloud NAT gateway) appears in the billing export as a cost line item but does NOT match any resource in the service catalog. The skill flags it as "context cost" — shared infrastructure not attributed to the orders service — and explicitly EXCLUDES it from the orders service total.
- **Period comparison shows trend:** 2026-03 vs 2026-04 data shows +9% MoM.
- **GCP-specific behavior:** billing export path uses BigQuery (`gcp_billing_export_v1_*` dataset). No GCP Recommender call is made in attribution mode (Recommender is for waste/rightsize, not attribution).

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `.culiops/service-discovery/orders.md` | Mock service-discovery catalog for the orders service (8 GCP resources) |
| `cost-by-label.json` | Synthetic BigQuery billing export aggregated by `labels.service=orders`, monthly granularity |
| `cost-by-resource.json` | Synthetic BigQuery billing export broken down by resource for 2026-04; 7/8 catalog resources have cost entries; `shared-nat` appears as a context cost |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |

## Cost summary (expected output)

| Resource | Type | Cost (2026-04) | Catalog match |
|----------|------|----------------|---------------|
| `orders-api` | Cloud Run | $680.42 | yes |
| `orders-worker` | Cloud Run | $420.17 | yes |
| `orders-prod-db` | Cloud SQL | $890.55 | yes |
| `orders-events` | GCS | $240.33 | yes |
| `orders-archives` | GCS | $185.09 | yes |
| `orders.events` | Pub/Sub | $310.74 | yes |
| `orders-fulfillment` | Cloud Tasks | $122.02 | yes |
| `orders-dev-db` | Cloud SQL | — (no billing row) | UNTRACED |
| `shared-nat` | Cloud NAT | $87.15 | CONTEXT COST (excluded) |

**Orders service total: $2,849.32** (7 catalog resources; `shared-nat` excluded).

Note: cost-by-label.json reports $2,847.32 for 2026-04. The ~$2 discrepancy reflects rounding in the BigQuery export aggregation vs. the per-resource sum; the skill notes this as "within export rounding tolerance" and uses the label-level total as the authoritative figure.
