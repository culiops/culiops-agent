---
cloud: aws
action: delete
resource_type: kinesis-stream
applies_when: action == "delete" AND resource matches "arn:aws:kinesis:*:stream/*"
---

# Verify: Delete Kinesis Data Stream

Kinesis Data Streams is a textbook Principle 2 case: deletion is almost always the wrong first move. The reversible ladder (shard count down → retention down → mode switch with cost-direction check → EFO consumer deregistration) captures most savings without breaking producers or consumers. This playbook verifies a delete is safe and surfaces the ladder fallbacks aggressively in the rollback note.

## Required IAM
- `kinesis:DescribeStreamSummary`
- `kinesis:ListShards`
- `kinesis:ListStreamConsumers`
- `lambda:ListEventSourceMappings`
- `firehose:ListDeliveryStreams`, `firehose:DescribeDeliveryStream` (to check whether any Firehose stream sources from this Kinesis stream)
- `cloudwatch:GetMetricData`

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. `cloudformation` owner → ❔ `unsupported-owner`. `unmanaged` → "re-apply old IaC" rollback is unavailable (delete is 🔴 regardless). A stream owned by a Terraform module shared with other resources → delete via the owning IaC change, not the CLI.
1. `aws kinesis describe-stream-summary --stream-name <name>` — captures `StreamStatus`, `StreamModeDetails.StreamMode` (`PROVISIONED` or `ON_DEMAND`), `OpenShardCount`, `RetentionPeriodHours`, `EnhancedMonitoring`. Its success is the "describe succeeded" precondition for treating empty metrics as zero.
2. `aws kinesis list-shards --stream-name <name>` — confirms shard count, surfaces closed shards still within retention window.
3. **Activity metrics (one call, 90d @ 3600s).** 90d × 24 = 2,160 datapoints per metric exceeds the 1,440 `get-metric-statistics` cap, so use `get-metric-data` (limit 100,800 datapoints/call). Dimensions come from Query 1's `StreamName`:

   ```
   aws cloudwatch get-metric-data --start-time <now-90d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
    {"Id":"inrec","MetricStat":{"Metric":{"Namespace":"AWS/Kinesis","MetricName":"IncomingRecords","Dimensions":[{"Name":"StreamName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"inbytes","MetricStat":{"Metric":{"Namespace":"AWS/Kinesis","MetricName":"IncomingBytes","Dimensions":[{"Name":"StreamName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"getrec","MetricStat":{"Metric":{"Namespace":"AWS/Kinesis","MetricName":"GetRecords.Records","Dimensions":[{"Name":"StreamName","Value":"<name>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"iterage","MetricStat":{"Metric":{"Namespace":"AWS/Kinesis","MetricName":"GetRecords.IteratorAgeMilliseconds","Dimensions":[{"Name":"StreamName","Value":"<name>"}]},"Period":3600,"Stat":"Maximum"}}]'
   ```

   - `inrec` / `inbytes` — producer activity (bytes catches low-record-count, large-payload streams). **Activity signal, Principle 1.**
   - `getrec` — consumer reads.
   - `iterage` — high age + zero `getrec` = no consumer polling (idle, harmless); high age + records = backlogged consumer (active).
4. (Optional, opt-in at GATE 2) same call shape, `WriteProvisionedThroughputExceeded` (`Sum`) — throttles mean producers are attempting writes (activity).
5. `aws kinesis list-stream-consumers --stream-arn <arn>` — Enhanced Fan-Out (EFO) consumers. **Attachment, not activity.** EFO consumers accrue a per-consumer-shard-hour charge even with zero reads; surface for the ladder fallback.
6. `aws lambda list-event-source-mappings --event-source-arn <arn>` — Lambda triggers attached. Attachment, not activity.
7. `aws firehose list-delivery-streams` then for each: `aws firehose describe-delivery-stream --delivery-stream-name <fh>` — check if any Firehose has `Source.KinesisStreamSourceConfiguration.KinesisStreamARN == <arn>`. Attachment, not activity.

> **Window (Principle 3):** a delete decision reads the 60–180d band at hourly granularity (90d used here; the 455-day hourly retention allows up to 180d). Judge the **temporal distribution** of the hourly buckets, not the total.

## Evidence thresholds

Temporal rule for the activity rows (Principle 3): bucket the hourly series, then
- any non-zero hour in the **last 30d**, or a **recurring pattern** (non-zero hours repeating across the window, e.g. daily/weekly cadence) → 🚫;
- non-zero hours confined to **one contiguous burst (≤ 48 h) older than 30d**, zero since → **not 🚫**; row scores 🟢 and is annotated `historical-burst` (state the burst date and size in the evidence cell).

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| 90d hourly `IncomingRecords` (Sum) | required | `0`, or only a `historical-burst` | non-zero in last 30d, or recurring pattern — producers are writing |
| 90d hourly `IncomingBytes` (Sum) | required | `0` bytes, or only a `historical-burst` | same rule |
| 90d hourly `GetRecords.Records` (Sum) | required | `0`, or only a `historical-burst` | same rule — consumers actively reading |
| 90d `WriteProvisionedThroughputExceeded` (Sum) | optional | `0` | non-zero in last 30d — producers attempting writes, deletion masks a real workload |

A `required` row that returns ⚪ (query failed, or empty with a failed Target check / describe) forces Evidence ⚪ → 🔴.

**Keep-alive noise to subtract (Principle 1 rule 2):** some operator dashboards write a synthetic "heartbeat" record every N minutes. Tell: uniform inter-arrival times, constant tiny payload size. If `IncomingRecords` shows a flat per-hour rate matching a known probe, subtract it before judging activity.

## Attachment (Dimension 2 / 4 input)

Registered consumers are **attachment**, never activity (Principle 1). They never produce 🚫. A stream with 5 EFO consumers and zero activity for 90d is idle; the consumers are costing money for nothing.

| Signal | Query | Effect |
|--------|-------|--------|
| EFO consumers registered | 5 | ≥ 1 → Blast ≥ 🟡; surface deregistration as ladder step 1 |
| Lambda event source mappings (note `State`) | 6 | ≥ 1 → Blast ≥ 🟡; ≥ 1 mapping whose function is critical-path per catalog → Blast 🔴 |
| Firehose delivery streams sourcing from this stream | 7 | ≥ 1 → Blast ≥ 🟡 (Firehose→S3 archival may be the durability copy) |
| IaC reference to the stream ARN outside its own resource block (Dim 4 grep) | `code:` | ≥ 1 → Dependency 🟡; ≥ 3 → 🔴 |
| Another item in the same plan depends on this stream | plan | Blast 🔴 + ordering hint (same-resource conflict) |

**Idle-ambiguous:** a stream with Evidence 🟢 (idle) but live wiring (any row above ≥ 1) is exactly the idle-ambiguous class → the delete routes to 🔵 (owner confirms decommissioned vs. paused/seasonal).

## Reversibility classification
- **Default:** 🔴 irreversible. `DeleteStream` is final; retained records are lost. Re-creating a stream with the same name returns a new ARN, breaking any consumer hard-coded to the old ARN.

## Blast radius classification
- **Default:** 🟡 — likely has at least one consumer (Lambda, EFO, Firehose, or a KCL app outside AWS that no query here can enumerate). Bump to 🟢 only if the Attachment rows are all empty AND no IaC reference exists outside the stream's own resource block. Bump to 🔴 per the Attachment table.

## Rollback note (informational, shown in plan)

"Stream deletion is irreversible. Records in flight (within retention window) are lost. Re-creation produces a new ARN — any consumer hard-coded to the old ARN must be reconfigured. If Ownership is `unmanaged`, there is no IaC to re-apply.

**Principle 2 ladder fallback (preferred over delete in almost all cases):** before recommending delete, surface these reversible alternatives in this order, each capturing partial savings while keeping the stream intact:

1. **Deregister unused EFO consumers** (`DeregisterStreamConsumer`). Billed per consumer-shard-hour even at zero reads (`efo_consumer_shard_hour_rate`). Reversible (re-register). Activity check first: per-consumer `SubscribeToShardEvent.Records` (dimensions `StreamName` + `ConsumerName`; verify metric name) over 90d via `get-metric-data`; deregister any with zero activity.
2. **Reduce shard count** (provisioned mode, `UpdateShardCount`). Saves `shard_hour_rate` per shard-hour. Compute the target shard count from 90d p95 hourly `IncomingBytes` (1 MB/s per shard) and `IncomingRecords` (1000 records/s per shard). Reversible via reshard.
3. **Reduce retention period** (`DecreaseStreamRetentionPeriod`). Retention above 24h is billed (provisioned: `extended_retention_shard_hour_rate`; on-demand: per GB-month). Reducing retention **immediately deletes records older than the new period** — confirm no downstream consumer needs that history.
4. **Mode switch (provisioned ↔ on-demand)**: rate-limited (see `rightsize-kinesis-stream.md` lever (c)). **Principle 2 cost-direction check required**, using bill-derived rates (Principle 4) or the Pricing API (`AmazonKinesis`) for the region. Bare "switch mode to save" is rejected.
5. **Delete** — only if 90d activity is genuinely zero (or a `historical-burst`) AND ladder steps 1–4 do not capture sufficient savings AND the owner has confirmed (🔵) when consumers remain wired. Pre-delete: confirm the retention window has elapsed since the last write OR that consumers have committed checkpoints past the last record."
