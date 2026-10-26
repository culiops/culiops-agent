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

## Round 2

Run against b76eccc. The draft and the fact table pass. Every row is now `operator-supplied`, including l.30 `operator-supplied (not given)`. The process failed the one-batch MUST. GATE 1 only asked "Is this right?". The facts came only because the operator volunteered them, and the PR link was then asked in a second round. The skill had GATE 1 before the batch even when there are no records. Fixed: with no records, GATE 1 and the batch are now one message.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-rds-resize-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: <TODO: pre-flight verdict>
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123
Reply here if this window conflicts.
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: all missing fields asked in ONE batch | FAIL | transcript: `no-records-r2.md` l.17-21: GATE 1 asked only `No records found; ... Is this right?`; the operator volunteered the facts; l.40-45 a second question round asked the PR link |
| MUST: every fact-table row `operator-supplied` | pass | heads-up.md: l.23-34 all `operator-supplied` (l.30 `operator-supplied (not given)`) |
| MUST: a heads-up produced | pass | heads-up.md: file present |
| MUST: unsourced facts as visible TODOs | pass | heads-up.md: l.13 `Risk: <TODO: pre-flight verdict>`; PR omitted because the operator said none raised (l.33) |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md: l.10 |
| MUST-NOT: any `record:` source | pass | heads-up.md: none |
| MUST-NOT: invented risk verdict | pass | heads-up.md: l.13 |
| MUST-NOT: guessed PR URL | pass | heads-up.md: none |

Round 2: 7 pass, 1 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 3

Run against 621129a. GATE 1 and the question batch went out as one message: "No records found; ..." plus the batch, with no second question round (transcript `no-records-r3.md` l.29-43). The round-2 FAIL is closed.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-rds-resize-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: <TODO: pre-flight verdict>
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123
Reply here if this window conflicts.
```

### Findings and fixes (round 3)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: all missing fields asked in ONE batch | pass | transcript: l.29-43: one message carries service, environment, what, window with timezone, impact, rollback, ticket, PR; turns 2-4 answer it, nothing re-asked |
| MUST: every fact-table row `operator-supplied` | pass | heads-up.md: l.23-33 (l.30 `operator-supplied (not given)`) |
| MUST: a heads-up produced | pass | heads-up.md: file present |
| MUST: unsourced facts as visible TODOs | pass | heads-up.md: l.13 `Risk: <TODO: pre-flight verdict>`; PR omitted because the operator said none raised (l.33) |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md: l.10 |
| MUST-NOT: any `record:` source | pass | heads-up.md: none |
| MUST-NOT: invented risk verdict | pass | heads-up.md: l.13 |
| MUST-NOT: guessed PR URL | pass | heads-up.md: none |

Round 3: 8 pass, 0 FAIL. No skill change.

## Round 4 (final skill 51fdbe8)

GATE 1 and the batch went out as one numbered message. Item 4 was trimmed to the fields that items 1-3 do not already ask (service, environment, what, rollback, ticket, PR link), so nothing is asked twice. Every Source cell starts with `operator-supplied`.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-rds-resize-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: <TODO: pre-flight verdict>
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123
Reply here if this window conflicts.
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: all missing fields asked in ONE batch | pass | `no-records-r4.md` l.30 |
| MUST: every fact-table row `operator-supplied` | pass | heads-up.md l.23 |
| MUST: a heads-up produced | pass | heads-up.md l.16 |
| MUST: unsourced facts as visible TODOs | pass | heads-up.md l.13 |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md l.10 |
| MUST-NOT: any `record:` source | pass | no `record:` in the file |
| MUST-NOT: invented risk verdict | pass | heads-up.md l.13 |
| MUST-NOT: guessed PR URL | pass | no PR URL; the operator said none raised, so the segment is omitted |
| Fix-round: no-records batch asks nothing twice | pass | `no-records-r4.md` l.30 |

Round 4: 9 pass, 0 FAIL (README lines plus fix-round checks). No skill change.
