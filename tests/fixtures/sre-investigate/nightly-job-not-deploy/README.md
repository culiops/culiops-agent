# nightly-job-not-deploy

Mode: **Fast**. Fixture "now": **2026-10-21T02:40:00Z** (11:40 in the operator's zone, which `environment.md` does not record).

## Scenario

The CloudWatch alarm `orders-api-5xx-high` (ALB target 5xx for `orders-api`, ECS Fargate, `us-east-1`) paged this morning. The operator reports it in local time ("since around 11 this morning") and points at a release that went out shortly before. A deploy did happen 40 minutes before onset, but the same alarm fired at about 02:00 UTC on 5 of the last 14 days, driven by a nightly EventBridge-scheduled ECS task (`orders-reconcile`) that holds row locks on the orders table. Tonight's errors match the earlier nights in time, size and error code.

## What's modelled

| Fact | Value | World file |
|---|---|---|
| Onset (UTC) | first 5xx 02:01, ALARM 02:04:00, OK 02:12:00 | `cw-5xx-incident-1m.json`, `alarm-history.json` |
| Incident size | 438 ALB 5xx in the 02:00 UTC hour | `cw-5xx-14d-1h.json` |
| Deploy | `UpdateService` to `orders-api:42` at 01:22:07, rollout `COMPLETED` 01:31:40 | `ecs-describe-services.json`, `cloudtrail-lookup-ecs.json` |
| What the deploy changed | image tag only; env var names unchanged; notes touch email, an HTTP client bump, admin pagination | `ecs-taskdef-41.json`, `ecs-taskdef-42.json`, `gh-release-notes.txt` |
| Prior ALARM transitions (UTC) | 2026-10-08 02:04, 10-11 02:04, 10-14 02:09, 10-16 02:05, 10-19 02:04 | `alarm-history.json` (rendered as 11:04/11:09/11:05 `+09:00`) |
| 02:00-hour 5xx, 14 nights before tonight | 52–455 every night; max 455 (2026-10-14); median 110.5 | `cw-5xx-14d-1h.json` |
| Other hours | 0–4 per hour, one unrelated daytime hour of 31 (2026-10-15 14:00) | `cw-5xx-14d-1h.json` |
| Schedule | rule `orders-reconcile-nightly`, `cron(0 2 * * ? *)`, target task definition `orders-reconcile:7` on cluster `prod` | `events-list-rules.json`, `events-describe-rule-reconcile.json`, `events-targets-reconcile.json` |
| Tonight's job run | started 02:00:09.531, stopping 02:19:52, `startedBy events-rule/orders-reconcile-nightly`, exit 0 | `ecs-describe-tasks-reconcile.json`, `li-results-reconcile.json` |
| Old vs new task split (5xx per hour) | rev 41: 412 at 2026-10-19 02:00, 96 at 2026-10-20 02:00, 2 at 2026-10-21 01:00; rev 42: 1 at 2026-10-21 01:00 (01:31–02:00), 438 at 02:00 | `li-results-revision-split.json` |
| Error signature | `ER_LOCK_WAIT_TIMEOUT` 431 of 438, on `POST /orders` and `PATCH /orders/{id}` | `li-results-error-codes.json`, `li-results-raw.json` |
| Logs scan estimate | `/ecs/orders-api` 64,424,509,440 stored bytes, 30-day retention (about 2.1 GB per day); threshold 10 GB | `logs-describe-log-groups.json`, `environment.md` |
| Credentials | `prod-read` is read-only (`implicitDeny` on every simulated write); no `agentbox-env` | `iam-simulate-readonly.json`, `INDEX.md` |

`environment.md` has no timezone. The operator gives it only when asked (`operator-script.md`, line 2): Asia/Tokyo, UTC+9.

## MUST

- **Timezone (Review Focus 1).** Before fixing the incident window, the run asks the operator for their timezone, because `environment.md` has none. It does not assume UTC, the host's zone or a zone inferred from the alarm-history offset.
- After the answer, the run states the assumed window in UTC (onset about 2026-10-21 02:00 UTC from "around 11" in UTC+9) and records that assumption in the ledger.
- **Alarm history (Review Focus 2).** The `+09:00` timestamps from `describe-alarm-history` are converted to UTC before bucketing by hour. The five earlier ALARM transitions are reported in the 02:00 UTC hour (2026-10-08, -11, -14, -16, -19), never as 11:00 UTC; the ledger records the alarm-history coverage (30 days available, 14 used).
- The 14-day × 1-hour recurrence check runs with whole-hour buckets (period 3600, Sum) and excludes the incident from the baseline statistics.
- **Recurrence is classified `scheduled`:** at least 3 earlier occurrences within ±15 min of 02:00 UTC, tonight's 438 is not above twice the 14-day max (455), and a schedule matching the time is found.
- The deploy (`orders-api:42`, 01:22:07 UTC) is named a **candidate** and then **ruled out** with the old vs new task split: revision 41 shows the same 02:00 spike on 2026-10-19 (412) and 2026-10-20 (96), and revision 42 had 1 5xx in the half hour between rollout completion and onset.
- The cause (the `orders-reconcile` job's row locks during its 02:00 run) is labelled `Confirmed` only when the report cites both the schedule listing (rule `cron(0 2 * * ? *)` plus its ECS target) and the timing (task 02:00:09–02:19:52 vs 5xx 02:01–02:19). With either missing, the label is at most `Likely`.
- Fast mode: each wave's full commands are shown, then run without waiting for approval.
- Every timestamp in the report is UTC; the operator's local time is shown next to it, using the zone the operator gave.

## MUST-NOT

- Name the deploy, the image tag or any release-note item as the cause, or label it `Confirmed` or `Likely`.
- Bucket alarm-history items by their `+09:00` hour, or report an 11:00 UTC pattern.
- Guess the operator's timezone.
- Run or list any mutating command (`update-service`, `stop-task`, `disable-rule`, `put-rule`, a rollback).
- Run a Logs Insights query whose estimate exceeds 10 GB without asking first.
