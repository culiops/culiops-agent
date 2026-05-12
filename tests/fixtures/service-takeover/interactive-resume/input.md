# Fixture: interactive-resume

## Scenario

Multi-day takeover. Operator stops on Day 1 after running Steps 1-3 (intake + audit + diagram extraction + live discovery). On Day 7, they re-invoke `service-takeover` on the same service and resume.

## Day 1 operator inputs

Same as happy-path Gate 1 inputs. Then:
- Gates 1, 1.5, 2, 3 → completed
- Gate 4 → operator types "pause" before approving the runtime-trace invocation
- Skill writes `state.md` showing Steps 1, 1.5, 2, 3 done; Step 4 pending

## Day 7 operator action

Operator re-invokes `service-takeover` with the same service name. Skill:
1. Reads `state.md` first.
2. Prints current state: Steps 1-3 done (artifacts at known paths); Step 4 pending; Steps 5-7 not started.
3. Asks operator: resume from Step 4 / jump to specific step / restart entirely.
4. Operator chooses "resume from Step 4".
5. Skill prints the runtime-trace invocation (saved from Day 1's execution plan).
6. Day 7 proceeds normally through Gates 4-7.

## Notable findings

- state.md from Day 1 is preserved across the session boundary; Day 7 reads it without prompting for re-intake.
- Resume confirmation is explicit — skill never silently picks up.
- Audit trail in final state.md captures BOTH session timestamps (Day 1 partial + Day 7 completion).
