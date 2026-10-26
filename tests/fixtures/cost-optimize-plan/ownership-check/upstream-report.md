**Cloud cost investigation**
**Mode:** waste
**Scope:** 111122223333 / acme-data (single)
**Time range:** 2026-05-03 → 2026-06-02
**Catalog used:** none
**Date:** 2026-06-02 10:20
**Cloud:** aws

## Question

Run a waste audit on our AWS data account (ap-southeast-1). What can we delete or rightsize?

## Scoping decisions

- Mode: waste.
- Scope: account 111122223333 (acme-data), single account, region ap-southeast-1.
- Time range: 30d rolling (2026-05-03 → 2026-06-02).
- Compute Optimizer: enabled, EC2 recommendations available.
- Savings floor: $5/mo.

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | ec2:DescribeVolumes (state=available) | ap-southeast-1 | ec2:Describe* | ok | 1 volume returned |
| 2 | compute-optimizer:GetEC2InstanceRecommendations | account | compute-optimizer:GetEC2InstanceRecommendations | ok | 1 recommendation returned |
| 3 | ce:GetCostAndUsage | account / 30d | ce:GetCostAndUsage | ok | Line items by resource |

## Findings

### Unattached EBS volumes

1 volume in state `available` with no attachments.

| Volume | Size | Type | Unattached since | Est. monthly cost |
|--------|------|------|-----------------|-------------------|
| vol-0dddd1 | 500 GB | gp3 | 2026-04-09 | $40/mo |

### Compute Optimizer rightsizing

| Instance | Current type | Recommended type | Projected savings | Avg CPU (14d) | Max CPU (14d) |
|----------|-------------|-----------------|-------------------|---------------|---------------|
| i-0eeee1 (web) | m5.2xlarge | m5.xlarge | $90/mo | 9% | 22% |

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Delete unattached EBS volume | vol-0dddd1 | $40/mo | line-item-computation | high | state=available since 2026-04-09; no attachments; 500 GB gp3 |
| 2 | Rightsize web instance from m5.2xlarge to m5.xlarge | i-0eeee1 | $90/mo | compute-optimizer | medium | CO recommendation; 14d avg CPU 9%, max 22% |

**Total estimated savings:** $130/mo combined

## Gaps

- Resource tags and ownership were not examined by this audit.
- Kubernetes and Auto Scaling relationships were not enumerated.

## Next steps (informational)

- Delete volume for item #1 via `iac-change-execution`.
- Rightsize item #2 via `iac-change-execution` (update instance type in IaC).
