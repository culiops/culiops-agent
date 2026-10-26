**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan showed no changes, alarm state OK
Rollback: not needed. Remove the alarm resource and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| What | CloudWatch alarm added for orders-api ALB 5xx rate (Phase 1 of 1: add 5xx alarm; 1 resource to add) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` and `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (Change line) |
| Outcome | success (completed; apply complete, 1 added, 0 changed, 0 destroyed) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome and .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution line) |
| PR | none (direct apply); PR line omitted | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (Execution path) |
| Applied | <TODO: apply time> | operator-supplied (not given) |
| Verification | re-plan showed no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification line) |
| Rollback status | not needed (confirmed success) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome and .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution line) |
| Rollback instruction | remove the alarm resource and re-apply (no PR to revert, command omitted) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` (Rollback path) |
| Ticket key | OPS-123 (not shown in the Jira comment; it is the ticket) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Platform | Jira comment (always for ticket-close) | operator-supplied |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- <TODO: apply time> (the Execution Log states none and the operator did not know it)

## Flags

none
