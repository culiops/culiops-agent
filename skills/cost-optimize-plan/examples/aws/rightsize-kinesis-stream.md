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
- `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData` (Query 8)
- `pricing:GetProducts` (fallback for the mode-switch cost-direction math when the bill-derived rate is unavailable)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. `cloudformation` owner → ❔ `unsupported-owner`. If Ownership is `terraform`, make the change in IaC (cite `code:<path:line>`), not via the CLI shown in the rollback note, or the next apply reverts it; `unmanaged` → "re-apply old IaC" is unavailable and the CLI commands are the rollback.
1. `aws kinesis describe-stream-summary --stream-name <name>` — captures `StreamMode` (`PROVISIONED` or `ON_DEMAND`), `OpenShardCount`, `RetentionPeriodHours`, `EnhancedMonitoring`.
2. `aws kinesis list-shards --stream-name <name> --query 'Shards[].[ShardId,SequenceNumberRange.EndingSequenceNumber]'` — closed-but-retained shards count toward retention storage but not active capacity.
3. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --statistics Sum,Maximum` — 30d producer activity (720 hourly points, under the 1,440 cap). The hourly p99 used for shard-sizing is computed client-side from the hourly `Sum` values; `Maximum` is the peak 1-minute sum inside each hour (burst check: `Maximum / 60` per second vs the per-shard limit).
4. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingBytes --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --statistics Sum,Maximum` — bytes-side activity (1 MB/s/shard is the hard limit).
5. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.Records --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --statistics Sum,Maximum` — consumer activity.
   Also fetch `--metric-name GetRecords.Bytes` with the same shape: the 2 MB/s/shard read limit is a bandwidth limit, so bytes (not record count) is the read-side sizing signal.
6. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name WriteProvisionedThroughputExceeded --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --statistics Sum` — throttles → **🚫 trigger for shard-reduction**.
7. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name ReadProvisionedThroughputExceeded --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --statistics Sum` — read-side throttles → **🚫 trigger for shard-reduction**.
8. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.IteratorAgeMilliseconds --dimensions Name=StreamName,Value=<name> --start-time <now-30d> --end-time <now> --period 3600 --extended-statistics p99` — high p99 iterator age indicates consumers reading old data. **🚫 trigger for retention reduction** if p99 age > 75% of current retention window.
   **Period choice:** 3600s over 30d (720 points). A 60s period is not usable for 30d: 1-minute data is retained only 15 days and 43,200 points exceeds the 1,440 `get-metric-statistics` cap (would need ≤ 1-day chunks over ≤ 15d). Hourly p99 is sufficient because the thresholds are percentages of the retention window (hours), and it keeps the full 30d resize window (Principle 3). Percentiles go in `--extended-statistics` — it cannot be combined with `--statistics` in one call (CLI help). If p99 is not published for this metric (verify), fall back to hourly `Maximum` and take the 99th percentile of the hourly maxima client-side (conservative).
9. `aws kinesis list-stream-consumers --stream-arn <arn>` — EFO consumers accrue `efo_consumer_shard_hour_rate` per consumer-shard-hour even at zero reads. **Attachment** (Blast input), not activity. Surfaced for the operator; deregistration handled in the `delete-kinesis-stream.md` rollback ladder.

## Evidence thresholds — lever (a): reduce `OpenShardCount`

Applies only when `StreamMode == PROVISIONED`. Compute the minimum required shard count from p99 hourly write bytes (1 MB/s/shard = 3.6 GB/hr/shard), p99 hourly write records (1000 records/s/shard = 3.6 M records/hr/shard) and p99 hourly read bytes (2 MB/s/shard = 7.2 GB/hr/shard).

| Signal | Req | 🟢 Threshold (safe to reduce) | 🚫 Trigger (do not reduce) |
|--------|-----|-------------------------------|-------------------------------|
| 30d p99 hourly `IncomingBytes` / `OpenShardCount` | required | ≤ 40% of 3.6 GB/hr/shard | ≥ 80% — at risk of write throttling |
| 30d p99 hourly `IncomingRecords` / `OpenShardCount` | required | ≤ 40% of 3.6 M records/hr/shard | ≥ 80% |
| 30d p99 hourly `GetRecords.Bytes` / `OpenShardCount` | required | ≤ 40% of 7.2 GB/hr/shard | ≥ 80% — at risk of read throttling |
| 30d `WriteProvisionedThroughputExceeded` (Sum) | required | `0` | ≥ 1 — already throttling |
| 30d `ReadProvisionedThroughputExceeded` (Sum) | required | `0` | ≥ 1 |

Reducing shard count uses `aws kinesis update-shard-count --target-shard-count <N> --scaling-type UNIFORM_SCALING` — splits/merges shards; closed shards retain data for the retention window so consumer offsets are preserved.

**Mechanical execution limit (surface during triage).** `UpdateShardCount` cannot drop below half the current open shard count per call. A large reduction is therefore staged over multiple rounds — e.g. 8 → 1 shard is four halvings (8→4→2→1), not one step, each round settling before the next. Note the staging (rounds + per-round ×0.5 limit) in the item's execution/rollback note so the rollout shape is known before `iac-change-execution` runs it.

## Evidence thresholds — lever (b): reduce `RetentionPeriodHours`

Retention above the 24h default is billed (provisioned: `extended_retention_shard_hour_rate` per shard-hour; on-demand: per GB-month). Rates: bill-derived (Principle 4) or Pricing API for the region.

| Signal | Req | 🟢 Threshold (safe to reduce) | 🚫 Trigger (do not reduce) |
|--------|-----|-------------------------------|-------------------------------|
| 30d p99 `GetRecords.IteratorAgeMilliseconds` (Query 8) | required | ≤ 25% of current retention window (consumers far ahead) | ≥ 75% — consumers regularly read old data; reduction would drop in-flight records |

**Attachment / constraints for lever (b)** (never 🚫 — Principle 1):

| Signal | Query | Effect |
|--------|-------|--------|
| Catalog-documented retention requirement (compliance, replay window) | catalog | requires ≥ current retention → lever (b) is not proposed |
| Firehose → S3 archive consuming this stream | `delete-kinesis-stream.md` Query 7; Firehose `DeliveryToS3.Success` | absent or failing → lever (b) not proposed (retention is the only durability buffer); present and replay SLA depends on it → Blast 🔴 |

**Critical:** `DecreaseStreamRetentionPeriod` immediately deletes records older than the new period. There is no undo. Confirm no downstream consumer needs the truncated history.

## Evidence thresholds — lever (c): switch `StreamMode` (Principle 2 cost-direction)

This is the textbook Principle 2 case. **Never assume direction.** One mode switch per 24h per stream.

Compute steps (mandatory before recommending the switch):

1. Sum 30d `IncomingBytes` per hour. Compute p99 and average.
2. Compute current cost for both modes at the observed throughput:
   - **Provisioned:** `OpenShards × shard_hour_rate × 730 + (retention > 24h ? OpenShards × extended_retention_shard_hour_rate × 730 : 0) + PUT_payload_units × put_payload_unit_rate` (PUT payload units are 25 KB each) `+ EFO consumer-shard-hours × efo_consumer_shard_hour_rate + EFO_GB × efo_retrieval_gb_rate`
   - **On-demand:** `730 × stream_hour_rate + IncomingBytes_GB × ingest_gb_rate + GetRecords_GB × retrieval_gb_rate + extended_retention_GB_months × retention_gb_month_rate + EFO_GB × efo_retrieval_gb_rate`
3. Rate variables: **bill-derived** (Principle 4: usage quantity ÷ line-item cost from the bill) first; otherwise the Pricing API for the region (`aws pricing get-products --service-code AmazonKinesis`). Never hardcode; label list-price fallbacks as such. Check commitment coverage (a covered line saves ~$0 until the commitment ends).
4. Result must be `$X/mo current → $Y/mo proposed (Z% savings)` with input numbers cited. Show the transition path (on-demand → provisioned inherits a high shard count and costs more until stepped down; Principle 2).

| Workload shape (from Queries 3-5 over 30d) | Cheaper mode | Why |
|--------------------------------------------|--------------|-----|
| Steady high throughput (p99 / average bytes ratio ≤ 2.0, all shards utilized > 30%) | **provisioned** at rightsized count | On-demand's per-GB premium accumulates against the per-shard-hour cost. |
| Spiky (p99 / average > 5.0, sustained low baseline < 10% utilization) | **on-demand** | Provisioned ceiling paid 24/7 dominates; per-GB premium only applies during real spikes. |
| Predictable diurnal (p99 / average between 2–5) | recompute monthly | Marginal; small workload-shape changes flip direction. |

**Cost-direction gate (Principle 2 — a cost result, not an activity signal, so it never produces 🚫):**

| Gate | Req | Pass | Fail |
|------|-----|------|------|
| Computed cost delta (realizable, after commitment coverage) | required | ≥ 20% savings AND ≥ $25/mo absolute (materiality threshold) | lever (c) not proposed; record the computed numbers in Gaps. If the upstream item *is* the mode switch → 🚫 via SKILL tier rule 1 |
| Workload-shape data (Queries 3–5) | required | all three queries succeeded | ⚪ → Evidence ⚪ → 🔴 |

**Attachment / constraints for lever (c)** (never 🚫):

| Signal | Query | Effect |
|--------|-------|--------|
| Hours since last mode switch (CloudTrail `UpdateStreamMode`, management event, 90d) | `cloudtrail lookup-events` | < 24 → defer the switch (rate-limited), not a 🚫 |
| Producers using `ExplicitHashKey` / shard-aware partitioning | operator / code | present → Blast 🟡; verify routing assumptions after the switch |

## Reversibility classification
- **Lever (a) shard count:** 🟢 reversible — `update-shard-count` reshards back. ~minutes.
- **Lever (b) retention reduction:** 🔴 — records older than new retention are immediately deleted, irrecoverable. Reversibility classifies the **action**, not the parameter; this lever is 🔴 even though the parameter can be re-raised.
- **Lever (c) mode switch:** 🟡 — fully reversible but rate-limited to one switch per 24h. Rollback waits.

**Default for the composed playbook:** 🟡 — the playbook's reversibility is the most restrictive lever in the operator's chosen set. If only lever (a) is proposed: 🟢. If lever (b) is included: 🔴. If only lever (c): 🟡.

## Blast radius classification
- **Default:** 🟡 — touches a live stream with consumers. Bump to 🟢 only if no Lambda mappings AND no EFO consumers AND no Firehose sources (per the `delete-kinesis-stream.md` Attachment table). Bump to 🔴 if any consumer is a critical-path service per catalog OR if Firehose-to-S3 archival depends on the current retention window for replay SLA.

## Rollback note (informational, shown in plan)

"Per-lever rollback:
- **Shard count:** `aws kinesis update-shard-count --target-shard-count <original> --scaling-type UNIFORM_SCALING`. Takes minutes; consumer offsets preserved via shard close/open semantics.
- **Retention:** `aws kinesis increase-stream-retention-period --retention-period-hours <original>` — but records deleted during the reduction window are NOT restored. There is no records-side undo.
- **Mode switch:** `aws kinesis update-stream-mode --stream-arn <arn> --stream-mode-details StreamMode=<original>`. Must wait 24h since last switch.

**Principle 2 reminder:** the cost-direction math in lever (c) is computed against bill-derived rates (or Pricing API) × observed utilization. If either changes materially (regional repricing, workload shape shift), rerun the math before reapplying any mode change. The cheaper mode flips; the operator should set a calendar reminder to recompute quarterly if the workload is in the marginal band (p99/avg ratio 2–5)."
