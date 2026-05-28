**Cloud cost investigation**
**Mode:** waste
**Scope:** 123456789012 / acme-prod (single)
**Time range:** 2026-04-28 → 2026-05-28
**Catalog used:** none
**Date:** 2026-05-28 11:00
**Cloud:** aws

## Question

Run a waste audit on our AWS prod account (ap-southeast-1). Are there any Lambda functions we can delete?

## Scoping decisions

- Mode: waste (operator confirmed "delete" intent targeting Lambda).
- Scope: account 123456789012 (acme-prod), single account, region ap-southeast-1.
- Time range: 30d rolling (2026-04-28 → 2026-05-28).
- Savings floor: $5/mo.
- Untagged spend: not flagged (all resources carry required tags in this account).

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | lambda:ListFunctions | ap-southeast-1 | lambda:ListFunctions | ok | 14 functions enumerated |
| 2 | cloudwatch:GetMetricStatistics (Lambda.Invocations, 30d) | per-function | cloudwatch:GetMetricStatistics | ok | idle-worker: 0 invocations in 30d |
| 3 | ce:GetCostAndUsage (Lambda line items) | account / 30d | ce:GetCostAndUsage | ok | idle-worker accruing $35/mo in provisioned-concurrency charges despite 0 invocations |

## Findings

### Idle Lambda functions (0 invocations in 30d)

1 function with zero invocations in the last 30 days and non-trivial provisioned-concurrency cost.

| Function | Runtime | Last invocation | Provisioned concurrency | Est. monthly cost |
|----------|---------|----------------|------------------------|-------------------|
| idle-worker | python3.11 | >30d ago (no CloudWatch data point in window) | 2 units | $35/mo |

The function carries 2 provisioned-concurrency units configured. It has not been invoked in at least 30 days. The $35/mo charge is entirely attributable to provisioned concurrency — the function would cost ~$0 if invocations remain at zero without provisioned concurrency, or $0 if deleted.

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Delete Lambda function idle-worker | arn:aws:lambda:ap-southeast-1:123456789012:function:idle-worker | $35/mo | line-item-computation | medium | 0 invocations in last 30d per CloudWatch Lambda.Invocations metric |

**Total estimated savings:** $35/mo (medium-confidence)

## Gaps

- Invocation history checked for 30d window only; function may have legitimate seasonal usage patterns outside this window.
- EventBridge rules, API Gateway integrations, and other event-source mappings not checked by this waste audit — dependency verification requires operator review.

## Next steps (informational)

- Verify no active event sources trigger the function before deleting.
- Delete idle-worker via `iac-change-execution` once dependencies are confirmed clear.
