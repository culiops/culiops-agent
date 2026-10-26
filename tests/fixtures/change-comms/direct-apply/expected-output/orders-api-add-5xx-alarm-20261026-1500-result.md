**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Slack`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`; operator-supplied (platform; apply time not given)

## Draft

```text
*✅ Done: orders-api add CloudWatch alarm for ALB 5xx rate (prod), applied <TODO: apply time>*
Verified: re-plan shows no changes, alarm state OK
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Platform | Slack | `operator-supplied` |
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (IaC change execution for)` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Execution path)` |
| What | Add CloudWatch alarm for orders-api ALB 5xx rate | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Change)` |
| Outcome | completed (success, direct apply, so `✅ Done`) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Applied | `<TODO: apply time>` (Execution Log states no time; operator answered "don't know") | `operator-supplied (not given)` |
| Timezone | not given; no time is shown in this draft, so none is needed | `operator-supplied (not given)` |
| Verification | re-plan shows no changes, alarm state OK (CLI command omitted from draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification) |
| Ticket | OPS-123 (key parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| PR | omitted: direct apply, no PR exists | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Execution path)` |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | plan output (counts) | `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` | summarised in words, not carried into any draft (dropped) |
| 2 | plan output (counts) | `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` | summarised in words, not carried into any draft (dropped) |

## Open TODOs
- `<TODO: apply time>` (title line)

## Flags
none
