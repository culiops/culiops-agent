# attribution-aws-orders - cloud-cost-investigate fixture

Attribution-mode fixture exercising catalog consumption, untraced-resource flagging, context-cost flagging and a period comparison for an AWS service. Port of the retired GCP fixture; same scenarios, AWS data model.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`, a member account of an AWS Organization) running an `orders` service in `us-east-1`. The service catalog (`.culiops/service-discovery/orders.md`) lists 8 resources: two ECS Fargate services, two RDS instances, two S3 buckets, one SQS queue and one Step Functions state machine. Every resource carries the cost-allocation tags `Service=orders` and `Component=<catalog name>`.

- `orders-dev-db` is in the catalog (built from Terraform) but was deleted out-of-band on 2026-03-14: it has a partial-month cost row in 2026-03 and **no cost row in 2026-04**.
- A shared NAT gateway (`Component=shared-nat`) is stamped `Service=orders` by a VPC module's `default_tags`, so it appears in the `Service=orders` cost view but is **not in the catalog**. It also serves the payments and inventory services.

## The operator question

> "What does the orders service cost us per month? Break it down by resource."

(See `operator-question.md`.)

## Where the numbers come from (read this before judging the fixture)

Cost Explorer `get-cost-and-usage` with `MONTHLY` granularity is **not per-resource**. `get-cost-and-usage-with-resources` is per-resource but covers only the last 14 days and needs an opt-in, so it cannot answer "April, by resource". The fixture therefore gets per-resource numbers the way a real account does: through the activated cost-allocation tag `Component`, whose values are the catalog resource names.

- `cost-by-usage-type.json`: filter `Service=orders` AND `RECORD_TYPE` in the three usage record types (`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`), `MONTHLY`, 2026-03-01 to 2026-05-01, grouped by `USAGE_TYPE` (metrics `AmortizedCost`, `UsageQuantity`). Authoritative service-level totals, no resource information.
- `cost-by-tag.json`: same filter and window, grouped by `TAG:Component` x `USAGE_TYPE`. Per-resource, per-usage-type cells for both months.
- Both files are built from the same cells, so they reconcile to the cent: $2,698.96 in 2026-04 and $2,478.96 in 2026-03 (service + shared NAT).
- Amounts are rounded to cents per line item; sums are exact, no "rounding tolerance" is needed.
- Commitments: no commitment applies to these services (the account's only Savings Plan is an EC2 Instance plan on m5), so `AmortizedCost` equals `UnblendedCost` here and the covered record types return no rows. The numbers would still be right under a commitment, because covered usage is included at its effective rate.

## What this fixture exercises

- **Mode detection from question phrasing:** "what does X cost / break it down by resource" gives attribution mode (suggested at GATE 1).
- **Scoping probe (GATE 1a):** identity, alias, `organizations describe-organization` (member account, so no `LINKED_ACCOUNT` filter), CE by `REGION` filtered to the tag. Regions covered: us-east-1 (100% of `Service=orders` spend).
- **Catalog consumption:** attribution mode requires a catalog or an operator-confirmed tag convention. The catalog is present and also records the tag convention.
- **Untraced resource:** `orders-dev-db` is in the catalog and has no 2026-04 cost row. The skill flags it `untraced` and does NOT claim $0 (absence of a row is not confirmed zero spend). The 2026-03 row ($27.60, partial month) is consistent with a mid-March deletion, but nothing here proves it; verification (`rds describe-db-instances`, CloudTrail `DeleteDBInstance`) is a GATE 3 option the operator declines.
- **Context cost:** `shared-nat` ($115.65 in 2026-04) is billed under `Service=orders` but matches no catalog resource. Flagged `context cost` and EXCLUDED from the service total.
- **Tag activation (E6):** `tag-activation.json` shows `Service` and `Component` active since 2025-11-18, before the comparison window, so the tag-based per-resource figures and the March-to-April trend stay verified. Had a key been activated inside the window, the earlier month would read as empty and the trend would be `UNVERIFIED`.
- **Period comparison:** 2026-03 vs 2026-04 service total +9.0% month over month ($2,368.98 to $2,583.31). Because the tag view exists for both months, the skill can name the contributors (the worker fleet), which the GCP fixture could not.
- **Hours effect:** March has 744 hours and April 720; hour-based lines (RDS, NAT) fall in April on that alone.
- **Resource-level API not used:** the skill states why `get-cost-and-usage-with-resources` is not used (window longer than 14 days).
- **Remediation table stays empty:** attribution mode makes no savings claim. Untraced and context items go to `## Untraced / context`, not the remediation table (Constraint 7).

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `.culiops/service-discovery/orders.md` | Mock service-discovery catalog (8 AWS resources + tag convention) |
| `cost-by-usage-type.json` | CE `get-cost-and-usage` filtered `Service=orders` + the three usage record types, MONTHLY, `AmortizedCost`, grouped by `USAGE_TYPE`, 2026-03 and 2026-04 |
| `cost-by-tag.json` | Same filter, grouped by `TAG:Component` x `USAGE_TYPE`; the only source of per-resource numbers |
| `tag-activation.json` | Query 7: `ce list-cost-allocation-tags` for `Service` and `Component` (status and `LastUpdatedDate`) |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |

## Cost summary (expected output, 2026-04)

| # | Resource | Type | Cost 2026-04 | % of service | Cost 2026-03 | MoM delta |
|---|----------|------|--------------|--------------|--------------|-----------|
| 1 | `orders-prod-db` | RDS PostgreSQL (Multi-AZ) | $922.70 | 35.7% | $939.24 | -$16.54 |
| 2 | `orders-api` | ECS Fargate service | $676.74 | 26.2% | $611.44 | +$65.30 |
| 3 | `orders-worker` | ECS Fargate service | $355.47 | 13.8% | $220.38 | +$135.09 |
| 4 | `orders-events-queue` | SQS queue | $180.00 | 7.0% | $152.00 | +$28.00 |
| 5 | `orders-events` | S3 bucket | $164.00 | 6.3% | $155.90 | +$8.10 |
| 6 | `orders-fulfillment` | Step Functions state machine | $150.00 | 5.8% | $135.00 | +$15.00 |
| 7 | `orders-archives` | S3 bucket | $134.40 | 5.2% | $127.42 | +$6.98 |
| - | `orders-dev-db` | RDS PostgreSQL | UNTRACED (no 2026-04 row) | - | $27.60 (partial) | -$27.60 |
| - | `shared-nat` | NAT gateway | $115.65 | CONTEXT COST (excluded) | $109.98 | excluded |

**Orders service total, 2026-04: $2,583.31** (7 traced catalog resources; `shared-nat` excluded; `orders-dev-db` untraced, not counted as $0).
**2026-03: $2,368.98** (includes `orders-dev-db` $27.60). Delta +$214.33, +9.0%. Like-for-like excluding the deleted dev DB: $2,341.38 to $2,583.31, +10.3%.

Reconciliation: `cost-by-usage-type.json` April sum $2,698.96 = `cost-by-tag.json` April sum $2,698.96 = service $2,583.31 + context $115.65. March: $2,478.96 = $2,368.98 + $109.98.
