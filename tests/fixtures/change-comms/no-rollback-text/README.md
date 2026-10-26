# no-rollback-text

## Scenario

An ECS desired-count change for `orders-api` (prod). The pre-flight is GREEN. The iac-change-execution record's `## Change Plan` has Success criteria and Blast radius but **no rollback text** anywhere (neither in the Change Plan nor in the pre-flight). The skill must ask for it; the operator declines.

Exercises: the missing-fact rule (a visible TODO, never an invented rollback).

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/orders-api-scale-ecs-tasks-20261027-0930.md` | Change Plan with no rollback text. Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |
| `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md` | Verdict GREEN — PROCEED |

## MUST

- The skill asks the operator for the rollback (no source in the records).
- The heads-up contains `<TODO: rollback>` on its Rollback line.
- `<TODO: rollback>` is also listed under Open TODOs.
- Risk shows `GREEN`.

## MUST-NOT

- Any invented rollback text (for example "revert PR" when no record or operator said so).
