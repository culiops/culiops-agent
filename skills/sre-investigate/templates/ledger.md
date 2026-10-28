# Ledger: <service> <env> <YYYYMMDD-HHMM>

The ledger is the working record of one run. It lives at `<output root>/runs/<service>-<env>-<YYYYMMDD-HHMM>/ledger.md`, next to `report.md` and the raw pulls. Only the main session writes it. Workers return text and the main session merges it.

How to fill it in:

- Times are UTC. Convert anything that arrives in another zone before it goes in a table, and say so in the row.
- Every query gets a row in the query log before its result is used anywhere else. Other sections cite query IDs, not copies of results.
- Every claim carries one label: `Confirmed`, `Likely`, `Assumed` or `Ruled out`. A cause is never labelled more strongly than the weakest link in its chain.
- Secrets, tokens, cookie values and header values never go in. Environment variable names are fine.
- Delete the guidance lines when you copy the file; keep the headings exactly as written.

Mode: <Fast | Deep>
Budget used: <queries used / allowed> · <log GB scanned / allowed> · <CloudWatch metric requests / allowed> · <other metered units, if any>

## Problem

| Field | Value |
|---|---|
| What | <the symptom as reported, in the reporter's words, then restated as something measurable> |
| Where | <service, environment, and which siblings (regions, shards, tenants, AZs, replicas) are in scope> |
| When | <reported time and the true onset, both UTC; if the onset is a guess, say so> |
| Who is affected | <users, callers or jobs, as far as known> |
| Trigger | <alarm, chat thread or ticket that started the run, with a link> |
| Mitigations already applied | <UTC time and action, one line each; "none known" is an answer> |
| Assumptions made at intake | <each assumption on its own line, for example the window chosen when the report said "this morning", and the zone used to convert it> |

## Impact

Source order: the SLO or error-budget burn named in `environment.md`, then load-balancer or APM request/error/duration metrics against the baseline, then `Assumed`.

| Field | Value |
|---|---|
| Symptom | <what is measurably wrong> |
| Affected | <flows, endpoints, populations; core flows named in `environment.md` count> |
| Since / ongoing | <UTC start; ongoing, or the UTC end> |
| Suggested severity | <level from the scale in `environment.md`> because <the criterion it met> |
| Basis | <query IDs> · label: <Confirmed, Likely, Assumed or Ruled out> |
| Third party in the path | <vendor and the contact route from the profile, or "none". The run cannot contact vendors; a human has to.> |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | <UTC> | <UTC> |
| Baseline (previous) | <UTC, same length, immediately before> | <UTC> |
| Baseline (−7d) | <UTC, incident window shifted back seven days> | <UTC> |

## Recurrence

Classify before blaming a change. Classes: `scheduled`, `chronic`, `recurring`, `sudden`, `unclassified`. Shapes seen in the signal: `step`, `ramp`, `periodic`, `ceiling`, `volume`.

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | <timestamps of the alarm that fired, converted to UTC, plus sibling alarms> |
| Signal, 14d at 1h resolution | <statistic used and why> · median <v> · p95 <v> · max excluding the incident <v> · incident <v> |
| Coverage | <per source: how far back the data really goes, gaps in alarm history, retention limits hit> |
| Class | <one of the five classes> · shape: <one of the five shapes, or "none clear"> |
| Reason | <the rule that matched, with the occurrence times that support it> |
| Label and queries | <label> · <query IDs> |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| <UTC> | <a change, a metric moving, an alarm, a mitigation> | <backend or tool> | <deeplink for a human, or query ID> |

Keep changes, signals and mitigations in one list, ordered by time. Mark rows that come from the reporter and not from a query as such.

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| <H1> | <one cause, specific enough to be wrong> | <what the data should show at the right time and scope> | <the query that would disprove it, written first> | <default, strong, default→strong or main> | <label> |

Below the table, one line per hypothesis for what the table has no column for:

- `<ID>` status: <open | testing | supported | refuted> · evidence: <query IDs> · note: <why the model tier, any reused earlier verdict>
- Hypotheses seeded from memory use the ID `from-history:<file>` and stay leads until a query of this run supports them.

## Code repos

Fill this in only when application code or IaC was read. Read by ref; no pull, no checkout.

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| <owner>/<repo> | <branch> | <sha> | <UTC> | <sha for each environment or revision read> |

## Query log

Every query, in the order it ran. Workers read this table before they query and never repeat a row.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| <W1-Q1> | <UTC> | <backend, profile or datasource, and the exact query text or a pointer to the file under the run directory> | <window in UTC, and step or period> | <estimate before; actual after, in the backend's own unit> | <one line, with its label> |

Notes on filling it in:

- IDs read `W<wave>-Q<n>`. A worker's queries are prefixed with its hypothesis ID until merged.
- Record what happened to slow queries too: stopped at about two minutes, backed off, narrowed. A query that failed is a row, and usually a gap.
- Log lines quoted in a result are cut to 300 characters and have secrets removed.
- Identifiers used in the query appear in the cell, each marked verified or `(unverified)` as in the profile.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| <what could not be read: an expired session, a missing token, a denied call, a retention limit, a stale clone, a source nobody gave access to> | <which hypotheses or labels this weakens> | <the exact command or variable, with names only, or the person to ask> |

Backend gaps from Phase 0 go here first. A denied call or an AccessDenied is recorded as a gap and left alone.

## Memory

| Item | Value |
|---|---|
| Lessons loaded | <lesson lines from `lessons.md` used as hints, with the sources they cover> |
| Re-verified this run | <lessons flagged `re-verify` that were checked, and the outcome> |
| History lookup | <the grep over `incidents/` front matter, run after the ranked hypotheses existed, and each match> |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| <process, identifier, noise or failure-mode> | <backend> | <one line, at most 300 characters, specific and actionable> | <the query of this run that backs it> |

Workers send candidates in their verdicts; copy them here unchanged. Nothing is written to `lessons.md` until the record phase and the user's reply.
