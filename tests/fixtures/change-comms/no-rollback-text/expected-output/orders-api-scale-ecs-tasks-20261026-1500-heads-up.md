**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md`, `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 11:00 ICT, 10 min
What: scale orders-api ECS desired task count from 3 to 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header (IaC change execution for)` |
| Execution path | PR (heads-up is before the merge that triggers apply) | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header (Execution path)` |
| Platform | Google Chat | `operator-supplied` (skill default, operator confirmed) |
| When | 2026-10-27 11:00 ICT, 10 min | `operator-supplied` (operator said "tomorrow 11:00, 10 min ICT"; "tomorrow" resolved to 2026-10-27 against session date 2026-10-26) |
| What | scale orders-api ECS desired task count from 3 to 5 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header (Change)` |
| Impact | none expected, tasks are added alongside the existing ones | `operator-supplied` |
| Risk | GREEN | `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#Verdict` |
| Rollback | <TODO: rollback> | `operator-supplied (not given)` (the Change Plan holds no rollback text; operator declined to supply one) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Ticket Reference` (key parsed from the ticket URL) |
| PR | https://github.com/acme/orders-infra/pull/495 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` (Phase 1, `Execution:` line) |

Facts that came from the operator: platform, When, Impact. Rollback was asked and not given.

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | plan output (counts) | `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Change Plan` | omitted (dropped) |
| 2 | plan output (counts) | `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` | omitted (dropped) |

## Open TODOs
- `<TODO: rollback>`: the Change Plan has no rollback text and the operator declined to give one.

## Flags
none
