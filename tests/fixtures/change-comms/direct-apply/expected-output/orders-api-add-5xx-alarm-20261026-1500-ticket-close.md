**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
Change completed
What: Added CloudWatch alarm for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan showed no changes; alarm state OK
Rollback: not needed. Remove the alarm definition and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| What | Added CloudWatch alarm for orders-api ALB 5xx rate | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header (Change)` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Outcome | completed (direct apply, single phase 1 of 1), so no `Outcome:` line | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| PR | line omitted: direct apply, no PR exists | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header (Execution path)` |
| Applied | `<TODO: apply time>` (operator answered "don't know"; the Execution line states no time; record Date is not an apply time) | `operator-supplied (not given)` |
| Verification | re-plan showed no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log (Phase 1, Verification line)` |
| Rollback status | not needed (outcome is a completed direct apply) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Rollback instruction | remove the alarm definition and re-apply (summarised, no command) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan (Rollback path line)` |
| Ticket key (not shown in this draft; the comment is posted on it) | OPS-123 | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Platform | Jira comment (ticket-close is always a Jira comment) | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: apply time>` (Applied line)

## Flags
none
