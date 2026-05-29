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

# NAT Gateways — list all, then per-NAT BytesOutToDestination 14d (activity check)
# Principle 1: existence + attached route tables is NOT use evidence; bytes is.
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" \
  --query "NatGateways[].[NatGatewayId,VpcId,CreateTime]"
# Per NAT: see utilization metrics section for BytesOutToDestination query.

# Lambda functions with zero recent invocations
# Principle 1: event source mappings and aliases are attachment, not activity.
aws lambda list-functions --query "Functions[].[FunctionName,Runtime,LastModified,MemorySize]"
# Per function: see utilization metrics section for Invocations query.
# Also flag: any function with ProvisionedConcurrencyConfig — paying for warm capacity:
# aws lambda get-function-concurrency --function-name <name>

# DynamoDB tables — surface provisioned-mode tables with low consumed:provisioned ratio
aws dynamodb list-tables --query "TableNames[]"
# Per table:
aws dynamodb describe-table --table-name <name> \
  --query "Table.[TableName,BillingModeSummary.BillingMode,ProvisionedThroughput,TableSizeBytes]"
# Then ConsumedReadCapacityUnits / ConsumedWriteCapacityUnits vs Provisioned* — see utilization section.

# EKS managed nodegroups — surface low-utilization nodegroups
aws eks list-clusters --query "clusters[]"
# Per cluster:
aws eks list-nodegroups --cluster-name <cluster> --query "nodegroups[]"
# Per nodegroup:
aws eks describe-nodegroup --cluster-name <cluster> --nodegroup-name <ng> \
  --query "nodegroup.[nodegroupName,instanceTypes,scalingConfig,capacityType]"
# Then node-level CPU/memory + Container Insights — see utilization section.

# Kinesis Data Streams — list, then per-stream IncomingRecords/GetRecords activity
# Principle 1: registered EFO consumers + Lambda mappings + Firehose sources are attachment, not activity.
aws kinesis list-streams --query "StreamNames[]"
# Per stream:
aws kinesis describe-stream-summary --stream-name <name> \
  --query "StreamDescriptionSummary.[StreamName,StreamModeDetails.StreamMode,OpenShardCount,RetentionPeriodHours]"
# Attachment surfaces (NOT activity, but inform blast radius):
aws kinesis list-stream-consumers --stream-arn <arn>
aws lambda list-event-source-mappings --event-source-arn <arn>
# Activity — see utilization metrics section for IncomingRecords / GetRecords.Records.
```

**IAM:** `ec2:DescribeVolumes`, `ec2:DescribeSnapshots`, `ec2:DescribeAddresses`, `ec2:DescribeNatGateways`, `ec2:DescribeRouteTables`, `elasticloadbalancing:DescribeLoadBalancers`, `s3:ListAllMyBuckets`, `s3:GetLifecycleConfiguration`, `lambda:ListFunctions`, `lambda:GetFunctionConcurrency`, `lambda:ListEventSourceMappings`, `dynamodb:ListTables`, `dynamodb:DescribeTable`, `eks:ListClusters`, `eks:ListNodegroups`, `eks:DescribeNodegroup`, `kinesis:ListStreams`, `kinesis:DescribeStreamSummary`, `kinesis:ListStreamConsumers`.
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

### Utilization metrics (required for activity verification)

**Required (not optional)** per Principle 1 for any rightsize / idle-resource candidate whose resource type has an activity dimension. Exempt only when the resource type has no activity dimension at all (unattached EBS, unallocated EIP, orphaned snapshot — attachment state alone is sufficient evidence).

```bash
# EC2 — 14d average CPU per instance
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 --statistics Average,Maximum

# NAT Gateway — 14d egress bytes (Principle 1 activity signal)
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=<nat-id> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 --statistics Sum
# Sum == 0 over 14d → idle. Route-table attachment count is NOT this signal.

# Lambda — 30d invocations (30d catches monthly-cron functions)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda --metric-name Invocations \
  --dimensions Name=FunctionName,Value=<function-name> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 --statistics Sum
# Subtract ProvisionedConcurrencyInvocations (keep-warm noise) before judging idle:
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda --metric-name ProvisionedConcurrencyInvocations \
  --dimensions Name=FunctionName,Value=<function-name> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 --statistics Sum

# DynamoDB — 14d consumed vs provisioned capacity (provisioned mode)
# Principle 2: mode-switch savings claim requires both sides of this math.
for metric in ConsumedReadCapacityUnits ConsumedWriteCapacityUnits ProvisionedReadCapacityUnits ProvisionedWriteCapacityUnits ReadThrottleEvents WriteThrottleEvents; do
  aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB --metric-name $metric \
    --dimensions Name=TableName,Value=<table-name> \
    --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 --statistics Sum,Maximum
done
# Throttle events > 0 → table is under-provisioned, NOT a rightsize candidate.

# EKS nodegroup — Container Insights aggregated CPU/memory (cluster-side activity)
aws cloudwatch get-metric-statistics \
  --namespace ContainerInsights --metric-name node_cpu_utilization \
  --dimensions Name=ClusterName,Value=<cluster>,Name=NodegroupName,Value=<ng> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average,Maximum
# Repeat for node_memory_utilization. Container Insights must be enabled on the cluster.
# Subtract daemonset baseline (~5-10% CPU, ~150-300 MB memory per node) before judging idle.

# Kinesis — 14d producer + consumer activity
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis --metric-name IncomingRecords \
  --dimensions Name=StreamName,Value=<stream-name> \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Sum
# Repeat for IncomingBytes, GetRecords.Records, WriteProvisionedThroughputExceeded.
# Throttles > 0 → stream is under-provisioned, NOT a delete candidate.
# Registered EFO consumers / Lambda mappings are attachment, NOT activity.
```

**IAM:** `cloudwatch:GetMetricStatistics`.
**API cost:** none for `GetMetricStatistics`; first 1M `GetMetricData` requests/month free, then per-request charges apply (the skill prefers `GetMetricStatistics` for batch utilization to keep costs zero).

**Principle 2 cost-direction reminder:** for DynamoDB and Kinesis, any savings claim involving a billing-mode switch (provisioned ↔ on-demand) MUST compute the delta from observed throughput × current-region real pricing for both modes. Bare "switch to on-demand to save" is rejected — the cheaper mode flips with workload shape (steady → provisioned; spiky / low-baseline → on-demand). Fetch live pricing via `aws pricing get-products` rather than hardcoding.

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
