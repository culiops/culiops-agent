# Dry-run notes: change-comms against aborted

## Baseline (no skill)

A general assistant with no skill read both records, asked which platform, and (good behaviour) asked whether anything had been merged or applied before saying "no change was made". It then drafted a result and a ticket-close that both state the change was aborted and nothing was applied. The facts of the abort are right: RED, replace of `orders-db`, no apply. The failures are the missing ❌ marker and, mainly, a large amount of invented content: a next-steps plan, a customer-impact statement and a promise to post a new window, none of which came from the records or the operator. Both drafts also carry raw plan counts, and the ticket-close shows record times with no timezone.

| MUST/MUST-NOT line | Result (pass/FAIL) | Evidence (quoted from transcript) |
|---|---|---|
| MUST: result uses ❌ | FAIL | Result starts "*orders-api prod: RDS resize NOT applied (aborted)*" with no ❌ anywhere in the draft |
| MUST: result uses the word `aborted` | pass | "RDS resize NOT applied (aborted)" |
| MUST: result states nothing was applied | pass | "stopped before anything was applied. Prod is unchanged." and "Nothing was applied, so there is nothing to roll back." |
| MUST: result gives the reason from the record (pre-flight RED, replace of `orders-db`) | pass | "the pre-flight check came back RED (hard block). The Terraform plan did not resize the instance in place. It would have destroyed and recreated aws_db_instance.orders (1 to destroy, 1 to add)" |
| MUST: what happens next is a TODO or operator-supplied | FAIL | The operator gave no next steps. The draft supplies them: "*Next:* the resize will not be retried until the replacement is understood and removed from the plan (and a manual snapshot is taken first as a safeguard). I'll post here when there's a new window." The retry condition and the promised window have no source. The snapshot comes from the pre-flight mitigation but the operator never chose it. There is no `<TODO: next steps>` |
| MUST: ticket-close produced | pass | Draft 2 is a Jira comment on OPS-123 |
| MUST: ticket-close lists outcome `aborted` | pass | "Closing as not done: change aborted, nothing applied." and "Outcome: aborted." |
| MUST: ticket-close has no applied time | pass | No applied time. It states "No apply was run. Prod was not changed." |
| MUST-NOT: `✅` in any draft | pass | Not present |
| MUST-NOT: `Done` in any draft | pass | Not as a completion claim. The ticket-close opens "Closing as not done: change aborted, nothing applied." ("done" lowercase, inside "not done"). The closing chat line was "Both accepted." |
| MUST-NOT: any statement that the change was applied, verified or completed | pass | Both drafts say the opposite. "Rollback and post-change verification are not applicable." |

### Behaviours the README does not list but the spec's anti-goals forbid

- Operator-supplied impact was invented: "*Impact:* none. Nothing was applied, so there is nothing to roll back. No customer impact and no verification was needed." The operator gave no impact. "No customer impact" is an assertion nobody supplied.
- Pre-flight content turned into decided next steps and a cause statement for a broad audience, with unsourced steps and commitments added. Sourced from the pre-flight: the L1 detail ("A changed `identifier` argument in the working tree forces replacement"), "no snapshot configured", and the mitigations "Do not apply; find what forces replacement" and "Take a manual snapshot first". Unsourced: the word "likely" in "The likely cause is a changed `identifier` argument", the decided retry sequence ("remove the replace-forcing change so the plan shows an in-place modify, take a manual snapshot, re-run pre-flight"), "then raise a new change or reopen this ticket", and "the resize will not be retried until the replacement is understood and removed from the plan". The record gives options as mitigations. The draft presents them as the plan.
- Ticket-close is not in plain `Label: value` lines. It opens with prose ("Closing as not done: ..."), has a prose paragraph ("Cause (from the pre-flight scan): ...") and uses "- " bullets.
- Raw plan counts in both drafts: "(1 to destroy, 1 to add)".
- Record times without a timezone: ticket-close shows "Pre-flight (2026-10-27 10:00)" and "IaC change execution (2026-10-27 10:15)". The pre-flight record said `(UTC)`, which the draft dropped, and the iac record carries no timezone. The operator was never asked.
- Noise a Jira reader cannot use: the commit hash "Commit: d9e0f1a" and the repo-local `.culiops/` paths.
- A promise on the operator's behalf: "I'll post here when there's a new window."
- Nothing is saved to `.culiops/change-comms/`. No blockquotes were used.

### Failures to answer in SKILL.md

- Failure message had no ❌ marker, so it does not match the style the recorded outcome calls for.
- What happens next was not operator-supplied and not marked `<TODO: next steps>`: the retry condition ("will not be retried until ..."), the promised new window and the reopen route have no source. (The snapshot is sourced from the pre-flight mitigations, so it is not counted as invented.)
- Impact was asserted ("No customer impact") although impact is always operator-supplied.
- Pre-flight mitigations and L1 detail were turned into a decided retry sequence and a cause statement for a broad audience, and unsourced retry steps and commitments were added ("likely cause", "will not be retried until ...", "raise a new change or reopen this ticket").
- Jira ticket-close used prose and "- " bullets instead of plain `Label: value` lines.
- Raw plan counts ("1 to destroy, 1 to add") were put in chat and Jira drafts.
- Record `Date` times were shown with no timezone and the `(UTC)` tag was dropped.
- A promise to post later was made on the operator's behalf.
- No draft was saved to the `.culiops/change-comms/` output path.

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md; transcript in the SDD dryrun folder. The runner confirmed the 1015 record and the 1000 pre-flight at GATE 1, asked one batch (timezone, apply time, PR link, next steps, anything applied, abort reason), took "Nothing was applied, the pre-flight blocked it" as the answer, and saved a result and a ticket-close. No invented next steps, no impact claim, no plan counts, plain `Label: value` Jira lines. Two README MUSTs failed, both caused by the skill: the skill told it to use `⛔` for an abort (the README and the spec say ❌), and its batch asked for the abort reason even though the record's `Execution:` line already states it, so the draft carries the operator's vaguer "the pre-flight blocked it" instead of RED and the replace of `orders-db`.

Drafts as produced:

result (Google Chat), saved as `expected-output/orders-api-resize-rds-20261026-1500-result.md`:

```text
⛔ Aborted: orders-api RDS resize (prod), nothing applied
Reason: the pre-flight blocked it
Next: <TODO: next steps>
Ticket: OPS-123
```

ticket-close (Jira comment), saved as `expected-output/orders-api-resize-rds-20261026-1500-ticket-close.md`:

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
PR: <TODO: PR link>
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: result uses ❌ | FAIL | Draft opens `⛔ Aborted: ...`. SKILL.md Constraint 10 mapped aborted to ⛔ |
| MUST: result uses the word `aborted` | pass | `⛔ Aborted: orders-api RDS resize (prod), nothing applied` |
| MUST: result states that nothing was applied | pass | `..., nothing applied` |
| MUST: result gives the reason from the record (pre-flight RED, replace of `orders-db`) | FAIL | `Reason: the pre-flight blocked it` (operator wording). Neither RED nor the replace of orders-db appears; batch item 8 asked for a reason the record already held |
| MUST: what happens next is a TODO or operator-supplied | pass | `Next: <TODO: next steps>` |
| MUST: ticket-close produced | pass | `...-ticket-close.md` saved, Jira comment |
| MUST: ticket-close lists outcome `aborted` | pass | `Outcome: aborted, nothing applied` |
| MUST: ticket-close has no applied time | pass | `Applied: not applied` |
| MUST-NOT: `✅` in any draft | pass | `grep -rn '✅\|Done' aborted/expected-output` returns nothing; same for the transcript's `text` blocks |
| MUST-NOT: `Done` in any draft | pass | as above |
| MUST-NOT: any statement that the change was applied, verified or completed | pass | `Applied: not applied`, `Verification: not run`, `Rollback: not needed, nothing was applied` |

Round 1: 9 pass, 2 FAIL.

Not a README line, but an anti-goal: the ticket-close shows `PR: <TODO: PR link>` although the abort happened at the gate and no PR was ever created. A visible TODO for something that does not exist reads as a gap.

Fixes made in the skill (re-run required):
- Aborted now uses ❌ with the word `Aborted` (Constraint 10, Red Flag row, `messages.md#result`).
- The abort reason is taken from the record's `Execution:` line when it states one; the batch asks for it only otherwise (Constraint 10, batch, `messages.md` Aborted rule and example).
- When no PR exists the PR line is omitted (Constraint 8, Red Flag row, `messages.md` ticket-close rule and the "Not completed" example).
- Timezone and apply time are no longer asked for an abort that shows no time.

## Round 2

Run against b76eccc. The runner used ❌ and took the reason from the record's `Execution:` line. It left out the PR line because the abort happened at the gate. It asked no timezone or apply-time question. Two leftovers from the batch: it still asked for the PR link, and it logged plan counts as `dropped`. Both are closed by the round-2 skill edits (see the end).

Drafts as produced:

result (Google Chat), `expected-output/orders-api-resize-rds-20261026-1500-result.md`:

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: pre-flight RED, replace of orders-db
Next: <TODO: next steps>
Ticket: OPS-123
```

ticket-close (Jira comment), `expected-output/orders-api-resize-rds-20261026-1500-ticket-close.md`:

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: result uses ❌ | pass | result.md: l.9 `*❌ Aborted: orders-api RDS resize (prod), nothing applied*` |
| MUST: result uses the word `aborted` | pass | result.md: l.9 |
| MUST: result states nothing was applied | pass | result.md: l.9 `nothing applied` |
| MUST: reason from the record (pre-flight RED, replace of `orders-db`) | pass | result.md: l.10 `Reason: pre-flight RED, replace of orders-db`, cited `#Execution Log` l.24 |
| MUST: next steps TODO or operator-supplied | pass | result.md: l.11 `Next: <TODO: next steps>` |
| MUST: ticket-close produced | pass | ticket-close.md: file present, Jira comment |
| MUST: ticket-close outcome `aborted` | pass | ticket-close.md: l.10 `Outcome: aborted, nothing applied` |
| MUST: ticket-close has no applied time | pass | ticket-close.md: l.12 `Applied: not applied` |
| MUST-NOT: `✅` | pass | both: `grep -rn '✅\|Done' aborted/expected-output` returns nothing |
| MUST-NOT: `Done` | pass | both: as above |
| MUST-NOT: statement of applied/verified/completed | pass | both: TC l.12-14 `not applied` / `not run` / `nothing was applied` |

Round 2: 11 pass, 0 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 3

Run against 621129a. The batch no longer asks for a PR link; it asks only "Next steps" and "Was anything applied?" (transcript `aborted-r3.md` l.59-62). The PR line is omitted, citing the abort at the gate. The redaction log has no plan-count rows.

Drafts as produced:

result (Google Chat), `expected-output/orders-api-resize-rds-20261026-1500-result.md`:

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: aborted at GATE, pre-flight RED (replace of orders-db)
Next: <TODO: next steps>
Ticket: OPS-123
```

ticket-close (Jira comment), `expected-output/orders-api-resize-rds-20261026-1500-ticket-close.md`:

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

### Findings and fixes (round 3)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: result uses ❌ | pass | result.md: l.9 `*❌ Aborted: ...*` |
| MUST: result uses the word `aborted` | pass | result.md: l.9 |
| MUST: result states nothing was applied | pass | result.md: l.9 |
| MUST: reason from the record (pre-flight RED, replace of `orders-db`) | pass | result.md: l.10 `Reason: aborted at GATE, pre-flight RED (replace of orders-db)`, cited l.25 |
| MUST: next steps TODO or operator-supplied | pass | result.md: l.11 |
| MUST: ticket-close produced | pass | ticket-close.md: file present |
| MUST: ticket-close outcome `aborted` | pass | ticket-close.md: l.10 |
| MUST: ticket-close has no applied time | pass | ticket-close.md: l.12 `Applied: not applied` |
| MUST-NOT: `✅` | pass | both: `grep -rn '✅\|Done' aborted/expected-output` returns nothing |
| MUST-NOT: `Done` | pass | both: as above |
| MUST-NOT: statement of applied/verified/completed | pass | both: TC l.12-14 |

Round 3: 11 pass, 0 FAIL. No skill change.

## Round 4 (final skill 51fdbe8)

The ticket-close now carries `Reason: stopped before apply: pre-flight check failed (replace of orders-db)`: plain words, no GATE or HARD BLOCK jargon. The result uses the same reason. The batch is numbered and asks only Next steps and "Was anything applied?". There is no PR line. Citations use `#header`.

Drafts as produced:

result (Google Chat), `expected-output/orders-api-resize-rds-20261026-1500-result.md`:

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
Next: <TODO: next steps>
Ticket: OPS-123
```

ticket-close (Jira comment), `expected-output/orders-api-resize-rds-20261026-1500-ticket-close.md`:

```text
Change aborted
Outcome: aborted, nothing applied
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
What: RDS orders-db resize db.t3.medium → db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: result uses ❌ | pass | result.md l.9 |
| MUST: result uses the word `aborted` | pass | result.md l.9 |
| MUST: result states nothing was applied | pass | result.md l.9 |
| MUST: reason from the record (pre-flight RED, replace of `orders-db`) | pass | result.md l.10 |
| MUST: next steps TODO or operator-supplied | pass | result.md l.11 |
| MUST: ticket-close produced | pass | ticket-close.md l.9 |
| MUST: ticket-close outcome `aborted` | pass | ticket-close.md l.10 |
| MUST: ticket-close has no applied time | pass | ticket-close.md l.13 |
| MUST-NOT: `✅` in any draft | pass | `grep -rn '✅\|Done' aborted/expected-output` returns nothing |
| MUST-NOT: `Done` in any draft | pass | `grep -rn '✅\|Done' aborted/expected-output` returns nothing |
| MUST-NOT: applied/verified/completed claim | pass | ticket-close.md l.15 |
| Fix-round: ticket-close `Reason:` in plain words, no jargon | pass | ticket-close.md l.11 |
| Fix-round: numbered batch | pass | `aborted-r4.md` l.62 |

Round 4: 13 pass, 0 FAIL (README lines plus fix-round checks). No skill change.
