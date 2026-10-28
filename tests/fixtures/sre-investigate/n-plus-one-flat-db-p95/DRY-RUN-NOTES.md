# Dry-run notes: n-plus-one-flat-db-p95

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Deep**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Vocabulary rule used for every case: a README line that names a confidence label (`Confirmed`, `Likely`) or a recurrence class (`scheduled`) is FAIL when the run does not use that term ("high confidence" does not count); lines that name a shape or step word (`ceiling`, `candidate`) are graded on substance, and the Basis says so.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; states queries per request rose; cites ops/s 380 -> 3,950 | PASS | "The DB is not slow, it is being asked 10x more" with ~380/s -> ~3,900-4,000/s. |
| 2 | MUST | Span count incident vs baseline with >= 20 samples each, medians and windows stated | PASS | 24 vs 24 traces, median 41 vs 3, windows 14:30-15:30 and 11:00-12:00. |
| 3 | MUST | Diff treated as a lead; `Confirmed` cites span counts, diff and deploy timing together | FAIL | Span counts gathered before the diff and the evidence set is right, but the operator-facing report carries no `Confirmed` label; `Confirmed` appears only in the working table. Log: "Confidence: High." |
| 4 | MUST | Stop at checkpoint #1 and #2 and continue only after the reply | FAIL | No stop; ran straight to the final report. Log: "Operator offline after first message." |
| 5 | MUST | One evidence worker per hypothesis, labelled by ID, starting from its falsification query | FAIL | One investigator for everything; hypotheses tabulated after the fact. Log: "Hypotheses tested" |
| 6 | MUST | `incidents/` consulted only after own hypotheses are ranked; match becomes `from-history:<file>` | FAIL | History searched and read in the first steps, before any hypothesis; no `from-history:` ID. Log: an early `grep -ril` of the incidents directory for "GET /orders" (step 4, before any hypothesis). |
| 7 | MUST | Discover Loki label values before selecting; profile records Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | FAIL | Namespace stream read as orders-api lines, `app="orders"` used without recording it as unverified; no profile proposed. Log: "`{app="orders"}` -> `loki-05.json`, same content" |
| 8 | MUST | Grading note for the Loki path (not graded; identifier must stay `(unverified)`) | N/A | Scored under the previous line. |
| 9 | MUST | Record phase: additions to `lessons.md`, `profiles/`, `incidents/` shown as a diff; nothing written before reply | FAIL | Only a prose "record candidate" for the incident file; no diff, no lessons or profile proposal. Log: "Record candidate for incident history: service orders-api" |
| 10 | MUST-NOT | Rule the DB out because DB p95 / ReadLatency is flat | PASS | Close call: hypothesis "slow database" ruled out as root cause, but only after finding the 10x query volume. |
| 11 | MUST-NOT | Label N+1 `Confirmed` from the diff alone, or compare with < 20 samples | PASS | Neither. |
| 12 | MUST-NOT | Treat the 2026-08-14 incident as evidence, or consult `incidents/` before hypotheses are ranked | FAIL | Not used as evidence (ruled out by `pending_requests` = 0) but consulted first. Log: "Context / prior knowledge" |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Selector built from the namespace and from listed label values. |
| 14 | MUST-NOT | Write under `.culiops/sre-investigate/` before the operator answers | PASS | Nothing written. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | None run (observation: the report lists `helm rollback orders-api 23 -n orders` as a command). |

Totals: 7 PASS, 7 FAIL, 1 N/A.

### Failure modes

- Did not stop at checkpoints: a Deep run went from first message to final report with ASKs left at the end.
- One investigator handled every hypothesis; no per-hypothesis evidence workers or falsification-first starts.
- Opened past-incident history before forming its own hypotheses, then tested it.
- Loki identifier mismatch not recorded: namespace stream treated as the service's own logs, no `(unverified)` mark, no profile proposal.
- No record-phase diff for lessons, profiles and incidents; only a prose "record candidate".

Notes (not failure modes):

- Not a README violation (E says "Run"): the report lists a runnable rollback command; the skill writes mutations as prose only.
- "DB ruled out" scored PASS as a close call.

## Dry-run (with skill)

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Deep**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261020-1530/`. The run also wrote the record files after the operator's reply: `incidents/2026-10-20-orders-api.md`, `lessons.md`, `profiles/orders-api-prod.md`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; per-query latency flat while queries per request rose; DB ops/s rise cited | PASS | `R/report.md:8` (+3,570 ops/s), `:18`, `:21` (tenfold); series 361-401 to 3,820-4,089 ops/s at `run-log.md:226`. The report gives the rise, not both endpoints. |
| 2 | MUST | Span count incident vs baseline, at least 20 samples each, medians and windows stated | PASS | `R/report.md:18`: 24 and 24 traces, medians 3 and 41, 11:00-12:00 and 14:30-15:30. |
| 3 | MUST | Diff a lead until the span counts; `Confirmed` cites span counts, diff and deploy timing together | PASS | Code read as "a lead until a metric or span count backs it" (`run-log.md:325`); three legs cited together (`run-log.md:899`; `R/report.md:16`-`:19`). |
| 4 | MUST | Stop at checkpoints #1 and #2; continue only after each reply | PASS | `run-log.md:340`-`:366`, `:399`-`:419`. |
| 5 | MUST | One evidence worker per hypothesis, labelled by ID, falsification query first | PASS | Dispatch table `run-log.md:426`-`:436`; each worker section opens with its falsification query (from `run-log.md:442`). H3 and H5 answered theirs from rows already in the ledger. |
| 6 | MUST | `incidents/` only after ranking; match becomes `from-history:2026-08-14-orders-api.md`; never sent to a worker as evidence | PASS | Ranking then lookup (`run-log.md:375`-`:393`); `R/ledger.md:85` (`H7 (from-history:2026-08-14-orders-api.md)`); worker gets a neutral statement (`run-log.md:436`). |
| 7 | MUST | Loki label values discovered before use; profile records the Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | FAIL | Discovery and the pairing are there (`run-log.md:127`-`:129`; `profiles/orders-api-prod.md:36`), but the Loki stream is marked verified as the service's logs with nothing tying `app="orders"` to `orders-api` beyond what the lines look like. `profiles/orders-api-prod.md:36`: "Loki `{namespace="orders", app="orders", container="api"}` ... \| (verified 2026-10-20)". Also: the wave 0 log probe used `{namespace="orders"}` (`run-log.md:70`) before the label discovery at `run-log.md:127`-`:129`; the namespace came from `environment.md` and was listed in the namespace values afterwards, which the grading note allows. |
| 8 | MUST | Grading note for the Loki path | N/A | Scored under row 7. |
| 9 | MUST | Record phase: diff shown, nothing written before the reply | PASS | Diff `run-log.md:935`-`:982`; reply `:984`; writes after it (`:986`-`:991`). |
| 10 | MUST-NOT | Rule the DB out because DB p95 or ReadLatency is flat | PASS | Only "slow on its own" is ruled out, and with CPU timing; the database load is the mechanism (`R/report.md:25`, `:21`). |
| 11 | MUST-NOT | `Confirmed` from the diff alone, or fewer than 20 samples | PASS | 24 vs 24 (`R/report.md:18`). |
| 12 | MUST-NOT | 2026-08-14 incident as evidence, or `incidents/` before ranking | PASS | `run-log.md:375`-`:393`; ruled out by pool metrics (`R/report.md:26`). |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Every selector value appears in the listed values (`run-log.md:128`-`:129`). |
| 14 | MUST-NOT | Write under the output root (outside `runs/`) before the reply | PASS | `run-log.md:984`-`:991`. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | Code read by ref (`run-log.md:270`-`:273`, `:314`-`:315`); rollback in prose (`R/report.md:12`). |

Totals: 13 PASS, 1 FAIL, 1 N/A.

### Compared with the baseline

- Baseline: 7 PASS, 7 FAIL, 1 N/A. Now: 13 PASS, 1 FAIL, 1 N/A.
- Fixed: row 3 (`Confirmed` stated in the report with all three legs), row 4 (both checkpoints), row 5 (one worker per hypothesis), rows 6 and 12 (history after ranking, `from-history:` ID), row 9 (record diff, then wait). The runnable rollback the baseline listed is now prose.
- Improved but still FAIL: row 7. Label discovery and the per-backend names are new; the verified mark on the Loki stream is the open part.

### Not covered by a README line

- The ledger's first full write came after wave 3 (`run-log.md:55`), not after every wave. See P7 (text in `nightly-job-not-deploy/DRY-RUN-NOTES.md`).
- The Deep report lacks the template's Impact, Recurrence, Timeline and Evidence headings and renames "Open hypotheses" to "Open" (`R/report.md` headings at `:4`, `:16`, `:23`, `:30`, `:34`, `:47`, `:55`, `:60`). Deep mode fills every section. The report was saved from the text the run returned, so part of this may come from that hand-off. See P9 (text in `injection-in-logs/DRY-RUN-NOTES.md`).

## Findings and fixes

- **Row 7 (FAIL): "verified" means "returned data", not "belongs to this service".** `templates/profile.md` (line 7) and SKILL.md Constraint 14 promote a mark once a query returns data. A differently named log label that returns plausible lines is therefore marked verified, although nothing ties it to the service. Proposed fix P3:
  - `skills/sre-investigate/SKILL.md`, Constraint 14: append "A log label or stream whose value differs from the service's name stays `(unverified)` even after it returns data, until a query ties it to the service: a pod or host name shared with the service's pods, or a trace or request ID found in both. Lines that look like the service's traffic are a lead, not that tie."
  - `skills/sre-investigate/templates/profile.md`, the guidance line that starts "Every identifier is marked": append "A log label whose value differs from the service's name stays `(unverified)` until a query ties it to the service (shared pod or host names, or a trace or request ID present in both)."
- **Row 7 note: wave 0 probes logs before any label is discovered.** SKILL.md Phase 0 step 7 puts "one cheap log probe" in wave 0, before the profile build, so on a first run with a label-based log backend the probe has to use a selector nobody listed yet. Proposed fix P4, `skills/sre-investigate/SKILL.md`, Phase 0 step 7, replace "one cheap log probe: a stats or size estimate over the last 15 minutes for the service's log source (the only log call in wave 0);" with "one cheap log probe: a stats or size estimate over the last 15 minutes for the service's log source (the only log call in wave 0), on an identifier from the stored profile or a log group listed by prefix; on a first run against a label-based log backend, run it right after the profile build, on a discovered label value;".
