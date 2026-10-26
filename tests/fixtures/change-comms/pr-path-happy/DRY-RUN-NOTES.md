# Dry-run notes: change-comms against pr-path-happy

## Baseline (no skill)

A general assistant with no skill listed the three candidate records, left out the stale `rotate-logs` record as unrelated, and asked the operator to confirm the 1015 record and the 1000 pre-flight. It then asked for the timezone, the impact and the platform, and drafted all three messages in `text` blocks. It asked for the apply time, outcome and verification before the result draft. It did not claim the change was applied from `Outcome: completed`. The core flow is sound. The failures are in sourcing and in invented content: the heads-up has no record citation for the rollback, the impact and the other statements are embellished, and several assurances come from no source. Nothing is saved to `.culiops/change-comms/`, and there are no `<TODO: ...>` markers anywhere.

| MUST/MUST-NOT line | Result (pass/FAIL) | Evidence (quoted from transcript) |
|---|---|---|
| MUST: confirm chosen record (1015 + 1000 pre-flight), not rotate-logs | pass | "Can you confirm I should use the 1015 record and the 1000 pre-flight?" |
| MUST: ask for timezone when window arrives without one | pass | "Tomorrow is 2026-10-27. Which timezone is 14:00?" |
| MUST: heads-up at most 8 lines, contains `YELLOW`, `OPS-123`, PR URL | pass (borderline) | 8 non-blank lines, 10 raw lines; contains "*Risk:* The pre-flight check rated this YELLOW (proceed with caution)", the PR URL and the OPS-123 URL. Each line is a multi-sentence paragraph, so the length is only nominally within bounds |
| MUST: heads-up impact is the operator's text | FAIL | Operator said "~30-60s Multi-AZ failover, writes may fail briefly". Draft: "The resize triggers a Multi-AZ failover, about 30-60 seconds. Writes to orders-api may fail briefly during that time. After the failover, the service should recover on its own." The last sentence is invented reassurance |
| MUST: rollback cites `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` | FAIL | Draft: "the rollback is to revert the PR and re-apply (about 10 min), which causes a second short failover." No record citation. The "second short failover" is also an invented consequence. The source only appears in a chat note: "the rollback and PR from the execution record" |
| MUST: ask apply time, outcome, verification BEFORE the result draft | pass | "Please give me: 1. When was it applied (time and timezone)? 2. Did it succeed? 3. What did you check afterwards" |
| MUST: result draft contains `14:12 ICT` | pass | "*Applied:* 2026-10-27 at 14:12 ICT, inside the 14:00-14:15 window" |
| MUST: ticket-close contains PR URL, `14:12 ICT`, operator's verification | pass | "Applied: 2026-10-27 14:12 ICT (window 14:00-14:15 ICT)." and "Verification: database connections and orders-api error rate normal for 15 minutes after the apply." plus the PR URL |
| MUST: timezone never taken from records (pre-flight `(UTC)`, iac `Date`) | pass | Assistant noted "the records only have '2026-10-27 10:00/10:15', with no timezone" and asked the operator |
| MUST: date is 2026-10-27 or `tomorrow` | pass | "*When:* 2026-10-27, 14:00-14:15 ICT (15 min window)" |
| MUST-NOT: apply claim sourced from `Outcome: completed` | pass | The apply claims come from the operator's turn 8. The assistant noted "The execution record still says 'Verification: pending' and 'Outcome: completed'" and did not use it |
| MUST-NOT: `10:15` shown as apply time | pass | `10:15` appears only inside the evidence filename `...-1015.md`, never as a time |
| MUST-NOT: stale `rotate-logs` record used as a source | pass | "I'm leaving it out as unrelated." It was read "to check whether it is relevant" but not used |

### Behaviours the README does not list but the spec's anti-goals forbid

- Unsourced facts presented as fact in drafts: heads-up "CI applies it on merge, which will be inside the window" (no source for merge timing); result "No further action is needed from anyone"; ticket-close "Planned and announced beforehand" (the heads-up was only drafted, never posted) and "Rollback: not needed".
- Sourced content stated without a citation: "We are applying in a low-traffic window to limit exposure" comes from the pre-flight's "Mitigations Committed" ("Apply in an agreed low-traffic window", operator), and "no hard blocks" matches the pre-flight's "Hard Blocks: None". Neither is invented. But the draft states the mitigation as a present fact (the assistant admitted "I haven't seen traffic data") and cites neither record.
- Ticket-close is not in plain `Label: value` lines: it opens with a prose sentence ("Closing OPS-123. orders-db (orders-api, prod) was resized ...") and uses "- " bullets. The spec's Jira format is plain `Label: value` lines.
- Inference stated as fact: result "The expected Multi-AZ failover occurred as part of the resize". The assistant admitted the operator never said so, yet left it in.
- Missing facts were handled by asking the operator or inferring, never by a visible `<TODO: field>`.
- Heads-up and result are long prose paragraphs, not tight messages (heads-up ends with an extra "Please tell us in this thread..." ask the operator never requested).
- Ticket-close lists the repo-local `.culiops/...` record paths, which Jira readers cannot open. The assistant noticed this and only mentioned it in chat.
- Nothing is saved to `.culiops/change-comms/<service>-<action>-<ts>-<type>.md` and there is no review-gate fact table. The final message says "Done." and ends.
- No blockquotes were used, and no raw plan output appeared in this case.

### Failures to answer in SKILL.md

- Rollback line in a heads-up carried no `record: <path>#<section>` citation, so the reader cannot see where it came from.
- Operator-supplied impact was paraphrased and extended with reassurance ("should recover on its own") instead of being used as given.
- Asserted facts that no source or operator statement supports (merge happens inside the window, "no further action needed", "announced beforehand", "rollback not needed") instead of writing `<TODO: field>`.
- Stated a committed mitigation and a recorded finding as present facts without citing the record ("low-traffic window", "no hard blocks"), so the reader cannot tell sourced content from assumption.
- Jira ticket-close used prose and "- " bullets instead of plain `Label: value` lines.
- Stated an inference as an observed fact ("the failover occurred") when the operator had not reported it.
- Heads-up and result drafts are paragraph-length, with extra asks the operator did not request, not short copy-paste messages.
- Missing facts never became visible `<TODO: ...>` markers.
- No draft was saved to the `.culiops/change-comms/` output path and there was no fact table for the review gate.

## Dry-run (with skill)

Run 2026-10-26 by a sonnet runner following SKILL.md. The runner offered the 1015 record and the 1000 pre-flight at GATE 1 (the stale rotate-logs record was not offered), asked a heads-up batch (timezone, window, impact), then a separate post-apply batch (apply time, outcome, verification) before the result. The record `Outcome: completed` was never used as an apply claim. All README lines pass.

Drafts as produced:

heads-up (Google Chat), saved as `expected-output/orders-api-resize-rds-20261026-1500-heads-up.md`:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: YELLOW (pre-flight)
Rollback: revert PR + apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/482
Reply here if this window conflicts.
```

result (Google Chat), saved as `expected-output/orders-api-resize-rds-20261026-1500-result.md`:

```text
✅ Done: orders-api RDS resize (prod), applied 14:12 ICT
Verified: connections + error rate normal for 15 min
Ticket: OPS-123
```

ticket-close (Jira comment), saved as `expected-output/orders-api-resize-rds-20261026-1500-ticket-close.md`:

```text
Change completed
What: RDS orders-db resized db.t3.medium → db.t3.large
PR: https://github.com/acme/orders-infra/pull/482
Applied: 14:12 ICT
Verification: connections + error rate normal for 15 min
Rollback: not needed. Revert PR + apply if required.
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: confirm the 1015 record and 1000 pre-flight, not rotate-logs | pass | GATE 1: `I'll use .../orders-api-resize-rds-20261027-1015.md (Date 2026-10-27 10:15 ...) and .../orders-api-resize-rds-20261027-1000.md ...`; operator turn 2 confirms |
| MUST: ask for the timezone when the window arrives without one | pass | Batch A item 1 asked the timezone; turn 3 had none, turn 4 `ICT` answered it |
| MUST: heads-up at most 8 lines with `YELLOW`, `OPS-123`, PR 482 | pass | 8 lines; `Risk: YELLOW (pre-flight)`; `Ticket: OPS-123 \| PR: https://github.com/acme/orders-infra/pull/482` |
| MUST: impact is the operator's text; rollback cites `#Change Plan` | pass | `Impact: ~30-60s Multi-AZ failover, writes may fail briefly`; fact-table Rollback cites `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| MUST: ask apply time, outcome and verification BEFORE the result | pass | Transcript: Batch B asked before Step 3 (result) |
| MUST: result contains `14:12 ICT` | pass | `✅ Done: orders-api RDS resize (prod), applied 14:12 ICT` |
| MUST: ticket-close has the PR URL, `14:12 ICT` and the operator's verification | pass | `PR: https://github.com/acme/orders-infra/pull/482`, `Applied: 14:12 ICT`, `Verification: connections + error rate normal for 15 min` |
| MUST: pre-flight `(UTC)` and record `Date` never used as the window timezone | pass | window `2026-10-27 14:00 ICT`; ICT is operator-supplied |
| MUST: date 2026-10-27 or `tomorrow` | pass | `When: 2026-10-27 14:00 ICT, 15 min` |
| MUST-NOT: an apply claim sourced from `Outcome: completed` | pass | Apply outcome, time, verification all `operator-supplied` |
| MUST-NOT: `10:15` shown as an apply time | pass | `10:15` only in the GATE 1 line and a fact-table note as the record write time |
| MUST-NOT: the stale rotate-logs record used as a source | pass | not in any Sources line or fact-table row |

Round 1: 12 pass, 0 FAIL.

No fix targeted a failure here. The runner's own choices (batch per point in time, a GATE 2 per message, `applied` in the title, the slug derivation) are now written into the skill. Re-run because the output changes: chat title lines bold and no fixed-shape fact-table rows.
