# verification-fail — cost-optimize-plan fixture

Single-item report recommending deletion of `bucket-logs-active` ($400/mo). Verification queries reveal active GetObject traffic — the skill places the item in 🚫 Do not act, demonstrating Iron Law #3 (no tier without evidence) and resisting the upstream recommendation.

## What's modelled

Account `123456789012` (`acme-prod`), region `ap-southeast-1`. The upstream `cloud-cost-investigate` waste audit found one remediation candidate: delete `bucket-logs-active` to save $400/mo. The bucket carries no S3 lifecycle policy and its name did not appear in the account's tag-scope. All 7 verification queries succeed. However, `cloudtrail:LookupEvents` returns 1,247 GetObject events in the last 30d (last event 2026-05-27 14:32 UTC, principal `AssumedRole/lambda-export-fn`) — the skill places the item in 🚫 Do not act with full disqualifying evidence shown. No actionable items reach the plan.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md"

(See `operator-question.md`.)

## What this fixture exercises

- **Single-item batch verification (7 queries):** GetBucketLocation, GetBucketPolicy, GetBucketLogging, GetBucketReplication, GetBucketVersioning, CloudTrail LookupEvents (30d), ListObjectsV2.
- **`cloudtrail:LookupEvents` returns 1,247 GetObject events in last 30d → triggers 🚫 column on Evidence dimension.** Last event 2026-05-27 14:32 UTC, principal `AssumedRole/lambda-export-fn`. Active log-processing pipeline reads from this bucket.
- **Skill resists the upstream recommendation:** places item in 🚫 with full disqualifying evidence shown, NOT silently dropped.
- **Plan summary table shows 0 actionable items** — the zero-count case for all four actionable tiers is exercised.

> **Mock response note:** `lookup-events-bucket-logs-active-90d.json` contains 5 representative events. The top-level `EventsCount` field (`1247`) is a **fixture convention** — it is not a real AWS SDK response field. The fixture README and `DRY-RUN-NOTES.md` document this so reviewers know the count is the signal, not the JSON array length.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform operator request to feed the skill |
| `upstream-report.md` | Synthetic `cloud-cost-investigate` waste report — skill input |
| `mock-responses/get-bucket-location-bucket-logs-active.json` | Bucket region (ap-southeast-1) |
| `mock-responses/get-bucket-policy-bucket-logs-active.json` | Bucket policy (empty statements) |
| `mock-responses/get-bucket-logging-bucket-logs-active.json` | Server access logging (not enabled) |
| `mock-responses/get-bucket-replication-bucket-logs-active.json` | Replication config (none — AWS error shape) |
| `mock-responses/get-bucket-versioning-bucket-logs-active.json` | Versioning state (Suspended) |
| `mock-responses/lookup-events-bucket-logs-active-90d.json` | **CloudTrail: 1,247 GetObject events in 30d — the disqualifying signal** |
| `mock-responses/list-objects-v2-bucket-logs-active.json` | Object count (47 objects, most-recent 2026-05-27) |
| `expected-output.md` | The plan markdown the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | Gate transitions and acceptance check |

## Expected outcome

The single item lands in 🚫 Do not act. The Disqualifying evidence column quotes the CloudTrail signal (1,247 GetObject events, last event date, principal). The plan summary table shows 0 items in all four actionable tiers. The Gaps section reads "None." No item is silently dropped.
