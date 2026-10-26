# window-and-tier-check — cost-optimize-plan fixture

Two-item report exercising **Principle 3** (scale the verification window to the action's destructiveness) and the **🔵 Requires owner confirmation** tier with its dev-note artifact.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream waste audit ran with a **short 14-day window** and flagged two delete candidates:

1. **`archive-exports-2023` S3 bucket** — $60/mo. Upstream saw no request-charge line items over 14d and flagged it `window-too-short`. Re-checking over 90d with a **real S3 data-event source** finds **214 `GetObject` events distributed steadily across the window**. Server access logging is off and no request-metrics configuration exists, so the source is **CloudTrail Lake** (`StartQuery` against the existing event data store `org-data-events`, billed per GB scanned). Correct outcome: **🚫 Do not act**.

2. **`orders-ingest` Kinesis stream** — $180/mo, PROVISIONED, 2 shards, 168h retention. Genuinely idle over 90d (0 IncomingRecords, IncomingBytes and GetRecords.Records, hourly), but it has **2 registered EFO consumers + 1 enabled Lambda mapping**. Correct outcome: **🔵 Requires owner confirmation** with an emitted dev-note and a reversible fallback.

**IaC repo: simulated** (`~/acme-infra`); `mock-responses/iac-grep-simulated.json` stands in for the grep and the `code:` refs are illustrative.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md and build me an execution plan. Apply the Principle 3 (scale the verification window to the action) and the 🔵 owner-confirmation tier when scoring evidence..."

(See `operator-question.md`.)

## What this fixture exercises

- **Principle 3 window scaling.** A delete flagged idle on 14d is re-verified over the 60-180d band; steady activity over 90d flips item #1 into 🚫.
- **A valid S3 activity source.** `delete-s3-bucket.md` order: request metrics (none) → access logs (not enabled) → CloudTrail Lake on an existing store. `lookup-events` is never used for S3 objects; it cannot return data events, which is why the earlier version of this fixture was unrealistic.
- **Billed query itemized.** The Lake scan is the one non-free item at GATE 2, allowed by Law 1 because the store already exists.
- **🔵 tier + dev-note.** Item #2 is idle over the delete window (Evidence 🟢) but idle-ambiguous (live consumers / mapping) → 🔵, with a templated dev-note.
- **Attachment kept out of Evidence** (Principle 1): EFO consumers and the Lambda mapping feed Blast and Dependency; they are also what makes the stream idle-ambiguous.
- **Temporal-distribution reasoning.** 214 steady events (13 of 13 weekly buckets non-zero) = active; flat zero across 90d = idle.
- **One-call 90d hourly metrics** via `get-metric-data` (2,160 points per series would exceed the 1,440 cap of `get-metric-statistics`).
- **Freshness gate no-op path.** A same-day report does not trip the >14d staleness warning.
- **No fabrication.** "Next steps" names the reversible levers but does not inject them as plan items.

## Files in this fixture

Row = the `#` in the plan's "Verification queries run" table.

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | — | freeform operator prompt |
| `upstream-report.md` | — | synthetic waste report; both items flagged on a 14d window |
| `mock-responses/sts-get-caller-identity.json` | 0a | target check |
| `mock-responses/iac-grep-simulated.json` | 0b-1, 0b-2, Dim 4 | simulated IaC grep |
| `mock-responses/get-bucket-tagging-archive-exports-2023.json` | 0b-1 | bucket tags |
| `mock-responses/list-tags-for-stream-orders-ingest.json` | 0b-2 | stream tags |
| `mock-responses/get-bucket-location-archive-exports-2023.json` | 1 | bucket region |
| `mock-responses/get-bucket-versioning-archive-exports-2023.json` | 2 | versioning Suspended |
| `mock-responses/get-bucket-lifecycle-configuration-archive-exports-2023.json` | 2 | no lifecycle rule |
| `mock-responses/list-bucket-metrics-configurations-archive-exports-2023.json` | 3 | no request metrics |
| `mock-responses/get-bucket-logging-archive-exports-2023.json` | 4 | access logging not enabled |
| `mock-responses/cloudtrail-event-data-store-org-data-events.json` | 5 | existing Lake store that captures S3 data events |
| `mock-responses/cloudtrail-lake-query-archive-exports-2023.json` | 6 | **90d Lake query: 214 GetObject, steady distribution** |
| `mock-responses/get-metric-data-bucket-size-archive-exports-2023-90d.json` | 7 | size / object count (flat) |
| `mock-responses/list-objects-archive-exports-2023.json` | 7 | non-empty check |
| `mock-responses/get-bucket-policy-archive-exports-2023.json` | 8 | principals summary |
| `mock-responses/get-bucket-replication-archive-exports-2023.json` | 9 | no replication |
| `mock-responses/log-target-sweep-archive-exports-2023.json` | 10 | not a log destination |
| `mock-responses/dns-sweep-archive-exports-2023.json` | 11 | no DNS reference |
| `mock-responses/describe-stream-summary-orders-ingest.json` | 12 | Kinesis metadata (2 shards, 168h) |
| `mock-responses/list-shards-orders-ingest.json` | 12 | 2 open shards |
| `mock-responses/get-metric-data-orders-ingest-90d-hourly.json` | 13 | 90d hourly records / bytes in and out: all 0 |
| `mock-responses/get-metric-data-orders-ingest-90d-write-throttles.json` | 14 | optional row (opted in): 0 write throttles |
| `mock-responses/list-stream-consumers-orders-ingest.json` | 15 | 2 ACTIVE EFO consumers (attachment) |
| `mock-responses/list-event-source-mappings-orders-ingest.json` | 16 | 1 enabled Lambda mapping (attachment) |
| `mock-responses/firehose-list-delivery-streams.json` | 17 | no Firehose source |
| `expected-output.md` | — | the plan at GATE 3, incl. the emitted dev-note |
| `DRY-RUN-NOTES.md` | — | gate transitions, scoring, acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | Tier | Dominant reason |
|---|------|-------------------|------|-----------------|
| 1 | Delete S3 bucket archive-exports-2023 | 1 ($60/mo) | 🚫 Do not act | **Principle 3** — the 90d Lake query shows 214 steady `GetObject` events; the upstream 14d proxy was `window-too-short` |
| 2 | Delete Kinesis stream orders-ingest | 2 ($180/mo) | 🔵 Requires owner confirmation | **Idle-ambiguous** — 0 throughput over 90d but live EFO / Lambda wiring |

## Why this fixture was added

A staging engagement surfaced two traps the earlier fixtures did not cover: delete candidates that read idle on a short window but were active over a longer one, and idle-but-wired resources where only an owner can confirm decommissioned-vs-paused. This fixture validates Principle 3 and the 🔵 tier under realistic inputs.
