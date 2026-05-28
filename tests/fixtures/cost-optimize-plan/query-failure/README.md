# query-failure — cost-optimize-plan fixture

3-item upstream report. Mid-verification, query #2 (`cloudtrail:LookupEvents` for an S3 bucket) returns an IAM AccessDeniedException. Skill MUST stop the batch, surface the failure to the operator, and NOT write a partial plan. Validates spec Constraint #8 (stop on query failure) and Iron Law #3 (no silent promotion of items with incomplete evidence).

## What's modelled

Account `123456789012` (acme-prod), region ap-southeast-1. 3-item waste report. The IAM principal running the skill has full `ec2:Describe*` but lacks `cloudtrail:LookupEvents`. The skill plans the verification batch successfully at GATE 2 (it doesn't pre-check IAM, just lists what permissions are needed), the operator approves, and the failure surfaces at Step 3 mid-execution.

## The operator question

(see `operator-question.md`)

## What this fixture exercises

- Query #1 (`ec2:DescribeVolumes`) succeeds — skill captures evidence.
- Query #2 (`cloudtrail:LookupEvents`) returns `AccessDeniedException` — skill stops.
- Queries #3+ are NEVER executed — mock-responses/ omits these intentionally.
- Skill surfaces the failure with: failure reason, required permission, suggested fix (grant perm and re-run OR trim item from batch at GATE 2).
- **No plan file is written to `.culiops/cost-optimize-plan/`.** This is the key validation — partial plans must not be confused with complete ones.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | freeform operator prompt |
| `upstream-report.md` | synthetic 3-item cloud-cost-investigate report |
| `mock-responses/describe-volumes-vol-0cccc1.json` | query #1 success response |
| `mock-responses/lookup-events-bucket-logs-2019-90d.json` | query #2 IAM error response |
| `expected-output.md` | the error message surfaced to operator (NOT a plan file) |
| `DRY-RUN-NOTES.md` | gate transitions + acceptance check |

> Note: queries #3 through #N (for the 2nd and 3rd items in the upstream report) are never reached because the skill aborts after query #2. No mocks for those queries are included.

## Expected outcome

Skill aborts at Step 3 with an error message. No plan file written. Operator must either grant the missing IAM permission and re-run, OR return to GATE 2 to trim the offending item from the batch.
