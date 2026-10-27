# AWS — cloud-cost-investigate examples

Read-only commands per workflow step. All commands are `Get*` / `Describe*` / `List*` / `Lookup*` only — no mutations.

**Regional calls.** Everything except Cost Explorer, IAM, Organizations and `s3api list-buckets` is regional. Run each regional command once per sweep region from Step 1.4 (`--region <r>`), and record the region with the result.

**Single-account scope in a payer account.** When the scoping probe shows the caller is the Organizations management account, add the account to **every** Cost Explorer call. Combine it with any other filter using `And`:

```json
{"And": [
  {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": ["<account-id>"]}},
  {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage", "DiscountedUsage", "SavingsPlanCoveredUsage"]}}
]}
```

**Usage record types.** "Usage" in this skill means all three usage `RECORD_TYPE`s: `Usage` (on-demand), `DiscountedUsage` (RI-covered) and `SavingsPlanCoveredUsage` (SP-covered). Filtering on `Usage` alone drops every commitment-covered line, so a Savings Plan expiry looks like brand-new spend. Read them with **`AmortizedCost`**, which prices covered usage at its effective commitment rate. Everything else (`RIFee`, `SavingsPlanRecurringFee` = unused commitment under amortization, `SavingsPlanUpfrontFee`, `SavingsPlanNegation`, `Credit`, `Refund`, `Tax`, `Support`) is a non-usage bill change, reported on its own line.

**Cost Explorer pricing.** $0.01 per request and **each paginated page is a request**; there is no free tier (AWS Cost Explorer pricing page, verified 2026-10-26 — re-check before quoting). Estimate pages, not calls: DAILY × 30d × 50 services paginates.

**Docs behind the billing claims** (read in this session before quoting them in a report; re-check, they move): Cost Explorer retention, refresh and per-page price — `https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html` · how a Savings Plan is applied (hourly, largest-saving usage first, no carry-over) — `https://repost.aws/knowledge-center/savings-plans-billing` · `DescribeOrganization` works from any account — `https://docs.aws.amazon.com/sdk-for-go/api/service/organizations/index.html` · cost-allocation tag activation — `https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html`. A claim with no page read this session is `UNVERIFIED`.

## Step 1 — Detect & Scope: cloud detection + scoping probe

```bash
# Local only (no API call): profile and region in use
echo "AWS_PROFILE=${AWS_PROFILE:-<default>} AWS_REGION=${AWS_REGION:-$(aws configure get region)}"
aws configure list-profiles
```

Scoping probe — shown as a mini batch and run only on approval (GATE 1a):

```bash
# 1. Who am I — compare with the account the operator means to investigate
aws sts get-caller-identity --output json
# 2. Human-readable alias (may be empty)
aws iam list-account-aliases --query "AccountAliases[]"
# 3. Payer or member? Works from any account in the organization.
#    MasterAccountId == caller → payer; different → member;
#    AWSOrganizationsNotInUseException → standalone;
#    any other error (AccessDenied included) → payer status unverified, treat as payer.
aws organizations describe-organization \
  --query "Organization.[MasterAccountId,Id]"
#    payer or unverified → LINKED_ACCOUNT filter on every CE call (a no-op on a member / standalone account)
# 4. Regions with spend (sweep regions), last 30d, usage only. AmortizedCost: covered
#    usage carries its commitment rate, so a region served by a Savings Plan is not
#    read as empty and skipped.
#    Run after #3: if payer or unverified, wrap the filter with LINKED_ACCOUNT as shown above.
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '32 days ago' +%Y-%m-%d),End=$(date -u -d '2 days ago' +%Y-%m-%d) \
  --granularity MONTHLY --metrics AmortizedCost \
  --filter '{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage","DiscountedUsage","SavingsPlanCoveredUsage"]}}' \
  --group-by Type=DIMENSION,Key=REGION
```

**IAM:** `sts:GetCallerIdentity`, `iam:ListAccountAliases`, `organizations:DescribeOrganization`, `ce:GetCostAndUsage`.
**API cost:** ~$0.01 (one CE page); the rest are free.

## Step 2A — Anomaly mode

### Native anomaly findings (if Cost Anomaly Detection is configured)

```bash
aws ce get-anomalies \
  --date-interval StartDate=<start>,EndDate=<end> \
  --query "Anomalies[].[AnomalyStartDate,Impact.TotalImpact,RootCauses]"
# No monitors configured → empty. That is "no data", not "no anomaly".
```

**IAM:** `ce:GetAnomalies`. **API cost:** $0.01 per page.

### Usage spend by service, time series (both windows)

```bash
# Window ends 2 days ago: the most recent CE days are estimated and still filling in.
# Each ResultsByTime entry carries "Estimated": true|false — drop estimated days from the comparison.
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '32 days ago' +%Y-%m-%d),End=$(date -u -d '2 days ago' +%Y-%m-%d) \
  --granularity DAILY \
  --metrics AmortizedCost UnblendedCost \
  --filter '{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage","DiscountedUsage","SavingsPlanCoveredUsage"]}}' \
  --group-by Type=DIMENSION,Key=SERVICE
# Repeat for the previous window (same length). End date is exclusive.
```

### Non-usage bill changes (purchases, credits, refunds, tax, support)

```bash
aws ce get-cost-and-usage \
  --time-period Start=<prev-start>,End=<end> \
  --granularity MONTHLY \
  --metrics AmortizedCost UnblendedCost \
  --group-by Type=DIMENSION,Key=RECORD_TYPE
# An all-upfront RI / Savings Plan purchase, a credit running out, or a refund
# shows here — report it as a bill change, not as a usage anomaly.
```

**IAM:** `ce:GetCostAndUsage`. **API cost:** $0.01 per page — DAILY × SERVICE over 30d usually paginates; estimate 2–4 pages per window.

### Commitment coverage and expiry

```bash
# Savings Plans coverage, both windows (a drop with no resource change = expiry or scale-out)
aws ce get-savings-plans-coverage \
  --time-period Start=<prev-start>,End=<end> --granularity MONTHLY
# RI coverage
aws ce get-reservation-coverage \
  --time-period Start=<prev-start>,End=<end> --granularity MONTHLY
# Commitments ending in or near the window
aws savingsplans describe-savings-plans \
  --query "savingsPlans[].[savingsPlanId,savingsPlanType,commitment,end,state]"
aws ec2 describe-reserved-instances \
  --query "ReservedInstances[].[ReservedInstancesId,InstanceType,InstanceCount,End,State]"   # regional
aws rds describe-reserved-db-instances \
  --query "ReservedDBInstances[].[ReservedDBInstanceId,DBInstanceClass,DBInstanceCount,StartTime,Duration,State]"   # regional
```

**IAM:** `ce:GetSavingsPlansCoverage`, `ce:GetReservationCoverage`, `savingsplans:DescribeSavingsPlans`, `ec2:DescribeReservedInstances`, `rds:DescribeReservedDBInstances`.
**API cost:** $0.01 per page for the two `ce` calls; the rest are free.

### Drill into a service by region / usage type / linked account / tag

```bash
# Top usage types within a service
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity DAILY \
  --metrics AmortizedCost UsageQuantity \
  --filter '{"And":[{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]}},{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage","DiscountedUsage","SavingsPlanCoveredUsage"]}}]}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
# UsageQuantity per usage type: units up, rate flat = more usage; units flat, $/unit up
# = rate change (commitment expiry, tier, credit). Compare like usage types only.
```

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per page.

### Tying a driver to a change (Amount / Timing / Cause)

Amount and Timing come from the calls above (the day the DAILY series steps; units × bill-derived rate). Cause is a named change, read from one of:

```bash
# Who/what created or changed it (Event history, <= 90 days, management events)
aws cloudtrail lookup-events --region <r> \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=<resource-id> \
  --start-time <start-iso> --end-time <end-iso> \
  --query "Events[].[EventTime,EventName,Username]"
# Repo history for the resource definition (local checkout, or: gh api repos/<owner>/<repo>/commits?path=<file>&since=<start-iso>)
git log --since=<start-iso> --format='%h %ad %s' --date=short -- <path>
```

Three legs cited = `confirmed`; fewer, see SKILL.md Step 4A. A CloudTrail row proves who changed the resource, not that the change moved the bill.

### New resources in an anomalous window

```bash
# Run in the region(s) the drill-down named.
# LaunchTime resets on stop/start — a match is a candidate, not proof of creation.
aws ec2 describe-instances --region <r> \
  --filters "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[].Instances[?LaunchTime>='<start-iso>'].[InstanceId,InstanceType,LaunchTime,Tags]"

# RDS instances
aws rds describe-db-instances --region <r> \
  --query "DBInstances[?InstanceCreateTime>='<start-iso>'].[DBInstanceIdentifier,DBInstanceClass,InstanceCreateTime]"

# Instances already terminated don't appear above. Creation events (≤ 90 days, Event history):
aws cloudtrail lookup-events --region <r> \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --start-time <start-iso> --end-time <end-iso> \
  --query "Events[].[EventTime,Username,Resources[0].ResourceName]"

# Resource-level cost (only if "resource-level data" is enabled in CE settings; last 14 days only)
aws ce get-cost-and-usage-with-resources \
  --time-period Start=<start>,End=<end> --granularity DAILY --metrics UnblendedCost \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]}}' \
  --group-by Type=DIMENSION,Key=RESOURCE_ID
```

**IAM:** `ec2:DescribeInstances`, `rds:DescribeDBInstances`, `cloudtrail:LookupEvents`, `ce:GetCostAndUsageWithResources`.
**API cost:** none for the describe / LookupEvents calls; $0.01 per page for `get-cost-and-usage-with-resources`.

## Step 2B — Waste mode

### Compute Optimizer rightsizing recommendations

```bash
# Regional — run per sweep region. Pre-scored, but: priced at on-demand (unless
# savings-estimation mode includes discounts) and based on a 14-day default lookback.
# A CO row starts at confidence: low until the ≥30d hourly drill-down + coverage check.
aws compute-optimizer get-ec2-instance-recommendations --region <r> --output json
aws compute-optimizer get-ebs-volume-recommendations --region <r> --output json
aws compute-optimizer get-lambda-function-recommendations --region <r> --output json
aws compute-optimizer get-auto-scaling-group-recommendations --region <r> --output json
aws compute-optimizer get-ecs-service-recommendations --region <r> --output json
aws compute-optimizer get-rds-database-recommendations --region <r> --output json
# Idle-resource findings (EC2, EBS, RDS, ASG, ECS…): a lead, not delete evidence — still needs
# the activity window (Principle 3) and both delete signals (Principle 1 rule 5).
aws compute-optimizer get-idle-recommendations --region <r> --output json
```

**IAM:** `compute-optimizer:GetEC2InstanceRecommendations`, `compute-optimizer:GetEBSVolumeRecommendations`, `compute-optimizer:GetLambdaFunctionRecommendations`, `compute-optimizer:GetAutoScalingGroupRecommendations`, `compute-optimizer:GetECSServiceRecommendations`, `compute-optimizer:GetRDSDatabaseRecommendations`, `compute-optimizer:GetIdleRecommendations`.
**API cost:** none.

### Resource-state sweeps

```bash
# Unattached EBS volumes — with tags, so the owner can be read without another query
aws ec2 describe-volumes --region <r> \
  --filters "Name=status,Values=available" \
  --query "Volumes[].[VolumeId,Size,VolumeType,CreateTime,Tags]"
# Owner tags to read: kubernetes.io/created-for/pvc/name, ebs.csi.aws.com/cluster
# (StatefulSet PV — holds data), aws:cloudformation:stack-name (unsupported-owner).
# CreateTime is NOT "unused since". Detach time (Event history, ≤ 90 days):
aws cloudtrail lookup-events --region <r> \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=<vol-id> \
  --start-time $(date -u -d '90 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --query "Events[?EventName=='DetachVolume'].[EventTime,Username]"
# No DetachVolume in 90 days and no AWS Config history → confidence: low, window-unverified.

# Snapshot ORPHAN candidates — age is not orphaned. Three checks:
# (a) snapshots whose source volume no longer exists
aws ec2 describe-snapshots --region <r> --owner-ids self \
  --query "Snapshots[].[SnapshotId,VolumeId,VolumeSize,StartTime,Description,Tags]"
aws ec2 describe-volumes --region <r> --query "Volumes[].VolumeId"   # live volumes; VolumeId not in this list → source gone
# (b) not referenced by an AMI
aws ec2 describe-images --region <r> --owners self \
  --query "Images[].BlockDeviceMappings[].Ebs.SnapshotId"
# (c) not managed by a backup policy: tag aws:backup:source-resource (AWS Backup),
#     tag dlm:managed=true or Description "Created for policy: …" (DLM),
#     or Description "This snapshot is created by the AWS Backup service".
# Fails any check → it's a backup: Informational (retention review), not a delete.
# Savings: snapshots are incremental — never VolumeSize × rate. Bill-derived or confidence: low.

# Unassociated Elastic IPs (no AssociationId). Cost regardless of use; "unused since"
# = DisassociateAddress event (Event history ≤ 90d). External allowlists that pin the IP
# are invisible here — say so in the row.
aws ec2 describe-addresses --region <r> \
  --query "Addresses[?AssociationId==null].[AllocationId,PublicIp,Tags]"

# Load balancers — ALB / NLB / GWLB and Classic are separate APIs and metric namespaces
aws elbv2 describe-load-balancers --region <r> \
  --query "LoadBalancers[].[LoadBalancerArn,Type,DNSName,CreatedTime]"
aws elb describe-load-balancers --region <r> \
  --query "LoadBalancerDescriptions[].[LoadBalancerName,DNSName,CreatedTime]"
# Activity metric per type (utilization section): ALB AWS/ApplicationELB RequestCount;
# NLB AWS/NetworkELB NewFlowCount (NLB has no RequestCount); CLB AWS/ELB RequestCount.

# S3 buckets without lifecycle policies — a hygiene flag, not a saving
aws s3api list-buckets --query "Buckets[].Name"
# For each bucket: aws s3api get-bucket-lifecycle-configuration --bucket <name>
# NoSuchLifecycleConfiguration → flag under Informational. No $ without a storage-class
# analysis (S3 Storage Lens / storage-class metrics) — transitions have per-object
# request fees and minimum-duration charges.

# NAT Gateways — list all, then per-NAT BytesOutToDestination 30d (activity check)
# Principle 1: existence + attached route tables is NOT use evidence; bytes is.
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" \
  --query "NatGateways[].[NatGatewayId,VpcId,CreateTime]"
# Per NAT: see utilization metrics section for BytesOutToDestination query.

# Lambda functions with zero recent invocations
# Principle 1: event source mappings and aliases are attachment, not activity.
# The --query projection is MANDATORY: the full response carries every function's
# Environment.Variables (secrets) — never run it unprojected (Constraint 10).
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

**IAM:** `ec2:DescribeVolumes`, `ec2:DescribeSnapshots`, `ec2:DescribeImages`, `ec2:DescribeAddresses`, `ec2:DescribeNatGateways`, `cloudtrail:LookupEvents`, `elasticloadbalancing:DescribeLoadBalancers`, `s3:ListAllMyBuckets`, `s3:GetLifecycleConfiguration`, `lambda:ListFunctions`, `lambda:GetFunctionConcurrency`, `lambda:ListEventSourceMappings`, `dynamodb:ListTables`, `dynamodb:DescribeTable`, `eks:ListClusters`, `eks:ListNodegroups`, `eks:DescribeNodegroup`, `kinesis:ListStreams`, `kinesis:DescribeStreamSummary`, `kinesis:ListStreamConsumers`.
**API cost:** none.

### Untagged spend

```bash
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity MONTHLY \
  --metrics AmortizedCost \
  --filter '{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage","DiscountedUsage","SavingsPlanCoveredUsage"]}}' \
  --group-by Type=TAG,Key=<tag-key>
```

`<tag-key>` is the team's own key (catalog or operator-confirmed; `aws ce list-cost-allocation-tags --status Active` lists the options). Resources missing the tag appear under the key `<tag-key>$` (nothing after the `$`). The tag must be activated as a cost-allocation tag to appear at all. The skill flags these as "untagged spend" under Informational — never as "waste".

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per page.

### Commitment coverage for candidates (Principle 4 — realizable)

Same `ce get-savings-plans-coverage` / `ce get-reservation-coverage` calls as anomaly mode, filtered to the services carrying rightsize / delete candidates. Savings Plans coverage groups only by `INSTANCE_FAMILY`, `REGION` or `SERVICE`; RI coverage can group by `INSTANCE_TYPE` (CLI help). Any coverage → the row's `Realizable` is `covered until <end>` and it leaves the totals (a freed Savings Plan commitment can be absorbed by other usage, so it is an owner decision, not a $0 verdict); no coverage fetched → `unknown`, also out of the totals; fetched and none → `yes`.

### Utilization metrics (required for activity verification)

**Required (not optional)** per Principle 1 for any rightsize / idle-resource candidate whose resource type has an activity dimension. Exempt only when the resource type has no activity dimension at all (unattached EBS, unallocated EIP, orphaned snapshot — attachment state alone is sufficient evidence).

**Mechanics for every query below:**
- Run in the resource's region (`--region <r>`, from its ARN or the sweep region).
- `--period 3600` (hourly, Principle 3). CloudWatch returns at most **1,440 datapoints per call**: 60 days hourly is the ceiling, so a 60–180d delete window is split into ≤ 60-day calls.
- **Existence check in the same batch.** `Datapoints: []` is also what a wrong region / namespace / dimension / account returns. Pair each metric with:
  ```bash
  aws cloudwatch list-metrics --region <r> --namespace <ns> --metric-name <name> \
    --dimensions Name=<dim>,Value=<value>
  ```
  Metric listed + empty series → genuinely zero. Metric not listed → `UNVERIFIED`, never "idle".

```bash
# EC2 — 30d hourly CPU per instance (memory needs the CloudWatch agent: CWAgent mem_used_percent)
aws cloudwatch get-metric-statistics --region <r> \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average,Maximum

# NAT Gateway — hourly bytes, both directions (Principle 1 activity signal)
for metric in BytesOutToDestination BytesInFromSource; do
  aws cloudwatch get-metric-statistics --region <r> \
    --namespace AWS/NATGateway --metric-name $metric \
    --dimensions Name=NatGatewayId,Value=<nat-id> \
    --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 --statistics Sum
done
# Sum == 0 (metric listed) → idle. Route-table attachment count is NOT this signal.

# Lambda — hourly invocations (30d catches monthly-cron functions; delete needs 60–180d)
aws cloudwatch get-metric-statistics --region <r> \
  --namespace AWS/Lambda --metric-name Invocations \
  --dimensions Name=FunctionName,Value=<function-name> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Sum
# Do NOT subtract ProvisionedConcurrencyInvocations: those are real invocations
# served by provisioned concurrency, not keep-warm pings. Keep-alive noise is
# identified only by its uniform, workload-independent cadence (Principle 1 rule 3).

# Load balancers — activity metric depends on the type
#   ALB: AWS/ApplicationELB RequestCount, Name=LoadBalancer,Value=app/<name>/<id>
#   NLB: AWS/NetworkELB NewFlowCount (+ ProcessedBytes), Name=LoadBalancer,Value=net/<name>/<id>
#   CLB: AWS/ELB RequestCount, Name=LoadBalancerName,Value=<name>
aws cloudwatch get-metric-statistics --region <r> \
  --namespace AWS/ApplicationELB --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/<name>/<id> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Sum

# DynamoDB — 30d consumed vs provisioned capacity (provisioned mode)
# Principle 2: mode-switch savings claim requires both sides of this math.
for metric in ConsumedReadCapacityUnits ConsumedWriteCapacityUnits ProvisionedReadCapacityUnits ProvisionedWriteCapacityUnits ReadThrottleEvents WriteThrottleEvents; do
  aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB --metric-name $metric \
    --dimensions Name=TableName,Value=<table-name> \
    --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 --statistics Sum,Maximum
done
# Throttle events > 0 → table is under-provisioned, NOT a rightsize candidate.

# RDS / Aurora — the BINDING CONSTRAINT is memory/connections, not CPU (Principle 3).
# CPU can read low on a DB that cannot be downsized. Pull all three over ≥30d hourly:
for metric in CPUUtilization FreeableMemory DatabaseConnections; do
  aws cloudwatch get-metric-statistics \
    --namespace AWS/RDS --metric-name $metric \
    --dimensions Name=DBInstanceIdentifier,Value=<db-id> \
    --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 --statistics Average,Minimum,Maximum
done
# Worked case: writer at 12% avg CPU but only ~1.7 GB FreeableMemory of 16 GB and
# rising DatabaseConnections → memory-bound, NOT downsizeable. Compute Optimizer
# "Optimized" was right; the low-CPU line-item instinct was wrong.

# EKS nodegroup — Container Insights CPU/memory (cluster-side activity).
# Container Insights must be enabled. Its dimension sets vary by agent version —
# discover them first instead of assuming (an unpublished dimension set returns []):
aws cloudwatch list-metrics --region <r> \
  --namespace ContainerInsights --metric-name node_cpu_utilization \
  --dimensions Name=ClusterName,Value=<cluster>
# Then query with a dimension set list-metrics actually returned, e.g.:
aws cloudwatch get-metric-statistics --region <r> \
  --namespace ContainerInsights --metric-name node_cpu_utilization \
  --dimensions Name=ClusterName,Value=<cluster> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average,Maximum
# Repeat for node_memory_utilization. Measure the DaemonSet baseline from the data
# (or the allocation API, examples/kubernetes.md) rather than assuming a fixed figure.
# Nodes in a nodegroup / Karpenter NodePool: the group's scaling config is the change
# target, not an instance.

# Kinesis — 30d producer + consumer activity
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis --metric-name IncomingRecords \
  --dimensions Name=StreamName,Value=<stream-name> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Sum
# Repeat for IncomingBytes, GetRecords.Records, WriteProvisionedThroughputExceeded.
# Throttles > 0 → stream is under-provisioned, NOT a delete candidate.
# Registered EFO consumers / Lambda mappings are attachment, NOT activity.
```

**IAM:** `cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics`.
**API cost:** CloudWatch API pricing changes — check the CloudWatch pricing page before quoting. `GetMetricStatistics` / `ListMetrics` have historically fallen under the free API-request allowance; `GetMetricData` is billed per metric requested. The skill prefers `GetMetricStatistics` for batch utilization.

**Principle 2 cost-direction reminder:** for DynamoDB and Kinesis, any savings claim involving a billing-mode switch (provisioned ↔ on-demand) MUST compute the delta from observed throughput × current-region real pricing for both modes. Bare "switch to on-demand to save" is rejected — the cheaper mode flips with workload shape (steady → provisioned; spiky / low-baseline → on-demand). Fetch live pricing via `aws pricing get-products` rather than hardcoding.

## Step 2C — Attribution mode

### Cost filtered by tag

```bash
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity MONTHLY \
  --metrics AmortizedCost \
  --filter '{"And":[{"Tags":{"Key":"<tag-key>","Values":["<service-name>"]}},{"Dimensions":{"Key":"RECORD_TYPE","Values":["Usage","DiscountedUsage","SavingsPlanCoveredUsage"]}}]}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
# Check the key's activation first (aws ce list-cost-allocation-tags --tag-keys <tag-key>,
# LastUpdatedDate): a period before activation is UNVERIFIED, and so is a trend across it.
# In a payer account add the LINKED_ACCOUNT filter inside the And (see top of file).
```

**IAM:** `ce:GetCostAndUsage`.
**API cost:** $0.01 per page.

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
**API cost:** $0.01 per page.

## Step 5 — Verification (shared)

No mutation occurs, so verification is just re-reading the report file before commit:

```bash
# Operator inspects the report draft
cat .culiops/cloud-cost-investigate/<scope-slug>-<mode>-<YYYYMMDD-HHmm>.md
```

## Iron Law reminders

- These commands are read-only by name. The skill MUST refuse if the operator asks for any `terminate`, `delete`, `modify`, `update`, `purchase`, `put`, `create` API.
- Cost Explorer bills $0.01 per request and every paginated page is a request (no free tier). The query plan presented at GATE 2 must include estimated pages × $0.01.
- Describe calls whose full response can carry secrets (`lambda list-functions` / `get-function`, `ecs describe-task-definition`) run only with a `--query` projection that excludes environment / secrets fields. Raw output never goes into the report.
- Compute Optimizer is enabled per-organization. If `compute-optimizer get-*` returns "OptInRequired", the skill stops and tells the operator to opt in (operator action, not skill action).
