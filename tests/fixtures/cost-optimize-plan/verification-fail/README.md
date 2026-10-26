# verification-fail — cost-optimize-plan fixture

Single-item report recommending deletion of `bucket-logs-active` ($400/mo). Verification reads real S3 request activity from the bucket's server access logs and finds daily GET traffic; the skill places the item in 🚫 Do not act, demonstrating Law 3 (no tier without evidence) and resisting the upstream recommendation.

## What's modelled

Account `123456789012` (`acme-prod`), region `ap-southeast-1`. The upstream waste audit flagged `bucket-logs-active` because its $400/mo cost was flat for 90+ days, it has no lifecycle policy and the name is not in the active-service tag scope. The bucket has **server access logging enabled** into `acme-s3-access-logs` (same account), with history from 2025-11-10. No S3 request-metrics configuration exists.

**IaC repo: simulated** (`~/acme-infra`); `mock-responses/iac-grep-simulated.json` stands in for the grep, and the `code:` refs (`s3.tf:88`, `lambda.tf:140`) are illustrative.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md"

(See `operator-question.md`.)

## What this fixture exercises

- **S3 activity from a real data-event source.** `delete-s3-bucket.md` order: (3a) request metrics: none → (3b) server access logs: available, read from the log bucket → (3c) CloudTrail Lake: not needed. `cloudtrail lookup-events` is never used for object activity (management events only).
- **Target check + ownership probe** (`0a`, `0b`).
- **Evidence 🚫 on a recurring, recent pattern:** 3,694 GETs in 90d, 1,247 in the last 30d, every day, last 2026-05-27 14:32 UTC, single principal `lambda-export-fn`. Principle 3: steady use, not a historical burst.
- **Skill resists the upstream recommendation:** a `high`-confidence delete lands in 🚫 with the evidence quoted, NOT silently dropped.
- **Zero-actionable plan:** every actionable tier empty, `$0/mo` total.
- **Secrets rule:** the access-log result is a summary (counts and distribution); no rows, IPs or keys.

> **Mock convention:** `access-log-summary-bucket-logs-active.json` is a summary of reading ~3,800 log objects, not a real response shape. The counts are the signal.

## Files in this fixture

Row = the `#` in the plan's "Verification queries run" table.

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | — | The freeform operator request |
| `upstream-report.md` | — | Synthetic waste report (skill input) |
| `mock-responses/sts-get-caller-identity.json` | 0a | Target check |
| `mock-responses/iac-grep-simulated.json` | 0b | Simulated IaC grep (owner terraform) |
| `mock-responses/get-bucket-tagging-bucket-logs-active.json` | 0b | Bucket tags |
| `mock-responses/get-bucket-location-bucket-logs-active.json` | 1 | Bucket region (Metrics-rule precondition) |
| `mock-responses/get-bucket-versioning-bucket-logs-active.json` | 2 | Versioning Suspended |
| `mock-responses/get-bucket-lifecycle-configuration-bucket-logs-active.json` | 2 | No lifecycle rule |
| `mock-responses/list-bucket-metrics-configurations-bucket-logs-active.json` | 3 | No request-metrics configuration |
| `mock-responses/get-bucket-logging-bucket-logs-active.json` | 4 | Access logging enabled → `acme-s3-access-logs` |
| `mock-responses/access-log-summary-bucket-logs-active.json` | 4 | **Summarized 90d access-log read: the disqualifying signal** |
| `mock-responses/get-metric-data-bucket-size-bucket-logs-active-90d.json` | 5 | Object count growth + non-empty check |
| `mock-responses/get-bucket-policy-bucket-logs-active.json` | 6 | `NoSuchBucketPolicy` |
| `mock-responses/get-bucket-replication-bucket-logs-active.json` | 7 | No replication |
| `mock-responses/log-target-sweep-bucket-logs-active.json` | 8 | Not a log destination |
| `mock-responses/dns-sweep-bucket-logs-active.json` | 9 | No DNS reference |
| `expected-output.md` | — | The plan the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | — | Gate transitions and acceptance check |

## Expected outcome

The single item lands in 🚫 Do not act. The disqualifying-evidence cell quotes the access-log signal with the `live:4` reference. The plan summary shows 0 in every actionable tier. The item is neither dropped nor in any other tier.
