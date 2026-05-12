# Dry-run notes — happy-path

## What this fixture validates

- All eight gates fire in sequence with operator approval.
- Step 1.5 audit correctly identifies all needs and proposes one action per gap.
- All three delegated steps (2, 3, 4) execute with sibling skills, return artifact paths, get snapshotted into handoff directory.
- Step 5 emits and ingests a fully-filled interview.
- Step 6 auto-marks 22 items from artifacts, prompts for 3 manual items, all get ✓.
- Step 7 assembles the full handoff package with all 8 files.
- Final verdict: ready.

---

## Gate transitions

**Gate 1 → Step 1 complete**
Operator provides: service=payments, account 123456789012, region us-east-1, takeover intent, 2 diagram PNGs, no IaC, outgoing=Pay Team, incoming=Platform Team. Skill accepts and moves to Step 1.5.

**Gate 1.5 → Step 1.5 complete (execution plan approved)**
Skill runs capability probes: AWS access ✓, CloudTrail ✓, Resource Explorer ✓, Cost Explorer ✓. Identifies gap: no existing catalog, no runtime profile, no IaC. Proposes: service-discovery diagram mode (Step 2), service-discovery live mode (Step 3), runtime-trace (Step 4). Emits execution-plan.md. Operator reviews and responds "plan approved" at 2026-05-12T14:10:00Z.

**Gate 2 → Step 2 complete (diagram extraction)**
Skill instructs operator to invoke service-discovery with the two PNG files. Operator returns catalog path. Skill snapshots to mock-artifacts/service-catalog.md (diagram phase).

**Gate 3 → Step 3 complete (live discovery)**
Skill instructs operator to invoke service-discovery in AWS CLI mode. Operator returns merged catalog path. Skill updates snapshot at mock-artifacts/service-catalog.md (merged). Resource Inventory now shows 8 resources (3 Lambda, 2 SQS, 1 DynamoDB, 2 Secrets Manager).

**Gate 4 → Step 4 complete (runtime profile)**
Skill instructs operator to invoke runtime-trace. Run costs $0.04 (CE charge). All 4 sources ran: Cost Explorer ✓, CloudTrail ✓, CloudWatch ✓, Resource Explorer ✓. Operator returns profile path. Skill snapshots to mock-artifacts/runtime-profile.md.

**Gate 5 → Step 5 complete (interview ingested)**
Skill emits interview-questionnaire.md (template). Operator forwards to Bob L. (Pay Team) via Slack. Bob and Carol fill in all 11 sections. Operator returns filled-interview.md path. Skill reads and classifies all 11 sections as complete.

**Gate 6 → Step 6 complete (scorecard auto-marked)**
Skill runs auto-mark rules across all artifacts. 23 items auto-marked ✓ from service-catalog.md, runtime-profile.md, and filled-interview.md. 2 items (Item 3: console+CLI access; Item 12: paging path) require manual confirmation. Operator confirms both. Verdict: ready. Scorecard written to expected-handoff/readiness-scorecard.md.

**Gate 7 → Step 7 complete (handoff package assembled)**
Skill assembles: README.md, readiness-scorecard.md, open-questions.md, state.md, execution-plan.md, plus artifact snapshots (service-catalog.md, runtime-profile.md, filled-interview.md). 8 files total. Run complete at 2026-05-12T16:05:00Z.

---

## Acceptance check

A reviewer steps through `input.md`, `mock-artifacts/`, and `filled-interview.md`, then confirms the skill would produce the contents of `expected-handoff/` with **representative** results (allowing for run-specific timestamps and operator usernames).

Specifically:
- `expected-handoff/readiness-scorecard.md` verdict would be `ready` for any run with this input set, regardless of timestamps.
- `expected-handoff/open-questions.md` would have 0 high-priority items and 2 medium-priority items (training schedule, DR drill) for any run with this fully-filled interview.
- `expected-handoff/state.md` timestamps and the `operator` field would differ per run; all step statuses would be `done`.
- `expected-handoff/execution-plan.md` approval status would be `approved`; proposed invocations are deterministic from the input.
