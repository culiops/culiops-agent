# Investigation: <service> <env>: <one-line symptom>

The report is the reader-facing result of one run. It lives at `<output root>/runs/<service>-<env>-<YYYYMMDD-HHMM>/report.md`. Everything in it comes from the ledger; if a statement has no query ID or code reference behind it, it is `Assumed` and says so.

How to fill it in:

- Times are shown in UTC and in the reader's local zone, taken from `environment.md`. If no zone is set there, ask; do not guess. Use two columns, or `HH:MM UTC (HH:MM local)`.
- Labels are `Confirmed`, `Likely`, `Assumed` and `Ruled out`. A cause is never labelled more strongly than its weakest causal link, and the TL;DR names that link.
- Fast mode writes the TL;DR first (also printed inline), then Impact, Causal chain, Gaps, To confirm and Cost. Deep mode fills every section.
- The run changed nothing it investigated. Wherever a mutation would be needed, describe it in prose. Never paste a runnable command that changes state into `## To confirm, a human would…` or `## Follow-ups`. Read-only commands a human can run to look for themselves are fine.
- Delete the guidance lines when you copy the file; keep the headings exactly as written.

Run: <run directory name> · Mode: <Fast | Deep> · Window: <incident window in UTC> (<same window in local zone>)

## TL;DR

| Field | Value |
|---|---|
| Cause | <one sentence> · label: <label> |
| Weakest link | <the least certain step of the causal chain and its label; this caps the cause's label> |
| Impact | <who or what, for how long, current status> |
| Severity | <suggested level> because <criterion met>. The incident owner decides. |
| Pattern | <scheduled, chronic, recurring, sudden or unclassified> · <basis> · <label> |
| Recommended action | <what a human should do first, in prose> |
| Time to cause | <minutes from start to the first Likely, and to Confirmed if reached> |
| Similar past incidents | <files from `incidents/` that matched, or "none", or "no history yet"> |

If a similar incident has happened before, say which occurrence this is and over what period, and make a permanent fix the first follow-up.

## Impact

<Symptom, affected population or flows, start and end, how it was measured (SLO burn, request metrics against baseline, or Assumed), and the third party in the path if there is one, with the route to contact it. Cite query IDs.>

## Recurrence

| Source | Window | Occurrences | When (UTC) | Normal vs incident |
|---|---|---|---|---|
| <trigger alarm> | 30d | <count> | <times> | <not applicable> |
| <sibling alarms> | 30d | <count> | <times> | <not applicable> |
| <signal> | 14d at 1h | <hours above normal> | <times> | <median/p95/max vs incident value> |

A recurring pattern names its count in the follow-ups. A chronic one adds an alert-tuning item.

## Timeline

| Time (local) | Time (UTC) | Event | Evidence |
|---|---|---|---|
| <local> | <UTC> | <change, signal, alarm or mitigation> | <query ID and deeplink for a human> |

## Causal chain

Trigger, then mechanism, then symptom. One line per step, each with its label and the query ID that supports it.

1. Trigger: <what started it> · <label> · <query IDs>
2. Mechanism: <how the trigger produced the failure> · <label> · <query IDs>
3. Symptom: <what users or callers saw> · <label> · <query IDs>

Deep mode adds why it became an incident: <what delayed detection, which limit or protection was missing, which capacity was short>. If several explanations are still standing, list them all in rank order and do not pick one for the sake of sounding decisive.

## Evidence

One entry per claim in the chain: what was observed, at what time and scope, the query ID, and a deeplink a human can open. Do not paste more than a few log lines; cut each to 300 characters and remove secrets.

## Ruled out

| Hypothesis | Why | Query |
|---|---|---|
| <statement> | <what the data showed instead> | <query ID> |

## Open hypotheses

| Hypothesis | Label | What would settle it |
|---|---|---|
| <statement> | <Likely or Assumed> | <the query or data that is missing, and why it could not be run> |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| <source not read> | <which statements it weakens> | <exact read-only step, names of variables only> |

If gaps exist, end the printed summary with: open items need your input.

## To confirm, a human would…

A numbered list of checks the run could not do because they would touch the system (reproducing the failure, calling an endpoint, opening a database session, looking at a vendor console, asking a vendor). Describe each in prose with what result would confirm or refute the cause. These are not commands to paste, and nothing in this list may change state.

1. <…>

## Follow-ups

Prose only, and never a runnable command that changes state. A new session with the right tool and approvals does any change.

| Kind | Item |
|---|---|
| Fix | <what should change to remove the cause> |
| Prevention | <the alert, limit, test or rollout step that would have stopped or shortened this> |
| Observability gap | <the signal that was missing or too coarse> |

## Cost

<queries run> queries · <log GB scanned> GB of logs · <CloudWatch metric requests> metric requests · <other metered units> · about <amount> in metered charges

This line is last in the report and is always printed.
