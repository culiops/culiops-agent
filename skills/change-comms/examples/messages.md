# Examples: Message Shapes for `change-comms`

Reference shapes for the `change-comms` skill. The skill reads this file when it drafts a message. Values below use the fixture world (service `orders-api`, env `prod`, ticket `OPS-123`, repo `github.com/acme/orders-infra`) and are illustrative only. Never copy a value from here into a real draft: every value in a real draft comes from a cited record or from the operator.

## Rules that apply to every draft

- Each draft goes in its own fenced `text` block with nothing else inside it. Never wrap a draft in a markdown blockquote (`>`), and never put commentary, labels or the redaction log inside the fence.
- English only. No raw plan output, plan counts, plan hashes, file paths, repo-local `.culiops/` paths or CLI commands.
- Every time carries the timezone the operator gave (`ICT` below). The record `Date` is never shown as the apply time.
- A fact with no source is written as a visible `<TODO: field>`, for example `<TODO: impact>`. Never infer it, soften it, or fill it with reassurance.
- Operator-supplied text (impact, next steps) is used as given. Do not extend it ("should recover on its own") and do not promise follow-ups on the operator's behalf ("I'll post here when...").
- Messages stay short and contain no extra asks beyond the closing line the shape defines.
- In the examples, `<link>` stands for a real URL parsed from the record or given by the operator. Where the URL is missing, the draft says `<TODO: PR link>`. Where no PR exists (direct apply, an abort before a PR was created, or the operator says none is raised yet), the PR line or `| PR:` segment is omitted.
- The shapes show plain text. In chat drafts (Google Chat, Slack) the title line is wrapped in `*...*`; see [Platform formatting](#platform-formatting).
- Fixed shape wording (emoji, title words, labels, closing line) is not a fact and needs no fact-table row. Every other value does.

## Heads-up

Sent before apply. Readable by an EM in about 5 seconds.

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, ~15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: YELLOW (pre-flight)
Rollback: revert PR + apply, ~10 min
Ticket: OPS-123 | PR: <link>
Reply here if this window conflicts.
```

Rules:
- **Length:** at most 8 lines, counting the non-blank lines inside the `text` block. The example above is exactly 8.
- **Required, in this order:** env (in the title), window with timezone, what, impact, risk, rollback, ticket (and PR if known), then the closing line `Reply here if this window conflicts.`
- **Risk** is the pre-flight verdict word exactly: `GREEN`, `YELLOW` or `RED`. If there is no pre-flight record, write `Risk: <TODO: pre-flight verdict>`.
- **Impact** is always operator-supplied. No record has an impact field. If the operator has not given it, write `Impact: <TODO: impact>`; do not reuse a pre-flight blast-radius sentence as impact.
- **Rollback** cites the record: `record: <path>#Change Plan`. Rollback text taken from the Change Plan is summarised, never copied wholesale. The `record: <path>#Change Plan` citation goes in the fact table, never in the draft text. No text found, no operator answer: `Rollback: <TODO: rollback>`.
- **PR** is shown only when parsed from an `Execution:` line or given by the operator. If a PR should exist but its URL is unknown, write `PR: <TODO: PR link>`; if no PR exists (yet), drop the `| PR:` segment. Never build a URL from the remote and branch.
- **When** is written as the operator gave it (the `~` above is the operator's). A relative day ("tomorrow") is resolved to an absolute date against the session date.
- **Committed mitigations** (for example "low-traffic window") may appear only as facts cited to the pre-flight `Mitigations Committed` section.

Same shape with missing facts left visible:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, ~15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: <TODO: impact>
Risk: YELLOW (pre-flight)
Rollback: <TODO: rollback>
Ticket: OPS-123 | PR: <TODO: PR link>
Reply here if this window conflicts.
```

## Result

Sent after the change is actually applied. 2-4 lines inside the block. The emoji and the wording must match the outcome exactly: `✅` success, `❌` failed or aborted, `⏸` partial. A failed, partial or aborted result never uses the ✅ shape or the word `Done`.

Success:

```text
✅ Done: orders-api RDS resize (prod), applied 14:12 ICT
Verified: connections + error rate normal for 15 min
Ticket: OPS-123
```

Failed:

```text
❌ Failed: orders-api RDS resize (prod), stopped 14:08 ICT
State: rolled back, orders-db is db.t3.medium again
Next: <TODO: next steps>
Ticket: OPS-123
```

Partial (multi-phase):

```text
⏸ Partial: orders-api upgrade (prod), phase 2 of 3 applied, 14:40 ICT
State: snapshot and upgrade applied, cleanup not started
Next: <TODO: next steps>
Ticket: OPS-123 | PR: <link>
```

Aborted:

```text
❌ Aborted: orders-api RDS resize (prod), nothing applied
Reason: pre-flight RED, the plan replaces orders-db
Next: <TODO: next steps>
Ticket: OPS-123
```

Rules:
- **Sources.** On the direct-apply path, outcome and verification come from the record's `Outcome` and `Execution Log`. On the PR path, Outcome `completed` means the PR was created, not applied: apply time, apply outcome and verification come from the operator. If neither source has them, they are `<TODO: apply time>` / `<TODO: verification>`. Never write `Verified:` from a PR-created record.
- **Failed** states whether it was rolled back (operator-supplied or record-cited; otherwise `State: <TODO: rolled back or not>`) and the next step.
- **Next** is operator-supplied only. Pre-flight mitigations and L1 cause detail are not next steps until the operator chooses them. Do not add a retry condition, a promised new window, a "reopen this ticket" route, or a stated cause ("likely...").
- **Aborted** is only written after the operator confirms nothing was applied. If anything was applied, use the failed or partial shape. `Reason:` summarises the record's `Execution:` line (for example `aborted at GATE — pre-flight RED (replace of orders-db)`), cited in the fact table; only when the record gives none is it operator-supplied, else `Reason: <TODO: reason>`. An aborted result carries no apply time.
- **Partial** says "phase N of M" and names the current state in one line.
- A result carries no `Rollback:` line. A failed result states the rollback outcome in its `State:` line; any other rollback detail goes in only if the operator asks for it.

## Ticket-close

A Jira comment, posted when the work is finished. Plain `Label: value` lines only: no wiki markup (`h3.`, `*bold*`), no `- ` bullets, no prose paragraphs, no commit hashes, no file paths, no raw plan counts.

```text
Change completed
What: RDS orders-db resized db.t3.medium → db.t3.large
PR: https://github.com/acme/orders-infra/pull/42
Applied: 2026-10-27 14:12 ICT
Verification: connections, error rate, p95 latency normal
Rollback: not needed. Revert PR + apply if required.
```

Rules:
- Lines are exactly `What`, `PR`, `Applied`, `Verification`, `Rollback`, in that order, under a one-line title. Add `Outcome:` (after the title) when the outcome is not success.
- `PR` is the real URL, parsed from the `Execution:` line or given by the operator. Otherwise `PR: <TODO: PR link>`. Omit the `PR` line when no PR exists (direct apply, abort before a PR was created).
- On a direct apply, the revert instruction after `Rollback: not needed.` is summarised from the Change Plan rollback path (no PR to revert, no CLI command).
- `Applied` and `Verification` come from the record only on the direct-apply path; on the PR path they come from the operator.
- `Rollback: not needed` is allowed only when the outcome is a confirmed success, or a confirmed abort where nothing was applied (write `Rollback: not needed, nothing was applied`). On success, the revert instruction after it must cite the Change Plan in the fact table, or become `<TODO: rollback>`.
- The ticket key comes from the Ticket Reference URL, or from the operator when the reference is "none".

Not completed (aborted at the gate, so no PR was created and the `PR` line is omitted):

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
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

The shapes above show plain text. In a chat draft, wrap the title line in `*...*` (for example `*✅ Done: orders-api RDS resize (prod), applied 14:12 ICT*`); labels stay plain unless the operator asks for bold labels (`*When:* 2026-10-27 14:00 ICT`). Never change the wording, order or line count. A Jira comment gets no markup at all. The default platform is Google Chat. Never use platform-specific mentions (`@channel`, `@here`) unless the operator typed them.

## Multi-phase

- **Heads-up:** one message for the whole change. `What` always names every phase on one line, for example `What: 3 phases: snapshot → upgrade → cleanup`, and the window covers all of them. If the operator's window covers only some phases, still name every phase, then the ones this window covers: `What: 3 phases: snapshot → upgrade → cleanup; this window: upgrade`.
- **Result:** one message per phase, saying `phase N of M`. The PR link is that phase's PR. A partial or aborted outcome says which phase stopped and the current state.
- **Ticket-close:** only after the last phase is applied, or after an abort. It lists every phase's PR URL and its outcome, one `Label: value` line each, so every phase gets both a `PR (phase N of M)` line and an `Outcome (phase N of M)` line:

```text
Change completed
What: orders-api upgrade: snapshot, upgrade, cleanup
PR (phase 1 of 3): https://github.com/acme/orders-infra/pull/40
Outcome (phase 1 of 3): applied
PR (phase 2 of 3): https://github.com/acme/orders-infra/pull/41
Outcome (phase 2 of 3): applied
PR (phase 3 of 3): https://github.com/acme/orders-infra/pull/42
Outcome (phase 3 of 3): applied
Applied: phase 1 <TODO: apply time>; phase 2 <TODO: apply time>; phase 3 <TODO: apply time>
Verification: <TODO: verification>
Rollback: not needed. Revert each PR + apply if required, <TODO: rollback>
```

- **Abort across phases:** title `Change aborted`, `Outcome: aborted at phase N of M, <state>`, and the same per-phase `PR` and `Outcome` lines (`applied`, `not applied`). Use `Rollback: not needed, nothing was applied` only if no phase was applied.
- **Partial with phases remaining:** a partial outcome gets a `⏸` result only. The skill refuses to write a ticket-close and says why: the ticket-close is posted when the work is finished, and the work is not. Offer it again after the last phase or an abort.
