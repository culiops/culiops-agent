# window-and-tier-check — cost-optimize-plan fixture

Two-item report exercising the v0.10 additions end-to-end: **Principle 3** (scale the verification window to the action's destructiveness) and the new **🔵 Requires owner confirmation** tier with its dev-note artifact.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream `cloud-cost-investigate` waste audit was run with a **short 14-day window** and flagged two delete candidates that the v0.10 guardrails should treat carefully:

1. **`archive-exports-2023` S3 bucket** — $60/mo. Upstream read 0 GetObject over 14d and flagged it `window-too-short`. Per Principle 3, a delete decision uses the 60–180d band. Re-checking over 90d (via `delete-s3-bucket.md`, which already queries 90d CloudTrail) finds **214 GetObject events distributed steadily across the window** — active use, not a historical burst. Correct outcome: **🚫 Do not act** (Principle 3 window flip).

2. **`orders-ingest` Kinesis stream** — $180/mo, PROVISIONED, 2 shards, 168h retention. Genuinely idle over 90d (0 IncomingRecords, 0 GetRecords.Records, hourly), but it has **2 registered EFO consumers + 1 enabled Lambda mapping** — live wiring. Metrics can't tell decommissioned from paused/seasonal. Correct outcome: **🔵 Requires owner confirmation** with an emitted dev-note and a reversible retention-reduction fallback.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260709-0900.md and build me an execution plan. Apply the Principle 3 (scale the verification window to the action) and the 🔵 owner-confirmation tier when scoring evidence..."

(See `operator-question.md`.)

## What this fixture exercises

- **Principle 3 window scaling (cost-optimize-plan).** A delete flagged idle on 14d is re-verified over the 60–180d band; steady activity found over 90d flips item #1 off delete into 🚫. The upstream `window-too-short` label is resolved downstream.
- **🔵 Requires owner confirmation tier + dev-note.** Item #2 is idle over the delete window (Evidence 🟢) but idle-ambiguous (live consumers/mappings) → 🔵, with a templated dev-note emitted at `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`.
- **Idle-ambiguous class + tier-rule determinism.** Validates the updated 5-rule tier assignment (🚫 → 🔵 → 🔴 → 🟡 → 🟢) and that attachment (EFO consumers, Lambda mapping) routes to blast radius, not Evidence (Principle 1).
- **Temporal-distribution reasoning.** 214 steady events = active (item #1); flat-zero across 90d = truly idle (item #2).
- **Freshness gate no-op path.** A same-day report does not trip the >14d staleness warning.
- **No fabrication.** "Next steps" names the correct reversible levers (S3 lifecycle for #1; retention reduction for #2) but does not inject them as plan items.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | freeform operator prompt |
| `upstream-report.md` | synthetic waste report; both items flagged on a 14d window |
| `mock-responses/cloudtrail-getobject-archive-exports-2023.json` | 90d CloudTrail — 214 GetObject events, steady distribution (Principle 3 activity) |
| `mock-responses/get-bucket-versioning-archive-exports-2023.json` | versioning Suspended (irreversible delete) |
| `mock-responses/list-objects-archive-exports-2023.json` | non-empty, recent object |
| `mock-responses/describe-stream-summary-orders-ingest.json` | Kinesis metadata (2 shards, 168h retention, 2 consumers) |
| `mock-responses/incoming-records-orders-ingest.json` | 90d hourly IncomingRecords all 0 |
| `mock-responses/get-records-orders-ingest.json` | 90d GetRecords.Records all 0 |
| `mock-responses/list-stream-consumers-orders-ingest.json` | 2 ACTIVE EFO consumers (attachment → idle-ambiguous) |
| `mock-responses/list-event-source-mappings-orders-ingest.json` | 1 enabled Lambda mapping (attachment) |
| `expected-output.md` | the plan markdown the skill produces at GATE 3, incl. the emitted dev-note |
| `DRY-RUN-NOTES.md` | gate transitions, per-dimension scoring, and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | cost-optimize-plan tier | Dominant reason |
|---|------|-------------------|------------------------|-----------------|
| 1 | Delete S3 bucket archive-exports-2023 | 1 ($60/mo) | 🚫 Do not act | **Principle 3** — 90d delete window shows 214 GetObject events; 14d "0" was window-too-short |
| 2 | Delete Kinesis stream orders-ingest | 2 ($180/mo) | 🔵 Requires owner confirmation | **Idle-ambiguous** — 0 throughput over 90d but live EFO/Lambda wiring; owner must confirm decommissioned vs paused |

## Why this fixture was added (v0.10)

The OPS-9169 staging engagement (pricing-engine) repeatedly hit two traps the v0.9 fixtures did not cover: delete candidates that read idle on a short window but were active over a longer one, and idle-but-wired resources where only a dev could confirm decommissioned-vs-paused. This fixture validates the v0.10 Principle 3 addition and the 🔵 owner-confirmation tier under realistic inputs.
