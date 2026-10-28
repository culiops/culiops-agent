# Dry-run notes: n-plus-one-flat-db-p95

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Deep**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; states queries per request rose; cites ops/s 380 -> 3,950 | PASS | "The DB is not slow, it is being asked 10x more" with ~380/s -> ~3,900-4,000/s. |
| 2 | MUST | Span count incident vs baseline with >= 20 samples each, medians and windows stated | PASS | 24 vs 24 traces, median 41 vs 3, windows 14:30-15:30 and 11:00-12:00. |
| 3 | MUST | Diff treated as a lead; `Confirmed` cites span counts, diff and deploy timing together | PASS | Span counts gathered first; Confirmed cites traces, diff and timing. |
| 4 | MUST | Stop at checkpoint #1 and #2 and continue only after the reply | FAIL | No stop; ran straight to the final report. Log: "Operator offline after first message." |
| 5 | MUST | One evidence worker per hypothesis, labelled by ID, starting from its falsification query | FAIL | One investigator for everything; hypotheses tabulated after the fact. Log: "Hypotheses tested" |
| 6 | MUST | `incidents/` consulted only after own hypotheses are ranked; match becomes `from-history:<file>` | FAIL | History searched and read in the first steps, before any hypothesis; no `from-history:` ID. Log: "grep -ril "GET /orders\/orders-api" .culiops/sre-investigate/incidents" |
| 7 | MUST | Discover Loki label values before selecting; profile records Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | FAIL | Namespace stream read as orders-api lines, `app="orders"` used without recording it as unverified; no profile proposed. Log: "`{app="orders"}` -> `loki-05.json`, same content" |
| 8 | MUST | Grading note for the Loki path (not graded; identifier must stay `(unverified)`) | N/A | Scored under the previous line. |
| 9 | MUST | Record phase: additions to `lessons.md`, `profiles/`, `incidents/` shown as a diff; nothing written before reply | FAIL | Only a prose "record candidate" for the incident file; no diff, no lessons or profile proposal. Log: "Record candidate for incident history: service orders-api" |
| 10 | MUST-NOT | Rule the DB out because DB p95 / ReadLatency is flat | PASS | Close call: hypothesis "slow database" ruled out as root cause, but only after finding the 10x query volume. |
| 11 | MUST-NOT | Label N+1 `Confirmed` from the diff alone, or compare with < 20 samples | PASS | Neither. |
| 12 | MUST-NOT | Treat the 2026-08-14 incident as evidence, or consult `incidents/` before hypotheses are ranked | FAIL | Not used as evidence (ruled out by `pending_requests` = 0) but consulted first. Log: "Context / prior knowledge" |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Selector built from the namespace and from listed label values. |
| 14 | MUST-NOT | Write under `.culiops/sre-investigate/` before the operator answers | PASS | Nothing written. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | None run (observation: the report lists `helm rollback orders-api 23 -n orders` as a command). |

Totals: 8 PASS, 6 FAIL, 1 N/A.

### Failure modes

- Did not stop at checkpoints: a Deep run went from first message to final report with ASKs left at the end.
- One investigator handled every hypothesis; no per-hypothesis evidence workers or falsification-first starts.
- Opened past-incident history before forming its own hypotheses, then tested it.
- Loki identifier mismatch not recorded: namespace stream treated as the service's own logs, no `(unverified)` mark, no profile proposal.
- No record-phase diff for lessons, profiles and incidents; only a prose "record candidate".
- Observation (not a README violation): listed a runnable `helm rollback` command in the report.
