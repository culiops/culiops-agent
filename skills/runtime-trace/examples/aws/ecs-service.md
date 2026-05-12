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

- `idle` — `RunningTaskCount` average is zero (or metric missing → log gap).
- `healthy` — peak CPU < 80% and peak Memory < 80%.
- `saturated` — peak CPU ≥ 80% OR peak Memory ≥ 80%.
- `unknown` — any required metric returned no datapoints (Container Insights may not be enabled).
