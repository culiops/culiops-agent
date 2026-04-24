# Examples: AWS CLI Templates for `iac-change-execution`

Reference command templates for the `iac-change-execution` skill when the target infrastructure is AWS. The skill reads this file during Step 1 (Research gap-filling), Step 4c (Apply), and Step 5a (Verification).

Replace placeholders (`{cluster}`, `{service}`, `{stack}`, `{region}`, `{T-1h}`, `{now}`, etc.) with the values resolved in Step 1 research or detected from the plan output.

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` >= 2.x).

**Authentication:** any of — named profile (`--profile` or `AWS_PROFILE`), AWS SSO (`aws sso login`), IAM role, or STS temporary credentials. Confirm identity: `aws sts get-caller-identity`.

**Least-privilege IAM — TWO tiers are required for this skill.**

- **Tier 1 (Steps 1 and 5 — read-only):** AWS-managed `ReadOnlyAccess`, or a scoped custom policy allowing `Describe*`, `List*`, `Get*` on relevant resource types, plus `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`, `logs:FilterLogEvents`. Never use `PowerUserAccess` or `AdministratorAccess` for read-only operations.
- **Tier 2 (Step 4 — mutation only):** the minimum role that permits the specific mutation — e.g., a scoped `cloudformation:ExecuteChangeSet` policy, or `lambda:UpdateFunctionCode` only on the target function ARN. Elevated permissions must be assumed immediately before the mutation and dropped after. Never hold an elevated session while running read-only queries.

**Cost awareness:** CloudWatch `GetMetric*` and `logs:FilterLogEvents` incur small per-call and per-GB-scanned charges.

---

## Research Queries (Step 1 — Read-Only)

### ECS — current service state

- Service status and configuration: `aws ecs describe-services --cluster {cluster} --services {service} --region {region}`
- Running vs desired tasks: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].{desired:desiredCount,running:runningCount,pending:pendingCount}' --region {region}`
- Current task definition: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].taskDefinition' --region {region}`
- Recent deployments: `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments' --region {region}`

### RDS / Aurora — current instance state

- Instance status and class: `aws rds describe-db-instances --db-instance-identifier {instance} --region {region}`
- Cluster status: `aws rds describe-db-clusters --db-cluster-identifier {cluster} --region {region}`
- Pending modifications: `aws rds describe-db-instances --db-instance-identifier {instance} --query 'DBInstances[].PendingModifiedValues' --region {region}`
- Parameter group: `aws rds describe-db-instances --db-instance-identifier {instance} --query 'DBInstances[].DBParameterGroups' --region {region}`

### Lambda — current function state

- Function configuration: `aws lambda get-function --function-name {function} --region {region}`
- Function state and last modified: `aws lambda get-function-configuration --function-name {function} --query '{State:State,LastModified:LastModified,Runtime:Runtime,MemorySize:MemorySize,Timeout:Timeout}' --region {region}`
- Current environment variables (names only, not values): `aws lambda get-function-configuration --function-name {function} --query 'Environment.Variables' --region {region}`
- Aliases and routing config: `aws lambda list-aliases --function-name {function} --region {region}`

### EC2 — current instance state

- Instance details: `aws ec2 describe-instances --instance-ids {instance-id} --region {region}`
- Instance type and state: `aws ec2 describe-instances --instance-ids {instance-id} --query 'Reservations[].Instances[].{Type:InstanceType,State:State.Name,AZ:Placement.AvailabilityZone}' --region {region}`

### ALB / Security Groups — current config

- Load balancer details: `aws elbv2 describe-load-balancers --names {lb-name} --region {region}`
- Listener rules: `aws elbv2 describe-rules --listener-arn {listener-arn} --region {region}`
- Security group rules: `aws ec2 describe-security-groups --group-ids {sg-id} --region {region}`

### Parameter Store and Secrets Manager — names only, never content

- List parameters by path (names only): `aws ssm get-parameters-by-path --path {/service/env/} --query 'Parameters[].Name' --region {region}`
- Describe a specific parameter (metadata only): `aws ssm describe-parameters --filters "Key=Name,Values={parameter-name}" --region {region}`
- List secrets (names only): `aws secretsmanager list-secrets --query 'SecretList[].{Name:Name,LastChanged:LastChangedDate}' --region {region}`

**Never retrieve secret values or parameter values during research.** If the change requires knowing a value, ask the operator to provide it.

### CloudFormation stack state

- Stack status: `aws cloudformation describe-stacks --stack-name {stack} --region {region}`
- Stack resources: `aws cloudformation list-stack-resources --stack-name {stack} --region {region}`
- Existing change sets: `aws cloudformation list-change-sets --stack-name {stack} --region {region}`
- Drift status: `aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id {detection-id} --region {region}`

---

## Verification Checks (Step 5 — Read-Only)

### ECS — post-apply health

- Running vs desired (expect parity): `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].{desired:desiredCount,running:runningCount,pending:pendingCount}' --region {region}`
- Deployment state (expect PRIMARY only): `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[].deployments[].{status:status,running:runningCount,desired:desiredCount}' --region {region}`
- CPU utilization (last 15m, expect within baseline): `aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value={cluster} Name=ServiceName,Value={service} --start-time {T-15m} --end-time {now} --period 60 --statistics Average Maximum --region {region}`

### RDS / Aurora — post-apply health

- Instance status (expect `available`): `aws rds describe-db-instances --db-instance-identifier {instance} --query 'DBInstances[].DBInstanceStatus' --region {region}`
- Pending modifications (expect empty after apply): `aws rds describe-db-instances --db-instance-identifier {instance} --query 'DBInstances[].PendingModifiedValues' --region {region}`
- Parameter group status (expect `in-sync`): `aws rds describe-db-instances --db-instance-identifier {instance} --query 'DBInstances[].DBParameterGroups' --region {region}`

### CloudWatch Alarms — alarm state check

- Alarms in ALARM state for the service: `aws cloudwatch describe-alarms --state-value ALARM --alarm-name-prefix {service} --region {region}`
- All alarm states for the service: `aws cloudwatch describe-alarms --alarm-name-prefix {service} --query 'MetricAlarms[].{Name:AlarmName,State:StateValue}' --region {region}`

### Lambda — post-apply state

- Function state (expect `Active`): `aws lambda get-function-configuration --function-name {function} --query '{State:State,LastModified:LastModified}' --region {region}`
- Recent errors (last 15m): `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value={function} --start-time {T-15m} --end-time {now} --period 60 --statistics Sum --region {region}`

### ALB — target health post-apply

- Target group health (expect all `healthy`): `aws elbv2 describe-target-health --target-group-arn {tg-arn} --region {region}`
- Recent 5xx count: `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value={lb-id} --start-time {T-15m} --end-time {now} --period 60 --statistics Sum --region {region}`

---

## Apply Commands (Step 4c — MUTATION)

Each command below changes cloud state. The skill presents each command to the operator and waits for explicit approval before running. Assume Tier 2 elevated IAM permissions are active.

### Terraform

**MUTATION** — `terraform apply tfplan`
- Blast radius: all resources in the plan output; varies by change. Review plan output before approving.
- Elevated permission required: IAM role or policy with create/update/delete rights on the specific resource types in the plan.
- Rollback path: `terraform apply` from the previous state file snapshot, or manual revert per resource; no automated rollback.
- Note: `tfplan` is the binary produced by `terraform plan -out=tfplan`. Never run `terraform apply` without the plan file.

### CloudFormation — execute change set

**MUTATION** — `aws cloudformation execute-change-set --change-set-name {change-set-name} --stack-name {stack} --region {region}`
- Blast radius: resources listed in the change set. Review with `aws cloudformation describe-change-set --change-set-name {change-set-name} --stack-name {stack}` before approving.
- Elevated permission required: `cloudformation:ExecuteChangeSet` scoped to the stack ARN, plus permissions for each resource type the change set modifies.
- Rollback path: CloudFormation automatic rollback if the update fails; for manual rollback, execute a change set that restores the previous template.

### Lambda — lambroll deploy

**MUTATION** — `lambroll deploy --function-json {function.json}`
- Blast radius: single Lambda function; all invocations in flight at deploy time may receive the old or new code depending on provisioned concurrency configuration.
- Elevated permission required: `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `lambda:PublishVersion` scoped to the target function ARN.
- Rollback path: `lambroll deploy` from the previous `function.json`, or `aws lambda update-alias` to point the alias back to the previous version.

### ECS — ecspresso deploy

**MUTATION** — `ecspresso deploy --config {ecspresso.yml}`
- Blast radius: single ECS service; rolling deployment replaces tasks gradually. If health checks fail, the deployment stalls (does not auto-rollback by default unless circuit breaker is enabled).
- Elevated permission required: `ecs:UpdateService`, `ecs:RegisterTaskDefinition`, `ecs:DescribeServices` scoped to the target cluster and service.
- Rollback path: `ecspresso rollback --config {ecspresso.yml}` (rolls back to the previous task definition revision), or `aws ecs update-service --cluster {cluster} --service {service} --task-definition {previous-task-def}`.

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{cluster}`, `{service}`, `{function}`, `{instance}` | Resource identifiers | `widgetapi-prod-eu-web` |
| `{stack}` | CloudFormation stack name | `widgetapi-prod-infra` |
| `{tg-arn}`, `{lb-id}`, `{listener-arn}`, `{sg-id}` | AWS identifiers (ARN or ID) | See the resource in the catalog |
| `{region}` | AWS region | `eu-west-1` |
| `{T-15m}`, `{T-1h}` | ISO-8601 time offsets | `2026-04-24T09:45:00Z` |
| `{now}` | Current time, ISO 8601 | `2026-04-24T10:00:00Z` |
| `{change-set-name}` | CloudFormation change set name | `cs-widgetapi-resize-20260424` |
