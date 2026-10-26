**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md`, `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets (target host <ip>)
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, about 10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` |
| What | restrict orders-db security group ingress to the app subnets | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#header` (Change line) |
| Window date | tomorrow → 2026-10-27 | `operator-supplied` |
| Window start | 14:00 | `operator-supplied` |
| Duration | 15 min | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Impact | connections drop briefly if the rule is wrong, otherwise none | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Verdict` |
| Rollback | revert the PR and re-apply, about 10 min | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` (Phase 1, Rollback path) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Ticket Reference` (Jira URL gives the key) |
| PR | https://github.com/acme/orders-infra/pull/490 | `record: .culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Execution Log` (Phase 1, Execution line) |
| Target host | `<ip>` (masked IPv4) | `operator-supplied` (GATE 2 edit) |
| Platform | Google Chat | `operator-supplied` |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | account ID | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#header` | `<account-id>` (dropped) |
| 2 | ARN | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `orders-db` (dropped) |
| 3 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Risk Scorecard` | `<cidr>` (dropped) |
| 4 | CIDR | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<cidr>` (dropped) |
| 5 | access key | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<redacted-secret>` (dropped) |
| 6 | inline credential | `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence` | `<redacted-secret>` (dropped) |
| 7 | account ID | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `<account-id>` (dropped) |
| 8 | account ID (in bucket name) | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `orders-backup-<account-id>` (dropped) |
| 9 | GitHub token | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary` | `<redacted-secret>` (dropped) |
| 10 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<cidr>` (dropped) |
| 11 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<ip>` (dropped) |
| 12 | access key | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<redacted-secret>` (dropped) |
| 13 | inline credential | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence` | `<redacted-secret>` (dropped) |
| 14 | ARN | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `orders-db` (dropped) |
| 15 | CIDR | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<cidr>` (dropped) |
| 16 | IPv4 | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `<ip>` (dropped) |
| 17 | password in URL | `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan` | `postgres://<redacted-secret>@orders-db.internal:5432/orders` (dropped) |
| 18 | Slack token | operator answer | `<redacted-secret>` (dropped) |
| 19 | IPv4 | operator edit (heads-up draft) | `<ip>` |

## Open TODOs

none

## Flags

- Flag: access key in `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence`. The value was exposed, rotate it.
- Flag: credential (secret access key style value) in `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md#Evidence`. The value was exposed, rotate it.
- Flag: GitHub token in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Research Summary`. The value was exposed, rotate it.
- Flag: access key in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence`. The value was exposed, rotate it.
- Flag: credential (secret access key style value) in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Evidence`. The value was exposed, rotate it.
- Flag: password in a connection URL in `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md#Change Plan`. The value was exposed, rotate it.
- Flag: Slack token in operator answer. The value was exposed, rotate it.
