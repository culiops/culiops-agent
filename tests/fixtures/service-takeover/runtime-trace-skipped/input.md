# Fixture: runtime-trace-skipped

## Scenario

The operator does not have `ce:*` IAM perms in the target account (corporate IAM policy restriction). At Step 1.5's capability probes, Cost Explorer access check fails. Operator chooses to accept the gap rather than escalate IAM.

## Operator inputs

Same as happy-path.

## Expected gate behavior

- Gate 1.5: capability probes detect Cost Explorer ACCESS DENIED. Execution-plan row for "Activity baseline (Step 4)" shows three options: escalate IAM and re-probe / proceed without runtime data / abort takeover.
- Operator selects "proceed without runtime data".
- Plan is updated to skip Step 4 entirely.
- Gates 2 and 3 run normally (service-discovery doesn't need ce:*).
- Step 4 is marked `skipped` in state.md. No `runtime-profile.md` snapshot in handoff directory.
- Step 5 (interview) and Step 7 (handoff) proceed.
- Step 6: scorecard auto-marks items 7-9 (Runtime category) all ? because no runtime-profile.md exists. Operator can mark items 2 (deploy role) and 9 (principals) manually if they have alternative evidence — fixture shows operator leaving them as ?.

## Notable findings

- Verdict: not-ready (Runtime category empty + scorecard reports the gap as "no runtime-profile.md available").
- open-questions.md surfaces "Activity baseline unavailable — recommend escalating IAM for ce:* read and re-running" as high priority.
- Handoff README first-day actions include "address IAM gap before signing off on takeover".
