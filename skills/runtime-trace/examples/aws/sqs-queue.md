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

- `idle` — `NumberOfMessagesSent` is 0 throughout window.
- `healthy` — `ApproximateNumberOfMessagesVisible` peak < 1000 and `ApproximateAgeOfOldestMessage` peak < 60s.
- `backlogged` — `ApproximateNumberOfMessagesVisible` peak ≥ 1000 OR `ApproximateAgeOfOldestMessage` peak ≥ 60s.
- `unknown` — any required metric returned no datapoints.
