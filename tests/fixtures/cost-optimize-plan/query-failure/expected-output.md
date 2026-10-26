# Expected skill behavior — query-failure fixture

The skill aborts at Step 3 (Execute Verification) and surfaces this message to the operator. **No plan is written.**

> **Verification query #6 failed: `cloudtrail:StartQuery` returned `AccessDeniedException`.**
>
> **Resource:** `bucket-logs-2019`
> **Item:** #1 - Delete S3 bucket bucket-logs-2019 ($180/mo)
> **Query:** `delete-s3-bucket.md` activity source 3c: CloudTrail Lake `StartQuery` on event data store `org-data-events` (the only remaining source: no request-metrics configuration, no access logging)
> **Required permission:** `cloudtrail:StartQuery` (and `cloudtrail:GetQueryResults`) on that event data store
> **AWS error:** `User: arn:aws:iam::123456789012:user/ops is not authorized to perform: cloudtrail:StartQuery on resource: arn:aws:cloudtrail:ap-southeast-1:123456789012:eventdatastore/11111111-2222-3333-4444-555555555555 because no identity-based policy allows the cloudtrail:StartQuery action`
>
> **The skill has stopped - no plan written.** A failed query is never downgraded to an unobserved signal and never skipped (Constraint 8): the batch stops.
>
> Suggested next actions:
> 1. **Grant the missing permission** and re-run the skill from scratch: add `cloudtrail:StartQuery` and `cloudtrail:GetQueryResults` for `org-data-events` to the principal's policy. Note this query is billed per GB scanned (itemized at GATE 2).
> 2. **Trim item #1 from the batch** at GATE 2 (re-run the skill and drop item #1 from scope). It is then not triaged and must not be acted on from this report.
> 3. **Investigate the denial** - there may be an SCP or permission boundary. Check `iam:SimulatePrincipalPolicy` against the calling principal.
>
> **State of evidence collected before abort (discarded, not committed):**
> - Query 0 (target check + ownership probes): `0a` ok (account 123456789012 = `Scope`); `0b-1`/`0b-2`/`0b-3` ok (owner `unknown` for all three: no IaC repo supplied).
> - Item #1 (bucket-logs-2019): rows 1-5 ok (region, versioning/lifecycle, no request metrics, no access logging, event data store found); row 6 failed.
> - Item #2 (vol-0cccc1): no playbook query executed beyond the ownership probe.
> - Item #3 (prod-old-lb): no playbook query executed beyond the ownership probe.

## What was NOT written

- No plan file at `.culiops/cost-optimize-plan/acme-prod-*.md`, and no dev-notes.
- No partial plan with items #2 or #3 promoted to a tier (would violate Law 3: no tier without a complete evidence set).
- No tier badge assigned to any item.

## What the operator should expect

After remediating the IAM gap (or trimming item #1), the operator re-runs the skill from scratch. There is no "resume" mode: every run is independent.
