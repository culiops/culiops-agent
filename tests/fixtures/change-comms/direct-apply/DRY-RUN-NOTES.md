# Dry-run notes: change-comms against direct-apply

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md. The runner confirmed the direct-apply record, asked the platform separately (Slack), asked the apply time ("don't know"), and saved a result and a ticket-close. Outcome and verification came from the record, as the direct-apply rule requires; the record `Date` 11:00 is never shown as the apply time. One README MUST failed: the Slack draft has no `*bold*`, because the skill treated bold as optional and the spec says both chat platforms use it.

Drafts as produced:

result (Slack), saved as `expected-output/orders-api-add-5xx-alarm-20261026-1500-result.md`:

```text
✅ Done: orders-api ALB 5xx alarm (prod), finished <TODO: apply time>
Verified: re-plan shows no changes, alarm in OK state
Ticket: OPS-123
```

ticket-close (Jira comment), saved as `expected-output/orders-api-add-5xx-alarm-20261026-1500-ticket-close.md`:

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate (prod)
PR: <TODO: PR link>
Applied: <TODO: apply time>
Verification: re-plan shows no changes, alarm in OK state
Rollback: not needed. Remove the alarm and re-apply if required.
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: result uses Slack formatting (`*bold*`, no wiki markup) | FAIL | No wiki markup, but no `*bold*` either: `✅ Done: orders-api ALB 5xx alarm (prod), finished <TODO: apply time>`. `messages.md` made bold optional |
| MUST: verification cited as `record: ...-20261027-1100.md#Execution Log` | pass | Fact table: Verification \| re-plan reported no changes; alarm state OK \| `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log` |
| MUST: outcome taken from the record and may be stated | pass | Fact table Outcome cites `#Outcome`; draft `Verified: re-plan shows no changes, alarm in OK state` |
| MUST: apply time omitted or `<TODO: apply time>`, listed under Open TODOs | pass | Title `finished <TODO: apply time>`; ticket-close `Applied: <TODO: apply time>`; both listed under Open TODOs |
| MUST: result and ticket-close drafts produced | pass | two files saved |
| MUST-NOT: `11:00` shown as the apply time | pass | `11:00` appears only in the fact table's Record Date row, labelled not an event time |
| MUST-NOT: an invented apply time | pass | no time in either draft |

Round 1: 6 pass, 1 FAIL.

Not a README line, but an anti-goal: the ticket-close carries `PR: <TODO: PR link>` on a direct apply, where no PR exists.

Fixes made in the skill (re-run required):
- Chat drafts bold the title line as `*...*` by default (Constraint 16, `messages.md#platform-formatting`).
- No PR line on a direct apply (Constraint 8, Red Flag row, `messages.md`).
- Success title wording is `applied <time>` instead of `finished <time>`.
- The platform is stated at GATE 1 instead of being asked separately.

## Round 2

Run against b76eccc. The Slack title is bold. Outcome and verification are taken from the record. The PR line is omitted because this was a direct apply. The apply time is a TODO.

Drafts as produced:

result (Slack), `expected-output/orders-api-add-5xx-alarm-20261026-1500-result.md`:

```text
*✅ Done: orders-api add CloudWatch alarm for ALB 5xx rate (prod), applied <TODO: apply time>*
Verified: re-plan shows no changes, alarm state OK
Ticket: OPS-123
```

ticket-close (Jira comment), `expected-output/orders-api-add-5xx-alarm-20261026-1500-ticket-close.md`:

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan showed no changes, alarm state OK
Rollback: not needed. Remove the alarm and re-apply if required.
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: Slack formatting (`*bold*`, no wiki markup) | pass | result.md: l.9 `*✅ Done: ... applied <TODO: apply time>*` |
| MUST: verification cited `...-20261027-1100.md#Execution Log` | pass | result.md: l.25 |
| MUST: outcome from the record | pass | result.md: l.22 cites `#Outcome`; l.10 `Verified: re-plan shows no changes, alarm state OK` |
| MUST: apply time omitted or `<TODO: apply time>`, listed under Open TODOs | pass | both: R l.9 + l.37; TC l.11 + l.40 |
| MUST: result and ticket-close produced | pass | both: two files |
| MUST-NOT: `11:00` as apply time | pass | both: `11:00` absent from both files |
| MUST-NOT: invented apply time | pass | both: TODO only |

Round 2: 7 pass, 0 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 4 (final skill 51fdbe8)

The Slack title is bold. Outcome and verification come from the record. The PR line is omitted (direct apply). The apply time is a TODO. Citations use `#header`, and the batch is numbered.

Drafts as produced:

result (Slack), `expected-output/orders-api-add-5xx-alarm-20261026-1500-result.md`:

```text
*✅ Done: orders-api ALB 5xx alarm (prod), applied <TODO: apply time>*
Verified: re-plan showed no changes, alarm state OK
Ticket: OPS-123
```

ticket-close (Jira comment), `expected-output/orders-api-add-5xx-alarm-20261026-1500-ticket-close.md`:

```text
Change completed
What: CloudWatch alarm added for orders-api ALB 5xx rate
Applied: <TODO: apply time>
Verification: re-plan showed no changes, alarm state OK
Rollback: not needed. Remove the alarm resource and re-apply if required.
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: Slack formatting (`*bold*`, no wiki markup) | pass | result.md l.9 |
| MUST: verification cited `...-20261027-1100.md#Execution Log` | pass | result.md l.21 |
| MUST: outcome taken from the record | pass | result.md l.21 |
| MUST: apply time omitted or TODO, listed under Open TODOs | pass | result.md l.9 |
| MUST: result and ticket-close produced | pass | ticket-close.md l.9 |
| MUST-NOT: `11:00` as the apply time | pass | `11:00` absent from both files |
| MUST-NOT: invented apply time | pass | ticket-close.md l.11 |
| Fix-round: numbered batch | pass | `direct-apply-r4.md` l.54 |

Round 4: 8 pass, 0 FAIL (README lines plus fix-round checks). No skill change.
