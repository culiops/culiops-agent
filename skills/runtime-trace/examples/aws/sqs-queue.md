# CloudWatch metrics — SQS Queue

For each SQS queue in scope, the skill fetches these metrics.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `NumberOfMessagesSent` | `AWS/SQS` | `QueueName=<name>` | `Sum` | Traffic | total enqueued |
| `NumberOfMessagesReceived` | `AWS/SQS` | `QueueName=<name>` | `Sum` | Traffic | total dequeued (receives, not deletes) |
| `ApproximateNumberOfMessagesVisible` | `AWS/SQS` | `QueueName=<name>` | `Maximum` | Saturation | peak backlog |
| `ApproximateAgeOfOldestMessage` | `AWS/SQS` | `QueueName=<name>` | `Maximum` | Saturation | peak message age (seconds) |
| `NumberOfMessagesDeleted` | `AWS/SQS` | `QueueName=<name>` | `Sum` | Traffic | consumer commits |

**Metric count per queue: 5.** 200-metric cap → 40 SQS queues per run.

**Verdict heuristic:**

First establish whether the queue is a **dead-letter queue** with `sqs:ListDeadLetterSourceQueues` (SKILL.md, source c): a non-empty list means it is one; an empty list means it is not. A source queue in the same account but outside the resolved set still shows up in this call, which is why the resolved set is not used; a source in another account is `UNVERIFIED` here, so the Gaps section says DLQ status covers same-account sources only. If the call was not run or failed, DLQ status is `unknown` and the verdict is `unknown` — never `no-activity-14d`. Messages that SQS moves to a DLQ automatically are **not** counted in `NumberOfMessagesSent` (SQS developer guide, verified 2026-10-26), so a DLQ always looks inactive on that metric.

- DLQ: `heuristic: has-failed-messages` if `ApproximateNumberOfMessagesVisible` peak > 0; `empty` otherwise. Never `no-activity-14d`.
- `no-activity-14d` — (not a DLQ) `NumberOfMessagesSent` is 0 throughout window and `ApproximateNumberOfMessagesVisible` peak is 0.
- `heuristic: backlog-growing` — `ApproximateAgeOfOldestMessage` rises across the window without returning to its baseline. A single high peak is normal for batch consumers and delay queues; show the peak age and the consumer's cadence if known, not a fixed 60s threshold.
- `heuristic: draining` — otherwise.
- `unknown` — any required metric returned `metric-not-found`.

Empty series are never zero: run the `ListMetrics` existence check (SKILL.md, source d) and record `no-data (metric exists)` or `metric-not-found`. Verdicts describe; they never recommend (Constraint 9). Thresholds are heuristics — always show the raw numbers next to the verdict.
