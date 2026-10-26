# Dry-run notes: change-comms against no-records

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md. With an empty `.culiops/`, the runner merged the Step 1 minimum fields into the Step 2 batch and asked everything once, then drafted an 8-line heads-up from operator-supplied facts with `Risk: <TODO: pre-flight verdict>`. The operator said no PR was raised yet, so the PR segment was dropped. One README MUST failed on a strict reading: not every fact-table row is labelled `operator-supplied` (the Risk TODO row says `none`, the title row cites the skill shape, and a "Saved at" row cites `session`).

Drafts as produced:

heads-up (Google Chat), saved as `expected-output/orders-api-rds-resize-20261026-1500-heads-up.md`:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: <TODO: pre-flight verdict>
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123
Reply here if this window conflicts.
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: all missing fields asked in one batch | pass | Transcript: one batch of 9 items (service/env, what, window with timezone, impact, rollback, ticket, PR, path, platform) before any draft |
| MUST: every fact-table row labelled `operator-supplied` | FAIL | Risk row source `none`; "Title, Reply here..." row source `skill shape examples/messages.md#heads-up`; "Saved at" row source `session`. No `record:` source anywhere |
| MUST: a heads-up draft is produced | pass | `orders-api-rds-resize-20261026-1500-heads-up.md` |
| MUST: facts with no source are visible `<TODO: ...>` | pass | `Risk: <TODO: pre-flight verdict>`. The PR is not missing: the operator said no PR was raised yet, so the segment is omitted (now the explicit rule) |
| MUST: date 2026-10-27 or `tomorrow` | pass | `When: 2026-10-27 14:00 ICT, 15 min` |
| MUST-NOT: any fact sourced `record: ...` | pass | no `record:` in the file |
| MUST-NOT: an invented risk verdict | pass | `Risk: <TODO: pre-flight verdict>` |
| MUST-NOT: a guessed PR URL | pass | no PR URL |

Round 1: 7 pass, 1 FAIL.

Fixes made in the skill (re-run required):
- Constraint 2: only `record:` and `operator-supplied` sources; a TODO row's source is `operator-supplied (not given)`; fixed shape wording gets no row (plus the Red Flag row).
- With no records, the minimum fields join the one batch; the execution path is asked only for a result or ticket-close.
- PR segment omitted when the operator says none is raised (now explicit in Constraint 8).
- GATE 1 has a no-records wording; chat title line bold.
