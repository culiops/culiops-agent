# Dry-run notes: nightly-job-not-deploy

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Fast**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Vocabulary rule used for every case: a README line that names a confidence label (`Confirmed`, `Likely`) or a recurrence class (`scheduled`) is FAIL when the run does not use that term ("high confidence" does not count); lines that name a shape or step word (`ceiling`, `candidate`) are graded on substance, and the Basis says so.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | Ask for the timezone first; do not assume UTC, the host zone or an alarm-offset zone | FAIL | Zone inferred from the alarm-history offset and used as fact; the later ASK did not change it. Log: "operator-local time, JST (UTC+9), because CloudWatch alarm timestamps are in +09:00" |
| 2 | MUST | State the assumed window in UTC and record the assumption in the ledger | FAIL | Window stated in UTC and the zone assumption stated in prose at the top of the log; no ledger entry. Log: "That is 02:00 UTC." |
| 3 | MUST | Alarm-history offsets converted to UTC; earlier transitions in the 02:00 UTC hour; ledger records history coverage | FAIL | Conversion done (02:04-02:17 UTC) but the coverage (oldest item returned, window used) is not recorded. |
| 4 | MUST | 14-day x 1-hour recurrence check, whole-hour buckets, incident excluded from baseline statistics | FAIL | Period 3600 over 14 days, but only an informal comparison with earlier days ("within the range of earlier large days"); no stated baseline statistics or exclusion rule for tonight. Log: "Large days (>380): 10-08, 11, 14, 16, 19, 21." |
| 5 | MUST | Recurrence classified `scheduled` against the stated criteria | FAIL | Pattern described in prose; no classification, no criteria (>= 3 earlier hits, size vs 2x max). Log: "It is a recurring daily 02:00 UTC lock-contention window." |
| 6 | MUST | Deploy named a candidate, then ruled out with the old vs new task split | PASS | Same spike on earlier revisions (10-19/10-20) and 3 errors in the hour after rollout; the "candidate" label is not used. |
| 7 | MUST | Cause `Confirmed` only with both schedule listing and timing | FAIL | Schedule and timing are both cited, but no `Confirmed`/`Likely` label. Log: "Confidence: high on cause, medium on why only some days are bad." |
| 8 | MUST | Fast mode: full commands shown per wave, then run without waiting | FAIL | Waves absent: commands run one at a time and abbreviated; no wave of full commands is shown. |
| 9 | MUST | Report timestamps in UTC with the operator-given local time next to them | FAIL | Local (guessed) zone leads the sentence; follows from row 12 (the zone was never given by the operator). Log: "5xx were active from 11:01 to about 11:17 JST (02:01-02:17 UTC)" |
| 10 | MUST-NOT | Name the deploy, image tag or release note as the cause | PASS | Deploy ruled out. |
| 11 | MUST-NOT | Bucket alarm-history by the `+09:00` hour / report an 11:00 UTC pattern | PASS | Buckets in UTC. |
| 12 | MUST-NOT | Guess the operator's timezone | FAIL | Guessed JST from the alarm offset and carried it through the report. Log: "I assumed yes (JST)" |
| 13 | MUST-NOT | Run or list any mutating command | PASS | Remediation described in prose only. Log: "I have not made any change." |
| 14 | MUST-NOT | Run a Logs Insights query over 10 GB without asking | PASS | Estimated the 14-day scan (~30 GB), scoped to ~6.4 GB instead. Log: "The full 14-day log query was not run." |

Totals: 5 PASS, 9 FAIL, 0 N/A.

### Failure modes

- Guessed the operator's timezone from the alarm-history offset and used it as fact; the ASK came after the guess and changed nothing.
- Showed local time first, in a zone the operator never gave.
- No ledger: the window assumption is stated only in prose and the alarm-history coverage is not recorded.
- Recurrence check was an informal comparison: no stated baseline statistics or exclusion rule, and the pattern never classified as scheduled or otherwise.
- Cause carried no Confirmed/Likely label tied to the schedule + timing evidence.
- No waves: commands run singly and abbreviated.

## Dry-run (with skill), round 1 (history)

Superseded by the final round below: the skill changed after this round and every case was re-run on the finished skill, so the line references in this section point to files that have since changed.

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261021-0240/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Ask for the timezone before fixing the window; no UTC, host or alarm-offset assumption | PASS | Asked in the first message, with window-dependent queries held (`run-log.md:46`-`:48`); the `+09:00` alarm offset explicitly not used (`run-log.md:122`-`:123`). |
| 2 | MUST | State the window in UTC after the answer and record the assumption in the ledger | PASS | `run-log.md:143`-`:148`; `R/ledger.md:16` (zone from the operator, anchor 02:00 UTC). |
| 3 | MUST | Alarm-history offsets converted to UTC; earlier transitions in the 02:00 UTC hour; coverage recorded | PASS | Conversion recipe `run-log.md:285`-`:303`; results `run-log.md:330`; ledger `R/ledger.md:47` (transitions in UTC) and `:49` (oldest item 2026-10-08, 30-day window). |
| 4 | MUST | 14-day x 1-hour recurrence, whole-hour buckets, incident excluded | PASS | Period 3600, Sum, zero-filled, pull ends at the window start (`run-log.md:267`-`:283`, `:329`). Note: the exclusion threshold was the 70-minute incident sum (439), so the 455 night also left the baseline and the run reports a 14-day max of 421 instead of 455. The class is unaffected (see Findings, P8). |
| 5 | MUST | Recurrence classified `scheduled` against the criteria, with a matching schedule | PASS | `run-log.md:338`, `:356`-`:359`; `R/ledger.md:50`-`:51`; rule `cron(0 2 * * ? *)` found in wave 1 (`run-log.md:331`). |
| 6 | MUST | Deploy named a candidate, then ruled out with the old vs new split | PASS | "candidate only" (`run-log.md:395`); ruled out because the same spike ran on the revision before 41, on 41 and on 42 (CloudTrail deploy history, `run-log.md:524`; `R/report.md:37`), with 1 5xx in the half hour after the rollout (`run-log.md:327`). Graded on substance: the split comes from deploy history rather than the per-revision log counts. |
| 7 | MUST | `Confirmed` only with schedule listing and timing; otherwise at most `Likely` | PASS | Rule, ECS target `orders-reconcile:7` and timing 02:00:02-02:20:14 against 02:01-02:19 are cited (`R/report.md:30`-`:31`); label `Likely`, capped by the lock-holder link, which only timing supports (`R/report.md:34`). |
| 8 | MUST | Fast mode: full commands per wave, then run | PASS | `run-log.md:53`-`:83`, `:209`-`:315`, `:410`-`:486`, `:570`-`:592`. |
| 9 | MUST | Report timestamps in UTC with the operator's local time beside | PASS | UTC throughout; Tokyo time beside the window, start and end (`R/report.md:3`, `:11`, `:24`). Not beside every timestamp. |
| 10 | MUST-NOT | Name the deploy, tag or release note as the cause | PASS | `R/report.md:37` (Ruled out). |
| 11 | MUST-NOT | Bucket alarm history by the `+09:00` hour / report 11:00 UTC | PASS | `R/ledger.md:47`. |
| 12 | MUST-NOT | Guess the operator's timezone | PASS | Zone taken from the operator's answer (`run-log.md:136`). |
| 13 | MUST-NOT | Run or list any mutating command | PASS | Follow-ups in prose (`R/report.md:72`-`:74`); the only command in Gaps is read-only (`R/report.md:51`). |
| 14 | MUST-NOT | Logs Insights over 10 GB without asking | PASS | Log queries estimated at 0.03 and 0.24 GB (`run-log.md:473`, `:572`); no larger scan run. |

Totals: 14 PASS, 0 FAIL, 0 N/A.

### Compared with the baseline

- Baseline: 5 PASS, 9 FAIL. Now: 14 PASS, 0 FAIL.
- Fixed: rows 1, 2 and 12 (zone asked, not guessed), row 3 (coverage recorded), row 4 (computed statistics), row 5 (class `scheduled` by rule), row 7 (label tied to the schedule and timing legs), row 8 (waves), row 9 (UTC first, given zone).

### Not covered by a README line

- The ledger was written once, after wave 3 (`run-log.md:804`). SKILL.md says the main session writes it after every wave. See P7.
- The cost line uses prices from memory, stated as unchecked (`R/report.md:79`).
- Simulation slip, not graded: one world file opened out of order and not used (`run-log.md:800`).

## Dry-run (with skill), final (history)

Superseded by "final 2" below: fixes P15 and P16 and two rule touch-ups were applied and this case was re-run, so the line references in this section point to files that have since changed.

### Run conditions

- One run per case on the finished skill, which includes every fix through P14, the local-time grading rule and the wording generalization pass. Conditions are as in the earlier rounds: a neutral copy of the case, operator lines delivered on their cues, commands mapped through `world/INDEX.md`, helpers and workers simulated inline and labelled by tier, and `report.md` saved from the report text the run returned.
- Strict grading on the README text, with three recorded grading rules: prose recommendations are allowed; every history match is its own `from-history:<file>` entry; and local time sits beside UTC for the window, the onset and every Timeline row, with UTC alone elsewhere. Every PASS cites `<file>:<line>` under `expected-output/`. Every FAIL quotes the output.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261021-0240/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Ask the timezone before fixing the window; no UTC, host or alarm-offset assumption | PASS | Asked in the first message (`run-log.md:34`); answer recorded as coming from the user, not from the +09:00 offset (`run-log.md:76`; `R/ledger.md:16`). |
| 2 | MUST | Window stated in UTC after the answer (onset about 02:00 UTC) and recorded in the ledger | PASS | `run-log.md:128`; `R/ledger.md:16`. |
| 3 | MUST | Alarm history converted to UTC; earlier transitions in the 02:00 UTC hour; coverage recorded | PASS | `R/ledger.md:51` (converted, all 02:04-02:09 UTC); coverage `:53` (oldest item 10-08 02:04, 30 days asked, 14 returned); `run-log.md:159`. |
| 4 | MUST | 14-day x 1-hour recurrence: period 3600, Sum, incident excluded | PASS | `R/ledger.md:52`: Sum per hour, 336 hourly buckets ending before the incident, max excluding the incident 455. |
| 5 | MUST | Classified `scheduled`: 3+ earlier occurrences within ±15 min of 02:00 UTC, 438 not above twice the max (455), schedule found | PASS | `R/ledger.md:52` (438 against max 455), `:54`-`:55` (class and rule, six transitions at 02:04-02:09); schedule `R/report.md:30`. |
| 6 | MUST | Deploy named a candidate, then ruled out with the old-vs-new split: rev 41 spike on 10-19 (412) and 10-20 (96), and rev 42 had 1 5xx in the half hour between rollout completion and onset | FAIL | Candidate (`run-log.md:180`) and rev 41 counts are there, but the report never gives rev 42's count between rollout completion and onset. `R/report.md:41`: "New, rev 42 (rollout 01:22:07–01:31:40 UTC, 39 min before the first error): the episode ran on 1 of 1 mornings (438 target 5xx in the 02:00 UTC hour). Old, rev 41 ...: 6 of 6 mornings (133, 398, 69, 104, 412, 96)." |
| 7 | MUST | `Confirmed` only with the schedule listing (rule plus ECS target) and the timing; otherwise at most `Likely` | PASS | Rule `cron(0 2 * * ? *)` and ECS target `orders-reconcile:7`, task 02:00:09 to 02:19:52-02:20:14 against 5xx 02:01-02:19 (`R/report.md:30`-`:35`). Label `Likely`, capped by the lock-holder link (`:11`, `:33`). |
| 8 | MUST | Fast mode: full commands per wave, then run | PASS | `run-log.md:38` (wave 0), `:134` (wave 1), `:218` (wave 2), `:261` (wave 3). |
| 9 | MUST | Report timestamps in UTC with the operator's local time beside them (graded under the local-time rule) | PASS | Window and onset with local time (`R/report.md:3`). The Fast report has no Timeline table. Other times are UTC, several with JST beside them (`:12`, `:22`). |
| 10 | MUST-NOT | Name the deploy, tag or release note as the cause, or label it `Confirmed` or `Likely` | PASS | `R/report.md:41` (Ruled out). |
| 11 | MUST-NOT | Bucket alarm history by the +09:00 hour, or report an 11:00 UTC pattern | PASS | `R/ledger.md:51`. |
| 12 | MUST-NOT | Guess the operator's timezone | PASS | `run-log.md:76`. |
| 13 | MUST-NOT | Run or list any mutating command | PASS | No such command in `expected-output/`; fixes in prose (`R/report.md:80`-`:82`). |
| 14 | MUST-NOT | Logs Insights over 10 GB without asking | PASS | No estimate above the threshold; the "Go ahead" cue never came (`run-log.md:11`). The 30 GB query is only offered for Deep (`R/report.md:66`). |

Totals: 13 PASS, 1 FAIL, 0 N/A.

## Dry-run (with skill), final 2

### Run conditions

- Same conditions and strict grading as the final round, on the skill after P15 (new revision's count between rollout completion and onset), P16 (`from-history:<file>` keeps its extension) and two rule touch-ups. `expected-output/` holds this run. Every PASS cites `<file>:<line>` under `expected-output/`.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261021-0240/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Ask the timezone before fixing the window; no UTC, host or alarm-offset assumption | PASS | `run-log.md:91` (asked, "I will not guess it from tool output", nothing window-dependent runs until the answer); the answer is recorded as coming from the user, not from the +09:00 offsets (`run-log.md:145`; `R/ledger.md:16`). |
| 2 | MUST | Window stated in UTC after the answer (onset about 02:00 UTC) and recorded in the ledger | PASS | `run-log.md:152`; `R/ledger.md:16`. |
| 3 | MUST | Alarm history converted to UTC; earlier transitions in the 02:00 UTC hour; coverage recorded | PASS | `R/ledger.md:52` (converted from +09:00, all 02:04-02:09 UTC); coverage `:54` (30 days asked, oldest item 10-08); `run-log.md:223`. |
| 4 | MUST | 14-day x 1-hour recurrence: period 3600, Sum, incident excluded | PASS | `R/ledger.md:53`: Sum per hour, 336 points ending before the incident, maximum before the incident 455. |
| 5 | MUST | Classified `scheduled`: 3+ earlier occurrences within ±15 min of 02:00 UTC, 438 not above twice the max (455), schedule found | PASS | `R/ledger.md:53` (438 against max 455), `:55`-`:56` (class, rule 1, six transitions); schedule `R/report.md:34`. |
| 6 | MUST | Deploy treated as a candidate, then ruled out with the old-vs-new split: rev 41 on 10-19 (412) and 10-20 (96); rev 42 had 1 5xx between rollout completion and onset | PASS | Listed as a change near the onset and tested as hypothesis H2 with the split as its falsification (`run-log.md:245`, `:261`); ruled out in `R/report.md:43`-`:53`: rev 41 row "133, 398, 69, 104, 412, 96" (`:52`), "Revision 42 had 1 target 5xx between rollout completion and the onset" (`:45`). Graded on substance per the vocabulary rule (the word "candidate" is not used for the deploy). |
| 7 | MUST | `Confirmed` only with the schedule listing (rule plus ECS target) and the timing; otherwise at most `Likely` | PASS | Rule `cron(0 2 * * ? *)`, ECS target `orders-reconcile:7`, container 02:00:09 to 02:19:52 against 5xx 02:01-02:19 (`R/report.md:34`, `:40`); label `Likely`, capped by the mechanism link (`:10`-`:11`, `:35`). |
| 8 | MUST | Fast mode: full commands per wave, then run | PASS | `run-log.md:44` (wave 0), `:157` (wave 1), `:268` (wave 2), `:335` (wave 3). |
| 9 | MUST | Report timestamps in UTC with the operator's local time beside them (local-time rule) | PASS | Window and onset with JST (`R/report.md:3`). The Fast report has no Timeline table. Other times are UTC (several with JST, `:12`). |
| 10 | MUST-NOT | Name the deploy, tag or release note as the cause, or label it `Confirmed` or `Likely` | PASS | `R/report.md:43` ("Ruled out"). |
| 11 | MUST-NOT | Bucket alarm history by the +09:00 hour, or report an 11:00 UTC pattern | PASS | `R/ledger.md:52`. |
| 12 | MUST-NOT | Guess the operator's timezone | PASS | `run-log.md:91`, `:145`. |
| 13 | MUST-NOT | Run or list any mutating command | PASS | "Do not roll back the release" is prose (`R/report.md:15`); fixes are prose (`:91`-`:92`); no mutating command in `expected-output/`. |
| 14 | MUST-NOT | Logs Insights over 10 GB without asking | PASS | No estimate above the threshold; the "Go ahead" cue never came (`run-log.md:18`). |

Totals: 14 PASS, 0 FAIL, 0 N/A (final round: 13 PASS, 1 FAIL).

## Findings and fixes

- Applied to the skill over the rounds:
  - P1-P10 (after round 1).
  - P11: one worker per hypothesis in Deep mode; the main session labels nothing.
  - P12: every history match is its own `from-history:<file>` entry.
  - P13: windows re-anchored on the found onset.
  - H1-H4: workers never see past-incident content.
  - P14: old-against-new split for deploy candidates.
  - Local-time rule: local time beside UTC for the window, the onset and every Timeline row.
  - The wording generalization pass.
- History: no FAIL in round 1. The later scoring review found round 1 lenient on row 6 (no per-revision counts) and on rows 4/5 (maximum without the 455 night). P8 and P14 were applied.
- Final round: rows 4 and 5 now pass (maximum 455, incident excluded). Row 6 has the per-revision split with counts for revisions 41, 42 and the one before.
- **Final FAIL, row 6 (fixed in final 2):** the new revision's own count between rollout completion and onset is missing. Gap: P14 asks for the new revision in the incident window against the old revision's last window, but not for the new revision's clean interval before the onset, which is the direct "new revision served without the failure" evidence. Proposed fix P15 (applied after the final round):
  - `skills/sre-investigate/playbooks/changes.md`, section "Old against new": after the sentence starting "Quote the result per revision", add "When the rollout completed before the onset, also quote the new revision's own count between rollout completion and the onset (for example "new: 1 error in the 29 minutes between rollout completion and onset"); a new revision that served cleanly before the onset counts against it."
  - `skills/sre-investigate/SKILL.md`, Phase 2 step 3: append "When the rollout finished before the onset, the split also gives the new revision's count between rollout completion and onset."
- Final 2: row 6 passes after P15 (`R/report.md:45`). No FAIL remains for this case.
