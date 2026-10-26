# no-records

## Scenario

No iac-change-execution or pre-flight records exist: `.culiops/` holds only `.gitkeep`. The skill must fall back to the operator-supplied path. The operator answers everything in one message: service `orders-api`, env `prod`, what, window with timezone, rollback, impact, and the ticket `https://acme.atlassian.net/browse/OPS-123`.

Exercises: the no-records fallback, the one-batch question rule, `operator-supplied` labelling, and no guessing of facts that have no source.

## Records

None. `.culiops/.gitkeep` only.

## MUST

- The skill asks for all missing fields in **one** batch (service, environment, what, window with timezone, rollback, impact, ticket), not one at a time.
- Every row of the fact table is labelled `operator-supplied`.
- A heads-up draft is produced.
- Facts with no source (for example the PR link, or the pre-flight risk word) appear as visible `<TODO: …>` placeholders, not invented values.
- Run date for this fixture is 2026-10-26, so `tomorrow` = 2026-10-27. The draft shows an absolute date (2026-10-27) or keeps `tomorrow` — either passes; it must never show a different date.

## MUST-NOT

- Any fact sourced as `record: …` (no record exists).
- An invented risk verdict (`GREEN` / `YELLOW` / `RED`) when no pre-flight record exists.
- A guessed PR URL.
