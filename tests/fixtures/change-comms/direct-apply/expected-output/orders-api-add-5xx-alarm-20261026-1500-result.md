**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Slack`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api ALB 5xx alarm added (prod), applied <TODO: apply time>*
Verified: re-plan shows no changes, alarm state is OK
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Change | Add CloudWatch alarm for orders-api ALB 5xx rate | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply (so no PR line) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Outcome | completed → Done, ✅ | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Execution result | apply finished with no error | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution line) |
| Verification | re-plan shows no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification line) |
| ✅ conditions (Constraint 10) | Outcome completed, Execution line clean, Verification clean: all three hold | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` and `#Execution Log` |
| Apply time | `<TODO: apply time>` | `operator-supplied (not given)` |
| Timezone | not given; no time is shown, so none is attached | `operator-supplied (not given)` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Platform | Slack | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: apply time>` (operator did not know it)

## Flags

none
