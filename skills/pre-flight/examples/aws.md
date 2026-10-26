# Examples: AWS CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer when the target infrastructure is AWS. The skill reads this file when the operator opts into L3 and the assessed change targets AWS resources.

Replace placeholders (`{cluster}`, `{service}`, `{T-1h}`, `{now}`, `{region}`, etc.) with the values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` >= 2.x).

**Authentication:** any of — named profile (`--profile` or `AWS_PROFILE`), AWS SSO (`aws sso login`), IAM role, or STS temporary credentials.

**Least-privilege IAM — every command below is read-only.** Grant the operator either:
- **Baseline:** AWS-managed `ReadOnlyAccess` policy
- **Tighter:** scoped policy: `Describe*`, `List*`, `Get*` on relevant resource types, plus `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `logs:FilterLogEvents`

**Never use `PowerUserAccess`, `AdministratorAccess`, or any `*:*` policy** for pre-flight read-only checks.

**Cost awareness:** CloudWatch `GetMetric*` and `logs:FilterLogEvents` incur small per-call and per-GB-scanned charges.

**Secrets:** several read-only calls return secret values — `lambda get-function`, `get-function-configuration` and `list-versions-by-function` return environment-variable values; `ecs describe-task-definition` returns container environment values. Always use the `--query` shown here (it fetches only the fields needed), and never paste raw output into the record.

---

## Target Check (run first)

The live identity must match the target recorded in Step 1. If it doesn't, stop L3.

- Account: `aws sts get-caller-identity --query Account --output text` → must equal the plan's account ID
- Region: the `--region` you pass below must equal the plan's region (check the provider block / var-file, not `aws configure get region`)

---

## Resource Health Checks

### ECS

- Running vs desired tasks: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount}' --region {region}`
- Deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments[].{status:status,rollout:rolloutState,taskDef:taskDefinition,created:createdAt}' --region {region}`
- Recent service events (failing tasks, unhealthy targets): `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].events[:10].{at:createdAt,msg:message}' --region {region}`
- CPU utilization (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --start-time {T-1h} --end-time {now} --period 300 --statistics Average Maximum --region {region}`
- Memory utilization (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name MemoryUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --start-time {T-1h} --end-time {now} --period 300 --statistics Average Maximum --region {region}`

### EKS

- Cluster status: `aws eks describe-cluster --name {cluster} --region {region} --query 'cluster.status'`
- Node group health: `aws eks describe-nodegroup --cluster-name {cluster} --nodegroup-name {nodegroup} --region {region} --query 'nodegroup.health'`

### RDS / Aurora

- Instance status: `aws rds describe-db-instances --db-instance-identifier {instance} --region {region} --query 'DBInstances[].DBInstanceStatus'`
- CPU utilization (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name CPUUtilization --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Average Maximum --region {region}`
- Freeable memory: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name FreeableMemory --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Minimum --region {region}`
- Free storage space: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name FreeStorageSpace --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Minimum --region {region}`
- Database connections: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name DatabaseConnections --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --region {region}`
- Read latency (average): `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name ReadLatency --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --region {region}`
- Read latency (p99 — percentiles need `--extended-statistics`, and one call takes either `--statistics` or `--extended-statistics`, not both): `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name ReadLatency --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --extended-statistics p99 --region {region}`
- Same two calls with `WriteLatency` for write latency.

### ALB / Application Load Balancer

- Target health: `aws elbv2 describe-target-health --target-group-arn {tg-arn} --region {region}`
- HTTP 5xx (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Target 5xx (last 1h): same call with `--metric-name HTTPCode_Target_5XX_Count`
- Target response time (average): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --region {region}`
- Target response time (p99): same call with `--extended-statistics p99` instead of `--statistics Average`
- Request count (traffic baseline): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCount --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}` — run again with `{T-7d}`…`{T-7d+1h}` for the same hour last week as the baseline

### Lambda

- Error count (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Duration (average): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Average --region {region}`
- Duration (p99): same call with `--extended-statistics p99` instead of `--statistics Average`
- Throttles: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Concurrent executions: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name ConcurrentExecutions --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --region {region}`

### SQS

- Queue depth: `aws sqs get-queue-attributes --queue-url {queue-url} --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible --region {region}`
- Age of oldest message: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --region {region}`

---

## Reversibility Checks (stateful destroys and one-way changes)

- RDS protection + backups: `aws rds describe-db-instances --db-instance-identifier {instance} --region {region} --query 'DBInstances[].{deletionProtection:DeletionProtection,backupRetention:BackupRetentionPeriod,latestRestorable:LatestRestorableTime}'`
- Aurora cluster: `aws rds describe-db-clusters --db-cluster-identifier {cluster} --region {region} --query 'DBClusters[].{deletionProtection:DeletionProtection,backupRetention:BackupRetentionPeriod,latestRestorable:LatestRestorableTime}'`
- Latest RDS snapshots: `aws rds describe-db-snapshots --db-instance-identifier {instance} --region {region} --query 'sort_by(DBSnapshots,&SnapshotCreateTime)[-3:].{id:DBSnapshotIdentifier,created:SnapshotCreateTime,status:Status,type:SnapshotType}'`
- Latest Aurora snapshots: `aws rds describe-db-cluster-snapshots --db-cluster-identifier {cluster} --region {region} --query 'sort_by(DBClusterSnapshots,&SnapshotCreateTime)[-3:].{id:DBClusterSnapshotIdentifier,created:SnapshotCreateTime,status:Status}'`
- AWS Backup recovery points: `aws backup list-recovery-points-by-resource --resource-arn {arn} --max-results 5 --region {region} --query 'RecoveryPoints[].{created:CreationDate,status:Status}'`
- S3 versioning: `aws s3api get-bucket-versioning --bucket {bucket}`
- S3 lifecycle rules (current): `aws s3api get-bucket-lifecycle-configuration --bucket {bucket}`
- DynamoDB PITR: `aws dynamodb describe-continuous-backups --table-name {table} --region {region} --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription'`
- NAT gateway egress (≥ 6 months, for the external-allowlist check): `aws cloudwatch get-metric-statistics --namespace AWS/NATGateway --metric-name BytesOutToDestination --dimensions Name=NatGatewayId,Value={nat-id} --start-time {T-180d} --end-time {now} --period 86400 --statistics Sum --region {region}`

---

## Application Compatibility Checks (category 11)

Live evidence of whether a contract the plan removes is still used. They complement the app source (Step 3b) and never replace it: use shows *that* the app calls something, only the code shows what it does when the call fails.

- Role's service-level last access (two calls; `iam:GenerateServiceLastAccessedDetails` is in `IAMReadOnlyAccess`, and it starts a report job without changing any resource): `aws iam generate-service-last-accessed-details --arn {role-arn} --granularity ACTION_LEVEL --query JobId --output text`, then `aws iam get-service-last-accessed-details --job-id {job-id} --query 'ServicesLastAccessed[?ServiceNamespace==`{namespace}`].{service:ServiceNamespace,last:LastAuthenticated,actions:TrackedActionsLastAccessed[].{a:ActionName,last:LastAccessedTime}}'`. Action-level data exists only for some services; "accessed" counts denied attempts too.
- Would the role still be allowed the action after the change? `aws iam simulate-principal-policy --policy-source-arn {role-arn} --action-names {action} --resource-arns {resource-arn} --query 'EvaluationResults[].{action:EvalActionName,decision:EvalDecision}'` evaluates the policies attached **now**: run it to find out whether another policy still grants the action. `aws iam simulate-custom-policy --policy-input-list file://{new-policy.json} --action-names {action} --resource-arns {resource-arn}` evaluates the proposed document alone (write the file outside the repo, delete it after).
- Is an alarm notify-only? List its actions from the plan, then read only the subscription **protocols** of each SNS action. Endpoints can carry tokens, so never read them: `aws sns list-subscriptions-by-topic --topic-arn {topic-arn} --query 'Subscriptions[].Protocol'`. All `email` / `email-json` / `sms` means notify-only. Anything else, or an action ARN for Auto Scaling, EC2 or SSM, means the alarm changes the system.
- Send / publish activity on the resource (≥ 30 days): SQS `NumberOfMessagesSent`, SNS `NumberOfMessagesPublished`, S3 request metrics (only if enabled on the bucket), DynamoDB `ConsumedWriteCapacityUnits`, e.g. `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name NumberOfMessagesSent --dimensions Name=QueueName,Value={queue} --start-time {T-30d} --end-time {now} --period 86400 --statistics Sum --region {region}`.

---

### CloudFront (cache behavior changes)

- Distribution behaviors (projected, no origin custom headers): `aws cloudfront get-distribution-config --id {dist-id} --query 'DistributionConfig.{default:DefaultCacheBehavior.{cache:CachePolicyId,orp:OriginRequestPolicyId},ordered:CacheBehaviors.Items[].{path:PathPattern,methods:AllowedMethods.Items,cache:CachePolicyId,orp:OriginRequestPolicyId}}'`
- Cache key and TTLs of a policy: `aws cloudfront get-cache-policy --id {policy-id} --query 'CachePolicy.CachePolicyConfig.{name:Name,min:MinTTL,default:DefaultTTL,max:MaxTTL,headers:ParametersInCacheKeyAndForwardedToOrigin.HeadersConfig,cookies:ParametersInCacheKeyAndForwardedToOrigin.CookiesConfig,query:ParametersInCacheKeyAndForwardedToOrigin.QueryStringsConfig}'`. A minimum TTL above 0 caches even when the origin sends `Cache-Control: private` / `no-store`.
- What reaches the origin: `aws cloudfront get-origin-request-policy --id {policy-id} --query 'OriginRequestPolicy.OriginRequestPolicyConfig.{name:Name,headers:HeadersConfig.HeaderBehavior,cookies:CookiesConfig.CookieBehavior,query:QueryStringsConfig.QueryStringBehavior}'`
- Metrics live in `us-east-1`: `aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name {Requests|4xxErrorRate|5xxErrorRate|CacheHitRate} --dimensions Name=DistributionId,Value={dist-id} Name=Region,Value=Global --start-time {T-24h} --end-time {now} --period 3600 --statistics {Sum|Average} --region us-east-1` (`CacheHitRate` needs additional metrics enabled). Methods a behavior rejects return 403, so watch `4xxErrorRate`, not only 5xx.

---

## Observability Checks

### CloudWatch Alarms

Find alarms by what they watch, not by name — an alarm named differently from the service is still the alarm that matters.

- Alarms on a metric of the changed resource: `aws cloudwatch describe-alarms-for-metric --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --region {region} --query 'MetricAlarms[].{name:AlarmName,state:StateValue}'` (repeat per namespace / metric the change touches)
- Everything currently firing in the region: `aws cloudwatch describe-alarms --state-value ALARM --region {region} --query '{metric:MetricAlarms[].{name:AlarmName,ns:Namespace,metric:MetricName,dims:Dimensions},composite:CompositeAlarms[].AlarmName}'` — then keep the ones whose dimensions reference the changed resources
- If the team uses an alarm-name prefix convention, `--alarm-name-prefix {prefix}` is a shortcut, never the only check
- Alarm history (last 24h): `aws cloudwatch describe-alarm-history --alarm-name {alarm} --history-item-type StateUpdate --start-date {T-24h} --end-date {now} --region {region}`

---

## Timing Context Checks

### Recent Deployments

- ECS deployments: see Resource Health → ECS → Deployments (`createdAt` per deployment)
- Lambda recent versions (no configuration values): `aws lambda list-versions-by-function --function-name {function} --region {region} --query 'Versions[-3:].{version:Version,modified:LastModified}'`
- CodeDeploy recent deployments: `aws deploy list-deployments --application-name {app} --deployment-group-name {group} --create-time-range start={T-24h} --region {region}`

### Last Terraform Apply (automation lag)

- S3 backend state object, metadata only: `aws s3api head-object --bucket {state-bucket} --key {state-key} --query '{modified:LastModified,version:VersionId}'`
- **Never** `aws s3 cp` / `get-object` the state file or run `terraform state pull` — state holds secrets in plaintext.

---

## Cost Checks

- Current price for a type in the target region: AWS Price List API, e.g. `aws pricing get-products --region us-east-1 --service-code AmazonEC2 --filters Type=TERM_MATCH,Field=instanceType,Value={type} Type=TERM_MATCH,Field=regionCode,Value={region} Type=TERM_MATCH,Field=operatingSystem,Value=Linux Type=TERM_MATCH,Field=tenancy,Value=Shared Type=TERM_MATCH,Field=preInstalledSw,Value=NA Type=TERM_MATCH,Field=capacitystatus,Value=Used --max-results 1` (`--region us-east-1` is the Price List API endpoint; the resource region goes in the `regionCode` filter). Record the lookup date.
