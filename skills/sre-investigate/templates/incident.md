# Incident summary format

One short summary per finished run, at `<output root>/incidents/<date>-<service>.md`. If that name is taken (another environment or a second incident the same day), append `-<env>`, then `-2`, `-3`. It is the memory a later run greps. It is not the report: link to the run directory and keep the body to a screen.

Write one when the run named a cause at any label, or when the user asks. A run that found no cause, Fast mode especially, does not create one unless asked. It is written after the user approves the record-phase diff.

## Front matter

```yaml
---
id: <date>-<service>-<env>-<short-slug>      # lowercase
date: <YYYY-MM-DD>
service: <service>
env: <environment>
siblings: [<members affected>]               # or [all]
window_utc: <start>/<end>
symptoms: [<terms from the symptom list>]
cause_category: <one term from the cause list>
cause: <one line>
deps: [<services or third parties on the failing path>]
label: <Confirmed|Likely|Assumed>                # unknown cause_category always takes Assumed
mode: <fast|deep>
time_to_cause_min: <minutes, or null>
run: runs/<run directory name>
---
```

Keep every value on one line so that a `grep` over the front matter finds it.

## Body

- What happened: two or three sentences.
- Causal chain: trigger, mechanism, symptom, each with its label.
- What found it: the query or signal that decided the case.
- What did not help: dead ends worth skipping next time.
- Follow-ups raised.

## Symptom vocabulary

Use these words, several if needed. Use `other` only when none fits.

| Group | Terms |
|---|---|
| Request outcomes | `latency`, `timeouts`, `unavailable`, `errors-5xx`, `errors-4xx`, `throughput-drop` |
| Background work | `queue-backlog`, `job-failure` |
| Resources and process health | `crash-restart`, `memory`, `cpu`, `disk`, `db-connections` |
| Correctness and money | `data-inconsistency`, `cost-spike` |
| Anything else | `other` |

## Cause vocabulary

Choose exactly one.

| Term | Meaning |
|---|---|
| `deploy` | A release of application code or its image. |
| `config` | A change to configuration, flags, limits or infrastructure definition. |
| `dependency` | A service of the same organisation that this one calls or consumes from. |
| `third-party` | A vendor or external service outside the organisation. |
| `capacity` | Load within expected bounds exceeded provisioned or configured capacity. |
| `resource-exhaustion` | A finite resource ran out: memory, descriptors, connections, disk, quota. |
| `infra-event` | The platform changed under the service: instance reclaim, zone impairment, host failure, node drain. |
| `schedule` | A timed job, scheduled scaling action or maintenance window. |
| `traffic` | An unusual request pattern: a spike, a bot fleet, a retry storm. |
| `data` | The content of the data (a bad record, a size, a skew) triggered the failure. |
| `credentials-cert` | An expired or revoked credential or certificate. |
| `network-dns` | Routing, DNS or connectivity. |
| `unknown` | No cause reached `Likely`. |

## Label vocabulary

`Confirmed`, `Likely` or `Assumed`, the label of the cause as in the report. When `cause_category` is `unknown`, the label is `Assumed`: the lead hypothesis, if any, goes in the body. `Ruled out` applies to hypotheses, not to an incident.

## Lookup rules

- Search only after the run's own ranked hypotheses exist, so history cannot set the agenda. `grep` the front matter of `incidents/` for the service, each entry of `deps`, and the symptom words.
- A match becomes its own hypothesis with ID `from-history:<file>.md` (the file name exactly, extension included), even when it overlaps another one. It is a lead, never evidence, and a query of the current run has to support it.
- Past incidents are never passed to evidence workers.
