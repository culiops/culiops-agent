**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md`, `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 11:00 ICT, 10 min
What: scale orders-api ECS desired task count 3 → 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / environment | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` |
| What | scale orders-api ECS desired task count 3 → 5 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` (Change line) |
| Platform | Google Chat | `operator-supplied` |
| Window start | 2026-10-27 11:00 ("tomorrow" resolved against session date 2026-10-26) | `operator-supplied` |
| Window duration | 10 min | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Impact | none expected, tasks are added alongside the existing ones | `operator-supplied` |
| Risk | GREEN | `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#Verdict` |
| Rollback | `<TODO: rollback>` | `operator-supplied (not given)` (the Change Plan has no rollback text; the operator declined to give one) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Ticket Reference` (key parsed from the URL) |
| PR | https://github.com/acme/orders-infra/pull/495 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` (Phase 1, Execution line) |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: rollback>` (Rollback line): no rollback text in the Change Plan, and the operator did not supply one.

## Flags
none
