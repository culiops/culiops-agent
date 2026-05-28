**Cloud cost investigation**
**Mode:** waste
**Scope:** 123456789012 / acme-prod (single)
**Time range:** 2026-04-28 → 2026-05-28
**Catalog used:** none
**Date:** 2026-05-28 09:15
**Cloud:** aws

## Question

Run a waste audit on our AWS prod account (ap-southeast-1). What can we delete or rightsize?

## Scoping decisions

- Mode: waste (operator confirmed "delete or rightsize" intent).
- Scope: account 123456789012 (acme-prod), single account, region ap-southeast-1.
- Time range: 30d rolling (2026-04-28 → 2026-05-28).
- Compute Optimizer: enabled and has been running >14 days — EC2 + EBS recommendations available.
- Savings floor: $5/mo.
- Untagged spend: not flagged (all resources carry required tags in this account).

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | ce:GetCostAndUsage | account / 30d | ce:GetCostAndUsage | ok | Line items by resource |
| 2 | compute-optimizer:GetEC2InstanceRecommendations | account | compute-optimizer:GetEC2InstanceRecommendations | ok | 1 recommendation returned |
| 3 | ec2:DescribeVolumes (state=available) | ap-southeast-1 | ec2:Describe* | ok | 1 volume returned |
| 4 | ec2:DescribeSnapshots | account / orphaned >30d | ec2:Describe* | ok | 0 orphaned snapshots |
| 5 | s3:ListBuckets + GetBucketLifecycleConfiguration | account | s3:GetBucketLifecycleConfiguration | ok | logs-bucket-app: no lifecycle policy |

## Findings

### Compute Optimizer rightsizing

Compute Optimizer has been active for 29 days and has 1 EC2 recommendation above the $5/mo floor.

| Instance | Current type | Recommended type | Projected savings | Avg CPU (14d) | Max CPU (14d) |
|----------|-------------|-----------------|-------------------|---------------|---------------|
| i-0a1b2c3d4e5f67890 (prod-api) | m5.4xlarge | m5.2xlarge | $280/mo | 4% | 12% |

### Unattached EBS volumes

1 volume in state `available` with no attachments.

| Volume | Size | Type | Unattached since | Est. monthly cost |
|--------|------|------|-----------------|-------------------|
| vol-0xxxxxxxxxxxxxxx1 | 200 GB | gp3 | 2026-02-14 | $48/mo |

### S3 storage without lifecycle management

1 bucket with >1 TB StandardStorage and no lifecycle policy or Intelligent-Tiering configuration.

| Bucket | StandardStorage | Est. age >90d | Missing policy | Est. savings (add 90d→Glacier) |
|--------|----------------|---------------|----------------|-------------------------------|
| logs-bucket-app | 4.2 TB | ~3.8 TB | lifecycle policy | $200/mo |

### Orphaned snapshots

0 orphaned snapshots found (all snapshots <30d old or associated with active volumes).

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Rightsize prod-api from m5.4xlarge to m5.2xlarge | i-0a1b2c3d4e5f67890 | $280/mo | compute-optimizer | medium | CO recommendation; 14d avg CPU 4%, max 12% |
| 2 | Add S3 lifecycle policy (StandardStorage → Glacier after 90 days) | logs-bucket-app | $200/mo | line-item-computation | high | 4.2 TB StandardStorage; ~3.8 TB estimated >90d aged; no existing lifecycle policy or Intelligent-Tiering |
| 3 | Delete unattached EBS volume | vol-0xxxxxxxxxxxxxxx1 | $48/mo | line-item-computation | high | state=available since 2026-02-14; no attachments; 200 GB gp3 |

**Total estimated savings:** $248/mo (high-confidence) + $280/mo (medium-confidence) = $528/mo combined

## Gaps

- NAT Gateway data transfer not broken out by destination (would require VPC flow logs — operator did not request).
- RDS instances not evaluated (Compute Optimizer RDS not enabled for this account).

## Next steps (informational)

- Rightsize item #1 via `iac-change-execution` (update instance type in IaC).
- Add lifecycle policy for item #2 via `iac-change-execution` (add `aws_s3_bucket_lifecycle_configuration` resource).
- Delete volume for item #3 via `iac-change-execution` (snapshot first, then destroy).
- Consider enabling Compute Optimizer for RDS to surface additional rightsizing opportunities.
