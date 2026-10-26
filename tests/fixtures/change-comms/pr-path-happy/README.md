# pr-path-happy

## Scenario

The default PR path for a one-phase Terraform change: resize RDS `orders-db` for `orders-api` (prod, `ap-southeast-1`). The iac-change-execution record `orders-api-resize-rds-20261027-1015.md` has Outcome `completed`, which on the PR path only means the PR was created: Verification reads `pending — pipeline applies after merge`. A pre-flight record `orders-api-resize-rds-20261027-1000.md` carries the verdict YELLOW. A **stale** record for the same service, `orders-api-rotate-logs-20261019-0900.md` (Outcome `aborted`), is also present as a trap for "newest matching record" logic.

Exercises: source selection, the PR-path no-apply-claim rule, timezone elicitation, operator-supplied impact, all three message types, Google Chat format.

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md` | The change. PR #482 in the Execution line. Rollback in Change Plan: `revert PR #482 and re-apply, ~10 min`. Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |
| `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` | Verdict YELLOW — PROCEED WITH CAUTION |
| `.culiops/iac-change-execution/orders-api-rotate-logs-20261019-0900.md` | Stale, Outcome aborted. Must NOT be used |

## MUST

- Confirm the chosen record with the operator: `orders-api-resize-rds-20261027-1015.md` (and the 1000 pre-flight), not `orders-api-rotate-logs-20261019-0900.md`.
- Ask for the timezone when the window `tomorrow 14:00, 15 min` arrives without one.
- Heads-up is at most 8 lines and contains `YELLOW`, `OPS-123` and `https://github.com/acme/orders-infra/pull/482`.
- Heads-up impact is the operator's `~30-60s Multi-AZ failover, writes may fail briefly`; rollback cites `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan`.
- Ask for the apply time, apply outcome and verification BEFORE producing the result draft.
- Result draft contains `14:12 ICT`.
- Ticket-close contains the PR URL, the applied time `14:12 ICT` and the operator's verification.

## MUST-NOT

- Any apply claim sourced from `Outcome: completed`.
- The string `10:15` shown as an apply time (the record `Date` is when the record was written).
- Use of the stale `orders-api-rotate-logs-20261019-0900.md` record as a source.
