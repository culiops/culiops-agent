# Runtime Trace — Plan Refused

**Service:** platform-core
**Generated:** 2026-05-12T15:30:00Z
**Operator:** arn:aws:iam::123456789012:user/alice

## Why this report was produced

Gate 3's query plan, priced against the 612 resolved resources, estimated **$1.22**. With the **$0.01** already spent on the GATE 1a Cost Explorer probe the cumulative estimate is **$1.23**, which exceeds the configured hard cost cap of **$1.00**. Per the Iron Law (`HARD COST CAP: $1.00 per run`), the skill refuses to run any further billable calls when the cumulative estimate would exceed the cap.

No runtime-profile doc was written. No API calls were made beyond the GATE 1a probes and the free Step 2b resource resolution.

## The refused plan

Cost Explorer bills **$0.01 per request, and every page is a request**. The CE grouping below returns far more rows than one page.

| # | Source | API call | Params (summary) | Time window | Basis | Est. cost |
|---|---|---|---|---|---|---|
| 1 | Cost Explorer | `ce:GetCostAndUsage` | DAILY, GROUP BY SERVICE + USAGE_TYPE, Filter Tags `service=platform-core` | 2025-05-11 -> 2026-05-11 (365d) | ~219,000 group rows (365 days x ~600 service/usage-type groups) at ~2,000 rows/page = ~110 pages x $0.01 | $1.10 |
| 2 | CloudTrail | `cloudtrail:LookupEvents` | one series per resource name, 612 series, page cap 20, <= 2 req/s | 90d | free | $0.00 |
| 3 | Wiring | `lambda:GetPolicy`, `lambda:ListEventSourceMappings`, `sqs:GetQueueAttributes`, `sqs:ListDeadLetterSourceQueues`, ... | per applicable resource | n/a | read-only; within free tiers | ~$0.00 |
| 4 | CloudWatch | `cloudwatch:GetMetricData` | **12,000 metrics** (operator override of default 200 cap) | 14d | 12,000 / 1,000 x $0.01 | $0.12 |
| — | Resource Explorer | `resource-explorer-2:Search` | tag:service=platform-core (already run at Step 2b, 612 resources) | n/a | free | $0.00 |

**Plan estimate:** $1.10 + $0.12 = **$1.22**.
**Already spent (GATE 1a CE probe):** $0.01.
**Cumulative:** $1.22 + $0.01 = **$1.23**.

**Cap:** $1.00. **Over by:** $0.23.

Cannot proceed: estimated cumulative cost $1.23 exceeds the hard cap of $1.00.

## Three options the operator was offered

1. **Reduce scope.** For example: CE `GROUP BY SERVICE` only over the last 30 days (about 1,200 rows, 1 page, $0.01 instead of $1.10), and/or lower the CloudWatch metric count (current override: 12,000) back toward the default 200 cap, or narrow the scoping primitive. Cutting the CE plan alone brings the cumulative estimate to about $0.14 (0.01 probe + 0.01 + 0.12), under the cap; cutting only the metrics does not ($1.10 of CE pagination remains).
2. **Raise the cap with documented justification.** Increase the hard cap above $1.23 and provide a written justification. The justification is recorded in this report and in the audit trail of the subsequent run. (Example: "Initial takeover audit; expected one-time cost.")
3. **Abort.** Make no further API calls; close this run.

## What the operator chose

*(For this fixture: operator chose option 3 — abort. No subsequent run.)*

## Audit trail (probe phase and resolution only)

| Call ID | Source | API | Cost |
|---|---|---|---|
| probe-001..009 | Scoping probe | sts, iam, organizations, resource-explorer-2 x4, cloudtrail x2 | $0.00 |
| probe-010 | Cost Explorer | ce:GetCostAndUsage (1d, tag-filtered, capability test) | $0.01 |
| re-001 | Resource Explorer | resource-explorer-2:Search (Step 2b, 612 resources) | $0.00 |

Total spent: $0.01. Planned-but-refused: $1.22.
