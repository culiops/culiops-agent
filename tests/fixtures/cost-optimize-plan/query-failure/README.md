# query-failure - cost-optimize-plan fixture

3-item upstream report. Mid-verification, a query the S3 playbook really uses (`cloudtrail:StartQuery` for CloudTrail Lake, the last-resort S3 activity source) returns `AccessDeniedException`. The skill MUST stop the batch, surface the failure, and NOT write a partial plan. Validates Constraint 8 (stop on query failure) and Law 3 (no silent promotion of items with incomplete evidence).

## What's modelled

Account `123456789012` (acme-prod), region ap-southeast-1. 3-item waste report: S3 bucket `bucket-logs-2019` ($180/mo), EBS volume `vol-0cccc1` ($35/mo), ALB `prod-old-lb` ($25/mo). The IAM principal running the skill can describe and list (including the CloudTrail event data store) but is not allowed `cloudtrail:StartQuery`. The skill plans the batch at GATE 2 (it lists the needed permissions, it does not pre-check them), the operator approves, and the failure surfaces at Step 3.

No IaC repo is supplied at GATE 1 ("none - ownership from tags only"), so ownership probes resolve to `unknown`.

## The operator question

(see `operator-question.md`)

## What this fixture exercises

- Query 0 succeeds: target check (`0a`) and ownership probes for all three items (`0b-1..3`).
- Item #1 queries 1-5 succeed: bucket has no request-metrics configuration and no access logging, so the playbook falls through to CloudTrail Lake; an existing event data store is found.
- **Query 6, `cloudtrail:StartQuery`, is denied** -> skill stops.
- Queries 7+ (rest of item #1, all of items #2 and #3) are NEVER executed; `mock-responses/` omits them intentionally.
- The skill surfaces: failure reason, required permission, and three remedies (grant, trim the item, investigate SCP / boundary).
- **No plan file is written.** A partial plan must not be confused with a complete one.

## Files in this fixture

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | - | freeform operator prompt |
| `upstream-report.md` | - | synthetic 3-item cloud-cost-investigate report |
| `mock-responses/sts-get-caller-identity.json` | 0a | target check ok |
| `mock-responses/get-bucket-tagging-bucket-logs-2019.json` | 0b-1 | ownership probe (owner unknown) |
| `mock-responses/describe-volumes-vol-0cccc1.json` | 0b-2 | ownership probe (owner unknown) |
| `mock-responses/describe-tags-prod-old-lb.json` | 0b-3 | ownership probe (owner unknown) |
| `mock-responses/get-bucket-location-bucket-logs-2019.json` | 1 | ok |
| `mock-responses/get-bucket-versioning-and-lifecycle-bucket-logs-2019.json` | 2 | ok |
| `mock-responses/list-bucket-metrics-configurations-bucket-logs-2019.json` | 3 | none (source 3a unavailable) |
| `mock-responses/get-bucket-logging-bucket-logs-2019.json` | 4 | logging off (source 3b unavailable) |
| `mock-responses/cloudtrail-event-data-store-org-data-events.json` | 5 | existing Lake store found (source 3c) |
| `mock-responses/start-query-bucket-logs-2019-denied.json` | 6 | **AccessDeniedException** (fixture error convention) |
| `expected-output.md` | - | the error surfaced to the operator (NOT a plan) |
| `DRY-RUN-NOTES.md` | - | gate transitions and acceptance check |

> Queries 7+ are never reached because the skill aborts after row 6. No mocks for them are included.

## Expected outcome

Skill aborts at Step 3 with an error message. No plan file written. The operator grants the missing permission and re-runs, or returns to GATE 2 to trim item #1 from scope.
