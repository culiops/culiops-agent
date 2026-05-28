# Dry-run notes — verification-fail

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides path to upstream report (`operator-question.md`). Skill loads `upstream-report.md`, extracts 1-item Remediation list, reads `**Cloud:** aws` (single-cloud), `**Scope:** 123456789012 / acme-prod`. Applies $5/mo floor — 1 item passes ($400). No catalog at `.culiops/service-discovery/` — Dimension 4 will score ⚪ (treated as 🟡-equivalent). Skill presents scoping summary: 1 item, $400/mo, aws, single account, no catalog. Operator confirms. Approved.

2. **GATE 2 (Verification batch)** — Skill looks up playbook for item #1 (delete S3 bucket): `examples/aws/delete-s3-bucket.md` → 7 queries (GetBucketLocation, GetBucketPolicy, GetBucketLogging, GetBucketReplication, GetBucketVersioning, CloudTrail LookupEvents GetObject 30d, ListObjectsV2). Playbook present; no manual-review items. Total: 7 queries, 0 deduplication opportunities (single resource). Estimated API cost: $1.20 (CloudTrail LookupEvents dominates). IAM perms list shown: `s3:GetBucketLocation`, `s3:GetBucketPolicy`, `s3:GetBucketLogging`, `s3:GetBucketReplication`, `s3:GetBucketVersioning`, `cloudtrail:LookupEvents`, `s3:ListObjectsV2`. Operator approves full batch.

3. **GATE 3 (Plan review)** — Skill executes 7 queries against mock-responses (all succeed). Query #6 (`cloudtrail:LookupEvents`) returns `EventsCount: 1247` with events spanning 2026-04-29 to 2026-05-27 14:32 UTC, all from principal `AssumedRole/lambda-export-fn`. Evidence dimension scores 🚫 — item placed in 🚫 Do not act with disqualifying evidence quoted. Plan summary shows 0 actionable items across all four tiers. Operator reviews — the 🚫 placement is correct and the evidence is clearly shown. No revisions. Approved. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-1022.md`.

## What this fixture validates

- **Skill resists upstream recommendation when evidence contradicts.** Upstream report's `Confidence: high` for a delete recommendation is overridden by live CloudTrail data. The plan outcome contradicts the upstream recommendation — this is correct behavior under Iron Law #3.
- **Item NOT silently dropped.** The 🚫 section is present with the full disqualifying evidence string. A reviewer can trace from the plan row back to query #6 and from query #6 to the mock response.
- **All 4 actionable tiers (🟢/🟡/🔴/🚫) render correctly even when only 🚫 is populated.** Tiers 🟢, 🟡, and 🔴 each show "No items in this tier." Plan summary table shows 0 for those three and 1 for 🚫.
- **Plan summary table handles zero-actionable-items case.** Total plan savings shows `$0/mo` with an explanation, not a blank or error.
- **Iron Law #3 enforcement:** disqualifying signal is quoted in the plan — query number, API name, count, last-event timestamp, and principal are all present in the Disqualifying evidence column.
- **`EventsCount` fixture convention documented.** The `lookup-events-bucket-logs-active-90d.json` mock contains 5 representative events. `EventsCount: 1247` is a fixture-only field (not a real AWS SDK response field) indicating the true event count. This note appears in both `README.md` and these dry-run notes so reviewers understand the JSON array length (5) is not the count that matters.

## Acceptance check

A reviewer walks through the 7 mock responses, confirms the CloudTrail lookup-events response shows active GetObject traffic (`EventsCount: 1247` in last 30d, most-recent `EventTime: 2026-05-27T14:32:18.000Z`, principal `AssumedRole/lambda-export-fn`), and verifies the skill places the item in 🚫 Do not act with the specific evidence quoted in the Disqualifying evidence column. The plan summary table must show 0 in all four actionable tiers except 🚫 Do not act (count = 1). The item must not appear in any other tier and must not be absent from the plan.
