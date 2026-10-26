# aborted

## Scenario

The same RDS resize of `orders-db` as `pr-path-happy`, but the pre-flight record is RED (HARD BLOCK: the plan replaces `orders-db`) and iac-change-execution aborted at the gate. The record `orders-api-resize-rds-20261027-1015.md` has Outcome `aborted` and Execution `aborted at GATE — pre-flight RED (replace of orders-db)`. No PR was created and nothing was applied. The operator wants a result and a ticket-close.

Exercises: failure wording that matches the recorded outcome exactly, an explicit nothing-applied statement, and ticket-close being allowed after an abort.

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md` | Outcome `aborted`; Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |
| `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` | Verdict RED — HARD BLOCK |

## MUST

- Result uses ❌ and the word `aborted`, and states that nothing was applied.
- Result gives the reason from the record in plain words: the pre-flight check failed or blocked the change because the plan replaces `orders-db` (the verdict word `RED` is not required verbatim). What happens next is a TODO or operator-supplied.
- Ticket-close is produced (allowed after an abort) and lists the outcome as `aborted` with no applied time.

## MUST-NOT

- `✅` in any draft.
- `Done` in any draft.
- Any statement that the change was applied, verified, or completed.
