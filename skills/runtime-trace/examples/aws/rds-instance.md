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

- `idle` — `DatabaseConnections` maximum is 0 throughout window.
- `healthy` — peak CPU < 80% and `FreeableMemory` minimum > 100 MB.
- `saturated` — peak CPU ≥ 80% OR `FreeableMemory` minimum ≤ 100 MB.
- `unknown` — any required metric returned no datapoints.
