# Dry-run notes - no-playbook

## Gate transitions

1. **GATE 1 (Scope)** - Operator provides the path to the upstream report. Skill loads `upstream-report.md`, extracts the 1-item Remediation list, reads `**Cloud:** aws` (single-cloud) and `**Scope:** 123456789012 / acme-prod`. Target = account 123456789012, region ap-southeast-1 (from the ARN). $5/mo floor: the item passes ($420). No catalog; no IaC repo supplied. Skill presents the scoping summary. Operator confirms. Approved.

2. **GATE 2: empty verification batch.** Skill looks up a playbook for `(aws, delete, aurora-cluster)`. None exists (`examples/aws.md` lists Aurora under unsupported). The item is routed to `manual-review-required`. Because no item has a playbook, the batch is empty: there is no Query 0 either (the target check and ownership probe belong to a playbook batch). Skill surfaces "1 item considered; 0 items have matching playbooks; 1 item routed to manual review. No verification queries to run." Operator approves-to-skip.

3. **Step 3 skipped** - no queries to run.

4. **Step 4 (Triage)** - the item is assigned to ❔ with a Reason that carries a manual-verification checklist (90d hourly activity via `get-metric-data`, Secrets Manager / SSM references, replicas and global clusters, application endpoint references, ownership incl. the CloudFormation stop rule, final-snapshot guidance).

5. **GATE 3 (Plan review)** - Plan drafted: ❔ is the only populated section; every actionable tier is present and empty. Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-1105.md`, uncommitted.

## What this fixture validates

- **Constraint 3: no-playbook items are NOT silently skipped** - they land in ❔ with an explicit, populated Reason.
- **Empty verification batch path:** GATE 2 is confirmable but effectively a no-op; the skill says so explicitly rather than bypassing it. No Query 0 is issued and the header says the target is "not sts-verified".
- **The skill never invents a verification strategy** for an uncovered type; the checklist is guidance for the operator, not queries the skill runs.
- **No ownership claim without a probe:** the plan states no owner for the item.
- **Plan compose handles the zero-actionable case:** 🟢 / 🟡 / 🔵 / 🔴 / 🚫 show "No items in this tier."; summary 0 everywhere except ❔ = 1.
- **No error on an unknown action type.**

## Acceptance check

A reviewer confirms: (a) the skill does not error on an Aurora cluster delete; (b) the item appears in ❔ with a specific reason; (c) no query of any kind (including sts / ownership) was attempted - the empty `mock-responses/` is consistent; (d) the Reason gives a concrete checklist; (e) header `Target` says it is not sts-verified; `IaC repo(s)` is `none`.

## History

This fixture originally used a Lambda delete as the no-playbook scenario; when `delete-lambda.md` was added it was swapped to an Aurora cluster delete, still uncovered. If a future release adds an Aurora playbook, swap this fixture to a resource type that remains uncovered.
