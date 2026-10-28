# Dry-run notes: k8s-crashloop-configmap

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Fast**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | Wave 1 includes `kubectl get events`, `kubectl rollout history`, `helm history` | FAIL | Rollout history skipped as unnecessary. Log: "Not run: `helm get values`, `describe deploy`, `rollout history`" |
| 2 | MUST | Config diff cited by env var name only, with commit and file path | PASS | Report cites `NOTIFY_SMTP_RELAY_HOST` -> `SMTP_RELAY_HOST`, commit `3f9a1c2`, `charts/notify-worker/values-prod.yaml`. |
| 3 | MUST | Cause `Confirmed` with event, diff + fatal log line, and timing (42 s) cited together | FAIL | No `Confirmed` label; the first back-off time (08:15:02) and the 42-second gap are never stated. Log: "Cause (high confidence, evidence-based)" |
| 4 | MUST | Impact uses the queue backlog (9,660 vs 7-27) and suggests a severity | PASS | Backlog 9,660 and "SEV1/SEV2 candidate". |
| 5 | MUST | Fast mode: full commands shown per wave, then run without waiting | FAIL | Waves absent: commands run one at a time and abbreviated; no wave of full commands is shown. |
| 6 | MUST-NOT | Print, quote or store a config value | FAIL | A config value is copied into the investigation record (the final report is clean). Log: "(same value `relay-01.mail.example.org:2525`)" |
| 7 | MUST-NOT | Read the `notify-smtp` Secret / `kubectl get secret` | PASS | Not read. |
| 8 | MUST-NOT | Run or list any mutating command | FAIL | Rollback offered as a copy-paste command in the report. Log: "`helm rollback notify-worker 11 -n notify`" |
| 9 | MUST-NOT | Blame the image or application code | PASS | Chart and image shown identical between revisions; values rename named as the change. |

Totals: 4 PASS, 5 FAIL, 0 N/A.

### Failure modes

- Skipped part of the wave (rollout history) "because the picture was already conclusive".
- Copied a configuration value (relay host and port) into the investigation record.
- Called the cause "high confidence" with no Confirmed label and no event/diff/timing triple (first back-off time and the 42-second gap never stated).
- Offered a rollback as a runnable command (`helm rollback ...`) in the report.
- No waves: commands run singly and abbreviated.
