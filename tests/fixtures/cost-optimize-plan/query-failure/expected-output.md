# Expected skill behavior — query-failure fixture

The skill aborts at Step 3 (Execute Verification) and surfaces this message to the operator:

> **Verification query #2 failed: `cloudtrail:LookupEvents` returned `AccessDeniedException`.**
>
> **Resource:** `bucket-logs-2019`
> **Item:** #2 — Delete S3 bucket bucket-logs-2019 ($180/mo)
> **Required permission:** `cloudtrail:LookupEvents`
> **AWS error:** `User: arn:aws:iam::123456789012:user/ops is not authorized to perform: cloudtrail:LookupEvents...`
>
> **The skill has stopped — no plan written.**
>
> Suggested next actions:
> 1. **Grant the missing permission** and re-run the skill from scratch: add `cloudtrail:LookupEvents` to the principal's IAM policy.
> 2. **Trim item #2 from the batch** at GATE 2 (re-run skill, drop item #2 when prompted), accepting that item #2 will route to ❔ Manual review instead of being verified.
> 3. **Investigate the IAM denial** — there may be an SCP or permission boundary blocking the action. Check `iam:SimulatePrincipalPolicy` against the calling principal.
>
> **State of evidence collected before abort:**
> - Item #1 (vol-0cccc1): query #1 (`ec2:DescribeVolumes`) succeeded. Evidence captured but not committed.
> - Item #2 (bucket-logs-2019): query #2 (`cloudtrail:LookupEvents`) failed.
> - Item #3 (prod-old-lb): no queries attempted (skill aborted before reaching this item).

## What was NOT written

- No plan file at `.culiops/cost-optimize-plan/acme-prod-*.md`.
- No partial plan with item #1 promoted to a tier (would violate Iron Law #3).
- No tier badge assigned to any item.

## What the operator should expect

After remediating the IAM gap (or trimming item #2), the operator re-runs the skill from scratch. The skill does not have a "resume from where we left off" mode in v1 — every run is independent.
