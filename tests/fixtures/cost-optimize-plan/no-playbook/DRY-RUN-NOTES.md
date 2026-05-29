# Dry-run notes — no-playbook

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides path to upstream report (`operator-question.md`). Skill loads `upstream-report.md`, extracts 1-item Remediation list, reads `**Cloud:** aws` (single-cloud), `**Scope:** 123456789012 / acme-prod`. Applies $5/mo floor — 1 item passes ($420). No catalog at `.culiops/service-discovery/` — Dimension 4 will score ⚪ (treated as 🟡-equivalent). Skill presents scoping summary: 1 item, $420/mo, aws, single account, no catalog. Operator confirms. Approved.

2. **GATE 2: empty verification batch.** Skill attempts to look up playbook for item #1 (delete Aurora cluster). No `(aws, delete, aurora-cluster)` playbook exists in v1 (`examples/aws/delete-aurora-cluster.md` is absent). Item is routed to `manual-review-required` queue. Skill surfaces: "1 item considered; 0 items have matching playbooks; 1 item routed to manual review. No verification queries to run." Operator can approve-to-skip (proceeding to Step 4) or trim (no-op since batch is empty). In this fixture: operator approves-to-skip.

3. **Step 3 skipped** — no verification queries to execute (batch is empty).

4. **Step 4 (Triage)** — 1 item with no playbook match assigned to ❔ tier. Skill populates Reason column with: (a) explicit statement that no `delete-aurora-cluster` playbook exists in v1; (b) concrete manual-verification checklist covering 90d connection / query history (extending the upstream 30d window to catch quarterly jobs), Secrets Manager / SSM Parameter Store endpoint references, read-replica + cross-region replication relationships, ECS / Lambda / EC2 endpoint references, and final-snapshot guidance.

5. **GATE 3 (Plan review)** — Plan drafted with ❔ section as the only populated section. All four actionable tiers (🟢/🟡/🔴/🚫) are present but empty. Operator reviews, approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-1105.md`.

## What this fixture validates

- **Spec Constraint #3: no-playbook items are NOT silently skipped** — they go to manual review with an explicit reason. The item appears in `## ❔ Manual review required` with a populated Reason column, not in a silent discard pile.
- **Empty verification batch path:** GATE 2 is confirmable but is effectively a no-op when there are no playbook matches. The skill surfaces the empty-batch state to the operator explicitly ("0 items have matching playbooks; 1 item routed to manual review") rather than silently bypassing GATE 2.
- **Plan compose handles zero-actionable-items case:** 🟢/🟡/🔴/🚫 sections all show "No items in this tier." ❔ section is the only populated one. Plan summary table shows 0 for all actionable tiers and 1 for ❔.
- **❔ Reason column carries operator guidance** — not just "no playbook" but a specific manual-verification checklist (CloudWatch 90d activity, Secrets Manager / SSM, read replicas + Global Database, application endpoint references, final-snapshot pre-deletion guidance).
- **No error on unknown action type:** the skill degrades gracefully when encountering an Aurora cluster delete recommendation rather than erroring out or producing a malformed plan.

## Acceptance check

A reviewer confirms: (a) the skill does not error out when encountering an Aurora cluster delete recommendation; (b) the item appears in the plan's ❔ Manual review section with a specific reason; (c) no verification queries were attempted against RDS / Aurora APIs (the fixture's empty mock-responses/ directory is consistent with the skill's actual behavior); (d) the reason column gives the operator a concrete checklist of what to verify manually.

## History

This fixture originally used a Lambda function delete (`idle-worker`) as the no-playbook scenario. In v0.9, `examples/aws/delete-lambda.md` was added, so the fixture was swapped to Aurora cluster delete — still uncovered in v1 — to preserve the "no playbook → manual review" test scenario. If a future release adds `delete-aurora-cluster.md`, swap this fixture again to a resource type that remains uncovered.
