# Examples: Message Shapes for `change-comms`

Reference shapes for the `change-comms` skill. The skill reads this file when it drafts a message. Values below use a made-up world (service `billing-api`, env `production`, ticket `PAY-77`, timezone `HKT`, repo `github.com/example-pay/billing-infra`) and are illustrative only. Never copy a value from here into a real draft: every value in a real draft comes from a cited record or from the operator.

## Rules that apply to every draft

- Each draft goes in its own fenced `text` block with nothing else inside it. Never wrap a draft in a markdown blockquote (`>`), and never put commentary, labels or the redaction log inside the fence.
- English only. No raw plan output, plan counts, plan hashes, file paths, repo-local `.culiops/` paths or CLI commands.
- Every time carries the timezone the operator gave (`HKT` below). The record `Date` is never shown as the apply time.
- A fact with no source is written as a visible `<TODO: field>`, for example `<TODO: impact>`. Never infer it, soften it, or fill it with reassurance.
- Operator-supplied text (impact, next steps) is used as given. Do not extend it ("should recover on its own") and do not promise follow-ups on the operator's behalf ("I'll post here when...").
- Messages stay short and contain no extra asks beyond the closing line the shape defines.
- In the examples, `<link>` stands for a real URL parsed from the record or given by the operator. Where the URL is missing, the draft says `<TODO: PR link>`. Where no PR exists (direct apply, an abort before a PR was created, or the operator says none is raised yet), the PR line or `| PR:` segment is omitted. On GitLab the label is `MR:`, the host's own term.
- The shapes show plain text. In chat drafts (Google Chat, Slack) the title line is wrapped in `*...*`; see [Platform formatting](#platform-formatting).
- Fixed shape wording (emoji, title words, labels, closing line) is not a fact and needs no fact-table row. Every other value does.

## Heads-up

Sent before apply. Readable by an EM in about 5 seconds.

```text
🔧 Heads-up: infra change on billing-api (production)
When: 2026-11-04 21:30 HKT, ~20 min
What: move ElastiCache billing-sessions cache.m5.large → cache.r6g.large
Impact: logins may take a few seconds longer while the cache warms up
Risk: YELLOW (pre-flight)
Rollback: switch the node type back, about 25 min
Ticket: PAY-77 | PR: <link>
Reply here if this window conflicts.
```

Rules:
- **Length:** at most 8 lines, counting the non-blank lines inside the `text` block. The example above is exactly 8.
- **Required, in this order:** env (in the title), window with timezone, what, impact, risk, rollback, ticket (and PR if known), then the closing line `Reply here if this window conflicts.`
- **Risk** is the pre-flight verdict word exactly: `GREEN`, `YELLOW` or `RED`. For a multi-phase change it is the verdict of the phase(s) this window covers (if they differ, the highest, or one per phase). If there is no record, a verdict the operator gives is used; otherwise write `Risk: <TODO: pre-flight verdict>`. A pre-flight `ABORTED` is not a risk level: ask the operator.
- **Impact** is always operator-supplied. No record has an impact field. If the operator has not given it, write `Impact: <TODO: impact>`; do not reuse a pre-flight blast-radius sentence as impact.
- **Rollback** cites the record: `record: <path>#Change Plan`. Rollback text taken from the Change Plan is summarised, never copied wholesale. The `record: <path>#Change Plan` citation goes in the fact table, never in the draft text. No text found, no operator answer: `Rollback: <TODO: rollback>`.
- **PR** is shown only when parsed from an `Execution:` line or given by the operator. If a PR should exist but its URL is unknown, write `PR: <TODO: PR link>`; if no PR exists (yet), drop the `| PR:` segment. Never build a URL from the remote and branch.
- **When** is written as the operator gave it (the `~` above is the operator's). A relative day ("today", "tomorrow") is resolved to an absolute date in the operator's stated timezone, and the resolved date is shown back in the fact table at the review gate.
- **Committed mitigations** (for example "low-traffic window") may appear only as facts cited to the pre-flight `Mitigations Committed` section.

Same shape with missing facts left visible:

```text
🔧 Heads-up: infra change on billing-api (production)
When: 2026-11-04 21:30 HKT, ~20 min
What: move ElastiCache billing-sessions cache.m5.large → cache.r6g.large
Impact: <TODO: impact>
Risk: YELLOW (pre-flight)
Rollback: <TODO: rollback>
Ticket: PAY-77 | PR: <TODO: PR link>
Reply here if this window conflicts.
```

## Result

Sent after the change is actually applied. 2-4 lines inside the block. The emoji and the wording map from the outcome: `✅` success, `❌` failed or aborted, `⏸` partial. A failed, partial or aborted result never uses the ✅ shape or the word `Done`.

Success:

```text
✅ Done: billing-api session cache move (production), applied 21:47 HKT
Verified: cache hit rate back above 90%, no checkout errors
Ticket: PAY-77
```

Failed:

```text
❌ Failed: billing-api session cache move (production), stopped 21:39 HKT
State: rolled back, billing-sessions is cache.m5.large again
Next: <TODO: next steps>
Ticket: PAY-77
```

Partial (multi-phase):

```text
⏸ Partial: billing-api ledger move (production), phase 2 of 3, 22:55 HKT
State: dual-write and cutover live, decommission not started
Next: <TODO: next steps>
Ticket: PAY-77 | PR: <link>
```

Aborted:

```text
❌ Aborted: billing-api invoice archive lifecycle (production), nothing applied
Reason: stopped before apply: plan validation failed (rule would expire unpaid invoices)
Next: <TODO: next steps>
Ticket: PAY-77
```

Rules:
- **Sources.** On the direct-apply path, outcome and verification come from the record's `Outcome` and `Execution Log`, and `✅ Done` needs all three: Outcome `completed`, an `Execution:` line with no error, and a `Verification:` line with a clean re-plan or passed checks. Anything else (an error, changes left on re-plan, a failed or missing check, no Outcome) means the operator is asked for the outcome, and the draft uses `❌` or `⏸`; never read an outcome from free text such as "Apply complete!". On the PR path, Outcome `completed` means the PR was created, not applied: apply time, apply outcome and verification come from the operator, unless that phase's `Execution:` line records an operator-confirmed merge and apply. If no source has them, they are `<TODO: apply time>` / `<TODO: verification>`. Never write `Verified:` from a PR-created record.
- **Failed** states whether it was rolled back (operator-supplied or record-cited; otherwise `State: <TODO: rolled back or not>`) and the next step. A direct apply whose verification was not clean states the problem in plain words, taken from the record's `Verification:` line.
- **Next** is operator-supplied only. Pre-flight mitigations and L1 cause detail are not next steps until the operator chooses them. Do not add a retry condition, a promised new window, a "reopen this ticket" route, or a stated cause ("likely...").
- **Aborted** is only written after the operator confirms nothing was applied. If anything was applied, use the failed or partial shape. `Reason:` summarises the record's `Execution:` line in plain words, cited in the fact table; only when the record gives none is it operator-supplied, else `Reason: <TODO: reason>`. An aborted result carries no apply time.
- **Reason lines are for managers and developers:** plain words, no skill jargon (GATE, HARD BLOCK, Step N). A record line like `aborted at GATE — pre-flight RED (<cause>)` becomes `stopped before apply: pre-flight check failed (<cause>)`.
- **Partial** says "phase N of M" and names the current state in one line. On the PR path, `partially completed (phase N of M)` means phase N's PR was created: the `State:` line says a phase is applied only when an `Execution:` line records an operator-confirmed apply or the operator says so. Operator-supplied verification goes in that `State:` line.
- **No verification done.** If the operator says nothing was checked, write `Verified: pending`; if verification was not given at all, `Verified: <TODO: verification>`.
- A result carries no `Rollback:` line. A failed result states the rollback outcome in its `State:` line; any other rollback detail goes in only if the operator asks for it.

## Ticket-close

A Jira comment, posted when the work is finished. Plain `Label: value` lines only: no wiki markup (`h3.`, `*bold*`), no `- ` bullets, no prose paragraphs, no commit hashes, no file paths, no raw plan counts.

```text
Change completed
What: ElastiCache billing-sessions moved cache.m5.large → cache.r6g.large
PR: https://github.com/example-pay/billing-infra/pull/318
Applied: 2026-11-04 21:47 HKT
Verification: cache hit rate, checkout errors, login latency normal
Rollback: not needed. Switch the node type back if required.
```

Rules:
- Lines are exactly `What`, `PR`, `Applied`, `Verification`, `Rollback`, in that order, under a one-line title. Add `Outcome:` (after the title) when the outcome is not success. An aborted ticket-close also adds one `Reason:` line after `Outcome:`, in plain words and with the same sources as the aborted result (record, else operator, else `<TODO: reason>`), so a Jira reader can tell why.
- `PR` is the real URL, parsed from the `Execution:` line or given by the operator. Otherwise `PR: <TODO: PR link>`. Omit the `PR` line when no PR exists (direct apply, abort before a PR was created). A GitLab merge request uses the label `MR`.
- On a direct apply, the revert instruction after `Rollback: not needed.` is summarised from the Change Plan rollback path (no PR to revert, no CLI command).
- `Applied` and `Verification` come from the record only on the direct-apply path (under the same three conditions as a `✅` result); on the PR path they come from the operator. A time given with no date is written `Applied: <TODO: apply date> 21:47 HKT`; never borrow the window date.
- `Rollback: not needed` is allowed only when the outcome is a confirmed success, or a confirmed abort where nothing was applied (write `Rollback: not needed, nothing was applied`). On success, the revert instruction after it must cite the Change Plan in the fact table, or become `<TODO: rollback>`.
- The ticket key comes from the Ticket Reference: a Jira URL gives the key; a bare Jira key is used as the key and the ticket URL becomes `<TODO: ticket URL>` wherever it is shown; a non-Jira URL is shown as given; "none" means the operator is asked.

Not completed (aborted at the gate, so no PR was created and the `PR` line is omitted):

```text
Change aborted
Outcome: aborted, nothing applied
Reason: stopped before apply: plan validation failed (rule would expire unpaid invoices)
What: S3 invoice archive lifecycle, move to Glacier after 30 days instead of 90
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Platform formatting

| Platform | Bold | Notes |
|---|---|---|
| Google Chat (default) | `*bold*` | Same shape as Slack. Emoji render. |
| Slack | `*bold*` | Same shape as Google Chat. Emoji render. |
| Jira comment | none | Plain `Label: value` lines. No markup of any kind. |

The shapes above show plain text. In a chat draft, wrap the title line in `*...*` (for example `*✅ Done: billing-api session cache move (production), applied 21:47 HKT*`); labels stay plain unless the operator asks for bold labels (`*When:* 2026-11-04 21:30 HKT`). Never change the wording, order or line count. A Jira comment gets no markup at all. The default platform is Google Chat. Never use platform-specific mentions (`@channel`, `@here`) unless the operator typed them.

## Multi-phase

- **Heads-up:** one message for the whole change. `What` names the change first, then every phase, on one line, for example `What: billing-ledger move to Aurora, 3 phases: dual-write → cutover → decommission`, and the window covers all of them. If the operator's window covers only some phases, still name the change and every phase, then the ones this window covers: `What: billing-ledger move to Aurora, 3 phases: dual-write → cutover → decommission; this window: cutover`. With more than one phase pending, the operator is asked which phase(s) the window covers. `Risk` is the verdict of the covered phase(s), and `PR` is the covered phase's PR.
- **Result:** one message per phase, saying `phase N of M`. The PR link is that phase's PR. A partial or aborted outcome says which phase stopped and the current state.
- **Ticket-close:** only after the last phase is applied, or after an abort. It lists every phase's PR URL and its outcome, one `Label: value` line each, so every phase gets both a `PR (phase N of M)` line and an `Outcome (phase N of M)` line:

```text
Change completed
What: billing-ledger move to Aurora: dual-write, cutover, decommission
PR (phase 1 of 3): https://github.com/example-pay/billing-infra/pull/315
Outcome (phase 1 of 3): applied
PR (phase 2 of 3): https://github.com/example-pay/billing-infra/pull/316
Outcome (phase 2 of 3): applied
PR (phase 3 of 3): https://github.com/example-pay/billing-infra/pull/317
Outcome (phase 3 of 3): applied
Applied: phase 1 <TODO: apply time>; phase 2 <TODO: apply time>; phase 3 <TODO: apply time>
Verification: <TODO: verification>
Rollback: not needed. Revert each PR + apply if required, <TODO: rollback>
```

- **Abort across phases:** title `Change aborted`, `Outcome: aborted at phase N of M, <state>`, one `Reason:` line, and the same per-phase `PR` and `Outcome` lines (`applied`, `not applied`). Use `Rollback: not needed, nothing was applied` only if no phase was applied.
- **Partial with phases remaining, or last phase not confirmed applied:** the change gets a result only. The skill refuses to write a ticket-close and says why: the ticket-close is posted when the work is finished, and the work is not. On the PR path the last phase's apply status arrives in the question batch, so the refusal can come after it. Offer it again after the last phase or an abort.
