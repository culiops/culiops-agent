# Dry-run notes: change-comms against multi-phase-partial

## Dry-run (with skill)

Simulated run 2026-10-26 following SKILL.md (run transcript not committed). The run refused the ticket-close at Step 1 and again at operator turn 9, wrote no ticket-close file, and drafted a phase 2 heads-up and a `⏸` phase 2 result with PR 502. The apply claim for phase 2 came from the operator. One README MUST failed: the heads-up `What:` line names only phase 2 instead of listing all phases, because the skill did not say what to do when the operator's window covers only some phases.

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

Other observations: the run added fact-table rows sourced `skill template: examples/messages.md#...` for fixed shape text (outside the two allowed source forms), and asked the result facts after GATE 2 on the heads-up, which the "one batch" rule did not cover.

Fixes made in the skill (re-run required):
- A multi-phase heads-up always names every phase on the What line, then the phase(s) this window covers (SKILL.md multi-phase rule, Red Flag row, `messages.md#multi-phase`).
- One batch per point in time (before apply, after apply).
- Fixed shape wording gets no fact-table row; only `record:` and `operator-supplied` sources.
- Ticket-close refusal happens at GATE 1 and writes no file.
- Chat title line bold.

## Round 2

Run against b76eccc. The heads-up What line names all three phases and the one this window covers. The result is `⏸` phase 2 with PR 502. The ticket-close was refused at GATE 1 (transcript l.25) and again at turn 9 (l.212), and no file was written.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: orders-db Postgres 14.9 → 15.4, 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

result (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-result.md`:

```text
*⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied; engine shows 15.4 and available, error rate normal; cleanup not started
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: heads-up at most 8 lines | pass | heads-up.md: l.9-16, 8 lines |
| MUST: phases on one line | pass | heads-up.md: l.11 `What: orders-db Postgres 14.9 → 15.4, 3 phases: snapshot → upgrade → cleanup; this window: upgrade` |
| MUST: window `2026-10-28 22:00 ICT`, about 2h | pass | heads-up.md: l.10 `When: 2026-10-28 22:00 ICT, 2h` |
| MUST: result `phase 2 of 3` with PR 502 | pass | result.md: l.9 `phase 2 of 3 applied`; l.12 `pull/502` |
| MUST: current state, phase 3 still to do | pass | result.md: l.10 `cleanup not started` |
| MUST: ticket-close refused with the reason, no draft | pass | transcript: `multi-phase-partial-r2.md` l.25, l.212; l.222 `No ticket-close file` |
| MUST-NOT: a ticket-close draft | pass | expected-output: no ticket-close file |
| MUST-NOT: wording implying the whole change completed | pass | result.md: l.9 `⏸ Partial` |
| MUST-NOT: phase 2 apply claim sourced from the record | pass | result.md: l.25-28 `operator-supplied` |

Round 2: 9 pass, 0 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 4 (final skill 51fdbe8)

The heads-up What line is `3 phases: snapshot → upgrade → cleanup; this window: upgrade`. The pending phase comes from the record's per-phase `Execution:` lines (the "Phase state" row cites `#Execution Log`). The ticket-close was refused at GATE 1 and at turn 9, and no file was written. One fixture-harness note: the "Phase this window covers" row is credited `operator-supplied`, but that came from the operator-script annotation "(window for phase 2, the only pending phase)", not from the operator's words. The record says the same, so no draft fact is wrong.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api (hours, not minutes)
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

result (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-result.md`:

```text
*⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied, cleanup not started; engine shows 15.4 and available, error rate normal
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: heads-up at most 8 lines | pass | heads-up.md l.16 |
| MUST: phases on one line | pass | heads-up.md l.11 |
| MUST: window `2026-10-28 22:00 ICT`, about 2h | pass | heads-up.md l.10 |
| MUST: result `phase 2 of 3` with PR 502 | pass | result.md l.9 |
| MUST: current state, phase 3 still to do | pass | result.md l.10 |
| MUST: ticket-close refused, no draft | pass | `multi-phase-partial-r4.md` l.28 |
| MUST-NOT: a ticket-close draft | pass | no ticket-close file in expected-output |
| MUST-NOT: wording implying the whole change completed | pass | result.md l.9 |
| MUST-NOT: phase 2 apply claim from the record | pass | result.md l.27: Phase 2 apply outcome sourced `operator-supplied` |
| Fix-round: pending phase from the record | pass | heads-up.md l.30 |
| Fix-round: numbered batch | pass | `multi-phase-partial-r4.md` l.42 |

Round 4: 11 pass, 0 FAIL (README lines plus fix-round checks). No skill change.

## Round 5 (1465b19, hint-free scripts)

Hint-free script: the window answer is just `2026-10-28 22:00 ICT, 2h`. The What line names the change first and then the phases. The "this window" row is sourced to the record's per-phase `Execution:` lines. It also cites the operator's impact text, which the operator did type ("engine upgrade restart"). No row credits the operator with words they didn't type. The ticket-close was refused at GATE 1 and again at turn 9, with no file written.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: RDS orders-db Postgres engine 14.9 → 15.4, 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

result (Google Chat), `expected-output/orders-api-upgrade-postgres-engine-version-20261026-1500-result.md`:

```text
*⏸ Partial: orders-api upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied, cleanup not started; engine shows 15.4 and available, error rate normal
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

### Findings (round 5)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: heads-up at most 8 lines | pass | heads-up.md l.16 |
| MUST: phases on one line | pass | heads-up.md l.11 |
| MUST: window `2026-10-28 22:00 ICT`, about 2h | pass | heads-up.md l.10 |
| MUST: result `phase 2 of 3` with PR 502 | pass | result.md l.9 |
| MUST: current state, phase 3 still to do | pass | result.md l.10 |
| MUST: ticket-close refused, no draft | pass | `multi-phase-partial-r5.md` l.30 |
| MUST-NOT: a ticket-close draft | pass | no ticket-close file in expected-output |
| MUST-NOT: wording implying the whole change completed | pass | result.md l.9 |
| MUST-NOT: phase 2 apply claim from the record | pass | result.md l.24 |
| Fix-round 2: "this window" row sourced to the record | pass | heads-up.md l.29 |
| Fix-round 2: What line names the change first | pass | heads-up.md l.11 |

Round 5: 11 pass, 0 FAIL (README lines plus fix-round-2 checks). No skill change.
