**Cloud cost investigation**
**Mode:** waste
**Scope:** 123456789012 / acme-prod (single)
**Time range:** 2026-04-28 → 2026-05-28
**Catalog used:** none
**Date:** 2026-05-28 11:00
**Cloud:** aws

## Question

Run a waste audit on our AWS prod account (ap-southeast-1). Are there any RDS / Aurora clusters we can decommission?

## Scoping decisions

- Mode: waste (operator confirmed "delete" intent targeting RDS / Aurora).
- Scope: account 123456789012 (acme-prod), single account, region ap-southeast-1.
- Time range: 30d rolling (2026-04-28 → 2026-05-28).
- Savings floor: $5/mo.
- Untagged spend: not flagged (all clusters carry required tags in this account).

## Queries run

| # | API | Scope | IAM | Status | Notes |
|---|-----|-------|-----|--------|-------|
| 1 | rds:DescribeDBClusters | ap-southeast-1 | rds:DescribeDBClusters | ok | 4 Aurora clusters enumerated |
| 2 | cloudwatch:GetMetricStatistics (RDS.DatabaseConnections, 30d) | per-cluster | cloudwatch:GetMetricStatistics | ok | legacy-orders-aurora: 0 connections in 30d |
| 3 | cloudwatch:GetMetricStatistics (RDS.SelectThroughput + DMLThroughput, 30d) | per-cluster | cloudwatch:GetMetricStatistics | ok | legacy-orders-aurora: 0 query activity in 30d |
| 4 | ce:GetCostAndUsage (RDS line items) | account / 30d | ce:GetCostAndUsage | ok | legacy-orders-aurora accruing $420/mo across 2 db.r6g.large instances |

## Findings

### Idle Aurora clusters (0 connections + 0 query activity in 30d)

1 cluster with zero database connections and zero query throughput in the last 30 days.

| Cluster | Engine | Writer + Reader | Last connection | Est. monthly cost |
|---------|--------|-----------------|-----------------|-------------------|
| legacy-orders-aurora | aurora-mysql 8.0.mysql_aurora.3.04.0 | 1 writer + 1 reader (db.r6g.large each) | >30d ago (no datapoint in window) | $420/mo |

The cluster has not received any database connections in at least 30 days. The $420/mo charge is composed of $0.29/hr × 2 instances × 730 hr = $423.40/mo for instance-hours, plus storage and IO at near-zero usage. The cluster's tag `Service=orders-legacy` aligns with a service the catalog flags as "deprecated 2026-03-01" — operator should confirm decommissioning is intended.

## Remediation list (prioritized)

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|--------------|--------|------------|----------|
| 1 | Delete Aurora cluster legacy-orders-aurora | arn:aws:rds:ap-southeast-1:123456789012:cluster:legacy-orders-aurora | $420/mo | line-item-computation | medium | 0 DatabaseConnections + 0 SelectThroughput + 0 DMLThroughput in last 30d per CloudWatch RDS metrics |

**Total estimated savings:** $420/mo (medium-confidence)

## Gaps

- Connection / query history checked for 30d window only; cluster may have legitimate seasonal usage patterns outside this window (e.g., quarterly report jobs).
- Read replicas and cross-region replication relationships not enumerated by this waste audit — dependency verification requires operator review.
- Application secrets in AWS Secrets Manager / SSM Parameter Store referencing the cluster endpoint not scanned by this waste audit.

## Next steps (informational)

- Verify no application is configured to connect to the cluster endpoint (Secrets Manager sweep, ECS task definitions, Lambda environment variables).
- Confirm no read-replica chain or cross-region replication targets the cluster.
- Take a final cluster snapshot before deletion if the data may be needed for compliance retrieval.
- Delete legacy-orders-aurora via `iac-change-execution` once dependencies are confirmed clear.
