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
