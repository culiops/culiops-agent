**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md`, `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets; target host <ip>
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert PR + apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Header` (title line) |
| Window | 2026-10-27 14:00 ICT, 15 min (operator said "tomorrow 14:00, 15 min ICT"; "tomorrow" resolved against session date 2026-10-26) | `operator-supplied` |
| What | restrict orders-db security group ingress to the app subnets | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Header` (Change) |
| What (added at review) | target host `<ip>` (value masked, see log #17; folded into the What line to stay within 8 lines) | `operator-supplied` |
| Impact | connections drop briefly if the rule is wrong, otherwise none | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Verdict` |
| Rollback | revert PR + apply, ~10 min (summarised from "revert PR and re-apply, ~10 min") | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/490 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Execution Log` (Phase 1, Execution line) |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | ARN | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `orders-db` (dropped) |
| 2 | ARN | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `orders-db` (dropped) |
| 3 | account ID | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `<account-id>` (dropped) |
| 4 | account ID (in bucket name) | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `orders-backup-<account-id>` (dropped) |
| 5 | account ID | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Header (Target line)` | `<account-id>` (dropped) |
| 6 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<cidr>` (dropped) |
| 7 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<cidr>` (dropped) |
| 8 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Risk Scorecard` | `<cidr>` (dropped) |
| 9 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<cidr>` (dropped) |
| 10 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<ip>` (dropped) |
| 11 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<ip>` (dropped) |
| 12 | access key | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<redacted-secret>` (dropped) |
| 13 | access key | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<redacted-secret>` (dropped) |
| 14 | plan output counts | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | omitted from draft (dropped) |
| 15 | plan output counts | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Execution Log` | omitted from draft (dropped) |
| 16 | plan output counts | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Risk Scorecard` | omitted from draft (dropped) |
| 17 | IPv4 | operator edit (heads-up draft) | `<ip>` |

## Open TODOs
none

## Flags
Flag: access key found in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` and `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence`. The value appears in a record, rotate it. It is masked and not used in any draft.
