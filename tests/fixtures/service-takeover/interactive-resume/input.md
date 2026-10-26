# Fixture: interactive-resume

## Scenario

Multi-day takeover. On Day 1 (2026-05-05) the operator runs intake, the audit and the single discovery delegation, then types "pause" at Gate 4. On Day 7 (2026-05-12) they re-invoke `service-takeover` for the same service and resume.

## Day 1 operator inputs

Same as happy-path Gate 1 inputs. Then: Gates 1, 1.5, 2, 3 completed; at Gate 4 the operator types "pause" before approving the runtime-trace invocation. The skill writes `day-1-state/state.md` (Steps 1-3 done, 4-7 pending, pause note). The catalog is generated 2026-05-05T10:20Z.

## Day 7 operator action

1. Re-invoke `service-takeover payments`. The skill reads `state.md` first and prints the current state (no intake re-entered).
2. The operator confirms the resume point: Step 4. Identity is re-checked.
3. **The catalog is now 7 days old**, so the skill offers use as-is / verify / re-run (resume rule). The operator chooses **use as-is**; the age (7 d) is recorded in `state.md`, the plan addendum and the scorecard notes.
4. Gates 4-7 proceed with 2026-05-12 timestamps. Interview variant B; the batch runs and finds that one named alarm does not exist.

## Notable findings

- Verdict: **partial** (14 ✓ verified, 3 ✓ attested, 6 ◐, 0 ✗, 2 ✗ conflict, 0 ?, 0 N/A): two conflicts (item 10: an alarm named in the interview is absent; item 19: unlisted queue sender), neither in a not-ready category.
- The expected handoff is **not** a copy of happy-path: different variant, different marks, timestamps spanning both sessions, the Day-7 resume addendum in the plan.
- `expected-handoff/state.md` equals `day-7-state/state.md`.
