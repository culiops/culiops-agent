# no-playbook — cost-optimize-plan fixture

Single-item report recommending Lambda function delete. v1 ships no `delete-lambda` playbook. Validates the spec's "no playbook → manual review" graceful-degradation path.

## What's modelled

Account `123456789012` (acme-prod), region ap-southeast-1. cloud-cost-investigate flagged `idle-worker` Lambda function as a $35/mo savings candidate based on 0 invocations in 30d. The skill should route this to manual review — there's no Lambda delete playbook in v1, so the skill cannot verify dependencies (EventBridge rules, API Gateway integrations, etc.) on its own.

## The operator question

(see `operator-question.md`)

## What this fixture exercises

- **No-playbook detection:** at Step 2 (Plan Verification Batch), skill recognizes no matching `(aws, delete, lambda-function)` playbook.
- **Graceful degradation:** item is routed to `manual-review-required` queue, NOT silently skipped.
- **Empty verification batch at GATE 2:** skill surfaces "1 item considered; 0 items have matching playbooks; 1 item routed to manual review. No verification queries to run." Operator approves-to-skip.
- **Step 3 skipped:** no queries to run since batch is empty.
- **Plan compose:** item lands in `## ❔ Manual review required` section with reason populated.
- **Plan summary:** 0 in all actionable tiers, 1 in ❔.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | freeform operator prompt |
| `upstream-report.md` | synthetic cloud-cost-investigate report with 1 Lambda delete recommendation |
| `mock-responses/.gitkeep` | placeholder — empty dir; no verification queries run since no playbook matches |
| `expected-output.md` | the plan the skill produces (only ❔ section populated) |
| `DRY-RUN-NOTES.md` | gate transitions + acceptance check |

## Why mock-responses/ is empty

No playbook matches the Lambda delete action, so the skill routes the item to manual review at Step 2 and produces no verification queries. There is nothing to mock. The `.gitkeep` file exists only to preserve the directory in git — it carries no fixture data.

## Expected outcome

| # | Action | Resource | Savings | Tier | Reason |
|---|--------|----------|---------|------|--------|
| 1 | Delete Lambda function idle-worker | idle-worker | $35/mo | ❔ Manual review | No `delete-lambda` playbook in v1 |
