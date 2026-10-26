**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md` (Date 2026-10-27 11:00, Execution path: Direct apply); operator-supplied (apply-time answer)

## Draft

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate (prod)
PR: <TODO: PR link>
Applied: <TODO: apply time>
Verification: re-plan shows no changes, alarm in OK state
Rollback: not needed. Remove the alarm and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Execution path | Direct apply | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` (`**Execution path:**`) |
| What | Add CloudWatch alarm for orders-api ALB 5xx rate (1 resource added; plan counts kept here, not in the draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` |
| Outcome | completed, confirmed success (Apply complete; verification passed) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` and `#Execution Log` (Phase 1) |
| PR | `<TODO: PR link>`: no `Execution:` line holds a PR URL (direct apply, `terraform apply` line only); operator did not supply one | `operator-supplied` (no value given) |
| Applied | `<TODO: apply time>`: Execution Log states none; operator answered "don't know" | `operator-supplied` (no value given) |
| Verification | re-plan reported no changes; alarm state OK | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` (Phase 1, Verification) |
| Rollback | Remove the alarm and re-apply (summarised from the Change Plan rollback path; the CLI command is not used in the draft) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Change Plan` |
| Rollback "not needed" | allowed because the outcome is a confirmed success | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Outcome` |
| Ticket key (not a draft line; Jira comment goes on this ticket) | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Ticket Reference` |
| Timezone | not supplied; no time is shown in this draft | `operator-supplied` (no answer) |
| Record Date (not used as an event time) | 2026-10-27 11:00, no timezone, time the record was written | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header` |
| Commit and plan hash (not in draft) | b1c2d3e; sha256:c4d6e8… | `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#header`, `#Execution Log` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: PR link>` (PR line). Operator did not supply one; the record has no PR URL.
- `<TODO: apply time>` (Applied line). Operator answered "don't know".
- Timezone was not supplied. No time appears in the draft, so no `<TODO: timezone>` is shown.

## Flags

none
