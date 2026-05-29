---
cloud: aws
action: rightsize
resource_type: dynamodb-table
applies_when: action == "rightsize" AND resource matches "arn:aws:dynamodb:*:table/*"
---

# Verify: Rightsize DynamoDB table

Covers two distinct rightsizing levers, which compose: (a) reduce provisioned capacity (provisioned mode), and (b) switch billing mode between provisioned and on-demand. Both are reversible; mode switch is rate-limited to one per 24 hours per table.

## Required IAM
- `dynamodb:DescribeTable`
- `dynamodb:DescribeTimeToLive`
- `application-autoscaling:DescribeScalingPolicies` (if autoscaling configured on provisioned tables)
- `cloudwatch:GetMetricStatistics`
- `pricing:GetProducts` (optional, for live pricing lookup — see Principle 2 cost-direction check)

## Queries

1. `aws dynamodb describe-table --table-name <name>` — captures `BillingMode` (`PROVISIONED` or `PAY_PER_REQUEST`), `ProvisionedThroughput.{Read,Write}CapacityUnits` (provisioned mode only), `TableSizeBytes`, `ItemCount`, `GlobalSecondaryIndexes[]` (GSI capacities are separate cost lines).
2. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedReadCapacityUnits --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum,Maximum` — 14d hourly consumed RCU. **Activity signal.**
3. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedWriteCapacityUnits --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum,Maximum` — 14d hourly consumed WCU.
4. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ProvisionedReadCapacityUnits --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Average,Maximum` — confirms current provisioned ceiling per hour (autoscaling-aware).
5. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ProvisionedWriteCapacityUnits --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Average,Maximum`
6. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ReadThrottleEvents --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — throttles indicate under-provisioning; do NOT shrink a table that's throttling.
7. `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name WriteThrottleEvents --dimensions Name=TableName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum`
8. For each GSI in Query 1: repeat Queries 2–7 with `Name=GlobalSecondaryIndexName,Value=<gsi>` — GSIs are billed independently.
9. (Optional) `aws application-autoscaling describe-scaling-policies --service-namespace dynamodb --resource-id table/<name>` — if autoscaling is on, the "provisioned" floor/ceiling is the cost lever, not the static capacity.

## Evidence thresholds

| Signal | 🟢 Threshold (safe to rightsize) | 🚫 Trigger (do not rightsize) |
|--------|--------------------------------|--------------------------------|
| 14d hourly p99 `ConsumedReadCapacityUnits` / `ProvisionedReadCapacityUnits` | ≤ 40% — over-provisioned | ≥ 80% sustained — at risk; rightsize-down would cause throttling |
| 14d hourly p99 `ConsumedWriteCapacityUnits` / `ProvisionedWriteCapacityUnits` | ≤ 40% | ≥ 80% sustained |
| 14d `ReadThrottleEvents` (Sum) | `0` | ≥ 1 — already under-provisioned, downsize would worsen |
| 14d `WriteThrottleEvents` (Sum) | `0` | ≥ 1 |
| Per-GSI capacity utilization | each GSI scored independently per rows above | any GSI throttling → 🚫 |
| TTL configured if table has time-bounded data (per catalog) | configured | not configured AND table size growing > 10%/month — flag for retention review before rightsize |

## Principle 2 — cost-direction check (mandatory for mode switches)

This playbook's **most common trap**. Switching `PROVISIONED` ↔ `PAY_PER_REQUEST` is one switch per 24h per table and the cheaper mode flips with workload shape. Compute, do not assume.

| Workload shape | Cheaper mode | Why |
|---|---|---|
| Steady throughput, predictable | **provisioned** at right-sized capacity | On-demand carries ~7× per-request premium vs reserved capacity. |
| Spiky, low-baseline (idle hours) | **on-demand** | Paying for provisioned ceiling 24/7 even at 0 traffic is worse than per-request premium during spikes. |
| Highly variable, peak ≫ 4× average | **on-demand** OR provisioned-with-autoscaling | Static provisioned at peak wastes; static at average throttles. |

Compute steps before recommending a mode switch:

1. Sum 14d `Consumed{Read,Write}CapacityUnits` per hour, including all GSIs.
2. Multiply by current region's on-demand request pricing (per million requests; $1.25 read / $6.25 write US East at time of writing — **fetch live via `aws pricing get-products` rather than hardcoding**).
3. Compare to current provisioned monthly cost: `provisioned_capacity × $0.00013 read-RCU-hour × 730 + same for write` (or autoscaling-floor × hours-at-floor + scaled-portions).
4. Include GSI capacities in both sides of the equation.
5. Result must be expressed as `$X/mo current → $Y/mo proposed (Z% savings)` with the input numbers cited. **Bare "switch to on-demand to save" is a 🚫 from this playbook.**

## Reversibility classification
- **Default:** 🟢 reversible. Capacity changes apply immediately; mode switches apply within minutes (one per 24h limit). Re-apply old IaC restores.
- **Caveat:** mode switch is rate-limited. If a switch is reversed within 24h, the rollback waits for the 24h window. Surface this in rollback note.

## Blast radius classification
- **Default:** 🟢 — capacity changes are transparent to consumers if rightsized correctly. Bump to 🟡 if 🚫 throttle thresholds are within 20% (close call; bad rightsize would cascade to consumer 5XX). Bump to 🔴 if the table is referenced by ≥ 3 services per catalog (production-critical shared table).

## Rollback note (informational, shown in plan)
"Re-apply old IaC. Capacity changes take effect within minutes. **Mode switch (provisioned ↔ on-demand) is rate-limited to one switch per 24h** — a rollback of a mode switch must wait. Pre-rightsize: snapshot via point-in-time recovery (PITR) if not already enabled, or take an on-demand backup (`aws dynamodb create-backup`). **Principle 2 reminder:** the cost-direction math in this playbook is computed against current pricing × observed utilization; if either changes materially (region price update, traffic pattern shift), rerun the math before reapplying any mode change."
