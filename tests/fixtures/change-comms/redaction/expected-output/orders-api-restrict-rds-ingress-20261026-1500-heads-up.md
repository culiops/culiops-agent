**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md`, `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md`, operator-supplied

## Draft

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets (target host <ip>)
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Message type / platform | heads-up / Google Chat | `operator-supplied` (type from the request; platform is the skill default, confirmed by the operator) |
| Title, closing line | fixed wording ("🔧 Heads-up: infra change on", "Reply here if this window conflicts.") | `skill shape: examples/messages.md#heads-up` |
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` (confirmed at GATE 1) |
| Execution path | PR (heads-up is before the merge that triggers apply) | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` (`Execution path`) |
| What | restrict orders-db security group ingress to the app subnets | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` (`Change`), summarised |
| Window start | 2026-10-27 14:00 ("tomorrow 14:00", resolved against session date 2026-10-26) | `operator-supplied` |
| Window duration | 15 min | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Impact | connections drop briefly if the rule is wrong, otherwise none (used as given) | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Verdict` |
| Rollback | revert the PR and re-apply, ~10 min | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` (Phase 1, Rollback path), summarised |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Ticket Reference` (parsed from the URL) |
| PR | https://github.com/acme/orders-infra/pull/490 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Execution Log` (Phase 1, `Execution:` line) |
| Target host | `<ip>` (value masked; operator typed a raw IP when editing, folded into the What line to stay within the 8-line cap) | `operator-supplied` (operator edit, heads-up draft) |

Not used as the window or as any event time: record `Date` fields (iac `2026-10-27 13:15`, no timezone, the time the record was written; pre-flight `2026-10-27 13:00 (UTC)`).

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | ARN | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `orders-db` |
| 2 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<cidr>` (dropped from the summary) |
| 3 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<cidr>` (dropped from the summary) |
| 4 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<ip>` (dropped from the summary) |
| 5 | access key | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<redacted-secret>` |
| 6 | access key | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<redacted-secret>` |
| 7 | IPv4 | operator edit (heads-up draft) | `<ip>` |

## Open TODOs
none

## Flags
- Flag: access key found in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` and `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` (both cite the same hard-coded credential in a deploy script). The value appears in a record, rotate it. Masked in all output, not repeated here.
