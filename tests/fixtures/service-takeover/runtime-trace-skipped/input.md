# Fixture: runtime-trace-skipped

## Scenario

The handoff meeting is moved up to 2026-05-14. The operator decides to **skip `runtime-trace` for this run** (time constraint: it takes about 30 minutes of gate approvals) and to do everything else, including the Step 6 read-only batch. Nothing is denied: `runtime-trace` now runs without Cost Explorer access, so a missing `ce:*` would only change the spend section, never skip the whole source.

## Operator inputs

Same as happy-path (including the delivery model: a GitHub Actions pipeline deploys on merge). Interview variant B.

## Expected gate behavior

- Gate 1.5: only the identity probe runs (the CloudTrail and Resource Explorer probes exist to plan Step 4, which is skipped). The plan's Step 4 row shows SKIPPED (operator choice) and its consequences.
- Gates 2-3 run normally.
- Step 4: `skipped` in `state.md` with the reason; no `runtime-profile.md`; the placeholder `mock-artifacts/.runtime-trace-not-run` states why.
- Step 6: items 5, 7, 8, 9 are `?` (no profile). Items 2, 4, 16, 18, 19, 25 cannot be cross-checked, so they stay `◐`. The batch still runs.
- Verdict: **partial** (4 ✓ verified, 3 ✓ attested, 14 ◐, 0 ✗, 0 ✗ conflict, 4 ?, 0 N/A). The package has 7 files.

## Notable findings

- `?` count: 4 (5, 7, 8, 9). The rows of the scorecard summary sum to 25.
- No Cost Explorer permission is requested and nothing is attributed to an access policy.
- MED-1 in `open-questions.md` is to run runtime-trace and resume at Step 4 (no High item: nothing is `✗`).
