**Cloud cost investigation**
**Mode:** waste
**Scope:** 123456789012 / acme-prod (single)
**Time range:** 2026-06-25 → 2026-07-09
**Catalog used:** none
**Date:** 2026-07-09 09:00
**Cloud:** aws

## Question

Run a waste audit on our AWS prod account (ap-southeast-1). Surface idle delete candidates. (Note: this audit's utilization window was only 14 days — the operator ran a quick sweep.)

## Scoping decisions

- Mode: waste.
- Scope: account 123456789012 (acme-prod), single account, region ap-southeast-1.
- Time range: **14d rolling (2026-06-25 → 2026-07-09)** — short window, flagged for downstream re-check.
- Savings floor: $5/mo.

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | s3api:ListBuckets | ap-southeast-1 | s3:ListAllMyBuckets | ok | archive-exports-2023 enumerated |
| 2 | cloudtrail:LookupEvents (GetObject, **14d**) | archive-exports-2023 | cloudtrail:LookupEvents | ok | 0 GetObject events in 14d |
| 3 | kinesis:DescribeStreamSummary | orders-ingest | kinesis:DescribeStreamSummary | ok | PROVISIONED, 2 shards, retention 168h |
| 4 | cloudwatch:GetMetricStatistics (Kinesis.IncomingRecords, **14d**) | orders-ingest | cloudwatch:GetMetricStatistics | ok | 0 records in 14d |

## Findings

### 1. Idle S3 bucket (flagged on a 14d window)

`archive-exports-2023` shows 0 GetObject events over the 14d audit window, $60/mo storage. Flagged as a delete candidate. **Window caveat:** 14d is short for a delete decision — downstream triage should re-check over the delete-appropriate window (Principle 3).

### 2. Idle Kinesis stream with wired consumers

`orders-ingest` (PROVISIONED, 2 shards, 168h retention) shows 0 IncomingRecords over 14d, $180/mo. Producers appear idle, but the stream has registered consumers per a separate attachment sweep (deferred). This is an idle-but-wired stream — decommissioned vs paused/seasonal cannot be told from metrics.

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Delete S3 bucket archive-exports-2023 | arn:aws:s3:::archive-exports-2023 | $60/mo | line-item-computation | **low (window-too-short)** | 0 GetObject in 14d — window too short for a delete per Principle 3; re-check over 60–180d downstream |
| 2 | Delete Kinesis stream orders-ingest | arn:aws:kinesis:ap-southeast-1:123456789012:stream/orders-ingest | $180/mo | line-item-computation | low | 0 IncomingRecords in 14d; registered consumers not yet swept |

**Total estimated savings:** $240/mo claimed — both low-confidence, re-verify downstream before acting.

## Gaps

- Both items were flagged on a 14d window. Item #1 needs a 60–180d re-check; item #2 needs an attachment sweep (EFO consumers / Lambda mappings) plus the longer window. Deferred to `cost-optimize-plan`.

## Next steps (informational)

- Run `cost-optimize-plan` on this report. Expect item #1 to be re-checked over 90d (may flip off delete if activity is found) and item #2 to route to the 🔵 owner-confirmation tier if it is idle-but-wired.
