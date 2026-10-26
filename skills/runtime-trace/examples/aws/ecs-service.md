# CloudWatch metrics — ECS Service

For each ECS service in scope, the skill fetches these metrics.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `CPUUtilization` | `AWS/ECS` | `ClusterName=<c>, ServiceName=<s>` | `Average` | Saturation | mean CPU across tasks |
| `CPUUtilization` | `AWS/ECS` | `ClusterName=<c>, ServiceName=<s>` | `Maximum` | Saturation | peak CPU across tasks |
| `MemoryUtilization` | `AWS/ECS` | `ClusterName=<c>, ServiceName=<s>` | `Average` | Saturation | mean memory across tasks |
| `MemoryUtilization` | `AWS/ECS` | `ClusterName=<c>, ServiceName=<s>` | `Maximum` | Saturation | peak memory across tasks |
| `RunningTaskCount` | `ECS/ContainerInsights` | `ClusterName=<c>, ServiceName=<s>` | `Average` | Traffic | running task count (requires Container Insights) |

**Metric count per service: 5.** With the 200-metric cap, the skill can cover 40 ECS services per run.

**Verdict heuristic:**

- `no-activity-14d` — `RunningTaskCount` average is 0 throughout the window. If Container Insights is off (`RunningTaskCount` → `metric-not-found`), the verdict comes from `AWS/ECS` CPU alone: CPU datapoints present → tasks were running; none → `unknown` (log gap: "Container Insights not enabled").
- `heuristic: healthy` — peak CPU < 80% and peak Memory < 80%.
- `heuristic: saturated` — peak CPU ≥ 80% OR peak Memory ≥ 80%.
- `unknown` — CPU and memory both `metric-not-found`.

Empty series are never zero: run the `ListMetrics` existence check (SKILL.md, source d) and record `no-data (metric exists)` or `metric-not-found`. Verdicts describe; they never recommend (Constraint 9). Thresholds are heuristics — always show the raw numbers next to the verdict.
