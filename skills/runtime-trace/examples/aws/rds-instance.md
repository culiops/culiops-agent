# CloudWatch metrics — RDS DB Instance

For each RDS instance in scope, the skill fetches these metrics.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `CPUUtilization` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Average` | Saturation | mean CPU |
| `CPUUtilization` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Maximum` | Saturation | peak CPU |
| `DatabaseConnections` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Maximum` | Traffic | peak concurrent connections |
| `ReadIOPS` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Average` | Traffic | mean read IOPS |
| `WriteIOPS` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Average` | Traffic | mean write IOPS |
| `FreeableMemory` | `AWS/RDS` | `DBInstanceIdentifier=<id>` | `Minimum` | Saturation | min free memory (bytes) |

**Metric count per instance: 6.** 200-metric cap → ~33 RDS instances per run.

**Verdict heuristic:**

- `no-activity-14d` — `DatabaseConnections` maximum is 0 throughout window. A non-zero value alone doesn't prove application use: monitoring agents, backup tools and admin sessions also connect.
- `heuristic: healthy` — peak CPU < 80% and `FreeableMemory` minimum ≥ 10% of the instance class's memory (look the class up from the resolved resource; if unknown, show the raw bytes with no verdict).
- `heuristic: saturated` — peak CPU ≥ 80% OR `FreeableMemory` minimum < 10% of instance memory.
- `unknown` — any required metric returned `metric-not-found`.

Aurora: these metrics apply per DB instance (`DBInstanceIdentifier`); cluster-level metrics (`DBClusterIdentifier`) are not collected by this file.

Empty series are never zero: run the `ListMetrics` existence check (SKILL.md, source d) and record `no-data (metric exists)` or `metric-not-found`. Verdicts describe; they never recommend (Constraint 9). Thresholds are heuristics — always show the raw numbers next to the verdict.
