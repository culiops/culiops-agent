**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-07-09 09:12
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md` (waste mode, single-cloud aws).
- **Report freshness:** report `Date:` is 2026-07-09 — same day, within the 14-day threshold. No staleness warning.
- 2 items above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) scores ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- **Principles applied this run:** Principle 3 (window scaling) — both upstream items were flagged on a 14d window; a delete decision requires the 60–180d band, so both are re-verified over 90d. The 🔵 owner-confirmation tier is in play for any idle-but-wired resource.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete archive-exports-2023 | cloudtrail:LookupEvents (GetObject, **90d**) | cloudtrail:LookupEvents | ok | **214 GetObject events across 90d**, distributed steadily (not one burst); last 2026-07-08 — **Principle 3: 14d read 0, but the delete-window read is active** |
| 2 | Delete archive-exports-2023 | s3api:GetBucketVersioning | s3:GetBucketVersioning | ok | `Status: Suspended` — delete would be irreversible (not the deciding dimension; Evidence 🚫 forces 🚫 first) |
| 3 | Delete archive-exports-2023 | s3api:ListObjectsV2 (--max-keys 1) | s3:ListBucket | ok | non-empty, most-recent object 2026-07-01 — live archive |
| 4 | Delete orders-ingest | kinesis:DescribeStreamSummary | kinesis:DescribeStreamSummary | ok | PROVISIONED, 2 shards, retention 168h, ConsumerCount 2 |
| 5 | Delete orders-ingest | cloudwatch:GetMetricStatistics (IncomingRecords, **90d hourly**) | cloudwatch:GetMetricStatistics | ok | Sum=0 across all ~2160 hourly datapoints — **Principle 3: genuinely idle over the delete window, no burst** |
| 6 | Delete orders-ingest | cloudwatch:GetMetricStatistics (GetRecords.Records, **90d hourly**) | cloudwatch:GetMetricStatistics | ok | Sum=0 — no consumer actually reads |
| 7 | Delete orders-ingest | kinesis:ListStreamConsumers | kinesis:ListStreamConsumers | ok | 2 ACTIVE EFO consumers (`fraud-scoring-efo`, `analytics-mirror-efo`) — **attachment**, live wiring |
| 8 | Delete orders-ingest | lambda:ListEventSourceMappings | lambda:ListEventSourceMappings | ok | 1 Enabled mapping → `orders-projector` — **attachment**, live wiring |

**Total estimated API cost:** $0.00 (LookupEvents + GetMetricStatistics within free tier).

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

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Dev-note |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 2 | Delete Kinesis stream orders-ingest | arn:aws:kinesis:ap-southeast-1:123456789012:stream/orders-ingest | $180/mo | 🔴 (re-create yields new ARN) | 🟡 2 EFO consumers + 1 Lambda mapping | 🟢 0 records / 90d | ⚪ → 🟡-equivalent (no catalog) | line-item-computation (high) | `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md` |

> **🔵 tier rationale:** Evidence is 🟢 (genuinely idle over the 90d delete window per Principle 3), but `orders-ingest` is **idle-ambiguous** — 2 registered EFO consumers and 1 enabled Lambda mapping are live wiring. Metrics cannot distinguish *decommissioned* from *paused / seasonal*; only the owner can. Routed to 🔵 (not 🟢/🟡) and an owner dev-note is emitted. Reversible fallback surfaced in the note: reduce retention 168h → 24h (captures the extended-retention portion of the $180/mo without deleting).

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Original Savings Claim | Reason |
|---|--------|----------|------------------------|--------|
| 1 | Delete S3 bucket archive-exports-2023 | arn:aws:s3:::archive-exports-2023 | $60/mo (line-item-computation, low — `window-too-short` upstream) | **Principle 3 window check failed the delete.** The upstream 14d window read 0 GetObject, but over the 60–180d delete window (90d fetched) there are **214 GetObject events distributed steadily across the period** (last 2026-07-08). This is active use, not a single historical burst. Reject the delete. |

## ❔ Manual review required

No items in this tier — both items had matching playbooks in v1 (`delete-s3-bucket.md`, `delete-kinesis-stream.md`).

## Gaps

- Item #2: the reversible-fallback saving (retention reduction) is an estimate; the exact split of the $180/mo between shard-hours and extended-retention is left to the `iac-change-execution` plan once the owner confirms decommission.

## Next steps (informational)

- **Item #1:** do NOT delete. If storage cost is still a concern, the reversible lever is an S3 lifecycle transition to Glacier/Deep Archive (the bucket is a live but cold archive) — run a fresh `cloud-cost-investigate` waste query for a lifecycle candidate.
- **Item #2:** route the emitted dev-note (`.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`) to the stream owner. If they confirm decommissioned, open `iac-change-execution` to delete the stream, its 2 EFO consumers, and the Lambda mapping (full-bundle delete). If they say paused/seasonal, apply the reversible retention reduction instead.

---

### Emitted artifact — `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`

```markdown
# Owner confirmation needed — orders-ingest

**Resource:** kinesis-stream / arn:aws:kinesis:ap-southeast-1:123456789012:stream/orders-ingest / ap-southeast-1
**Proposed action:** delete / decommission (est. saving $180/mo, source line-item-computation)
**Why it needs you:** metrics show no activity over 90d (0 IncomingRecords, 0 GetRecords.Records, hourly), but a Kinesis stream can be idle while *paused or seasonal*. Only you can confirm it is decommissioned, not paused.

**Evidence gathered**
- Activity: 0 IncomingRecords and 0 GetRecords.Records over 90d at hourly granularity.
- Attachment: 2 ACTIVE EFO consumers (fraud-scoring-efo, analytics-mirror-efo) + 1 enabled Lambda mapping (orders-projector) — live wiring, zero throughput.
- Temporal distribution: flat zero across the full 90d window — no historical burst.

**The one question:** Is orders-ingest decommissioned (safe to delete), or paused / seasonal (keep)?

**Reversible fallback if unsure:** reduce retention 168h → 24h — captures the extended-retention portion of the cost without deleting the stream or breaking the wired consumers.
```
