**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md`, `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 11:00 ICT, 10 min
What: increase orders-api ECS desired task count from 3 to 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` |
| What | increase orders-api ECS desired task count from 3 to 5 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` (Change line) |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` |
| Phases | 1 of 1 (single phase, no phase list needed in What) | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Change Plan` |
| Timezone | ICT | operator-supplied |
| Window start | 2026-10-27 11:00 ICT ("tomorrow 11:00" resolved against session date 2026-10-26) | operator-supplied |
| Window duration | 10 min (as given, no `~` added) | operator-supplied |
| Impact | none expected, tasks are added alongside the existing ones (as given) | operator-supplied |
| Risk | GREEN | `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#Verdict` |
| Rollback | not given | operator-supplied (not given) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/495 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` (Phase 1, Execution line) |
| Platform | Google Chat | operator-supplied |

Note: the Change Plan section holds no rollback text (only files, resources affected, blast radius, success criteria), so rollback was asked of the operator, who had none to give.

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: rollback>` (Change Plan has no rollback text; operator had none to give)

## Flags

none
