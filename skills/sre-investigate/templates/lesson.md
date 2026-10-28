# Lesson format

Lessons are short facts a later run can use as a hint. They live in one file, `<output root>/lessons.md`, one lesson per line, and are added only in the record phase after the user approves the diff.

## One lesson

```text
- type: <process|identifier|noise|failure-mode> | service: <service or "any"> | source: <backend> | statement: <one line> | run: <run directory name> | query_id: <ID> | re-verify: <yes|no>
```

| Field | Meaning |
|---|---|
| `type` | `process`: how to query well (a label that must be filtered, a limit that truncates silently). `identifier`: what a thing is called in a backend. `noise`: a harmless signal that keeps appearing, with how often it normally does. `failure-mode`: a cause that has come back before, plus what it looks like in the data. |
| `service` | The service it was learned on, or `any` when it holds for a whole class of services. |
| `source` | One word from this set, the lowercase backend name used in the ledger: `cloudwatch` (metrics and alarms), `cw-logs` (Logs and Logs Insights), `prometheus`, `loki`, `tempo`, `xray`, `sentry`, `kubectl`, `aws` (other AWS reads), `git`, `github`, `tickets`, `waf`. A mapped backend uses its own lowercase name (`datadog`, `newrelic`, `elastic`). |
| `statement` | One line, at most 300 characters, specific and actionable. Do not use the `|` character. No secrets. |
| `run` | The run directory where it was learned. |
| `query_id` | The ledger query that backs it. A lesson with no query behind it is not recorded. |
| `re-verify` | `yes` when it is old or was contradicted once. The first time a run touches that source, check it and report the outcome. |

## How lessons are used

- A lesson is a hint about how to query, never evidence about a cause. A wrong lesson is a finding: it goes into the ledger's lesson candidates with the query that showed it wrong.
- An evidence worker receives at most ten `process` and `identifier` lessons, only for the sources it will use. It never receives `failure-mode` lessons or past incidents; those can bias it toward a cause.
- Lessons that hold beyond the investigated estate are noted in the report as candidates for the skill itself. They are proposed outside an investigation, in a normal session.

## Updates

Proposed as part of the record-phase diff, each citing a query ID of the current run:

- `confirm`: the lesson held. Refresh `run` and `query_id`.
- `re-verified`: the check passed. Set `re-verify: no`.
- `contradict`: replace the statement, or remove the line.
- `drop`: remove the line.

The user can accept, edit or skip each item.
