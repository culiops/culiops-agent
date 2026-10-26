# Fixture: partial-interview

## Scenario

Same payments service as happy-path. The Pay Team only had time to answer part of the interview. Section 3 (SLOs) and Section 10 (compliance, backups, DR) are empty; Section 6 (runbooks and incidents) has runbooks but no incidents, recurring issues, MTTR or change failure rate; Section 11 has pending changes, deprecations and the outlook but no open issues. The operator accepts the partial interview rather than sending it back, and declines the Step 6 verification batch for time.

## Operator inputs

(Same as happy-path.) Interview variant B (role permitted, 5 deploys/quarter), so the only reasons the verdict is not `ready` are the gaps and the declined batch.

## Expected gate behavior

- Gates 1-4: as happy-path.
- Gate 5: ingest classifies **7 complete (1, 2, 4, 5, 7, 8, 9), 2 partial (6, 11), 2 empty (3, 10)**; operator chooses accept-as-is.
- Gate 6: items 22-25 and 14 are `?` (empty is never `✗`); PITR and TTL appear in the catalog and are noted on items 23 and 24 but do not substitute for the missing policy and restore-test answers; the batch is declined, so items 10 and 15 stay `◐`.
- Verdict: **partial** (11 ✓ verified, 3 ✓ attested, 5 ◐, 0 ✗, 1 ✗ conflict, 5 ?, 0 N/A).

## Notable findings

- The strict rule changes the old outcome: five `?` items no longer force `not-ready`; only a `✗` / `✗ conflict` in Access, Runtime, Deploy & Rollback or Compliance does.
- Item 19 is still a `✗ conflict` (Wiring vs Section 8), in Dependencies, so it does not change the verdict class.
- The skill never asks the operator to fill in the missing answers.
