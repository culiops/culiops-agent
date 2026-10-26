# Fixture: existing-stale-catalog

## Scenario

The operator ran `service-discovery` against the payments service 14 days ago (5 resources). That catalog still sits at `.culiops/service-discovery/payments-catalog.md` (see `preexisting/payments-catalog.md`). Today they start a takeover and want fresh discovery data, but keep the old picture for comparison.

## Operator inputs

Same as happy-path, plus: "Pre-existing service-discovery catalog at `.culiops/service-discovery/payments-catalog.md` (14 days old)." Interview variant B.

## Expected gate behavior

- Gate 1.5: the plan shows the existing catalog and offers **use as-is / verify with a thin re-scan / re-run**. Operator chooses re-run.
- The skill **never renames or edits the sibling skill's file** (consumed read-only). It copies the old catalog **into the takeover directory** as `service-catalog.2026-04-28.md`, and the fresh `service-discovery` output goes to a different path (`payments-prod.md`).
- After the snapshot the skill diffs old (5 resources) vs new (8): +3 (`payments-capture-dlq`, the two secrets), none removed, none changed. The drift becomes an open question.
- Rest of the run as happy-path (batch run; interview variant B).

## Notable findings

- Verdict: **partial** (15 ✓ verified, 3 ✓ attested, 6 ◐, 0 ✗, 1 ✗ conflict, 0 ?, 0 N/A).
- 9-file package: the usual 8 plus `service-catalog.2026-04-28.md`.
- The stale catalog lowered nothing: the re-run catalog is live-backed.
