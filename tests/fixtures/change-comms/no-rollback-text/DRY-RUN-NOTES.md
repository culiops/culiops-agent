# Dry-run notes: change-comms against no-rollback-text

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md. The runner found no rollback text in the Change Plan, asked for it in the one batch, got "leave it open", and drafted an 8-line heads-up with `Rollback: <TODO: rollback>` and `Risk: GREEN (pre-flight)`. It did not borrow the pre-flight Reversibility finding as rollback text. All README lines pass.

Drafts as produced:

heads-up (Google Chat), saved as `expected-output/orders-api-scale-ecs-tasks-20261026-1500-heads-up.md`:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 11:00 ICT, 10 min
What: increase orders-api ECS desired task count 3 → 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: the skill asks the operator for the rollback | pass | Batch item `4. Rollback text (the Change Plan has none).` |
| MUST: heads-up contains `<TODO: rollback>` on its Rollback line | pass | `Rollback: <TODO: rollback>` |
| MUST: `<TODO: rollback>` listed under Open TODOs | pass | Open TODOs: `<TODO: rollback>` (Rollback line) |
| MUST: Risk shows `GREEN` | pass | `Risk: GREEN (pre-flight)` |
| MUST: date 2026-10-27 or `tomorrow` | pass | `When: 2026-10-27 11:00 ICT, 10 min` |
| MUST-NOT: any invented rollback text | pass | no rollback wording in the draft or fact table other than the TODO |

Round 1: 6 pass, 0 FAIL.

No fix targeted this case. It is re-run because shared changes alter its output: chat title line bold, the platform stated at GATE 1, the batch shown as plain text (the runner used a `text` block, others used `>` blockquotes), and fixed shape text no longer gets a fact-table row.

## Round 2

Run against b76eccc. Rollback was asked in the batch (transcript l.49), the operator declined, and the draft shows `<TODO: rollback>`. The plan-count log rows in this round will disappear under the round-2 pattern-8 scope edit. That changes the log only, not any MUST line.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-scale-ecs-tasks-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 11:00 ICT, 10 min
What: scale orders-api ECS desired task count from 3 to 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: asks for the rollback | pass | transcript: `no-rollback-text-r2.md` l.49 `4. Rollback text (the Change Plan has none).` |
| MUST: `<TODO: rollback>` on the Rollback line | pass | heads-up.md: l.14 |
| MUST: `<TODO: rollback>` under Open TODOs | pass | heads-up.md: l.44 |
| MUST: Risk `GREEN` | pass | heads-up.md: l.13 |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md: l.10 |
| MUST-NOT: invented rollback text | pass | heads-up.md: only the TODO (l.14, l.30) |

Round 2: 6 pass, 0 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 4 (final skill 51fdbe8)

Rollback was asked as batch item 4 and declined, so it is `<TODO: rollback>`. The risk is GREEN, and the batch is numbered.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-scale-ecs-tasks-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 11:00 ICT, 10 min
What: scale orders-api ECS desired task count 3 → 5
Impact: none expected, tasks are added alongside the existing ones
Risk: GREEN (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/495
Reply here if this window conflicts.
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: asks for the rollback | pass | `no-rollback-text-r4.md` l.56 |
| MUST: `<TODO: rollback>` on the Rollback line | pass | heads-up.md l.14 |
| MUST: `<TODO: rollback>` under Open TODOs | pass | heads-up.md l.40 |
| MUST: Risk `GREEN` | pass | heads-up.md l.13 |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md l.10 |
| MUST-NOT: invented rollback text | pass | heads-up.md l.14 |
| Fix-round: numbered batch | pass | `no-rollback-text-r4.md` l.53 |

Round 4: 7 pass, 0 FAIL (README lines plus fix-round checks). No skill change.
