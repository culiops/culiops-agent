**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md`; operator-supplied (apply time not given)

## Draft

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan showed no changes, alarm state OK
Rollback: not needed. Remove the alarm and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (IaC change execution for)` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Execution path)` |
| What | CloudWatch alarm added for orders-api ALB 5xx rate (from Change: Add CloudWatch alarm for orders-api ALB 5xx rate) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Change)` |
| Outcome | completed (confirmed success on direct apply, so title `Change completed`, no `Outcome:` line) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| PR | line omitted: direct apply, no PR exists | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Header (Execution path)` |
| Applied | `<TODO: apply time>` (Execution Log states no time; operator answered "don't know") | `operator-supplied (not given)` |
| Timezone | not given; no time is shown in this draft, so none is needed | `operator-supplied (not given)` |
| Verification | re-plan showed no changes, alarm state OK (CLI command omitted from draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification) |
| Rollback status | not needed (outcome is a confirmed success) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Rollback instruction | remove the alarm and re-apply if required (summarised from rollback path; CLI command omitted from draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` |
| Ticket | OPS-123 (key parsed from the Ticket Reference URL; no Ticket line in this shape) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | plan output (counts) | `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` | summarised in words, not carried into any draft (dropped) |
| 2 | plan output (counts) | `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` | summarised in words, not carried into any draft (dropped) |

## Open TODOs
- `<TODO: apply time>` (Applied line)

## Flags
none
