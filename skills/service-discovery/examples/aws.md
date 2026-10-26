# Examples: AWS CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the discovered stack is AWS. The skill reads this file when Step 1 detects AWS resources.

Replace placeholders (`{cluster}`, `{service}`, `{function}`, `{profile}`, `{region}`, `{T-1h}`, `{now}`, etc.) with the values resolved in Step 2. Only the placeholders the repo actually uses should appear in the rendered runbook — see the SKILL.md section on placeholder taxonomy.

## Two uses of these commands

This file serves two different purposes. Do not mix them.

- **(a) Commands the skill itself runs** during discovery and enrichment. Their output can reach the catalog, so each one is **projected**: an explicit `--query` JMESPath allowlist of metadata fields. Projected commands never return environment variables, secret values, presigned URLs, header values or request payloads. These are the commands in the main bullets below.
- **(b) On-call terminal commands** for runbooks. A command that can print secrets or PII may appear only under (b), labelled **terminal only — never paste output into a catalog, ticket or chat**. The skill never runs these for enrichment.

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` ≥ 2.x). v1 still works for most calls but is deprecated.

**Authentication:** any of — a named profile (`aws configure`, selected via `--profile` or `AWS_PROFILE`), AWS SSO (`aws sso login`), IAM role on EC2 / ECS / EKS / Lambda, or temporary credentials from STS.

**Identity pinning.** Every command below carries `--profile {profile} --region {region}`; global services (CloudFront, WAF `CLOUDFRONT` scope, IAM, Route 53) use `--region us-east-1`. Before each batch, re-run the identity check and abort if the account differs from the target the operator confirmed:

```
aws sts get-caller-identity --profile {profile} --query Account --output text
```

`sts get-caller-identity` does not return a region. Show the region the batch will use from `aws configure get region --profile {profile}` (or `AWS_REGION` / `AWS_DEFAULT_REGION`).

**Least-privilege IAM — every command below is read-only.** Grant the operator either:

- **Baseline (simplest):** the AWS-managed `ReadOnlyAccess` policy. Broad but covers everything here.
- **Tighter (recommended):** a scoped custom policy allowing only `Describe*`, `List*`, `Get*` on the resource types in the catalog, plus `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `cloudwatch:ListMetrics`, `logs:FilterLogEvents`, `logs:DescribeLogGroups`, `logs:GetLogEvents`. Grant `s3:GetObject` + `s3:ListBucket` **only on the specific buckets** the runbooks actually reference (e.g., CloudFront / ALB log buckets) — S3 access should never be account-wide.
- **Never use `PowerUserAccess`, `AdministratorAccess`, or any `*:*` policy** for read-only investigation. If a runbook step needs write access, that step is a mutation and is labeled as such (see below).

**Mutations are flagged inline.** Most commands in this file are read-only. A few change state (e.g., CloudFront invalidation, SQS `receive-message` with `VisibilityTimeout=0`, any `*:put-*` / `*:update-*` / `*:delete-*`). Mutations are labeled explicitly where they appear. **Never run a mutation without explicit team approval and an elevated (non-read-only) role.**

**Cost awareness:** CloudWatch `GetMetric*` and `logs:FilterLogEvents` incur small per-call and per-GB-scanned charges. S3 access log downloads can be gigabytes per day and incur data-transfer charges — prefer CloudWatch metrics first and confirm before pulling logs.

---

## How to use this file

Each section below maps one AWS resource category to: a status/config check, plus the four golden signals (latency / traffic / errors / saturation) where applicable. Use these as the *concrete CLI realization* of the investigation-tree steps in the runbook — the runbook itself stays generic.

If you need logs in S3 (CloudFront access logs, ALB access logs, VPC flow logs), **always warn the human about data transfer costs before downloading**. Prefer CloudWatch metrics first.

**Reading metrics.** An empty `Datapoints` array means **"no data"**, not "zero" and not "healthy". Wrong dimension values, the wrong region (CloudFront metrics live in `us-east-1`), or a metric that was never emitted all return an empty array. Before concluding anything from an empty result, check what exists with the same namespace, metric and dimensions:

```
aws cloudwatch list-metrics --namespace {namespace-cw} --metric-name {metric} --dimensions Name={dim-name},Value={dim-value} --profile {profile} --region {region}
```

If `list-metrics` returns nothing, the dimensions or region are wrong; if it returns the metric, widen the time window or period before reading the series as quiet. Record such a series as `no data`.

---

## ECS

- Service status: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].{Name:serviceName,Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,TaskDef:taskDefinition,Launch:launchType}' --profile {profile} --region {region}`
- Running tasks: `aws ecs list-tasks --cluster {cluster} --service-name {service} --profile {profile} --region {region}`
- Recent deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments[].{Id:id,Status:status,Rollout:rolloutState,Desired:desiredCount,Running:runningCount,TaskDef:taskDefinition,Updated:updatedAt}' --profile {profile} --region {region}`
- Stopped tasks (recent): `aws ecs list-tasks --cluster {cluster} --service-name {service} --desired-status STOPPED --profile {profile} --region {region}`
- Task details (projected; omits `overrides`, which can carry environment values): `aws ecs describe-tasks --cluster {cluster} --tasks {task-arn} --query 'tasks[].{Arn:taskArn,Status:lastStatus,Desired:desiredStatus,Health:healthStatus,TaskDef:taskDefinitionArn,Started:startedAt,Stopped:stoppedAt,StopCode:stopCode,StoppedReason:stoppedReason,Containers:containers[].{Name:name,Status:lastStatus,Exit:exitCode,Reason:reason}}' --profile {profile} --region {region}`
- Task definition (projected; environment variable **names** only, secrets as name + `valueFrom` ARN only, never values): `aws ecs describe-task-definition --task-definition {taskdef} --query 'taskDefinition.{Family:family,Revision:revision,Cpu:cpu,Memory:memory,TaskRole:taskRoleArn,ExecRole:executionRoleArn,Containers:containerDefinitions[].{Name:name,Image:image,Cpu:cpu,Memory:memory,Ports:portMappings[].containerPort,EnvNames:environment[].name,SecretRefs:secrets[].{Name:name,ValueFrom:valueFrom}}}' --profile {profile} --region {region}`
- Task CPU / memory: `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`

Never run un-projected `describe-task-definition` or `describe-tasks` for enrichment: the full documents contain `environment` values and `overrides`.

## EKS (Elastic Kubernetes Service)

Requires `kubectl` in addition to the AWS CLI. Catalog compilation needs `eks:Describe*` and `eks:List*`; in-cluster reads additionally need Kubernetes RBAC permission (e.g., a `ClusterRole` like `view` bound to the caller's IAM principal via an EKS access entry or the legacy `aws-auth` ConfigMap). Every `kubectl` command carries `--context {context}`; re-run `kubectl config current-context` before each batch and abort if it differs from the confirmed target. For in-cluster detail, use `examples/kubernetes.md`.

- Cluster status: `aws eks describe-cluster --name {cluster} --query 'cluster.{Name:name,Status:status,Version:version,PlatformVersion:platformVersion,Endpoint:endpoint,AuthMode:accessConfig.authenticationMode,Logging:logging.clusterLogging}' --profile {profile} --region {region}`
- Node groups: `aws eks list-nodegroups --cluster-name {cluster} --profile {profile} --region {region}`
- Node group details: `aws eks describe-nodegroup --cluster-name {cluster} --nodegroup-name {nodegroup} --query 'nodegroup.{Name:nodegroupName,Status:status,Ami:amiType,InstanceTypes:instanceTypes,Scaling:scalingConfig,Version:version}' --profile {profile} --region {region}`
- Fargate profiles (if used): `aws eks list-fargate-profiles --cluster-name {cluster} --profile {profile} --region {region}`
- Addons: `aws eks list-addons --cluster-name {cluster} --profile {profile} --region {region}`
- Access entries (who can reach the cluster; newer model): `aws eks list-access-entries --cluster-name {cluster} --profile {profile} --region {region}` — the legacy model is the `aws-auth` ConfigMap in `kube-system`; check both
- Credentials for kubectl (writes the local kubeconfig; not a cluster mutation): `aws eks update-kubeconfig --name {cluster} --profile {profile} --region {region}`
- Workloads: `kubectl --context {context} get deploy -n {namespace}`; detail via the projected jsonpath in `examples/kubernetes.md` (`describe` is terminal only)
- Pod status: `kubectl --context {context} get pods -n {namespace} -l app={service}`
- Pod CPU / memory: `kubectl --context {context} top pods -n {namespace}` (requires metrics-server)
- Cluster events (recent): `kubectl --context {context} get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`
- Control-plane logs (if enabled): CloudWatch Logs group `/aws/eks/{cluster}/cluster` — **terminal only — never paste output into a catalog, ticket or chat** (audit logs can contain request bodies): `aws logs tail /aws/eks/{cluster}/cluster --since 15m --profile {profile} --region {region}`
- Container Insights (if enabled): CloudWatch namespace `ContainerInsights`, metrics like `pod_cpu_utilization`, `pod_memory_utilization`, `node_cpu_utilization`

## ALB / Application Load Balancer

The CloudWatch `LoadBalancer` dimension value is `app/<name>/<id>`: the part of the load balancer ARN **after** `loadbalancer/`. For `arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/app/widgetapi-alb/50dc6c495c0c9188` use `{alb-dim}` = `app/widgetapi-alb/50dc6c495c0c9188`. (Network load balancers use `net/<name>/<id>`.)

- Load balancer details: `aws elbv2 describe-load-balancers --load-balancer-arns {alb-arn} --query 'LoadBalancers[].{Name:LoadBalancerName,State:State.Code,Scheme:Scheme,Type:Type,DNS:DNSName}' --profile {profile} --region {region}`
- Target health: `aws elbv2 describe-target-health --target-group-arn {tg-arn} --query 'TargetHealthDescriptions[].{Target:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' --profile {profile} --region {region}`
- Target group details: `aws elbv2 describe-target-groups --target-group-arns {tg-arn} --query 'TargetGroups[].{Name:TargetGroupName,Protocol:Protocol,Port:Port,HealthPath:HealthCheckPath,TargetType:TargetType}' --profile {profile} --region {region}`
- Latency (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value={alb-dim} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99 --profile {profile} --region {region}`
- 5xx count (target): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_Target_5XX_Count --dimensions Name=LoadBalancer,Value={alb-dim} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- 5xx count (ELB itself): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value={alb-dim} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Active connection count: `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name ActiveConnectionCount --dimensions Name=LoadBalancer,Value={alb-dim} --start-time {T-1h} --end-time {now} --period 60 --statistics Sum --profile {profile} --region {region}`

## RDS / Aurora

- Cluster status: `aws rds describe-db-clusters --db-cluster-identifier {cluster} --query 'DBClusters[].{Id:DBClusterIdentifier,Status:Status,Engine:Engine,Version:EngineVersion,MultiAZ:MultiAZ,Endpoint:Endpoint,Members:DBClusterMembers[].{Id:DBInstanceIdentifier,Writer:IsClusterWriter}}' --profile {profile} --region {region}`
- Instance status: `aws rds describe-db-instances --filters Name=db-cluster-id,Values={cluster} --query 'DBInstances[].{Id:DBInstanceIdentifier,Class:DBInstanceClass,Status:DBInstanceStatus,Engine:Engine,AZ:AvailabilityZone}' --profile {profile} --region {region}`
- Recent events: `aws rds describe-events --source-identifier {cluster} --source-type db-cluster --duration 60 --query 'Events[].{Time:Date,Message:Message}' --profile {profile} --region {region}`
- CPU: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name CPUUtilization --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Connections: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name DatabaseConnections --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Read latency: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name ReadLatency --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Write latency: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name WriteLatency --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Replica lag: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name AuroraReplicaLag --dimensions Name=DBClusterIdentifier,Value={cluster} --start-time {T-1h} --end-time {now} --period 60 --statistics Maximum --profile {profile} --region {region}`

(The projections above deliberately omit the master username and similar account fields.)

## ElastiCache (Redis / Memcached)

`describe-replication-groups` only covers Redis/Valkey replication groups. Memcached clusters and standalone Redis nodes appear only in `describe-cache-clusters`; run both.

- Replication group status: `aws elasticache describe-replication-groups --replication-group-id {cluster} --query 'ReplicationGroups[].{Id:ReplicationGroupId,Status:Status,Members:MemberClusters,MultiAZ:MultiAZ,Failover:AutomaticFailover}' --profile {profile} --region {region}`
- Cache clusters (Memcached, standalone, and the member nodes of a replication group): `aws elasticache describe-cache-clusters --query 'CacheClusters[].{Id:CacheClusterId,Engine:Engine,Version:EngineVersion,Status:CacheClusterStatus,NodeType:CacheNodeType,Nodes:NumCacheNodes,ReplicationGroup:ReplicationGroupId}' --profile {profile} --region {region}`

CloudWatch dimensions are per `CacheClusterId` (one per node for replication-group members, e.g. `{cluster}-001`). UNVERIFIED: a `ReplicationGroupId` dimension on these metrics. Verify with `aws cloudwatch list-metrics --namespace AWS/ElastiCache --dimensions Name=CacheClusterId,Value={cache-cluster-id} --profile {profile} --region {region}` before relying on any series; an empty `Datapoints` array is "no data" (see "Reading metrics").

- CPU (engine): `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name EngineCPUUtilization --dimensions Name=CacheClusterId,Value={cache-cluster-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Freeable memory: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name FreeableMemory --dimensions Name=CacheClusterId,Value={cache-cluster-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Evictions: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name Evictions --dimensions Name=CacheClusterId,Value={cache-cluster-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Cache hits / misses: `aws cloudwatch get-metric-statistics --namespace AWS/ElastiCache --metric-name CacheHits --dimensions Name=CacheClusterId,Value={cache-cluster-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`

## Lambda

- Function config (projected; **never** `get-function`, which returns `Environment` and a presigned `Code.Location` URL; never `Environment` in a `--query`): `aws lambda get-function-configuration --function-name {function} --query '{Name:FunctionName,Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,Role:Role,Vpc:VpcConfig,LastModified:LastModified}' --profile {profile} --region {region}`
- Errors: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Duration (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99 --profile {profile} --region {region}`
- Invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Throttles: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Concurrent executions: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name ConcurrentExecutions --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 60 --statistics Maximum --profile {profile} --region {region}`
- Recent error logs — **terminal only — never paste output into a catalog, ticket or chat** (log lines can contain secrets and PII): `aws logs filter-log-events --log-group-name /aws/lambda/{function} --start-time {T-15m-epoch-ms} --filter-pattern "ERROR" --profile {profile} --region {region}`

## SQS

- Queue attributes (explicit list; never `All`): `aws sqs get-queue-attributes --queue-url {queue-url} --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible ApproximateNumberOfMessagesDelayed VisibilityTimeout MessageRetentionPeriod DelaySeconds RedrivePolicy --profile {profile} --region {region}`
- Messages visible: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateNumberOfMessagesVisible --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region {region}`
- Age of oldest message: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --profile {profile} --region {region}`
- DLQ depth: `aws sqs get-queue-attributes --queue-url {dlq-url} --attribute-names ApproximateNumberOfMessages --profile {profile} --region {region}`
- Peek at messages (non-destructive with `VisibilityTimeout=0` is NOT safe — always confirm with human before using `receive-message`; message bodies can contain secrets and PII, **terminal only**).

## SNS

- Topic attributes (projected): `aws sns get-topic-attributes --topic-arn {topic-arn} --query 'Attributes.{Owner:Owner,Display:DisplayName,Confirmed:SubscriptionsConfirmed,Pending:SubscriptionsPending,Fifo:FifoTopic}' --profile {profile} --region {region}`
- Subscriptions (protocol and ARN only; the endpoint is left out because webhook URLs can embed tokens): `aws sns list-subscriptions-by-topic --topic-arn {topic-arn} --query 'Subscriptions[].{Protocol:Protocol,Subscription:SubscriptionArn}' --profile {profile} --region {region}`
- Subscription endpoints — **terminal only — never paste output into a catalog, ticket or chat** (HTTP/S endpoints and e-mail addresses; webhook URLs can embed tokens): `aws sns list-subscriptions-by-topic --topic-arn {topic-arn} --query 'Subscriptions[].{Protocol:Protocol,Endpoint:Endpoint}' --profile {profile} --region {region}`
- Delivery failures: `aws cloudwatch get-metric-statistics --namespace AWS/SNS --metric-name NumberOfNotificationsFailed --dimensions Name=TopicName,Value={topic} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`

## Auto Scaling Group

- ASG status: `aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names {asg} --query 'AutoScalingGroups[].{Name:AutoScalingGroupName,Min:MinSize,Max:MaxSize,Desired:DesiredCapacity,Health:HealthCheckType}' --profile {profile} --region {region}`
- Scaling activities (recent): `aws autoscaling describe-scaling-activities --auto-scaling-group-name {asg} --max-items 10 --query 'Activities[].{Start:StartTime,Status:StatusCode,Cause:Cause}' --profile {profile} --region {region}`
- Instance health: `aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names {asg} --query 'AutoScalingGroups[0].Instances[].{Id:InstanceId,Health:HealthStatus,State:LifecycleState,AZ:AvailabilityZone}' --profile {profile} --region {region}`

## AWS Batch

- Job queue status: `aws batch describe-job-queues --job-queues {queue} --query 'jobQueues[].{Name:jobQueueName,State:state,Status:status,Priority:priority}' --profile {profile} --region {region}`
- Compute env status: `aws batch describe-compute-environments --compute-environments {env} --query 'computeEnvironments[].{Name:computeEnvironmentName,State:state,Status:status,Type:type}' --profile {profile} --region {region}`
- Failed jobs: `aws batch list-jobs --job-queue {queue} --job-status FAILED --query 'jobSummaryList[].{Id:jobId,Name:jobName,Reason:statusReason,Created:createdAt}' --profile {profile} --region {region}`
- Running jobs: `aws batch list-jobs --job-queue {queue} --job-status RUNNING --query 'jobSummaryList[].{Id:jobId,Name:jobName,Created:createdAt}' --profile {profile} --region {region}`

## EventBridge / CloudWatch Events

- List rules: `aws events list-rules --name-prefix {prefix} --query 'Rules[].{Name:Name,State:State,Schedule:ScheduleExpression}' --profile {profile} --region {region}`
- Rule targets (projected; omits `Input`, which can hold static payloads): `aws events list-targets-by-rule --rule {rule-name} --query 'Targets[].{Id:Id,Arn:Arn}' --profile {profile} --region {region}`
- Rule invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name Invocations --dimensions Name=RuleName,Value={rule-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Failed invocations: `aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name FailedInvocations --dimensions Name=RuleName,Value={rule-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`

## API Gateway

- REST API status: `aws apigateway get-rest-api --rest-api-id {api-id} --query '{Id:id,Name:name,Created:createdDate,Endpoint:endpointConfiguration.types}' --profile {profile} --region {region}`
- HTTP API status: `aws apigatewayv2 get-api --api-id {api-id} --query '{Id:ApiId,Name:Name,Protocol:ProtocolType,Endpoint:ApiEndpoint}' --profile {profile} --region {region}`
- 4xx / 5xx counts: `aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name 5XXError --dimensions Name=ApiName,Value={api-name} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Latency (p50/p99): `aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --metric-name Latency --dimensions Name=ApiName,Value={api-name} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p50 p99 --profile {profile} --region {region}`

## CloudFront

CloudFront is a global service: **every CloudFront and CloudFront-metric command uses `--region us-east-1`**. Metrics queried in any other region return an empty `Datapoints` array, which means "no data", not "0 errors".

- Distribution details (projected; omits `CustomHeaders`): `aws cloudfront get-distribution --id {distribution-id} --query 'Distribution.{Id:Id,Status:Status,Domain:DomainName,Aliases:DistributionConfig.Aliases.Items,Enabled:DistributionConfig.Enabled,Origins:DistributionConfig.Origins.Items[].{Id:Id,Domain:DomainName,Path:OriginPath}}' --profile {profile} --region us-east-1`
- Distribution config (projected; **never** the full output, because `Origins.Items[].CustomHeaders` holds origin auth header values that are shared secrets): `aws cloudfront get-distribution-config --id {distribution-id} --query 'DistributionConfig.{Aliases:Aliases.Items,Enabled:Enabled,WebACL:WebACLId,LoggingEnabled:Logging.Enabled,Origins:Origins.Items[].{Id:Id,Domain:DomainName,Path:OriginPath,Protocol:CustomOriginConfig.OriginProtocolPolicy}}' --profile {profile} --region us-east-1`
- Request count: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name Requests --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region us-east-1`
- 5xx error rate: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name 5xxErrorRate --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region us-east-1`
- Origin latency: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name OriginLatency --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region us-east-1`
- Cache hit rate: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name CacheHitRate --dimensions Name=DistributionId,Value={distribution-id} Name=Region,Value=Global --start-time {T-1h} --end-time {now} --period 300 --statistics Average --profile {profile} --region us-east-1`
- Invalidations: `aws cloudfront list-invalidations --distribution-id {distribution-id} --max-items 10 --profile {profile} --region us-east-1`
- **Access logs in S3:** `aws s3 ls s3://{cf-logs-bucket}/{cf-logs-prefix}/ --recursive --profile {profile} --region {region} | tail -20` — **WARNING: access logs can be very large. Confirm with human before downloading; data transfer costs apply. Prefer CloudWatch metrics first.** Access logs contain client IPs and URLs: **terminal only — never paste output into a catalog, ticket or chat**.

## WAF v2

Scope matters. A web ACL attached to an ALB / API Gateway / AppSync is `--scope REGIONAL` in the resource's region. A web ACL attached to CloudFront is `--scope CLOUDFRONT` and **must be called with `--region us-east-1`**. Use `{waf-scope}` and `{waf-region}` accordingly: `REGIONAL` + `{region}`, or `CLOUDFRONT` + `us-east-1`. A wrong scope or region returns nothing or a not-found error, which is not evidence the ACL is absent.

- Web ACL details (projected; omits rule `Statement`, which can hold header-match values that act as shared secrets): `aws wafv2 get-web-acl --name {waf-name} --scope {waf-scope} --id {waf-id} --query 'WebACL.{Name:Name,Id:Id,Capacity:Capacity,DefaultAction:DefaultAction,Rules:Rules[].{Name:Name,Priority:Priority,Action:Action,Override:OverrideAction,Metric:VisibilityConfig.MetricName}}' --profile {profile} --region {waf-region}`
- Sampled requests — **terminal only — never paste output into a catalog, ticket or chat** (client IPs, request headers incl. auth headers): `aws wafv2 get-sampled-requests --web-acl-arn {waf-arn} --rule-metric-name {rule-metric} --scope {waf-scope} --time-window StartTime={T-1h},EndTime={now} --max-items 100 --profile {profile} --region {waf-region}`
- Blocked requests (metric `Region` dimension is the region for `REGIONAL`, `Global` for `CLOUDFRONT`; CloudFront-scope metrics are in `us-east-1`): `aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name BlockedRequests --dimensions Name=WebACL,Value={waf-name} Name=Region,Value={waf-metric-region} Name=Rule,Value=ALL --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {waf-region}`
- Allowed requests: `aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name AllowedRequests --dimensions Name=WebACL,Value={waf-name} Name=Region,Value={waf-metric-region} Name=Rule,Value=ALL --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {waf-region}`
- Rate-based matches — **terminal only — never paste output into a catalog, ticket or chat** (returns the client IPs currently rate-limited): `aws wafv2 get-rate-based-statement-managed-keys --scope {waf-scope} --web-acl-name {waf-name} --web-acl-id {waf-id} --rule-name {rate-rule} --profile {profile} --region {waf-region}`
- Logging config (destinations only): `aws wafv2 get-logging-configuration --resource-arn {waf-arn} --query 'LoggingConfiguration.LogDestinationConfigs' --profile {profile} --region {waf-region}`

## S3

CloudWatch S3 metrics are reported in the bucket's own region; use that region for `--region` on the metric calls (`{bucket-region}`, from `get-bucket-location`).

- Bucket location: `aws s3api get-bucket-location --bucket {bucket} --profile {profile} --region {region}`
- Bucket policy: `aws s3api get-bucket-policy --bucket {bucket} --profile {profile} --region {region}`
- Versioning: `aws s3api get-bucket-versioning --bucket {bucket} --profile {profile} --region {region}`
- Object count (approximate, via CloudWatch): `aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name NumberOfObjects --dimensions Name=BucketName,Value={bucket} Name=StorageType,Value=AllStorageTypes --start-time {T-1d} --end-time {now} --period 86400 --statistics Average --profile {profile} --region {region}`
- Bucket size: `aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name BucketSizeBytes --dimensions Name=BucketName,Value={bucket} Name=StorageType,Value=StandardStorage --start-time {T-1d} --end-time {now} --period 86400 --statistics Average --profile {profile} --region {region}`

## DynamoDB

- Table status: `aws dynamodb describe-table --table-name {table} --query 'Table.{Name:TableName,Status:TableStatus,Billing:BillingModeSummary.BillingMode,Rcu:ProvisionedThroughput.ReadCapacityUnits,Wcu:ProvisionedThroughput.WriteCapacityUnits,Items:ItemCount,Indexes:GlobalSecondaryIndexes[].IndexName}' --profile {profile} --region {region}`
- Consumed read/write capacity: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedReadCapacityUnits --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 60 --statistics Sum --profile {profile} --region {region}`
- Throttled requests: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ThrottledRequests --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- System errors: `aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name SystemErrors --dimensions Name=TableName,Value={table} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`

## Kinesis Data Streams

- Stream status: `aws kinesis describe-stream-summary --stream-name {stream} --query 'StreamDescriptionSummary.{Name:StreamName,Status:StreamStatus,OpenShards:OpenShardCount,RetentionHours:RetentionPeriodHours}' --profile {profile} --region {region}`
- Incoming records: `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name IncomingRecords --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`
- Iterator age (p99): `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name GetRecords.IteratorAgeMilliseconds --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 60 --extended-statistics p99 --profile {profile} --region {region}`
- Read/write throttling: `aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name WriteProvisionedThroughputExceeded --dimensions Name=StreamName,Value={stream} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --profile {profile} --region {region}`

## Third-party services on AWS

For third-party services integrated into the stack (bot defenders, CDN edge functions, managed APM/logging vendors, feature-flag services), ask the human:
- Whether the service uses it and how it's integrated (Lambda@Edge, ALB header inspection, DNS routing, sidecar agent, etc.).
- Where its logs and metrics live (vendor dashboard URL, CloudWatch log group, S3 bucket).

For Lambda@Edge integrations, the function lives in `us-east-1`, but its logs are written to CloudWatch in the region nearest the edge location that ran it (per AWS docs; UNVERIFIED here), under log group `/aws/lambda/us-east-1.{edge-function}`. Set `{edge-region}` to the region where `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/us-east-1.{edge-function} --profile {profile} --region {edge-region}` finds the group. Log lines can contain secrets and PII — **terminal only — never paste output into a catalog, ticket or chat**:
- `aws logs filter-log-events --log-group-name /aws/lambda/us-east-1.{edge-function} --start-time {T-15m-epoch-ms} --filter-pattern "ERROR" --profile {profile} --region {edge-region}`

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{profile}` | AWS CLI profile confirmed at the gate | `widgetapi-prod-ro` |
| `{region}` | AWS region confirmed at the gate (shown from profile/env; not returned by `sts`) | `eu-west-1` |
| `{cluster}`, `{service}`, `{function}`, `{queue}`, `{table}`, `{stream}`, `{bucket}` | Resource identifiers | `widgetapi-prod-eu-web` |
| `{taskdef}` | ECS task definition (`family:revision` or ARN) | `widgetapi-web:42` |
| `{tg-arn}`, `{alb-arn}`, `{topic-arn}`, `{queue-url}`, `{distribution-id}`, `{waf-arn}` | AWS identifiers (ARN or ID) | See the resource in the catalog |
| `{alb-dim}` | CloudWatch `LoadBalancer` dimension: ARN text after `loadbalancer/` | `app/widgetapi-alb/50dc6c495c0c9188` |
| `{cache-cluster-id}` | ElastiCache node / cluster id (CloudWatch `CacheClusterId`) | `widgetapi-cache-001` |
| `{waf-scope}`, `{waf-region}`, `{waf-metric-region}` | WAF scope and the region to call it in; metric `Region` dimension | `REGIONAL` / `eu-west-1` / `eu-west-1`, or `CLOUDFRONT` / `us-east-1` / `Global` |
| `{bucket-region}` | Region of an S3 bucket (for S3 metrics) | `eu-west-1` |
| `{edge-region}` | Region where Lambda@Edge replica logs appear | `eu-central-1` |
| `{namespace-cw}`, `{metric}`, `{dim-name}`, `{dim-value}` | CloudWatch namespace, metric and dimension for a `list-metrics` check | `AWS/ApplicationELB`, `TargetResponseTime`, `LoadBalancer`, `app/…` |
| `{context}` | kubeconfig context (EKS commands) | `prod-eu-west-1` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{T-15m-epoch-ms}` | 15 minutes ago in epoch milliseconds (for `aws logs filter-log-events --profile {profile} --region {region}`) | `1744707600000` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
