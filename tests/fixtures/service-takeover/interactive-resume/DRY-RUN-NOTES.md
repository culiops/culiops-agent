# Dry-Run Notes — interactive-resume fixture

## Fixture purpose

Validates the skill's resumability across a multi-day takeover. Two separate operator sessions are simulated: Day 1 (2026-05-05) and Day 7 (2026-05-12). The fixture confirms that the skill correctly persists state between sessions, presents the current state on re-invocation, requires explicit resume confirmation from the operator, and merges audit trail entries from both sessions into the final state file.

---

## Session 1 — Day 1 (2026-05-05)

**What happens:**

1. Operator invokes `service-takeover` for service `payments`.
2. Skill runs Gates 1, 1.5, 2, 3 sequentially. Operator approves each gate.
3. At Gate 4 (runtime-trace invocation), operator types "pause" instead of approving.
4. Skill writes `state.md` to `.culiops/service-takeover/payments/state.md`:
   - Steps 1-3: `done` with 2026-05-05 timestamps.
   - Steps 4-7: `pending`.
   - Includes a pause note: "Operator paused at Gate 4 on 2026-05-05T10:30Z."
5. Session ends. No further progress.

**Artifacts produced:**

- `mock-artifacts/service-catalog.md` (diagram + live discovery merged)
- `expected-handoff/execution-plan.md` (from Step 1.5)
- `day-1-state/state.md` (state file at end of Day 1)

---

## Session 2 — Day 7 (2026-05-12)

**What happens:**

1. Operator re-invokes `service-takeover` for service `payments`.
2. Skill detects existing `state.md` and reads it before doing anything else.
3. Skill prints current state summary:

   ```
   Found existing run for service: payments

   Steps completed (Day 1 — 2026-05-05):
     Step 1  — done (Intake)
     Step 1.5 — done (Information audit)
     Step 2  — done (Diagram extraction)
     Step 3  — done (Live discovery)

   Steps pending:
     Step 4  — Runtime profile (runtime-trace)
     Step 5  — Outgoing team interview
     Step 6  — Readiness scorecard
     Step 7  — Handoff package assembly

   Artifacts on disk:
     mock-artifacts/service-catalog.md  (merged, 2026-05-05T10:30Z)
     expected-handoff/execution-plan.md (2026-05-05T09:20Z)

   Resume from Step 4 / jump to a specific step / restart entirely?
   ```

4. Operator responds: "resume from Step 4".
5. Skill adds audit trail entry: "Operator resumed run on 2026-05-12T08:00Z. Confirmed resume point: Step 4."
6. Skill proceeds through Gates 4-7 with 2026-05-12 timestamps.
7. Final `state.md` captures audit entries from both sessions.

**Key behaviors validated:**

- **No silent continuation.** Skill always prompts before resuming; it does not automatically pick up where it left off.
- **Artifact reuse.** `service-catalog.md` produced on Day 1 is used by Steps 4-7 without re-running discovery.
- **Execution plan reuse.** The runtime-trace invocation command printed at Gate 4 is sourced from the execution plan saved on Day 1 (Step 1.5).
- **Merged audit trail.** The final `state.md` includes timestamped entries from 2026-05-05 (Steps 1-3) and 2026-05-12 (resume entry + Steps 4-7). No entries are dropped or overwritten.
- **State file as source of truth.** Day 7 session never asks the operator to re-enter service name, account, region, or IAM ARN. All are read from `state.md`.

---

## Fixture files and their roles

| File | Role |
|---|---|
| `input.md` | Describes the two-session scenario and operator actions |
| `day-1-state/state.md` | State file as written at end of Day 1 (Steps 1-3 done, Steps 4-7 pending) |
| `day-7-state/state.md` | State file as written at end of Day 7 (all steps done, merged audit trail) |
| `mock-artifacts/service-catalog.md` | Produced on Day 1 Step 2-3; reused on Day 7 Steps 4-7 |
| `mock-artifacts/runtime-profile.md` | Produced on Day 7 Step 4 |
| `filled-interview.md` | Produced on Day 7 Step 5 |
| `expected-handoff/state.md` | Identical to `day-7-state/state.md` — the final state included in handoff package |
| `expected-handoff/README.md` | Handoff package README (same as happy-path) |
| `expected-handoff/readiness-scorecard.md` | PRR-style scorecard (same as happy-path) |
| `expected-handoff/open-questions.md` | Open questions list (same as happy-path) |
| `expected-handoff/execution-plan.md` | Execution plan from Step 1.5 (same as happy-path) |
| `DRY-RUN-NOTES.md` | This file |

---

## Deviations from happy-path

The handoff package contents (README, readiness-scorecard, open-questions, execution-plan) are identical to happy-path. The only differences are:

1. Steps 1-3 timestamps are 2026-05-05 (not 2026-05-12).
2. Steps 4-7 timestamps are 2026-05-12 (same date as happy-path, different wall-clock times).
3. The audit trail contains the session resume entry between the Day 1 pause and the Day 7 Step 4 start.
4. `run-started-at` in the state frontmatter is 2026-05-05T09:00:00Z (Day 1 intake), while `run-completed-at` is 2026-05-12T10:05:00Z (Day 7 completion).
