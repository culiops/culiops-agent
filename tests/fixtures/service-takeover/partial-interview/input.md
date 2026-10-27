# Fixture: partial-interview

## Scenario

Same payments service as happy-path. The Pay Team only had time to answer part of the interview. Section 3 (SLOs) and Section 10 (compliance, backups, DR) are empty; Section 6 (runbooks and incidents) has runbooks but no incidents, recurring issues, MTTR or change failure rate; Section 11 has pending changes, deprecations and the outlook but no open issues. The operator accepts the partial interview rather than sending it back, and declines the Step 6 verification batch for time.

## Operator inputs

(Same as happy-path, including the delivery model: a GitHub Actions pipeline deploys on merge.) Interview variant B (role permitted, 5 deploys/quarter), so the reasons the verdict is not `ready` are the gaps, the declined batch and the one conflict.

## Expected gate behavior

- Gates 1-4: as happy-path.
- Gate 5: ingest classifies **7 complete (1, 2, 4, 5, 7, 8, 9), 2 partial (6, 11), 2 empty (3, 10)**; operator chooses accept-as-is.
- Gate 6: items 22-25 and 14 are `?` (empty is never `✗`); PITR and TTL appear in the catalog and are noted on items 23 and 24 but do not substitute for the missing policy and restore-test answers; item 7 is `?` because the DynamoDB table has no baseline row; the batch is declined, so items 10 and 15 stay `◐`.
- Verdict: **not-ready** (10 ✓ verified, 3 ✓ attested, 5 ◐, 0 ✗, 1 ✗ conflict, 6 ?, 0 N/A): the conflict on item 19 decides it.

## Notable findings

- `?` items alone never force `not-ready`; they cap the verdict at `partial`. Any `✗` or `✗ conflict`, in any category, forces `not-ready`.
- Item 19 is a `✗ conflict` (Wiring vs Section 8), in Dependencies, so the verdict is `not-ready` even though the interview gaps would only give `partial`.
- The skill never asks the operator to fill in the missing answers.
