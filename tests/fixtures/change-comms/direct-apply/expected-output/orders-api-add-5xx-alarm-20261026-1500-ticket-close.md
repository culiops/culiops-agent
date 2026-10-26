**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan shows no changes, alarm state OK
Rollback: not needed. Remove the alarm and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Environment | prod (not shown in this draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| What | Add CloudWatch alarm for orders-api ALB 5xx rate | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply (so the PR line is omitted; nothing to link) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Outcome | completed → title "Change completed" | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Execution result | apply finished with no error | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution line) |
| Verification | re-plan shows no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification line) |
| Applied | `<TODO: apply time>` | `operator-supplied (not given)` |
| Rollback status | not needed (confirmed success: Outcome completed, clean Execution, clean Verification) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` and `#Execution Log` |
| Rollback revert instruction | remove the alarm and re-apply (summarised, no command) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` (Phase 1, Rollback path line) |
| Ticket key | OPS-123 (Jira URL gives the key; the comment goes on this ticket, so no key line in the shape) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Platform | Jira comment (ticket-close is always Jira) | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: apply time>` (operator did not know it)

## Flags

none
