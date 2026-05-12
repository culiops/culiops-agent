# Fixture: partial-interview

## Scenario

Same payments service as happy-path. The Pay Team only had bandwidth to fill in 6 of the 11 interview sections before the deadline. Empty sections: Section 3 (SLOs), Section 6 (Runbooks & incidents — partial: runbooks listed but no incidents), Section 10 (Compliance/DR — completely empty), Section 11 (Roadmap — partial: only roadmap, no open issues).

## Operator inputs

(Same as happy-path.)

## Expected gate behavior

- Gates 1-4: same as happy-path.
- Gate 5: ingest classifies sections — 6 `complete`, 3 `partial`, 2 `empty`. Operator chooses "accept as-is" rather than returning to outgoing team.
- Gate 6: scorecard auto-marks degrade — items 10-12 (Alerting) and 19-21 (Dependencies) still ✓ from completed sections; items 22-25 (Compliance) go to ✗ (Section 10 empty); items 7-9 (Runtime) auto-mark ✓ from runtime-profile (unchanged).
- Verdict: `not-ready` because 4 critical compliance items failed.
- open-questions.md: populated with 4-5 high-priority items.

## Notable findings

- The fixture demonstrates the skill correctly does NOT auto-pass empty sections.
- The scorecard's evidence citations correctly point to "interview-questionnaire.md: Section 10 — empty".
- The skill never asks the operator to fill in answers itself (Iron Law: operator is not the source of this knowledge).
