# CloudWatch metrics — Application Load Balancer

For each ALB in scope, the skill fetches these metrics.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `RequestCount` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>` | `Sum` | Traffic | total requests over window |
| `TargetResponseTime` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>` | `p50` | Latency | median backend response time |
| `TargetResponseTime` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>` | `p99` | Latency | tail backend response time |
| `HTTPCode_Target_5XX_Count` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>` | `Sum` | Errors | backend 5XX count |
| `HTTPCode_ELB_5XX_Count` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>` | `Sum` | Errors | LB-level 5XX (e.g., no healthy targets) |
| `HealthyHostCount` | `AWS/ApplicationELB` | `LoadBalancer=<arn-suffix>, TargetGroup=<arn-suffix>` | `Minimum` | Saturation | min healthy targets across window |

**Metric count per ALB: 6** (one per target group for `HealthyHostCount` — skill fans out to the target groups attached to the ALB if known; capped at 3 target groups per ALB).

**Verdict heuristic:**

- `no-activity-14d` — `RequestCount` has no datapoints (metric listed) or sums to 0.
- `heuristic: healthy` — backend 5XX rate < 1% and `HealthyHostCount` minimum > 0 throughout window.
- `heuristic: degraded` — backend 5XX rate ≥ 1% OR `HealthyHostCount` ever dropped to 0.
- `unknown` — `RequestCount` or `HealthyHostCount` returned `metric-not-found`. The `HTTPCode_*` metrics are sparse: empty with non-zero requests means none occurred.

Empty series are never zero: run the `ListMetrics` existence check (SKILL.md, source d) and record `no-data (metric exists)` or `metric-not-found`. Verdicts describe; they never recommend (Constraint 9). Thresholds are heuristics — always show the raw numbers next to the verdict.
