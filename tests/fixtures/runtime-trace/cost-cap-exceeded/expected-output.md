# Runtime Trace — Plan Refused

**Service:** platform-core
**Generated:** 2026-05-12T15:30:00Z
**Operator:** arn:aws:iam::123456789012:user/alice

## Why this report was produced

Gate 3's query plan estimated **$1.21**, which exceeds the configured hard cost cap of **$1.00**. Per the Iron Law (`HARD COST CAP: $1.00 per run`), the skill refuses to run any API calls when the cumulative estimate would exceed the cap.

No runtime-profile doc was written. No API calls were made beyond the capability probes at Gate 2.

## The refused plan

| # | Source | API call | Params (summary) | Time window | Est. cost |
|---|---|---|---|---|---|
| 1 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY SERVICE | 30d | $0.01 |
| 2 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY USAGE_TYPE | 30d | $0.01 |
| 3 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY LINKED_ACCOUNT | 30d | $0.01 |
| 4 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY TAG=service | 30d | $0.01 |
| 5 | CloudTrail | `cloudtrail:LookupEvents` | filter=EventSource (many) | 90d | free |
| 6 | CloudWatch | `cloudwatch:GetMetricData` | **12,000 metrics** (operator override of default 200 cap) | 14d | $0.12 |
| 7 | Resource Explorer | `resource-explorer-2:Search` | filter=tag:service=platform-core | n/a | free |

**Total estimated cost:** $1.21.

**Cap:** $1.00.

## Three options the operator was offered

1. **Reduce scope.** Lower the CloudWatch metric count (current override: 12,000) back toward the default 200 cap, or narrow the scoping primitive (e.g., supply a smaller ARN list).
2. **Raise the cap with documented justification.** Increase the hard cap above $1.21 and provide a written justification. The justification is recorded in this report and in the audit trail of the subsequent run. (Example: "Initial takeover audit; expected one-time cost.")
3. **Abort.** Make no API calls; close this run.

## What the operator chose

*(For this fixture: operator chose option 3 — abort. No subsequent run.)*

## Audit trail (probe phase only)

| Call ID | Source | API | Cost |
|---|---|---|---|
| ce-probe | Cost Explorer | ce:GetCostAndUsage (1d, capability test) | $0.01 |

Total: $0.01.
