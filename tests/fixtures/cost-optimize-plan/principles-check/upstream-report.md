**Cloud cost investigation**
**Mode:** waste
**Scope:** 123456789012 / acme-prod (single)
**Time range:** 2026-04-29 → 2026-05-29
**Catalog used:** none
**Date:** 2026-05-29 14:30
**Cloud:** aws

## Question

Run a waste audit on our AWS prod account (ap-southeast-1). We added v0.9 principle guardrails this week — surface candidates that would be flagged differently under the new rules (activity ≠ attachment, verify cost-change direction).

## Scoping decisions

- Mode: waste.
- Scope: account 123456789012 (acme-prod), single account, region ap-southeast-1.
- Time range: 30d rolling (2026-04-29 → 2026-05-29).
- Savings floor: $5/mo.
- Untagged spend: not flagged.

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | lambda:ListFunctions | ap-southeast-1 | lambda:ListFunctions | ok | 14 functions enumerated |
| 2 | cloudwatch:GetMetricStatistics (Lambda.Invocations, 30d) | per-function | cloudwatch:GetMetricStatistics | ok | cron-backfill-2024: 0 invocations |
| 3 | lambda:ListEventSourceMappings | per-function | lambda:ListEventSourceMappings | ok | cron-backfill-2024: 0 mappings — uses EventBridge rules not event source mappings (out of waste-audit scope) |
| 4 | dynamodb:DescribeTable | per-table | dynamodb:DescribeTable | ok | orders-canonical: PROVISIONED mode, 200 RCU / 100 WCU |
| 5 | cloudwatch:GetMetricStatistics (DynamoDB.ConsumedReadCapacityUnits + ConsumedWriteCapacityUnits, 14d hourly) | per-table | cloudwatch:GetMetricStatistics | ok | orders-canonical: steady ~70% utilization, p99/avg ratio ≈ 1.6 |

## Findings

### 1. Idle Lambda function with provisioned concurrency

`cron-backfill-2024` has zero invocations in 30d but accrues $35/mo from configured provisioned concurrency (2 units). The function code is committed to IaC (terraform/lambda/cron-backfill-2024). **Activity-unverified flag NOT applicable here** — Invocations metric is the activity dimension and it shows zero. However, the function is referenced by 2 EventBridge rules (`legacy-backfill-daily-cron`, `legacy-backfill-weekly-cleanup`) per a separate `events:ListRules` sweep below — these are **attachment** signals, not activity. Per Principle 1, attachment alone does not promote the function to in-use.

### 2. Over-provisioned DynamoDB table — mode-switch savings claim

`orders-canonical` is a 200 RCU / 100 WCU PROVISIONED-mode table at ~70% sustained utilization. AWS Compute-Optimizer-DynamoDB (preview) suggested switching to PAY_PER_REQUEST for "simplified billing and elastic capacity," labeled $80/mo savings. **Per Principle 2, this savings claim is `direction-unverified`** until the cost delta is computed from observed throughput × real pricing for both modes. Recomputation downstream (cost-optimize-plan playbook) is required before promoting to actionable.

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Delete Lambda function cron-backfill-2024 | arn:aws:lambda:ap-southeast-1:123456789012:function:cron-backfill-2024 | $35/mo | line-item-computation | medium | 0 Invocations in 30d per CloudWatch; $35/mo entirely from provisioned-concurrency (2 units) |
| 2 | Switch DynamoDB orders-canonical to on-demand mode | arn:aws:dynamodb:ap-southeast-1:123456789012:table/orders-canonical | $80/mo | compute-optimizer-preview | **low (direction-unverified)** | Compute Optimizer DynamoDB preview suggests on-demand for "elastic capacity"; **cost-delta math not yet computed against observed throughput** |

**Total estimated savings:** $115/mo combined ($35 medium + $80 low/unverified — verify before relying on item #2)

## Gaps

- Item #2 savings claim is `direction-unverified` per Principle 2 — downstream `cost-optimize-plan` will recompute before promoting to any actionable tier.
- EventBridge rule sweep for item #1 not performed in this batch (operator declined drill-down to keep API costs bounded); deferred to cost-optimize-plan's playbook verification step.

## Next steps (informational)

- Run `cost-optimize-plan` on this report. Item #1 should land 🟡 Coordinated (EventBridge attachment is blast-radius, not activity). Item #2 should land in 🚫 Do not act if recomputation confirms on-demand would cost MORE at steady ~70% utilization, with a sibling recommendation to instead reduce provisioned capacity by ~30%.
