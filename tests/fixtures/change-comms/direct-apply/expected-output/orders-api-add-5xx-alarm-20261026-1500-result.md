**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Slack`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api ALB 5xx alarm (prod), applied <TODO: apply time>*
Verified: re-plan showed no changes, alarm state OK
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| What | Add CloudWatch alarm for orders-api ALB 5xx rate (title shortened to "orders-api ALB 5xx alarm") | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (Change line) |
| Outcome | success (completed; apply complete, 1 added, 0 changed, 0 destroyed) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome and .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution line) |
| Verification | re-plan showed no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification line) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| PR | none (direct apply); PR line omitted | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (Execution path) |
| Platform | Slack | operator-supplied |
| Apply time | <TODO: apply time> | operator-supplied (not given) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- <TODO: apply time> (the Execution Log states none and the operator did not know it)

## Flags

none
