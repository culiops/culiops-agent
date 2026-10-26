**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Slack`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md` (Date 2026-10-27 11:00, Execution path: Direct apply); operator-supplied (platform, apply-time answer)

## Draft

```text
✅ Done: orders-api ALB 5xx alarm (prod), finished <TODO: apply time>
Verified: re-plan shows no changes, alarm in OK state
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (`**Execution path:**`) |
| Change | Add CloudWatch alarm for orders-api ALB 5xx rate | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (`**Change:**`) |
| Outcome | completed (direct apply: outcome comes from the record) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Apply result | Apply complete; 1 resource added, 0 changed, 0 destroyed (plan counts kept here, not in the draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Execution) |
| Verification | re-plan reported no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification) |
| Apply time | `<TODO: apply time>` (Execution Log states none; operator answered "don't know") | `operator-supplied` (no value given) |
| Timezone | not supplied; no time is shown in this draft | `operator-supplied` (no answer) |
| Ticket key | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Platform | Slack | `operator-supplied` |
| Record Date (not used as an event time) | 2026-10-27 11:00, no timezone, time the record was written | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Commit (not in draft) | b1c2d3e | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: apply time>` (result title line). Operator answered "don't know".
- Timezone was not supplied. No time appears in the draft, so no `<TODO: timezone>` is shown.

## Flags

none
