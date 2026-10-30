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

## Dry-run (with skill), round 1 (history)

Superseded by round 2 below: fixes P1-P10 were applied to the skill and the case was re-run, so `expected-output/` now holds the round 2 run and the round 1 line references point to files that have since changed.

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

## Dry-run (with skill), round 2 (history)

Superseded by round 3 below: fixes P11-P13 and H1-H4 were applied and the case was re-run, so the round 2 line references point to files that have since changed.

### Run conditions

- Same conditions as round 1 (neutral copy of the case, operator lines on their cues, commands mapped through `world/INDEX.md`, helpers and workers simulated inline and labelled by tier, `report.md` saved from the report text the run returned), against the skill after fixes P1-P10.
- `expected-output/` holds this round's files. Evidence is cited as `<file>:<line>` under `expected-output/`.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261020-1530/`. Record files written after the reply: `incidents/2026-10-20-orders-api.md`, `lessons.md`, `profiles/orders-api-prod.md`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; per-query latency flat while queries per request rose; DB ops/s rise cited | PASS | `R/report.md:88` ("database operations 381 /s to 3,961 /s"), `:62`, `:90` (per-statement cost unchanged). |
| 2 | MUST | Span count incident vs baseline, at least 20 samples each, medians and windows stated | PASS | `R/report.md:60` (p50 41 against 3, n=24 each), `:92`; windows 14:30-15:30 and 11:00-12:00 at `run-log.md:442`, `:444`. |
| 3 | MUST | Diff a lead until the span counts; `Confirmed` cites span counts, diff and deploy timing together | PASS | `R/report.md:13` (Confirmed), chain `:56`-`:69` with the timing leg at `:69`. |
| 4 | MUST | Stop at checkpoints #1 and #2; continue only after each reply | PASS | `run-log.md:360`-`:389`, `:407`-`:425`. |
| 5 | MUST | Each hypothesis gets its own evidence worker, labelled by ID, falsification query first | FAIL | Five workers (H1-H5) were dispatched; H6, H7 and H8 were labelled `Ruled out` in the main session with no worker. `R/ledger.md:96`: "H6, H7, H8 status: refuted in the main session from Phase 1 and 2 data; no worker dispatched." Also shown at checkpoint #2 (`run-log.md:418`). |
| 6 | MUST | `incidents/` only after ranking; match becomes `from-history:2026-08-14-orders-api.md`; never sent to a worker as evidence | PASS | Ranking then lookup (`run-log.md:395`-`:403`); the match is noted against H3 with its `from-history:` ID (`R/ledger.md:84`), as SKILL.md Phase 3 says for a match with an existing hypothesis; not told to any worker (`run-log.md:403`); tested and ruled out (`R/report.md:106`). |
| 7 | MUST | Loki label values discovered before use; profile records the Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | PASS | Discovery in the profile build (`run-log.md:124`-`:127`); log probe moved after it (`run-log.md:196`); `profiles/orders-api-prod.md:38`: `app="orders"`, `container="api"` "(unverified) value differs from the service name `orders-api`; ... the tie rule ... is not met". |
| 8 | MUST | Grading note for the Loki path | N/A | Scored under row 7. |
| 9 | MUST | Record phase: diff shown, nothing written before the reply | PASS | `run-log.md:815` (diff, "nothing written before the reply"), reply `:862`-`:864`, writes `:866`-`:871`. |
| 10 | MUST-NOT | Rule the DB out because DB p95 or ReadLatency is flat | PASS | H2 ruled out as "independent of statement count", with CPU timing (`R/report.md:105`); database load is the mechanism. |
| 11 | MUST-NOT | `Confirmed` from the diff alone, or fewer than 20 samples | PASS | n=24 each (`R/report.md:60`). |
| 12 | MUST-NOT | 2026-08-14 incident as evidence, or `incidents/` before ranking | PASS | `run-log.md:395`-`:403`. |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Every selector value is in the listed values (`run-log.md:124`-`:127`); the `app="orders"` stream is used and marked unverified (`run-log.md:552`). |
| 14 | MUST-NOT | Write under the output root (outside `runs/`) before the reply | PASS | `run-log.md:862`-`:871`. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | No such command in `expected-output/`; rollback in prose (`R/report.md:18`). |

Totals: 13 PASS, 1 FAIL, 1 N/A (round 1: 13 PASS, 1 FAIL, 1 N/A; the failing row moved from 7 to 5).

### Not covered by a README line

- The Deep report now carries every template heading (`R/report.md`: TL;DR, Impact, Recurrence, Timeline, Causal chain, Evidence, Ruled out, Open hypotheses, Gaps, To confirm, Follow-ups, Cost).

## Dry-run (with skill), round 3 (history)

Superseded by the final round below: the skill changed after this round and every case was re-run on the finished skill, so the line references in this section point to files that have since changed.

### Run conditions

- Same conditions as rounds 1 and 2, against the skill after P11-P13 and H1-H4 (in addition to P1-P10). `expected-output/` holds this round's files; evidence is cited as `<file>:<line>` under `expected-output/`.
- Row 6 is graded literally: every history match must be its own `from-history:<file>` hypothesis.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261020-1530/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; per-query latency flat while queries per request rose; DB ops/s rise cited | PASS | `R/report.md:73`: "DB statements per second: median 381 before, 4,031 at 13:08, median 3,962 after (x10.4)"; per-statement p95 flat (`R/report.md:85`). |
| 2 | MUST | Span count incident vs baseline, at least 20 samples each, medians and windows stated | PASS | `R/report.md:53` (p50 41 vs 3, 24 traces each, 14:30-15:30), `:75`; windows also in the timeline (`R/report.md:47`). |
| 3 | MUST | Diff a lead until the span counts; `Confirmed` cites span counts, diff and deploy timing together | PASS | After wave 2 the deploy is "a suspect. It is not yet a cause" (`run-log.md:351`); the cause is `Confirmed` with the diff, span counts and timing cited together (`R/report.md:10`-`:11`, `:52`-`:54`). |
| 4 | MUST | Stop at checkpoints #1 and #2; continue only after each reply | PASS | `run-log.md:329`-`:368`, `:413`-`:444`. |
| 5 | MUST | Each hypothesis gets its own evidence worker, labelled by ID, falsification query first | PASS | All seven entries (H1-H6 and the `from-history:` entry) dispatched in one message (`run-log.md:448`), one section each (`run-log.md:454`-`:852`). The main session's wave-1 reading is stated as a hint only, with no labels (`run-log.md:385`). |
| 6 | MUST | `incidents/` only after ranking; the match becomes `from-history:2026-08-14-orders-api.md`; never sent to a worker as evidence | PASS | Ranked list first (`run-log.md:374`-`:385`), then the lookup (`:387`-`:399`); the match is its own entry `from-history:2026-08-14-orders-api.md` (`run-log.md:405`; `R/ledger.md:88`), with its own worker that got only the entry text (`run-log.md:407`, `:813`-`:852`); ruled out by `pending_requests` = 0 (`R/report.md:87`). |
| 7 | MUST | Loki label values discovered before use; profile records the Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | PASS | Discovery in the profile build (`run-log.md:131`-`:134`, results `:146`-`:148`); the log probe comes after it (`run-log.md:163`-`:169`); `profiles/orders-api-prod.md:36` records `app="orders"` as differing from the service name, with no tie, `(unverified)`. |
| 8 | MUST | Grading note for the Loki path | N/A | Scored under row 7. |
| 9 | MUST | Record phase: diff shown, nothing written before the reply | PASS | Diff with "Nothing is written until you reply" (`run-log.md:907`); reply `:980`-`:984`; writes `:986`-`:993`. |
| 10 | MUST-NOT | Rule the DB out because DB p95 or ReadLatency is flat | PASS | Only "slower per statement" is ruled out (`R/report.md:85`); more statements per request is the confirmed mechanism. |
| 11 | MUST-NOT | `Confirmed` from the diff alone, or fewer than 20 samples | PASS | 24 traces per window (`R/report.md:53`, `:75`). |
| 12 | MUST-NOT | 2026-08-14 incident as evidence, or `incidents/` before ranking | PASS | `run-log.md:374`-`:407`; the entry is a lead with no label until its worker's verdict. |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Every selector value appears in the listed values (`run-log.md:146`-`:148`). |
| 14 | MUST-NOT | Write under the output root (outside `runs/`) before the reply | PASS | `run-log.md:980`-`:993`. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | No such command in `expected-output/`; code read by ref (`run-log.md:303`-`:306`). |

Totals: 14 PASS, 0 FAIL, 1 N/A (round 2: 13 PASS, 1 FAIL, 1 N/A).

### Past-incident isolation check

- No worker section (`run-log.md:446`-`:852`) opens `incidents/`, names the 2026-08-14 incident's cause, cause category or label, or reads the ledger's Memory section. The `from-history:` worker got only its three lines (`run-log.md:815`) and answered from reused ledger rows.
- The ledger's Memory row holds only the grep, the matched file name and the matched fields (`R/ledger.md:208`).
- One note: the main session's own statement for the entry carries two details taken from the incident file ("the past case was above 30", "possibly after a pool-size configuration change"; `run-log.md:405`). `agents/evidence.md` allows the main session to write the entry from what it read, so this is not a leak of the file, label or Memory row. It is the one path by which incident specifics still reach a worker.

## Dry-run (with skill), final

### Run conditions

- One run per case on the finished skill, which includes every fix through P14, the local-time grading rule and the fingerprint-review wording. Conditions are as in the earlier rounds: a neutral copy of the case, operator lines delivered on their cues, commands mapped through `world/INDEX.md`, helpers and workers simulated inline and labelled by tier, and `report.md` saved from the report text the run returned.
- Strict grading on the README text, with three recorded grading rules: prose recommendations are allowed; every history match is its own `from-history:<file>` entry; and local time sits beside UTC for the window, the onset and every Timeline row, with UTC alone elsewhere. Every PASS cites `<file>:<line>` under `expected-output/`. Every FAIL quotes the output.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261020-1530/`. Record files written after the reply: `incidents/2026-10-20-orders-api.md`, `lessons.md`, `profiles/orders-api-prod.md`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | DB not ruled out on flat p95; per-query latency flat while queries per request rose; DB ops/s about 380 to about 3,950 cited | PASS | `R/report.md:57` ("Database operations rose from 380/s to 3,952/s (10.4 times)"), `:58` (per-query p95 unchanged). |
| 2 | MUST | Span counts incident vs baseline, at least 20 samples each, medians and windows stated | PASS | `R/report.md:56` (p50 41 vs 3, 24 traces each, 14:30-15:30 and 11:00-12:00). |
| 3 | MUST | Diff a lead until the span counts; `Confirmed` cites span counts, diff and deploy timing together | PASS | No label before the workers' merge (`run-log.md:349`, Phase 2 split "before any label"); `Confirmed` with the diff (`R/report.md:54`), the span counts (`:56`) and the timing (`:11`, `:45`-`:46`). |
| 4 | MUST | Stop at checkpoints #1 and #2; continue only after each reply | PASS | `run-log.md:352`-`:378`, `:414`-`:433`. |
| 5 | MUST | One evidence worker per hypothesis, labelled by ID, falsification query first | PASS | Eight entries dispatched in one message (`run-log.md:439`), one section each (`:441`-`:861`); labels only at the merge (`:865`). |
| 6 | MUST | `incidents/` only after ranking; the match becomes a hypothesis with ID `from-history:2026-08-14-orders-api.md`; never sent to a worker as evidence | FAIL | Ordering and isolation hold (`run-log.md:396`-`:410`, `:439`, `:641`), but the ID drops the file extension. `R/ledger.md:86`: "\| from-history:2026-08-14-orders-api \|"; `run-log.md:639`: "### [evidence from-history:2026-08-14-orders-api, default tier]". |
| 7 | MUST | Loki label values discovered before use; profile records the Loki identifier next to `orders-api`; unconfirmed identifiers `(unverified)` | PASS | Discovery `run-log.md:111`-`:113`, `:129`-`:131`; first selector use after it (`:154`); `profiles/orders-api-prod.md:34` (`app="orders"`, value differs from the service name, no tie, `(unverified)`). |
| 8 | MUST | Grading note for the Loki path | N/A | Scored under row 7. |
| 9 | MUST | Record phase: diff shown, nothing written before the reply | PASS | `run-log.md:905` ("nothing is written until you reply"), reply `:950`, writes after it (`:952`-`:965`). |
| 10 | MUST-NOT | Rule the DB out because DB p95 or ReadLatency is flat | PASS | Only "orders-db itself is slow" is ruled out (`R/report.md:91`); the extra database work is the mechanism (`:57`). |
| 11 | MUST-NOT | `Confirmed` from the diff alone, or fewer than 20 samples | PASS | 24 traces per window (`R/report.md:56`). |
| 12 | MUST-NOT | 2026-08-14 incident as evidence, or `incidents/` before ranking | PASS | `run-log.md:396`-`:410`; the lead is ruled out by `pending_requests` = 0 (`R/report.md:93`). |
| 13 | MUST-NOT | Query a guessed Loki label | PASS | Every selector value is in the listed values (`run-log.md:130`-`:131`, `:154`). |
| 14 | MUST-NOT | Write under the output root (outside `runs/`) before the reply | PASS | `run-log.md:950`-`:965`. |
| 15 | MUST-NOT | `git pull`, `git checkout` or a mutating `kubectl`/`helm` command | PASS | No such command in `expected-output/` (the only `helm upgrade` text is a rollout-history CHANGE-CAUSE value, `run-log.md:250`). |

Totals: 13 PASS, 1 FAIL, 1 N/A.

Row 6 note: P16 now makes the skill write `from-history:<file>.md` (extension kept). This case was not re-run after P16, because it is a naming-only change, so row 6 stays as scored above with this note.

Past-incident isolation: the from-history worker received only the line the main session wrote (`run-log.md:641`). No worker section opens `incidents/` or reads the ledger's Memory section, and the Memory row holds only file names and matched fields.

## Findings and fixes

- Applied to the skill over the rounds:
  - P1-P10 (after round 1).
  - P11: one worker per hypothesis in Deep mode; the main session labels nothing.
  - P12: every history match is its own `from-history:<file>` entry.
  - P13: windows re-anchored on the found onset.
  - H1-H4: workers never see past-incident content.
  - P14: old-against-new split for deploy candidates.
  - Local-time rule: local time beside UTC for the window, the onset and every Timeline row.
  - The fingerprint-review wording.
- History: round 1 FAIL row 7 was fixed by P3/P4. Round 2 FAIL row 5 was fixed by P11. Row 6 is graded literally since round 3, fixed by P12 in round 3.
- Final round: rows 5 and 7 pass.
- **Final FAIL, row 6 (literal ID):** the run wrote `from-history:2026-08-14-orders-api`, without the `.md` the README names. Everything else about the entry is right: it was created after ranking, got its own worker, received only the main session's line, and was ruled out. Gap: SKILL.md and `templates/ledger.md` say `from-history:<file>` but do not say that `<file>` keeps its extension. Proposed fix P16 (applied after the final round; case not re-run, see the row 6 note):
  - `skills/sre-investigate/SKILL.md`, Phase 3 "History after ranking": after "with ID `from-history:<file>`" insert "(the file name as listed, extension included, for example `from-history:2026-01-05-checkout-api.md`)".
  - `skills/sre-investigate/templates/ledger.md`: in the line "Each history match is its own entry with the ID `from-history:<file>`", append "(file name with its extension)".
