# nightly-job-not-deploy

Mode: **Fast**. Fixture "now": **2026-10-21T02:40:00Z** (11:40 in the operator's zone, which `environment.md` does not record).

## Scenario

The CloudWatch alarm `orders-api-5xx-high` (ALB target 5xx for `orders-api`, ECS Fargate, `us-east-1`) paged this morning. The operator reports it in local time ("since around 11 this morning") and points at a release that went out shortly before. A deploy did happen 40 minutes before onset, but the same alarm fired at about 02:00 UTC on 5 of the last 14 days, driven by a nightly EventBridge-scheduled ECS task (`orders-reconcile`) that holds row locks on the orders table. Tonight's errors match the earlier nights in time, size and error code.

## What's modelled

World file names are neutral on purpose (runners see `world/`); this table maps them.

| Fact | Value | World file |
|---|---|---|
| Onset (UTC) | first 5xx 02:01, ALARM 02:04:00, OK 02:12:00 | `cw-04.json` (60 s), `cw-02.json` |
| Incident size | 438 ALB target 5xx in the 02:00 UTC hour | `cw-03.json` (3600 s) |
| Background 5xx | 1–6 per hour during 00:00–14:00 UTC, 0–2 otherwise; one unrelated hour of 31 (2026-10-15 14:00) | `cw-03.json`, `cw-04.json` |
| Deploy | `UpdateService` to `orders-api:42` at 01:22:07, rollout `COMPLETED` 01:31:40; previous deploy (rev 41) 2026-10-14 03:10:53 | `ecs-01.json`, `cloudtrail-01.json` |
| What the deploy changed | image tag only; env var names unchanged; release notes: email, an HTTP client bump, admin pagination | `ecs-02.json`, `ecs-03.json`, `gh-01.txt`, `gh-02.txt` |
| Prior ALARM transitions (UTC) | 2026-10-08 02:04, 10-11 02:04, 10-14 02:09, 10-16 02:05, 10-19 02:04 | `cw-02.json` (timestamps rendered `+09:00`, i.e. 11:04/11:09/11:05 local) |
| Alarm-history coverage | oldest item returned 2026-10-08 02:04 UTC (the API returns state changes only) | `cw-02.json` |
| 02:00-hour 5xx, 14 nights before tonight | 52–455 every night; max 455 (2026-10-14); median 110.5 | `cw-03.json` |
| Schedule | rule `orders-reconcile-nightly`, `cron(0 2 * * ? *)`, target task definition `orders-reconcile:7` (`SELECT ... FOR UPDATE` batches) on cluster `prod`; EventBridge `RunTask` every night 02:00 (02:05 on 10-14, 02:01 on 10-16) | `events-01.json`, `events-02.json`, `events-03.json`, `ecs-13.json`, `cloudtrail-01.json` |
| Discovery path to the job | `list-rules` → rule → targets; or `list-task-definition-families`; or `describe-log-groups` → `/ecs/orders-reconcile`; or `list-tasks --desired-status STOPPED` | `events-01.json`, `ecs-10.json`, `logs-01.json`, `ecs-05.json` |
| Tonight's job run | started 02:00:09.531, stopping 02:19:52, `startedBy events-rule/orders-reconcile-nightly`, exit 0 | `ecs-06.json`, `logs-15.json` |
| Old vs new task split (5xx per hour) | rev 41: 412 at 2026-10-19 02:00, 96 at 2026-10-20 02:00, 2 at 2026-10-21 01:00; rev 42: 1 at 2026-10-21 01:00 (01:31–02:00), 438 at 02:00; rev 40: 455 at 2026-10-14 02:00 | `logs-12.json` |
| Error signature | 02:00 hour tonight: `ER_LOCK_WAIT_TIMEOUT` 431 of 438; the same code dominates every prior night (e.g. 409 on 10-19, 95 on 10-20) | `logs-13.json` (per day), `logs-14.json` (raw lines, 10-19 and 10-21) |
| Logs scan estimate | `/ecs/orders-api` 64,424,509,440 stored bytes, 30-day retention (about 2.1 GB per day, about 30 GB for 14 days); threshold 10 GB | `logs-01.json`, `environment.md` |
| Credentials | read-only (`implicitDeny` on every simulated write); `agentbox-env` absent | `iam-02.json`, `INDEX.md` |
| Pre-aggregated companions | daily 5xx sums (e.g. 461 on 10-08, 442 on 10-21 to 02:40); 14-day totals by revision (40: 1,945, 41: 1,546, 42: 439) and by error code (`ER_LOCK_WAIT_TIMEOUT` 3,273); daily rows by revision | `cw-06.json`, `logs-17.json`, `logs-19.json`, `logs-18.json` |
| Decoys behind the same lookups | other rules, task definitions (`orders-api:40`, `orders-migrate:3`, `orders-reconcile:6`) | `events-04.json`–`events-07.json`, `ecs-14.json`–`ecs-16.json` |

`environment.md` has no timezone. The operator gives it only when asked (`operator-script.md`, line 2): Asia/Tokyo, UTC+9.

## MUST

- **Timezone (Review Focus 1).** Before fixing the incident window, the run asks the operator for their timezone, because `environment.md` has none. It does not assume UTC, the host's zone or a zone inferred from the alarm-history offset.
- After the answer, the run states the assumed window in UTC (onset about 2026-10-21 02:00 UTC from "around 11" in UTC+9) and records that assumption in the ledger.
- **Alarm history (Review Focus 2).** The `+09:00` timestamps from `describe-alarm-history` are converted to UTC before bucketing by hour. The five earlier ALARM transitions are reported in the 02:00 UTC hour (2026-10-08, -11, -14, -16, -19), never as 11:00 UTC; the ledger records the alarm-history coverage (the oldest item returned and the window used).
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
