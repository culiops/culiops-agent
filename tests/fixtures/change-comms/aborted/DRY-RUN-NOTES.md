# Dry-run notes: change-comms against aborted

## Baseline (no skill)

A general assistant with no skill read both records, asked which platform, and (good behaviour) asked whether anything had been merged or applied before saying "no change was made". It then drafted a result and a ticket-close that both state the change was aborted and nothing was applied. The facts of the abort are right: RED, replace of `orders-db`, no apply. The failures are the missing ❌ marker and, mainly, a large amount of invented content: a next-steps plan, a customer-impact statement and a promise to post a new window, none of which came from the records or the operator. Both drafts also carry raw plan counts, and the ticket-close shows record times with no timezone.

| MUST/MUST-NOT line | Result (pass/FAIL) | Evidence (quoted from transcript) |
|---|---|---|
| MUST: result uses ❌ | FAIL | Result starts "*orders-api prod: RDS resize NOT applied (aborted)*" with no ❌ anywhere in the draft |
| MUST: result uses the word `aborted` | pass | "RDS resize NOT applied (aborted)" |
| MUST: result states nothing was applied | pass | "stopped before anything was applied. Prod is unchanged." and "Nothing was applied, so there is nothing to roll back." |
| MUST: result gives the reason from the record (pre-flight RED, replace of `orders-db`) | pass | "the pre-flight check came back RED (hard block). The Terraform plan did not resize the instance in place. It would have destroyed and recreated aws_db_instance.orders (1 to destroy, 1 to add)" |
| MUST: what happens next is a TODO or operator-supplied | FAIL | The operator gave no next steps. The draft invents them: "*Next:* the resize will not be retried until the replacement is understood and removed from the plan (and a manual snapshot is taken first as a safeguard). I'll post here when there's a new window." There is no `<TODO: next steps>` |
| MUST: ticket-close produced | pass | Draft 2 is a Jira comment on OPS-123 |
| MUST: ticket-close lists outcome `aborted` | pass | "Closing as not done: change aborted, nothing applied." and "Outcome: aborted." |
| MUST: ticket-close has no applied time | pass | No applied time. It states "No apply was run. Prod was not changed." |
| MUST-NOT: `✅` in any draft | pass | Not present |
| MUST-NOT: `Done` in any draft | pass | Not in either draft. (The closing chat line was "Both accepted.") |
| MUST-NOT: any statement that the change was applied, verified or completed | pass | Both drafts say the opposite. "Rollback and post-change verification are not applicable." |

### Behaviours the README does not list but the spec's anti-goals forbid

- Operator-supplied impact was invented: "*Impact:* none. Nothing was applied, so there is nothing to roll back. No customer impact and no verification was needed." The operator gave no impact. "No customer impact" is an assertion nobody supplied.
- An invented remediation plan in the ticket-close: "Follow-up before any retry: remove the replace-forcing change so the plan shows an in-place modify, take a manual snapshot, re-run pre-flight, then raise a new change or reopen this ticket." It is partly derived from the pre-flight mitigations, but it is presented as a decided follow-up.
- A technical root-cause guess in a broad chat message: "The likely cause is a changed `identifier` argument in the working tree, which forces replacement." The result draft states a hypothesis from the L1 scan ("likely cause") as an explanation, and it is not suited to the chat audience.
- Raw plan counts in both drafts: "(1 to destroy, 1 to add)".
- Record times without a timezone: ticket-close shows "Pre-flight (2026-10-27 10:00)" and "IaC change execution (2026-10-27 10:15)". The pre-flight record said `(UTC)`, which the draft dropped, and the iac record carries no timezone. The operator was never asked.
- Noise a Jira reader cannot use: the commit hash "Commit: d9e0f1a" and the repo-local `.culiops/` paths.
- A promise on the operator's behalf: "I'll post here when there's a new window."
- Nothing is saved to `.culiops/change-comms/`. No blockquotes were used.

### Failures to answer in SKILL.md

- Failure message had no ❌ marker, so it does not match the style the recorded outcome calls for.
- What happens next was invented (retry conditions, snapshot, a promised new window) instead of being operator-supplied or `<TODO: next steps>`.
- Impact was asserted ("No customer impact") although impact is always operator-supplied.
- A root-cause hypothesis and a remediation plan were written into the drafts, beyond what the record states as outcome.
- Raw plan counts ("1 to destroy, 1 to add") were put in chat and Jira drafts.
- Record `Date` times were shown with no timezone and the `(UTC)` tag was dropped.
- A promise to post later was made on the operator's behalf.
- No draft was saved to the `.culiops/change-comms/` output path.
