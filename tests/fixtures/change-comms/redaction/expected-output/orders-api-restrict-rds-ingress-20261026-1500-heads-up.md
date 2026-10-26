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
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` |
| Platform | Google Chat | `operator-supplied` |
| Window start | 2026-10-27 14:00 ("tomorrow" resolved against session date 2026-10-26) | `operator-supplied` |
| Window duration | 15 min | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| What | restrict orders-db security group ingress to the app subnets | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` (Change line) |
| Target host | `<ip>` (value typed by the operator at GATE 2, masked) | `operator-supplied` |
| Impact | connections drop briefly if the rule is wrong, otherwise none (used as given) | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Verdict` |
| Rollback | revert the PR and re-apply, ~10 min | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` (Phase 1, Rollback path line) |
| Ticket | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/490 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Execution Log` (Phase 1, Execution line) |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | account ID | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `<account-id>` (dropped) |
| 2 | account ID (in bucket name) | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `orders-backup-<account-id>` (dropped) |
| 3 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<cidr>` (dropped) |
| 4 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<ip>` (dropped) |
| 5 | access key | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<redacted-secret>` (dropped) |
| 6 | ARN | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `orders-db` (dropped) |
| 7 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<cidr>` (dropped) |
| 8 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<ip>` (dropped) |
| 9 | account ID | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#header` | `<account-id>` (dropped) |
| 10 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Risk Scorecard` | `<cidr>` (dropped) |
| 11 | ARN | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `orders-db` (dropped) |
| 12 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<cidr>` (dropped) |
| 13 | access key | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<redacted-secret>` (dropped) |
| 14 | IPv4 | operator edit (heads-up draft) | `<ip>` |

## Open TODOs

none

## Flags

- Flag: access key found in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` and `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence`. The value appears in a record, rotate it. It was masked and kept out of every draft.
