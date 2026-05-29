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
- `firehose:ListDeliveryStreams` (to check whether any Firehose stream sources from this Kinesis stream)
- `cloudwatch:GetMetricStatistics`

## Queries

1. `aws kinesis describe-stream-summary --stream-name <name>` — captures `StreamStatus`, `StreamModeDetails.StreamMode` (`PROVISIONED` or `ON_DEMAND`), `OpenShardCount`, `RetentionPeriodHours`, `EnhancedMonitoring`.
2. `aws kinesis list-shards --stream-name <name>` — confirms shard count, surfaces closed shards still within retention window.
3. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — 14d producer activity. **Activity signal, Principle 1.**
4. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingBytes --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — bytes-side producer activity (catches low-record-count, large-payload streams).
5. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.Records --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — consumer reads.
6. `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.IteratorAgeMilliseconds --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Maximum` — high iterator age means active consumers falling behind (= active!) OR no consumer polling at all (= idle, but harmless). Cross-reference with `GetRecords.Records`: high age + zero records = no consumer; high age + records = backlogged consumer.
7. `aws kinesis list-stream-consumers --stream-arn <arn>` — Enhanced Fan-Out (EFO) consumers. **Attachment signal — NOT activity.** EFO costs $0.015/consumer-shard-hour even with zero reads; surface for ladder fallback.
8. `aws lambda list-event-source-mappings --event-source-arn <arn>` — Lambda triggers attached. Attachment, not activity.
9. `aws firehose list-delivery-streams` then for each: `aws firehose describe-delivery-stream --delivery-stream-name <fh>` — check if any Firehose has `Source.KinesisStreamSourceConfiguration.KinesisStreamARN == <arn>`. Attachment, not activity.
10. (Optional, opt-in at GATE 2) `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name WriteProvisionedThroughputExceeded --dimensions Name=StreamName,Value=<name> --start-time <now-14d> --end-time <now> --period 3600 --statistics Sum` — throttles signal under-provisioning, not waste. **🚫 trigger if ≥ 1.**

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| 14d `IncomingRecords` (Sum) | `0` | ≥ 1 record — producers are still writing |
| 14d `IncomingBytes` (Sum) | `0` bytes | ≥ 1 KB |
| 14d `GetRecords.Records` (Sum) | `0` (or non-zero but `IteratorAge` near retention period → records read for retention compliance only) | sustained ≥ 1/hr — consumers actively reading |
| 14d `WriteProvisionedThroughputExceeded` (Sum) | `0` | ≥ 1 — stream is under-provisioned, deletion masks a real workload |
| EFO consumers registered | any count — **not a 🚫 trigger** (attachment ≠ activity) | n/a |
| Lambda event source mappings | any count — **not a 🚫 trigger** | n/a |
| Firehose delivery streams sourcing from this stream | any count — **not a 🚫 trigger** for activity, but bumps blast radius | n/a |

**Principle 1 reminder:** registered EFO consumers, Lambda mappings, and Firehose sources are **attachment** — Dimension 2 (blast radius) input. A stream with 5 EFO consumers and zero `IncomingRecords` for 14d is idle; the consumers are paying $0.015/shard-hour each for nothing. Score Dimension 3 on `IncomingRecords` and `GetRecords.Records`, not on consumer count.

**Keep-alive noise to subtract:** the AWS Console's stream-monitoring page polls `DescribeStream` (free, doesn't show up in records metrics) but some operator dashboards write a synthetic "heartbeat" record every N minutes. Tell: uniform inter-arrival times, constant tiny payload size. If `IncomingRecords` shows a flat per-hour rate that matches a known dashboard probe, subtract before judging activity.

## Reversibility classification
- **Default:** 🔴 irreversible. `DeleteStream` is final; records older than the (new-stream-default) 24-hour retention are unrecoverable. Re-creating a stream with the same name returns a new ARN, breaking any consumer hard-coded to the old ARN.

## Blast radius classification
- **Default:** 🟡 — likely has at least one consumer (Lambda, EFO, Firehose, or KCL app outside AWS). Bump to 🟢 only if Queries 7 / 8 / 9 all return empty AND no IaC reference to the stream ARN exists outside the stream's own resource block. Bump to 🔴 if any attached consumer is itself in 🟢-fast-win tier of the same plan (deleting the stream while another item depends on it is a same-resource conflict — emit ordering hint).

## Rollback note (informational, shown in plan)

"Stream deletion is irreversible. Records in flight (within retention window) are lost. Re-creation produces a new ARN — any consumer hard-coded to the old ARN must be reconfigured.

**Principle 2 ladder fallback (preferred over delete in almost all cases):** before recommending delete, surface these reversible alternatives in this order, each capturing partial savings while keeping the stream intact:

1. **Deregister unused EFO consumers** (`DeregisterStreamConsumer`). Cost: $0.015/consumer-shard-hour. Reversible (re-register). Activity check first: query `EnhancedFanOut.OutgoingRecords` per consumer ARN; deregister any with zero 14d activity.
2. **Reduce shard count** (provisioned mode, `UpdateShardCount`). Cost: $0.015/shard-hour. Compute target shard count from 14d p95 `IncomingBytes` (1 MB/s per shard) and `IncomingRecords` (1000 records/s per shard). Reversible via reshard; takes effect after split/merge sequence completes (~minutes).
3. **Reduce retention period** (`DecreaseStreamRetentionPeriod`). Extended retention (> 24h) costs $0.02/shard-hour (provisioned) or per-GB (on-demand). Reducing retention **immediately deletes records older than the new period** — confirm no downstream consumer needs that history.
4. **Mode switch (provisioned ↔ on-demand)**: one switch per 24h. **Principle 2 cost-direction check required.** Compute: provisioned cost = `OpenShardCount × $0.015/hr × 730` vs on-demand cost ≈ `IncomingBytes_GB × $0.04 + GetRecords_GB × $0.04 + IncomingRecords × $0.0000001`. Workload shapes:
   - Steady high throughput → provisioned cheaper.
   - Spiky / low-baseline → on-demand cheaper.
   - Result must be expressed as `$X/mo current → $Y/mo proposed` with input numbers cited. Bare "switch mode to save" is rejected.
5. **Delete** — only if 14d activity is genuinely zero AND ladder steps 1–4 do not capture sufficient savings AND no attached consumer remains (per Queries 7 / 8 / 9). Pre-delete: confirm retention window has elapsed since last write OR confirm consumers have committed their checkpoints past the last record."
