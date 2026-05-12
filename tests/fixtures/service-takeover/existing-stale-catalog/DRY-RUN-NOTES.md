# Dry-run notes — existing-stale-catalog

## What this fixture validates

- Step 1.5 detects a pre-existing service-discovery catalog at `.culiops/service-discovery/payments-catalog.md`.
- Gate 1.5 presents three operator-decidable options for the existing-catalog row: use as-is / verify with thin re-scan / re-run from scratch.
- Operator selects re-run (option C).
- Skill renames the old catalog to `payments-catalog.20260428-stale.md` (timestamp suffix derived from the old catalog's `generated-at` frontmatter field `2026-04-28T15:00:00Z`).
- Old catalog is preserved — never deleted.
- `state.md` audit trail records the rename action with exact source, destination, timestamp, and decision authority.
- `execution-plan.md` existing-artifact row shows all three options and captures the operator's selection.
- New catalog snapshot in handoff directory is from today (2026-05-12), not from the stale 14-day-old artifact.
- Remainder of run proceeds identically to happy-path; final verdict: ready.

---

## Gate transitions

**Gate 1 → Step 1 complete**
Operator provides same inputs as happy-path, plus available materials note that a pre-existing catalog exists at `.culiops/service-discovery/payments-catalog.md` (14 days old, generated 2026-04-28).

**Gate 1.5 → Step 1.5 complete (execution plan approved)**
Skill runs capability probes: AWS access ✓, CloudTrail ✓, Resource Explorer ✓, Cost Explorer ✓. Additionally detects existing catalog: `generated-at: 2026-04-28T15:00:00Z` (14 days old). Execution plan includes the existing-artifact row with three options:
- (A) use as-is — accept 14-day-old data, skip re-run
- (B) verify with thin re-scan — re-run resource enumeration only, merge
- (C) re-run from scratch — rename old catalog with timestamp suffix, run full service-discovery

Operator selects option C (re-run). Plan approved at 2026-05-12T14:10:00Z.

**Pre-Step 2 rename action**
Before invoking service-discovery, skill renames `.culiops/service-discovery/payments-catalog.md` → `payments-catalog.20260428-stale.md`. Timestamp suffix (`20260428`) is derived from old catalog's `generated-at: 2026-04-28T15:00:00Z`. Action recorded in state.md audit trail at 2026-05-12T14:05:00Z.

**Gate 2 → Step 2 complete (diagram extraction)**
Fresh service-discovery invocation on diagram PNGs. Output at `.culiops/service-discovery/payments-diagrams-catalog.md`. Snapshot to `mock-artifacts/service-catalog.md` (diagrams phase).

**Gate 3 → Step 3 complete (live discovery)**
Fresh service-discovery in AWS CLI mode. Merged catalog reflects live state at 2026-05-12. Snapshot at `mock-artifacts/service-catalog.md` (merged). `generated-at: 2026-05-12T14:30:00Z` — confirming fresh data, not stale.

**Gate 4 → Step 4 complete (runtime profile)**
runtime-trace run. All 4 sources ✓. Cost $0.04. Snapshot at `mock-artifacts/runtime-profile.md`. `generated-at: 2026-05-12T15:00:00Z`.

**Gate 5–7** proceed identically to happy-path. Verdict: ready.

---

## Key differences from happy-path

| Area | happy-path | existing-stale-catalog |
|---|---|---|
| Pre-existing catalog | none | `.culiops/service-discovery/payments-catalog.md` (14 days old) |
| Gate 1.5 existing-catalog row | not present | shows use/verify/re-run options; operator selects re-run |
| Pre-Step 2 action | none | rename old catalog to `payments-catalog.20260428-stale.md` |
| state.md audit trail | no rename entry | rename recorded at 2026-05-12T14:05:00Z |
| preexisting/ directory | not present | `preexisting/payments-catalog.md` (stale fixture) |

---

## Acceptance check

A reviewer steps through `input.md`, `preexisting/payments-catalog.md`, `mock-artifacts/`, and `filled-interview.md`, then confirms the skill would produce the contents of `expected-handoff/` with these specific behaviors:

- `expected-handoff/execution-plan.md` must include the existing-catalog row with all three options and operator selection captured as "re-run".
- `expected-handoff/state.md` audit trail must include the rename event entry referencing the exact source path, destination filename, timestamp, and "per operator choice at Gate 1.5".
- `mock-artifacts/service-catalog.md` `generated-at` must be from today (2026-05-12), not from the stale catalog (2026-04-28).
- `expected-handoff/readiness-scorecard.md` verdict would be `ready` — stale catalog detection and re-run do not degrade scorecard if re-run completes successfully.
