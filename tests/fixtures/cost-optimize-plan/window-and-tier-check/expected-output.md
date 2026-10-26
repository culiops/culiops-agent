**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Target:** account 123456789012 (sts verified, live:0a), region(s) ap-southeast-1
**IaC repo(s):** ~/acme-infra (simulated for this fixture; code refs illustrative)
**Catalog used:** none
**Date:** 2026-07-09 09:12
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md` (waste mode, single-cloud aws).
- **Report freshness:** report `Date:` is 2026-07-09 — same day, within the 14-day threshold. No staleness warning.
- 2 items above $5/mo floor; 0 filtered below floor.
- Target: account `123456789012`, region `ap-southeast-1`. Catalog: none. IaC repo supplied: `~/acme-infra`.
- **Principles applied this run:** Principle 3 (window scaling) — both upstream items were flagged on a 14d window; a delete decision requires the 60-180d band, so both are re-verified over 90d. The 🔵 owner-confirmation tier is in play for any idle-but-wired resource.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

All queries executed 2026-07-09 09:04-09:10 UTC. Row numbering: `0a` target check, `0b-<item>` ownership probe, then `1..N`. Evidence is summarized (Constraint 14).

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 123456789012 = `Scope`; region ap-southeast-1 (2026-07-09T09:04Z) |
| 0b-1 | Delete archive-exports-2023 | s3:GetBucketTagging + IaC grep | s3:GetBucketTagging | ok | no CloudFormation / controller tag; `s3.tf:120` → owner **terraform** |
| 0b-2 | Delete orders-ingest | kinesis:ListTagsForStream + IaC grep | kinesis:ListTagsForStream | ok | no CloudFormation tag; `kinesis.tf:3`, single-resource (not a shared module) → owner **terraform** |
| 1 | Delete archive-exports-2023 | s3:GetBucketLocation | s3:GetBucketLocation | ok | ap-southeast-1: bucket exists in this account/region |
| 2 | Delete archive-exports-2023 | s3:GetBucketVersioning + s3:GetBucketLifecycleConfiguration | s3:GetBucketVersioning, s3:GetLifecycleConfiguration | ok | versioning `Suspended`; no lifecycle rule |
| 3 | Delete archive-exports-2023 | s3:ListBucketMetricsConfigurations (source 3a) | s3:GetMetricsConfiguration | ok | none: request metrics unavailable |
| 4 | Delete archive-exports-2023 | s3:GetBucketLogging (source 3b) | s3:GetBucketLogging | ok | server access logging NOT enabled: no access logs to read |
| 5 | Delete archive-exports-2023 | cloudtrail:ListEventDataStores + GetEventDataStore (source 3c) | cloudtrail:ListEventDataStores, GetEventDataStore | ok | store `org-data-events` exists, captures S3 data events (`AWS::S3::Object`), created 2025-09-01: covers the 90d window |
| 6 | Delete archive-exports-2023 | cloudtrail:StartQuery + GetQueryResults (CloudTrail Lake, 90d) | cloudtrail:StartQuery, GetQueryResults | ok | **214 `GetObject` in 90d, spread across all 13 weekly buckets (15-18 per week), first 2026-04-11, last 2026-07-08 18:22 UTC; principals `svc-report-exporter` 171, `svc-monthly-close` 43; 0 `PutObject`.** About 38 GB scanned (billed per GB) |
| 7 | Delete archive-exports-2023 | cloudwatch:GetMetricData (`NumberOfObjects`, `BucketSizeBytes`; daily, 90d) + KeyCount check | cloudwatch:GetMetricData, s3:ListBucket | ok | 1,204 objects, ~180 GB, flat (0% growth); non-empty |
| 8 | Delete archive-exports-2023 | s3:GetBucketPolicy | s3:GetBucketPolicy | ok | two same-account service roles; no cross-account / log-delivery principals |
| 9 | Delete archive-exports-2023 | s3:GetBucketReplication | s3:GetReplicationConfiguration | ok | none |
| 10 | Delete archive-exports-2023 | log-target sweep (trails, LB, CloudFront, flow logs, Config) | see `delete-s3-bucket.md` | ok | not a log destination |
| 11 | Delete archive-exports-2023 | route53:ListResourceRecordSets (all records) | route53:List* | ok | 1 zone, 38 records, no reference to the bucket |
| 12 | Delete orders-ingest | kinesis:DescribeStreamSummary + ListShards | kinesis:DescribeStreamSummary, ListShards | ok | PROVISIONED, 2 open shards, retention 168h, ConsumerCount 2; no closed shards |
| 13 | Delete orders-ingest | cloudwatch:GetMetricData (`IncomingRecords`, `IncomingBytes`, `GetRecords.Records`, `GetRecords.IteratorAgeMilliseconds`; **90d @ 3600s**, one call) | cloudwatch:GetMetricData | ok | all 2,160 hourly datapoints = 0 for records and bytes in and out; no burst anywhere; iterator age has no datapoints (nobody polls). Describe (row 12) succeeded, so zeros are observed values (Metrics rule) |
| 14 | Delete orders-ingest | cloudwatch:GetMetricData (`WriteProvisionedThroughputExceeded`, 90d @ 3600s; optional, opted in at GATE 2) | cloudwatch:GetMetricData | ok | 0 throttles across the window: producers are not even attempting writes |
| 15 | Delete orders-ingest | kinesis:ListStreamConsumers | kinesis:ListStreamConsumers | ok | 2 ACTIVE EFO consumers (`fraud-scoring-efo`, `analytics-mirror-efo`): **attachment** |
| 16 | Delete orders-ingest | lambda:ListEventSourceMappings | lambda:ListEventSourceMappings | ok | 1 Enabled mapping → `orders-projector`: **attachment** |
| 17 | Delete orders-ingest | firehose:ListDeliveryStreams + DescribeDeliveryStream | firehose:List*, Describe* | ok | no delivery stream sources from this stream |

The optional `WriteProvisionedThroughputExceeded` query was opted in at GATE 2 (row 14). An optional row that runs must pass for Evidence to be 🟢 (it does); had the operator declined it, Evidence would still be 🟢 and the row would be listed in Gaps.

**Total estimated API cost:** one CloudTrail Lake scan of about 38 GB (billed per GB scanned; itemized at GATE 2 and the only non-free item), plus free describe/list calls and GetMetricData. CloudTrail `LookupEvents` is not used for S3: it never returns data events.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔵 Requires owner confirmation | 1 | $180/mo (pending confirmation) |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 1 | ($60/mo claim — activity found in the delete window) |
| ❔ Manual review | 0 | — |

**Total plan savings:** $0/mo actionable now; $180/mo pending owner confirmation on item #2.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔵 Requires owner confirmation

| # | Action | Resource | Owner | Savings | Reversibility | Blast | Evidence | Dependency | Source | Dev-note |
|---|--------|----------|-------|---------|---------------|-------|----------|------------|--------|----------|
| 2 | Delete Kinesis stream orders-ingest | arn:aws:kinesis:ap-southeast-1:123456789012:stream/orders-ingest | terraform `code:kinesis.tf:3` | $180/mo | 🔴 re-create yields a new ARN | 🟡 live:15,16 (2 EFO consumers + 1 Lambda mapping) | 🟢 live:13,14 (0 records in/out, 0 throttles, 90d hourly) | 🟡 code:kinesis.tf:19, code:lambda.tf:55 | line-item-computation (high) | `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md` |

> **🔵 tier rationale:** Evidence is 🟢 (genuinely idle over the 90d delete window: Principle 3, hourly, no burst), but `orders-ingest` is **idle-ambiguous** — 2 registered EFO consumers and 1 enabled Lambda mapping are live wiring. Metrics cannot distinguish *decommissioned* from *paused / seasonal*; only the owner can. Tier rule 2 fires before rule 3, so Reversibility 🔴 does not reroute the item. Reversible fallback in the dev-note: reduce retention 168h → 24h, and deregister the idle EFO consumers.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Savings claimed | Disqualifying evidence |
|---|--------|----------|-----------------|------------------------|
| 1 | Delete S3 bucket archive-exports-2023 | arn:aws:s3:::archive-exports-2023 | $60/mo (line-item-computation, low — `window-too-short` upstream) | **Principle 3 window check failed the delete.** CloudTrail Lake (S3 data events, existing store `org-data-events`) shows 214 `GetObject` over the 90d delete window, in every one of 13 weekly buckets (15-18/week), last 2026-07-08 18:22 UTC, by `svc-report-exporter` and `svc-monthly-close` (live:6). The upstream 14d view was a cost-line proxy, not an access measurement. This is steady use, not one historical burst. |

**Dimension detail (#1):** Evidence 🚫 (required activity row, recurring and recent) → tier rule 1. Owner terraform (`code:s3.tf:120`). Other dimensions not scored. Not silently dropped.

## ❔ Manual review required

No items in this tier — both items had matching playbooks (`delete-s3-bucket.md`, `delete-kinesis-stream.md`).

## Drift

None — neither item reached a code-versus-live comparison that differs (`kinesis.tf:3` shard_count 2 / retention 168 match live, live:12).

## Gaps

- Item #1: bucket access logging is off (live:4) and no request-metrics configuration exists (live:3), so the only activity source was CloudTrail Lake (billed, existing store). Without that store the activity signal would have been ⚪ `activity-unobservable` and the item would have landed in 🔴.
- Item #2: consumer `analytics-mirror-efo` has no IaC resource (registered at runtime by an application); deleting the stream through IaC alone would remove it without its owner knowing. Name it in the owner question.
- Item #2: the reversible-fallback saving (retention reduction, EFO deregistration) is not quantified: it needs bill-derived rates (Principle 4) the run did not fetch. Left to the `iac-change-execution` plan.

## Next steps (informational)

- **Item #1:** do NOT delete. If storage cost is still a concern, a lifecycle transition for this cold archive is the reversible lever: run a fresh `cloud-cost-investigate` for it, then `cost-optimize-plan` with access-pattern evidence.
- **Item #2:** route the emitted dev-note to the stream owner. If they confirm decommissioned, open `iac-change-execution` to delete the stream, its EFO consumers and the Lambda mapping as one bundle (`kinesis.tf:3,19`, `lambda.tf:55`, plus the runtime-registered consumer). If paused/seasonal, apply the reversible fallback instead.

---

### Emitted artifact — `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`

```markdown
# Owner confirmation needed — orders-ingest

**Resource:** kinesis-stream / arn:aws:kinesis:ap-southeast-1:123456789012:stream/orders-ingest / ap-southeast-1
**Proposed action:** delete / decommission (est. saving $180/mo, source line-item-computation)
**Why it needs you:** metrics show no activity over 90d (0 IncomingRecords, 0 IncomingBytes, 0 GetRecords.Records, hourly), but a Kinesis stream can be idle while *paused or seasonal*. Only you can confirm it is decommissioned, not paused.

**Evidence gathered**
- Activity: 0 IncomingRecords, 0 IncomingBytes, 0 GetRecords.Records and 0 write throttles over 90d at hourly granularity (live:13,14).
- Attachment: 2 ACTIVE EFO consumers (fraud-scoring-efo, analytics-mirror-efo; the second is not in IaC) + 1 enabled Lambda mapping (orders-projector) — live wiring, zero throughput (live:15,16).
- Temporal distribution: flat zero across the full 90d window — no historical burst.

**The one question:** Is orders-ingest decommissioned (safe to delete), or paused / seasonal (keep)?

**Reversible fallback if unsure:** reduce retention 168h → 24h and deregister the idle EFO consumers — captures part of the cost without deleting the stream or breaking the wired consumers.
```
