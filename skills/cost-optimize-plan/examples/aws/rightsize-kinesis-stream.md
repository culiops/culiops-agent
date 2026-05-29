---
cloud: aws
action: rightsize
resource_type: kinesis-stream
applies_when: action == "rightsize" AND resource matches "arn:aws:kinesis:*:stream/*"
---

# Verify: Rightsize Kinesis Data Stream

Three composable rightsizing levers, all reversible: (a) reduce `OpenShardCount` (provisioned mode only), (b) reduce `RetentionPeriodHours`, (c) switch `StreamMode` between `PROVISIONED` and `ON_DEMAND`. EFO-consumer deregistration is covered in `delete-kinesis-stream.md` rollback section as a fourth lever (it shares the same activity-check pattern).

Each lever has independent thresholds, but they compose: a typical recommendation reduces shards first (cheapest, most reversible), then re-evaluates whether retention or mode switch are still warranted.

## Required IAM
- `kinesis:DescribeStreamSummary`
- `kinesis:ListShards`
- `kinesis:ListStreamConsumers`
- `cloudwatch:GetMetricStatistics`
- `pricing:GetProducts` (for the mode-switch cost-direction math)

## Queries

1. `aws kinesis describe-stream-summary --stream-name <name>` — captures `StreamMode` (`PROVISIONED` or `ON_DEMAND`), `OpenShardCount`, `RetentionPeriodHours`, `EnhancedMonitoring`.
2. `aws kinesis list-shards --stream-name <name> --query 'Shards[].[ShardId,SequenceNumberRange.EndingSequenceNumber]'` — closed-but-retained shards count toward retention storage but not active capacity.
3. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum,Maximum` — 14d producer activity, hourly p99 used for shard-sizing math.
4. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingBytes --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum,Maximum` — bytes-side activity (1 MB/s/shard is the hard limit).
5. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.Records --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum,Maximum` — consumer activity (2 MB/s/shard read limit).
6. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name WriteProvisionedThroughputExceeded --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — throttles → **🚫 trigger for shard-reduction**.
7. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name ReadProvisionedThroughputExceeded --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — read-side throttles → **🚫 trigger for shard-reduction**.
8. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.IteratorAgeMilliseconds --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 60 --extended-statistics p99` — high p99 iterator age indicates consumers reading old data. **🚫 trigger for retention reduction** if p99 age > 75% of current retention window.
9. `aws kinesis list-stream-consumers --stream-arn <arn>` — EFO consumers paying $0.015/consumer-shard-hour even at zero reads. Surfaced for the operator; deregistration handled in `delete-kinesis-stream.md` rollback ladder.

## Evidence thresholds — lever (a): reduce `OpenShardCount`

Applies only when `StreamMode == PROVISIONED`. Compute the minimum required shard count from p99 hourly bytes (1 MB/s/shard = 3.6 GB/hr/shard) and p99 hourly records (1000 records/s/shard = 3.6 M records/hr/shard).

| Signal | 🟢 Threshold (safe to reduce) | 🚫 Trigger (do not reduce) |
|--------|-------------------------------|-------------------------------|
| 14d p99 hourly `IncomingBytes` / `OpenShardCount` | ≤ 40% of 3.6 GB/hr/shard | ≥ 80% — at risk of write throttling |
| 14d p99 hourly `GetRecords.Records` / `OpenShardCount` / 2 | ≤ 40% of 3.6 M records/hr/shard (read limit is 2× write) | ≥ 80% — at risk of read throttling |
| 14d `WriteProvisionedThroughputExceeded` (Sum) | `0` | ≥ 1 — already throttling |
| 14d `ReadProvisionedThroughputExceeded` (Sum) | `0` | ≥ 1 |

Reducing shard count uses `aws kinesis update-shard-count --target-shard-count <N> --scaling-type UNIFORM_SCALING` — splits/merges shards; closed shards retain data for the retention window so consumer offsets are preserved.

## Evidence thresholds — lever (b): reduce `RetentionPeriodHours`

Extended retention costs apply above 24h: $0.02/shard-hour (provisioned) or per-GB (on-demand). Default 24h is free.

| Signal | 🟢 Threshold (safe to reduce) | 🚫 Trigger (do not reduce) |
|--------|-------------------------------|-------------------------------|
| 14d p99 `GetRecords.IteratorAgeMilliseconds` | ≤ 25% of current retention window (consumers far ahead) | ≥ 75% — consumers regularly read old data; reduction would drop in-flight records |
| Catalog-documented retention requirement (compliance, replay window) | none stricter than proposed | requires ≥ current retention — do not reduce |
| Backup / archive stream consuming this stream (Firehose → S3) | present and current per Firehose `DeliveryToS3.Success` ≥ 99% | absent or failing — retention is the only durability buffer; do not reduce |

**Critical:** `DecreaseStreamRetentionPeriod` immediately deletes records older than the new period. There is no undo. Confirm no downstream consumer needs the truncated history.

## Evidence thresholds — lever (c): switch `StreamMode` (Principle 2 cost-direction)

This is the textbook Principle 2 case. **Never assume direction.** One mode switch per 24h per stream.

Compute steps (mandatory before recommending the switch):

1. Sum 14d `IncomingBytes` per hour. Compute p99 and average.
2. Compute current cost for both modes at the observed throughput:
   - **Provisioned:** `shards × $0.015/hr × 730 + retention_hours_above_24 × shards × $0.02/hr × 730 + PUT_payload_units × $0.014/1M`
   - **On-demand:** `IncomingBytes_GB × $0.04 + GetRecords_GB × $0.04 + IncomingBytes_GB × records_per_GB × $0.0000001 + retention_GB_hours × $0.10`
3. Fetch pricing live via `aws pricing get-products --service-code AmazonKinesis` rather than hardcoding (regional variance).
4. Result must be `$X/mo current → $Y/mo proposed (Z% savings)` with input numbers cited.

| Workload shape (from Queries 3-5 over 14d) | Cheaper mode | Why |
|--------------------------------------------|--------------|-----|
| Steady high throughput (p99 / average bytes ratio ≤ 2.0, all shards utilized > 30%) | **provisioned** at rightsized count | On-demand's per-GB premium accumulates against the per-shard-hour cost. |
| Spiky (p99 / average > 5.0, sustained low baseline < 10% utilization) | **on-demand** | Provisioned ceiling paid 24/7 dominates; per-GB premium only applies during real spikes. |
| Predictable diurnal (p99 / average between 2–5) | recompute monthly | Marginal; small workload-shape changes flip direction. |

| Signal | 🟢 Threshold (safe to switch) | 🚫 Trigger (do not switch this mode) |
|--------|-------------------------------|---------------------------------------|
| Computed cost delta | ≥ 20% savings AND ≥ $25/mo absolute | < 20% savings OR computed cost INCREASES |
| Hours since last mode switch | ≥ 24 | < 24 — switch is rate-limited |
| Active producers / consumers writing on the old mode's idioms (e.g., bursting on provisioned, expecting shard-aware partitioning) | none broken | producer pinned to a specific shard via `ExplicitHashKey` — switch may disrupt routing semantics |

## Reversibility classification
- **Lever (a) shard count:** 🟢 reversible — `update-shard-count` reshards back. ~minutes.
- **Lever (b) retention reduction:** 🔴 — records older than new retention are immediately deleted, irrecoverable. Reversibility classifies the **action**, not the parameter; this lever is 🔴 even though the parameter can be re-raised.
- **Lever (c) mode switch:** 🟡 — fully reversible but rate-limited to one switch per 24h. Rollback waits.

**Default for the composed playbook:** 🟡 — the playbook's reversibility is the most restrictive lever in the operator's chosen set. If only lever (a) is proposed: 🟢. If lever (b) is included: 🔴. If only lever (c): 🟡.

## Blast radius classification
- **Default:** 🟡 — touches a live stream with consumers. Bump to 🟢 only if no Lambda mappings AND no EFO consumers AND no Firehose sources (per the `delete-kinesis-stream.md` attachment queries). Bump to 🔴 if any consumer is a critical-path service per catalog OR if Firehose-to-S3 archival depends on the current retention window for replay SLA.

## Rollback note (informational, shown in plan)

"Per-lever rollback:
- **Shard count:** `aws kinesis update-shard-count --target-shard-count <original> --scaling-type UNIFORM_SCALING`. Takes minutes; consumer offsets preserved via shard close/open semantics.
- **Retention:** `aws kinesis increase-stream-retention-period --retention-period-hours <original>` — but records deleted during the reduction window are NOT restored. There is no records-side undo.
- **Mode switch:** `aws kinesis update-stream-mode --stream-arn <arn> --stream-mode-details StreamMode=<original>`. Must wait 24h since last switch.

**Principle 2 reminder:** the cost-direction math in lever (c) is computed against current pricing × observed utilization. If either changes materially (regional repricing, workload shape shift), rerun the math before reapplying any mode change. The cheaper mode flips; the operator should set a calendar reminder to recompute quarterly if the workload is in the marginal band (p99/avg ratio 2–5)."
