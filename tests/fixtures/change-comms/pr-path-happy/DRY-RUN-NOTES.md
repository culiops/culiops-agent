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

- Invented facts presented as fact in drafts: heads-up "CI applies it on merge, which will be inside the window" (no source for merge timing); "We are applying in a low-traffic window to limit exposure" (the pre-flight only lists it as a mitigation; the assistant admitted "I haven't seen traffic data" and kept the line); result "No further action is needed from anyone"; ticket-close "Planned and announced beforehand" (the heads-up was only drafted, never posted), "Rollback: not needed", "no hard blocks".
- Inference stated as fact: result "The expected Multi-AZ failover occurred as part of the resize". The assistant admitted the operator never said so, yet left it in.
- Missing facts were handled by asking the operator or inferring, never by a visible `<TODO: field>`.
- Heads-up and result are long prose paragraphs, not tight messages (heads-up ends with an extra "Please tell us in this thread..." ask the operator never requested).
- Ticket-close lists the repo-local `.culiops/...` record paths, which Jira readers cannot open. The assistant noticed this and only mentioned it in chat.
- Nothing is saved to `.culiops/change-comms/<service>-<action>-<ts>-<type>.md` and there is no review-gate fact table. The final message says "Done." and ends.
- No blockquotes were used, and no raw plan output appeared in this case.

### Failures to answer in SKILL.md

- Rollback line in a heads-up carried no `record: <path>#<section>` citation, so the reader cannot see where it came from.
- Operator-supplied impact was paraphrased and extended with reassurance ("should recover on its own") instead of being used as given.
- Asserted facts that no source or operator statement supports (merge happens inside the window, "low-traffic window", "no further action needed", "announced beforehand", "rollback not needed", "no hard blocks") instead of writing `<TODO: field>`.
- Stated an inference as an observed fact ("the failover occurred") when the operator had not reported it.
- Heads-up and result drafts are paragraph-length, with extra asks the operator did not request, not short copy-paste messages.
- Missing facts never became visible `<TODO: ...>` markers.
- No draft was saved to the `.culiops/change-comms/` output path and there was no fact table for the review gate.
