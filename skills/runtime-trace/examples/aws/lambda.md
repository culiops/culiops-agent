# CloudWatch metrics — AWS Lambda

For each Lambda function in scope, the skill fetches these metrics with `cloudwatch:GetMetricData`.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `Invocations` | `AWS/Lambda` | `FunctionName=<name>` | `Sum` | Traffic | total invocation count over the window |
| `Errors` | `AWS/Lambda` | `FunctionName=<name>` | `Sum` | Errors | function errors (not throttles) |
| `Throttles` | `AWS/Lambda` | `FunctionName=<name>` | `Sum` | Errors | concurrency-limit throttles |
| `Duration` | `AWS/Lambda` | `FunctionName=<name>` | `p50` | Latency | median execution time |
| `Duration` | `AWS/Lambda` | `FunctionName=<name>` | `p99` | Latency | tail execution time |
| `ConcurrentExecutions` | `AWS/Lambda` | `FunctionName=<name>` | `Maximum` | Saturation | peak concurrency over the window |

**Metric count per function: 6.** With the 200-metric cap, the skill can cover ~33 Lambda functions per run. If a scope contains more, the operator is prompted at Gate 3 to narrow scope or accept partial coverage.

**Verdict heuristic (used in the four-golden-signals table):**

- `idle` — `Invocations` sum is zero over the 14-day window.
- `healthy` — `Errors`/`Invocations` < 1% and `Throttles` = 0.
- `degraded` — `Errors`/`Invocations` ≥ 1% OR `Throttles` > 0.
- `unknown` — any metric returned no datapoints.
