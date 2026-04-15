# Examples: AWS CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the discovered stack is AWS. The skill reads this file when Step 1 detects AWS resources.

Replace placeholders (`{cluster}`, `{service}`, `{function}`, `{T-1h}`, `{now}`, etc.) with the values resolved in Step 2. Only the placeholders the repo actually uses should appear in the rendered runbook — see the SKILL.md section on placeholder taxonomy.

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` ≥ 2.x). v1 still works for most calls but is deprecated.

**Authentication:** any of — a named profile (`aws configure`, selected via `--profile` or `AWS_PROFILE`), AWS SSO (`aws sso login`), IAM role on EC2 / ECS / EKS / Lambda, or temporary credentials from STS. Before running anything, confirm the active identity: `aws sts get-caller-identity`.

**Least-privilege IAM — every command below is read-only.** Grant the operator either:

- **Baseline (simplest):** the AWS-managed `ReadOnlyAccess` policy. Broad but covers everything here.
- **Tighter (recommended):** a scoped custom policy allowing only `Describe*`, `List*`, `Get*` on the resource types in the catalog, plus `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `logs:FilterLogEvents`, `logs:DescribeLogGroups`, `logs:GetLogEvents`. Grant `s3:GetObject` + `s3:ListBucket` **only on the specific buckets** the runbooks actually reference (e.g., CloudFront / ALB log buckets) — S3 access should never be account-wide.
- **Never use `PowerUserAccess`, `AdministratorAccess`, or any `*:*` policy** for read-only investigation. If a runbook step needs write access, that step is a mutation and is labeled as such (see below).

**Mutations are flagged inline.** Most commands in this file are read-only. A few change state (e.g., CloudFront invalidation, SQS `receive-message` with `VisibilityTimeout=0`, any `*:put-*` / `*:update-*` / `*:delete-*`). Mutations are labeled explicitly where they appear. **Never run a mutation without explicit team approval and an elevated (non-read-only) role.**

**Cost awareness:** CloudWatch `GetMetric*` and `logs:FilterLogEvents` incur small per-call and per-GB-scanned charges. S3 access log downloads can be gigabytes per day and incur data-transfer charges — prefer CloudWatch metrics first and confirm before pulling logs.

---

## How to use this file

Each section below maps one AWS resource category to: a status/config check, plus the four golden signals (latency / traffic / errors / saturation) where applicable. Use these as the *concrete CLI realization* of the investigation-tree steps in the runbook — the runbook itself stays generic.

If you need logs in S3 (CloudFront access logs, ALB access logs, VPC flow logs), **always warn the human about data transfer costs before downloading**. Prefer CloudWatch metrics first.

---

## ECS

- Service status: `aws ecs describe-services --cluster {cluster} --services {service}`
- Running tasks: `aws ecs list-tasks --cluster {cluster} --service-name {service}`
- Recent deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments'`
- Stopped tasks (recent): `aws ecs list-tasks --cluster {cluster} --desired-status STOPPED`
- Task details: `aws ecs describe-tasks --cluster {cluster} --tasks {task-arn}`
- Task CPU / memory: `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`

## ALB / Application Load Balancer

- Target health: `aws elbv2 describe-target-health --target-group-arn {tg-arn}`
- Target group details: `aws elbv2 describe-target-groups --target-group-arns {tg-arn}`
- Latency (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value={alb-id} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99`
- 5xx count (target): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_Target_5XX_Count --dimensions Name=LoadBalancer,Value={alb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- 5xx count (ELB itself): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value={alb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Active connection count: `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name ActiveConnectionCount --dimensions Name=LoadBalancer,Value={alb-id} --start-time {T-1h} --end-time {now} --period 60 --statistics Sum`

## RDS / Aurora

- Cluster status: `aws rds describe-db-clusters --db-cluster-identifier {cluster}`
- Instance status: `aws rds describe-db-instances --filters Name=db-cluster-id,Values={cluster}`
- Recent events: `aws rds describe-events --source-identifier {cluster} --source-type db-cluster --duration 60`
- CPU: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name CPUUtilization --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Connections: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name DatabaseConnections --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Read latency: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name ReadLatency --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Write latency: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name WriteLatency --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Replica lag: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name AuroraReplicaLag --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 60 --statistics Maximum`

## ElastiCache (Redis / Memcached)

- Cluster status: `aws elasticache describe-replication-groups --replication-group-id {cluster}`
- CPU (engine): `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name EngineCPUUtilization --dimensions Name=ReplicationGroupId,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Freeable memory: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name FreeableMemory --dimensions Name=ReplicationGroupId,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Evictions: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name Evictions --dimensions Name=ReplicationGroupId,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Cache hits / misses: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name CacheHits --dimensions Name=ReplicationGroupId,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`

## Lambda

- Function config: `aws lambda get-function --function-name {function}`
- Errors: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Duration (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99`
- Invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Throttles: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Concurrent executions: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name ConcurrentExecutions --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 60 --statistics Maximum`
- Recent error logs: `aws logs filter-log-events --log-group-name /aws/lambda/{function} --start-time {T-15m-epoch-ms} --filter-pattern "ERROR"`

## SQS

- Queue attributes: `aws sqs get-queue-attributes --queue-url {queue-url} --attribute-names All`
- Messages visible: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateNumberOfMessagesVisible --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Age of oldest message: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum`
- DLQ depth: `aws sqs get-queue-attributes --queue-url {dlq-url} --attribute-names ApproximateNumberOfMessages`
- Peek at messages (non-destructive with `VisibilityTimeout=0` is NOT safe — always confirm with human before using `receive-message`).

## SNS

- Topic attributes: `aws sns get-topic-attributes --topic-arn {topic-arn}`
- Subscriptions: `aws sns list-subscriptions-by-topic --topic-arn {topic-arn}`
- Delivery failures: `aws cloudwatch get-metric-statistics --namespace AWS/SNS --metric-name NumberOfNotificationsFailed --dimensions Name=TopicName,Value={topic} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`

## Auto Scaling Group

- ASG status: `aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names {asg}`
- Scaling activities (recent): `aws autoscaling describe-scaling-activities --auto-scaling-group-name {asg} --max-items 10`
- Instance health: `aws autoscaling describe-auto-scaling-instances --query 'AutoScalingInstances[?AutoScalingGroupName==\`{asg}\`]'`

## AWS Batch

- Job queue status: `aws batch describe-job-queues --job-queues {queue}`
- Compute env status: `aws batch describe-compute-environments --compute-environments {env}`
- Failed jobs: `aws batch list-jobs --job-queue {queue} --job-status FAILED`
- Running jobs: `aws batch list-jobs --job-queue {queue} --job-status RUNNING`

## EventBridge / CloudWatch Events

- List rules: `aws events list-rules --name-prefix {prefix}`
- Rule targets: `aws events list-targets-by-rule --rule {rule-name}`
- Rule invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name Invocations --dimensions Name=RuleName,Value={rule-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Failed invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name FailedInvocations --dimensions Name=RuleName,Value={rule-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`

## API Gateway

- REST API status: `aws apigateway get-rest-api --rest-api-id {api-id}`
- HTTP API status: `aws apigatewayv2 get-api --api-id {api-id}`
- 4xx / 5xx counts: `aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name 5XXError --dimensions Name=ApiName,Value={api-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Latency (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name Latency --dimensions Name=ApiName,Value={api-name} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99`

## CloudFront

- Distribution details: `aws cloudfront get-distribution --id {distribution-id}`
- Distribution config: `aws cloudfront get-distribution-config --id {distribution-id}`
- Request count: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name Requests --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- 5xx error rate: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name 5xxErrorRate --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Origin latency: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name OriginLatency --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Cache hit rate: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name CacheHitRate --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average`
- Invalidations: `aws cloudfront list-invalidations --distribution-id {distribution-id} --max-items 10`
- **Access logs in S3:** `aws s3 ls s3://{cf-logs-bucket}/{cf-logs-prefix}/ --recursive | tail -20` — **WARNING: access logs can be very large. Confirm with human before downloading; data transfer costs apply. Prefer CloudWatch metrics first.**

## WAF v2

- Web ACL details: `aws wafv2 get-web-acl --name {waf-name} --scope REGIONAL --id {waf-id}`
- Sampled requests: `aws wafv2 get-sampled-requests --web-acl-arn {waf-arn} --rule-metric-name {rule-metric} --scope REGIONAL --time-window StartTime={T-1h},EndTime={now} --max-items 100`
- Blocked requests: `aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name BlockedRequests --dimensions Name=WebACL,Value={waf-name} Name=Region,Value={region} Name=Rule,Value=ALL --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Allowed requests: `aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name AllowedRequests --dimensions Name=WebACL,Value={waf-name} Name=Region,Value={region} Name=Rule,Value=ALL --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Rate-based matches: `aws wafv2 get-rate-based-statement-managed-keys --scope REGIONAL --web-acl-name {waf-name} --web-acl-id {waf-id} --rule-name {rate-rule}`
- Logging config: `aws wafv2 get-logging-configuration --resource-arn {waf-arn}`

## S3

- Bucket details: `aws s3api get-bucket-location --bucket {bucket}` / `aws s3api get-bucket-policy --bucket {bucket}` / `aws s3api get-bucket-versioning --bucket {bucket}`
- Object count (approximate, via CloudWatch): `aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name NumberOfObjects --dimensions Name=BucketName,Value={bucket} Name=StorageType,Value=AllStorageTypes --start-time {T-1d} --end-time {now} --period 86400 --statistics Average`
- Bucket size: `aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name BucketSizeBytes --dimensions Name=BucketName,Value={bucket} Name=StorageType,Value=StandardStorage --start-time {T-1d} --end-time {now} --period 86400 --statistics Average`

## DynamoDB

- Table status: `aws dynamodb describe-table --table-name {table}`
- Consumed read/write capacity: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedReadCapacityUnits --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 60 --statistics Sum`
- Throttled requests: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ThrottledRequests --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- System errors: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name SystemErrors --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`

## Kinesis Data Streams

- Stream status: `aws kinesis describe-stream --stream-name {stream}`
- Incoming records: `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`
- Iterator age (p99): `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.IteratorAgeMilliseconds --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p99`
- Read/write throttling: `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name WriteProvisionedThroughputExceeded --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum`

## Third-party services on AWS

For third-party services integrated into the stack (bot defenders, CDN edge functions, managed APM/logging vendors, feature-flag services), ask the human:
- Whether the service uses it and how it's integrated (Lambda@Edge, ALB header inspection, DNS routing, sidecar agent, etc.).
- Where its logs and metrics live (vendor dashboard URL, CloudWatch log group, S3 bucket).

For Lambda@Edge integrations, region is `us-east-1` regardless of origin region:
- `aws logs filter-log-events --log-group-name /aws/lambda/us-east-1.{edge-function} --start-time {T-15m-epoch-ms} --filter-pattern "ERROR"`

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{cluster}`, `{service}`, `{function}`, `{queue}`, `{table}`, `{stream}`, `{bucket}` | Resource identifiers | `widgetapi-prod-eu-web` |
| `{tg-arn}`, `{alb-id}`, `{topic-arn}`, `{queue-url}`, `{distribution-id}`, `{waf-arn}` | AWS identifiers (ARN or ID) | See the resource in the catalog |
| `{region}` | AWS region | `eu-west-1` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{T-15m-epoch-ms}` | 15 minutes ago in epoch milliseconds (for `aws logs filter-log-events`) | `1744707600000` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
