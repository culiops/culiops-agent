**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md` (Date 2026-10-27 09:30, execution path PR), `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md` (Date 2026-10-27 09:15 UTC), operator-supplied

## Draft

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 11:00 ICT, 10 min
What: increase orders-api ECS desired task count 3 → 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` (title line) |
| Execution path | PR (heads-up is before the merge that triggers apply; no apply is claimed) | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` (`Execution path`) |
| Window start | 2026-10-27 11:00 | `operator-supplied` ("tomorrow 11:00"; "tomorrow" resolved to 2026-10-27 from the session date 2026-10-26) |
| Duration | 10 min | `operator-supplied` ("10 min") |
| Timezone | ICT | `operator-supplied` |
| What | increase orders-api ECS desired task count 3 → 5 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#header` (`Change`); same in `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#header` (`Action`) |
| Impact | none expected, tasks are added alongside the existing ones (as given, unedited) | `operator-supplied` |
| Risk | GREEN | `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#Verdict`; also `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` (Phase 1 pre-flight verdict) |
| Rollback | `<TODO: rollback>` | no rollback text in `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Change Plan`; operator declined to supply one (`operator-supplied`: "I don't have a rollback to give, leave it open") |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Ticket Reference` (key parsed from `https://acme.atlassian.net/browse/OPS-123`) |
| PR | https://github.com/acme/orders-infra/pull/495 | `record: .culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md#Execution Log` (Phase 1, `Execution:` line) |
| Title and closing line | fixed wording of the heads-up shape | `skills/change-comms/examples/messages.md#heads-up` |
| Committed mitigations | none to cite (pre-flight `Mitigations Committed` is "None"), so no mitigation line | `record: .culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md#Mitigations Committed` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: rollback>` (Rollback line): the Change Plan holds no rollback text and the operator declined to supply one.

## Flags

none
