# Examples: AWS CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer when the target infrastructure is AWS. The skill reads this file when the operator opts into L3 and the assessed change targets AWS resources.

Replace placeholders (`{cluster}`, `{service}`, `{T-1h}`, `{now}`, `{region}`, etc.) with the values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` >= 2.x).

**Authentication:** any of — named profile (`--profile` or `AWS_PROFILE`), AWS SSO (`aws sso login`), IAM role, or STS temporary credentials. Confirm identity: `aws sts get-caller-identity`.

**Least-privilege IAM — every command below is read-only.** Grant the operator either:
- **Baseline:** AWS-managed `ReadOnlyAccess` policy
- **Tighter:** scoped policy: `Describe*`, `List*`, `Get*` on relevant resource types, plus `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `logs:FilterLogEvents`

**Never use `PowerUserAccess`, `AdministratorAccess`, or any `*:*` policy** for pre-flight read-only checks.

**Cost awareness:** CloudWatch `GetMetric*` and `logs:FilterLogEvents` incur small per-call and per-GB-scanned charges.

---

## Resource Health Checks

### ECS

- Service status: `aws ecs describe-services --cluster {cluster} --services {service} --region {region}`
- Running vs desired tasks: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].{desired:desiredCount,running:runningCount,pending:pendingCount}' --region {region}`
- Recent deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments' --region {region}`
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
- Read/write latency: `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name ReadLatency --dimensions Name=DBInstanceIdentifier,Value={instance} --start-time {T-1h} --end-time {now} --period 300 --statistics Average p99 --region {region}`

### ALB / Application Load Balancer

- Target health: `aws elbv2 describe-target-health --target-group-arn {tg-arn} --region {region}`
- HTTP 5xx (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Target response time: `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Average p99 --region {region}`
- Request count (traffic baseline): `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCount --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`

### Lambda

- Error count (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Duration (last 1h): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Average p99 --region {region}`
- Throttles: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Throttles --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Sum --region {region}`
- Concurrent executions: `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name ConcurrentExecutions --dimensions Name=FunctionName,Value={function} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --region {region}`

### SQS

- Queue depth: `aws sqs get-queue-attributes --queue-url {queue-url} --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible --region {region}`
- Age of oldest message: `aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name ApproximateAgeOfOldestMessage --dimensions Name=QueueName,Value={queue} --start-time {T-1h} --end-time {now} --period 300 --statistics Maximum --region {region}`

---

## Observability Checks

### CloudWatch Alarms

- List alarms for a resource: `aws cloudwatch describe-alarms --alarm-name-prefix {service} --region {region} --query 'MetricAlarms[].{Name:AlarmName,State:StateValue}'`
- Currently firing alarms: `aws cloudwatch describe-alarms --state-value ALARM --alarm-name-prefix {service} --region {region}`
- Alarm history (last 24h): `aws cloudwatch describe-alarm-history --alarm-name {alarm} --history-item-type StateUpdate --start-date {T-24h} --end-date {now} --region {region}`

---

## Timing Context Checks

### Recent Deployments

- ECS recent deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments[?status!=`PRIMARY`]' --region {region}`
- Lambda recent versions: `aws lambda list-versions-by-function --function-name {function} --region {region} --query 'Versions[-3:]'`
- CodeDeploy recent deployments: `aws deploy list-deployments --application-name {app} --deployment-group-name {group} --create-time-range start={T-24h} --region {region}`
