# AWS — cloud-cost-investigate examples

Read-only commands per workflow step. All commands are `Get*` / `Describe*` / `List*` only — no mutations.

## Step 1 — Detect & Scope: cloud detection

```bash
# Detect current AWS account / region
aws sts get-caller-identity --output json
aws configure get region

# List configured profiles (for multi-account environments)
aws configure list-profiles
```

**IAM:** `sts:GetCallerIdentity` (default for any IAM principal).
**API cost:** none.

## Step 2A — Anomaly mode

### Total spend by service, time series

```bash
# Last 30 days, daily granularity, grouped by service
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '30 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per request after the first 100 of the calendar month. The skill MUST surface this in the query plan.

### Drill into a service by region / usage type / linked account / tag

```bash
# Top usage types within a service
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity DAILY \
  --metrics UnblendedCost \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]}}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
```

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per request.

### New resources in an anomalous window

```bash
# EC2 instances launched within window
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[].Instances[?LaunchTime>='<start-iso>'].[InstanceId,InstanceType,LaunchTime,Tags]"

# RDS instances
aws rds describe-db-instances \
  --query "DBInstances[?InstanceCreateTime>='<start-iso>'].[DBInstanceIdentifier,DBInstanceClass,InstanceCreateTime]"
```

**IAM:** `ec2:DescribeInstances`, `rds:DescribeDBInstances`.
**API cost:** none.

## Step 2B — Waste mode

### Compute Optimizer rightsizing recommendations

```bash
# EC2 rightsizing recommendations (skill must surface that recommendations come pre-scored)
aws compute-optimizer get-ec2-instance-recommendations \
  --output json

# EBS volume recommendations
aws compute-optimizer get-ebs-volume-recommendations --output json

# Lambda function recommendations
aws compute-optimizer get-lambda-function-recommendations --output json
```

**IAM:** `compute-optimizer:GetEC2InstanceRecommendations`, `compute-optimizer:GetEBSVolumeRecommendations`, `compute-optimizer:GetLambdaFunctionRecommendations`.
**API cost:** none.

### Resource-state sweeps

```bash
# Unattached EBS volumes
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query "Volumes[].[VolumeId,Size,VolumeType,CreateTime]"

# Snapshots older than 30 days, grouped by volume
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[?StartTime<='$(date -u -d '30 days ago' +%Y-%m-%d)'].[SnapshotId,VolumeSize,StartTime]"

# Unused Elastic IPs (no AssociationId)
aws ec2 describe-addresses \
  --query "Addresses[?AssociationId==null].[AllocationId,PublicIp]"

# Load balancers with no recent traffic — operator confirms via CloudWatch metric below
aws elbv2 describe-load-balancers --query "LoadBalancers[].[LoadBalancerArn,DNSName]"

# S3 buckets without lifecycle policies
aws s3api list-buckets --query "Buckets[].Name"
# For each bucket: aws s3api get-bucket-lifecycle-configuration --bucket <name>
# Buckets returning NoSuchLifecycleConfiguration are flagged.
```

**IAM:** `ec2:DescribeVolumes`, `ec2:DescribeSnapshots`, `ec2:DescribeAddresses`, `elasticloadbalancing:DescribeLoadBalancers`, `s3:ListAllMyBuckets`, `s3:GetLifecycleConfiguration`.
**API cost:** none.

### Untagged spend

```bash
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=Service
```

Resources missing the tag appear under `key=` (empty value). The skill flags these as "untagged spend" — never as "waste".

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per request.

### Optional — utilization metrics

```bash
# Last 14d average CPU for an instance (skill calls this per instance flagged as low-CPU candidate)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Average
```

**IAM:** `cloudwatch:GetMetricStatistics`.
**API cost:** none for `GetMetricStatistics`; first 1M `GetMetricData` requests/month free, then per-request charges apply (the skill prefers `GetMetricStatistics` for batch utilization to keep costs zero).

## Step 2C — Attribution mode

### Cost filtered by tag

```bash
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter '{"Tags":{"Key":"Service","Values":["<service-name>"]}}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
```

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per request.

### Cost filtered by linked account (org-wide opt-in only)

```bash
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter '{"Dimensions":{"Key":"LINKED_ACCOUNT","Values":["<account-id>"]}}' \
  --group-by Type=DIMENSION,Key=SERVICE
```

**IAM:** `ce:GetCostAndUsage`. Org-wide also requires the principal to be in the management account or a delegated admin.
**API cost:** $0.01 per request.

## Step 5 — Verification (shared)

No mutation occurs, so verification is just re-reading the report file before commit:

```bash
# Operator inspects the report draft
cat .culiops/cloud-cost-investigate/<scope-slug>-<mode>-<YYYYMMDD-HHmm>.md
```

## Iron Law reminders

- These commands are read-only by name. The skill MUST refuse if the operator asks for any `terminate`, `delete`, `modify`, `update`, `purchase`, `put`, `create` API.
- Cost Explorer requests after the first 100 in a calendar month cost $0.01 each. The query plan presented at GATE 2 must include estimated API cost.
- Compute Optimizer is enabled per-organization. If `compute-optimizer get-*` returns "OptInRequired", the skill stops and tells the operator to opt in (operator action, not skill action).
