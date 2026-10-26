# Dry-run of `pre-flight` against `app-impact-iam-narrowing`

Simulated runs on 2026-10-26: the operator from `operator-script.md`, live results from `live-responses.md`, and the app as a separate local checkout (Mode A), committed and tagged `v2.4.0`.

## Baseline (skill before category 11)

| Layout | Runs | Verdict | Asked for the app source | Cited the app / knew the failure is silent |
|---|---|---|---|---|
| App inside the IaC repo | 2 | RED | not needed (read it unprompted) | yes / yes |
| App in a separate repo | 2 | RED | no | no / no. App behaviour recorded as `UNVERIFIED` |

With a separate repo, the verdict came only from the live send metric (`NumberOfMessagesSent`). Nobody knew the app logs the failure and returns 201, and the removal was scored under blast radius or reversibility, not as an app break.

## With category 11

| Principle | Exercised by |
|---|---|
| Trigger | A removed IAM statement is an app-contract change, so Q8 is asked |
| Mode A, pinned version | `git rev-parse HEAD` → `37df8d8`, `git status --porcelain` clean, `git describe` → `v2.4.0`. The live image tag was not returned, so the record says "deployed version unverified" |
| Search | `SendMessage`, `LEDGER_QUEUE_URL`, `Getenv`, `/healthz` in the checkout |
| Silent breakage | `main.go:48-51` logs `WARN … (non-fatal)` and returns 201. `/healthz` is a static 200. So health, 5xx and alarms stay green after apply |
| Security vs breakage | Category 9 is Green (a narrowing). Category 11 is Red. The two are scored separately |
| Live evidence for category 11 | `live:13` IAM last-accessed shows `sqs` today. `live:15` shows about 1,150 sends a day |

## Scoring

| # | Category | Score | Signal |
|---|---|---|---|
| 1 | Blast radius | 🟢 | 1 in-place change, one role, one region (`plan:11-45`) |
| 2 | Reversibility | 🟡 | Policy rollback is minutes. Ledger entries lost meanwhile are not restored (`app:…/main.go:48-51`) |
| 3 | Change velocity | 🟢 | No other commits in 7 days (fixture condition) |
| 4 | Dependency impact | 🟡 | Ledger feeds finance reconciliation (`app:…/main.go:49`). No catalog |
| 5 | Timing context | 🟢 | `operator` Q1, Q2; `operator-stated` Q3 |
| 6 | Operator familiarity | 🟡 | "A few times" |
| 7 | Observability readiness | 🔴 | No alarms in the IaC; alarm existence unverified live |
| 8 | Cost impact | 🟢 | No new resources |
| 9 | Security posture | 🟢 | Narrowing, explicit ARN (`plan:28-37`) |
| 10 | Resource health | 🟢 | `live:3,7,8,9`. Does not clear category 11 |
| 11 | Application compatibility | 🔴 | `app:cartapi-app@37df8d8:cmd/cartapi/main.go:65` still calls `SendMessage`. Silent failure at `:48-51` |

Record header: plan hash `sha256:796bd22a582a4375ea5f05170aa88fb5c0bbb01b1b05d3f4f9ace8d0e303b3b9`, target `111122223333` / `eu-west-1`, App source `local cartapi-app @ 37df8d8 (v2.4.0)`.

**Verdict: RED — SOFT BLOCK** (categories 11 and 7 are Red; 3 Yellow).

## Mitigations the skill should recommend

- Keep the statement. It is already one action on one queue ARN, so the security review's goal is already met.
- If the ledger is being retired: first ship the app change that stops sending, then verify that `NumberOfMessagesSent` stays at 0 for at least 30 days, and only then remove the permission.
- Add detection before any narrowing on this path: a metric filter and alarm on `ledger send failed`, plus an alarm on sends dropping to 0.
