**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Slack`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api 5xx alarm (prod), applied <TODO: apply time>*
Verified: re-plan showed no changes; alarm state OK
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| What (title wording) | 5xx alarm (Add CloudWatch alarm for orders-api ALB 5xx rate) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Outcome | completed, so `✅ Done` (direct apply: Outcome read as applied) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Apply time | `<TODO: apply time>` (operator answered "don't know"; the Execution line states no time; record Date is not an apply time) | `operator-supplied (not given)` |
| Verification | re-plan showed no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log (Phase 1, Verification line)` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| PR | omitted: direct apply, no PR exists | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header (Execution path)` |
| Platform | Slack | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: apply time>` (title line)

## Flags
none
