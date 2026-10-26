# Dry-run notes: change-comms against multi-phase-partial

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md. The runner refused the ticket-close at Step 1 and again at operator turn 9, wrote no ticket-close file, and drafted a phase 2 heads-up and a `⏸` phase 2 result with PR 502. The apply claim for phase 2 came from the operator. One README MUST failed: the heads-up `What:` line names only phase 2 instead of listing all phases, because the skill did not say what to do when the operator's window covers only some phases.

Drafts as produced:

heads-up (Google Chat), saved as `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-heads-up.md`:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-28 22:00 ICT, 2h
What: phase 2 of 3: upgrade RDS orders-db Postgres engine 14.9 → 15.4
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance, repoint orders-api (takes hours)
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

result (Google Chat), saved as `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-result.md`:

```text
⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT
State: snapshot and upgrade applied, engine shows 15.4 and available, error rate normal, cleanup not started
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: heads-up at most 8 lines | pass | 8 non-blank lines |
| MUST: heads-up lists the phases on one line (`3 phases: snapshot → upgrade → cleanup`) | FAIL | `What: phase 2 of 3: upgrade RDS orders-db Postgres engine 14.9 → 15.4` (phases not listed) |
| MUST: window `2026-10-28 22:00 ICT`, about 2h | pass | `When: 2026-10-28 22:00 ICT, 2h` |
| MUST: result says `phase 2 of 3` and shows PR 502, not PR 501 | pass | `⏸ Partial: ..., phase 2 of 3 applied, 22:40 ICT`; `PR: https://github.com/acme/orders-infra/pull/502` |
| MUST: result states the current state (phase 3 still to do) | pass | `State: snapshot and upgrade applied, ..., cleanup not started` |
| MUST: ticket-close refused with the reason, no draft | pass | Transcript: refused at Step 1 and at turn 9 ("not the last phase and the change was not aborted"); no ticket-close file in expected-output |
| MUST-NOT: a ticket-close draft | pass | none saved or shown |
| MUST-NOT: result wording that implies the whole change completed | pass | `⏸ Partial`, `cleanup not started` |
| MUST-NOT: an apply claim for phase 2 sourced from the record | pass | Fact table: Phase 2 apply time / outcome / verification are `operator-supplied` |

Round 1: 8 pass, 1 FAIL.

Other observations: the runner added fact-table rows sourced `skill template: examples/messages.md#...` for fixed shape text (outside the two allowed source forms), and asked the result facts after GATE 2 on the heads-up, which the "one batch" rule did not cover.

Fixes made in the skill (re-run required):
- A multi-phase heads-up always names every phase on the What line, then the phase(s) this window covers (SKILL.md multi-phase rule, Red Flag row, `messages.md#multi-phase`).
- One batch per point in time (before apply, after apply).
- Fixed shape wording gets no fact-table row; only `record:` and `operator-supplied` sources.
- Ticket-close refusal happens at GATE 1 and writes no file.
- Chat title line bold.
