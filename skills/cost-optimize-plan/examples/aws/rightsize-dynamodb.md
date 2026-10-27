---
cloud: aws
action: rightsize
resource_type: dynamodb-table
applies_when: action == "rightsize" AND resource matches "arn:aws:dynamodb:*:table/*"
---

# Verify: Rightsize DynamoDB table

Covers two distinct rightsizing levers, which compose: (a) reduce provisioned capacity (provisioned mode), and (b) switch billing mode between provisioned and on-demand. Both are reversible; mode switch is rate-limited (provisioned → on-demand: up to four per rolling 24 h; on-demand → provisioned: any time; docs: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-switching-capacity-modes.html, re-read before relying).

## Required IAM
- `dynamodb:DescribeTable`
- `dynamodb:DescribeTimeToLive`
- `application-autoscaling:DescribeScalingPolicies` (if autoscaling configured on provisioned tables)
- `cloudwatch:GetMetricData`
- `pricing:GetProducts` (fallback for the Principle 2 cost-direction check when the bill-derived rate is unavailable)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. `cloudformation` → ❔ `unsupported-owner`. `terraform`: cite `code:<path:line>`; if the resource has `lifecycle { ignore_changes = [read_capacity, write_capacity] }` (typical with autoscaling), a direct capacity change is reverted/ignored — the lever is the autoscaling target's min/max (`aws_appautoscaling_target`). `unmanaged` → "re-apply old IaC" rollback unavailable.
1. `aws dynamodb describe-table --table-name <name>` — captures `BillingModeSummary.BillingMode` (`PAY_PER_REQUEST`; **absent** on a table that has always been provisioned, in which case `ProvisionedThroughput.ReadCapacityUnits > 0` means provisioned), `ProvisionedThroughput.{Read,Write}CapacityUnits`, `TableSizeBytes`, `ItemCount`, `GlobalSecondaryIndexes[]` (GSI capacities are separate cost lines), `TableClassSummary`.
2. **30d trend, hourly (one call; 720 points per query, under the 1,440 cap).** Dimension `TableName`; for a GSI add `{"Name":"GlobalSecondaryIndexName","Value":"<gsi>"}` to the dimensions:

   ```
   aws cloudwatch get-metric-data --start-time <now-30d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
   {"Id":"rcu_h","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ConsumedReadCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
   {"Id":"wcu_h","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ConsumedWriteCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
   {"Id":"prov_r","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ProvisionedReadCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Average"}},
   {"Id":"prov_w","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ProvisionedWriteCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Average"}},
   {"Id":"rthr","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ReadThrottleEvents","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
   {"Id":"wthr","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"WriteThrottleEvents","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}}]'
   ```

   **Unit conversion (mandatory):** `Consumed*CapacityUnits` `Sum` over a period is the *total* units consumed in that period, while provisioned capacity is *per second*. Average consumed CU/s = `Sum / period_seconds` (÷ 3600 for hourly). Compare that figure with provisioned CU, never the raw `Sum`. `Provisioned*CapacityUnits` exist only for provisioned tables.
3. **Burst view, per-minute, last ≤ 15d (one call per table/GSI).** An hourly average hides per-second bursts that throttle; 1-minute data is retained only 15 days, so this window is capped at 15d. 15d × 1,440 = 21,600 points per metric exceeds the `get-metric-statistics` cap (1,440), so use `get-metric-data` (limit 100,800 points/call), or `get-metric-statistics` in ≤ 1-day chunks:

   ```
   aws cloudwatch get-metric-data --start-time <now-15d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
   {"Id":"rcu_m","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ConsumedReadCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":60,"Stat":"Sum"}},
   {"Id":"wcu_m","MetricStat":{"Metric":{"Namespace":"AWS/DynamoDB","MetricName":"ConsumedWriteCapacityUnits","Dimensions":[{"Name":"TableName","Value":"<name>"}]},"Period":60,"Stat":"Sum"}}]'
   ```

   Peak consumed CU/s = `max(Sum / 60)` over the series. DynamoDB can absorb short bursts from up to ~5 minutes of retained unused capacity (verify), so per-minute is a fair proxy, but sub-minute spikes can still throttle — the throttle rows below are the ground truth.
4. For each GSI in Query 1: repeat Queries 2–3 with the GSI dimension — GSIs are billed independently, and a throttling GSI throttles table writes.
5. (Optional) `aws application-autoscaling describe-scaling-policies --service-namespace dynamodb --resource-id table/<name>` — if autoscaling is on, the min/max and target utilization are the cost lever, not the static capacity.

## Evidence thresholds

Thresholds are defaults. "Req" = required: ⚪ on a required row forces Evidence ⚪ → 🔴. Applies per table and per GSI.

| Signal | Req | 🟢 Threshold (safe to rightsize) | 🚫 Trigger (do not rightsize) |
|--------|-----|--------------------------------|--------------------------------|
| 30d hourly p99 of (`ConsumedReadCapacityUnits` Sum ÷ 3600) ÷ same-hour `ProvisionedReadCapacityUnits` | required | ≤ 40% — over-provisioned | ≥ 80% sustained — rightsize-down would cause throttling |
| 30d hourly p99 of (`ConsumedWriteCapacityUnits` Sum ÷ 3600) ÷ same-hour `ProvisionedWriteCapacityUnits` | required | ≤ 40% | ≥ 80% sustained |
| 15d per-minute peak read CU/s (Query 3) ÷ **proposed** read capacity | required | ≤ 80% | > 100% — the proposed capacity would throttle at observed bursts |
| 15d per-minute peak write CU/s ÷ **proposed** write capacity | required | ≤ 80% | > 100% |
| 30d `ReadThrottleEvents` (Sum) | required | `0` | ≥ 1 — already under-provisioned, downsize would worsen |
| 30d `WriteThrottleEvents` (Sum) | required | `0` | ≥ 1 |
| Per-GSI capacity utilization | required per GSI | each GSI scored independently per rows above | any GSI throttling → 🚫 |
| TTL configured if table has time-bounded data (per catalog) | optional | configured | not configured AND table size growing > 10%/month — flag for retention review before rightsize |

For the capacity-reduction lever: between 40% and 80% on a required utilization row, the row is ⚪ `marginal`: the downsize isn't supported by the evidence (Evidence ⚪ → 🔴). Record the measured headroom so the owner can decide.

## Principle 2 — cost-direction check (mandatory for mode switches)

This playbook's **most common trap**. Switching `PROVISIONED` ↔ `PAY_PER_REQUEST` is rate-limited (see the limits at the top of this playbook) and the cheaper mode flips with workload shape. Compute, do not assume. The cost-direction result is a **cost result, not an activity signal**: it never scores Evidence 🚫. A failed check means the lever is not proposed: the item goes to 🚫 only if this is the lever the upstream report recommends (SKILL tier rule 1); otherwise the lever is dropped and recorded in Gaps.

| Workload shape | Cheaper mode | Why |
|---|---|---|
| Steady throughput, predictable, well-utilized | **provisioned** at right-sized capacity | On-demand carries a per-request premium over well-utilized provisioned capacity; the size of the premium comes from the bill / Pricing API, not memory. |
| Spiky, low-baseline (idle hours) | **on-demand** | Paying for a provisioned ceiling 24/7 can exceed the per-request premium paid only during spikes. |
| Highly variable, peak ≫ 4× average | **on-demand** OR provisioned-with-autoscaling | Static provisioned at peak wastes; static at average throttles. |

Compute steps before recommending a mode switch:

1. Sum 30d `Consumed{Read,Write}CapacityUnits` (table + all GSIs). In on-demand billing the same quantity is the request units billed, so total units = request units.
2. On-demand cost ≈ `(read_units / 1e6) × read_request_unit_rate + (write_units / 1e6) × write_request_unit_rate`.
3. Provisioned cost ≈ `provisioned_RCU × rcu_hour_rate × hours + provisioned_WCU × wcu_hour_rate × hours` (autoscaling: floor × hours-at-floor + scaled portions, from the hourly `Provisioned*` series).
4. Rate variables: **bill-derived** (Principle 4: usage quantity ÷ line-item cost) first; otherwise the Pricing API for the region (`AmazonDynamoDB`). Never hardcode; label list-price fallbacks. If the provisioned capacity is covered by reserved capacity, the realizable saving is ~0 until it ends.
5. Include GSI capacities on both sides.
6. Result must be expressed as `$X/mo current → $Y/mo proposed (Z% savings)` with the input numbers cited. **A bare "switch to on-demand to save" is rejected by this playbook** (lever not proposed).

## Reversibility classification
- **Default:** 🟢 reversible when Ownership is `terraform`. Capacity changes apply within minutes; mode switches within minutes (rate-limited). Re-apply old IaC restores. `unmanaged` → 🟡 (manual update-table back; no IaC).
- **Caveat:** a switch to on-demand is rate-limited; a switch back to provisioned is not (docs link at the top). Surface this in the rollback note.

## Blast radius classification
- **Default:** 🟢 — capacity changes are transparent to consumers if rightsized correctly. Bump to 🟡 if throttle thresholds are within 20% (close call; a bad rightsize would cascade to consumer 5XX). Bump to 🔴 if the table is referenced by ≥ 3 services per catalog (production-critical shared table).

## Rollback note (informational, shown in plan)
"Re-apply old IaC (`unmanaged`: `update-table` back to the old capacity/mode). Capacity changes take effect within minutes. **Mode switch (provisioned ↔ on-demand) is rate-limited** — a switch to on-demand counts against the documented limit (a switch back to provisioned does not). Pre-rightsize: ensure point-in-time recovery (PITR) is enabled or take an on-demand backup (`aws dynamodb create-backup`). **Principle 2 reminder:** the cost-direction math in this playbook is computed against bill-derived rates × observed utilization; if either changes materially (price change, traffic pattern shift), rerun the math before reapplying any mode change."
