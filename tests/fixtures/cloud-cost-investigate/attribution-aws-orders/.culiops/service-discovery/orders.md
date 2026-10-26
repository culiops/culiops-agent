**Cataloged from commit:** `a3f9c12`
**Cataloging date:** `2026-04-20`
**Target instance:** `prod` (AWS account `123456789012` / `acme-prod`, region `us-east-1`)
**IaC tool(s):** Terraform

# orders - Service Discovery Catalog

## Overview

The `orders` service handles order intake, fulfillment orchestration, and event publishing for the ACME platform. It runs as two ECS Fargate services (API + async worker), persists order records in RDS PostgreSQL, publishes events to an SQS queue, and runs fulfillment as a Step Functions state machine. Raw event payloads and long-term audit archives are stored in S3.

Account: `123456789012` (`acme-prod`)
Instance: `prod`
Region: `us-east-1`

## Prerequisites

**CLI:** `aws` >= 2.15, authenticated as a principal with read-only access (`ReadOnlyAccess` or the narrower list below) on account `123456789012`.

**Authentication:**
```bash
aws sso login --profile acme-prod
export AWS_PROFILE=acme-prod
aws sts get-caller-identity
```

**Least-privilege read-only permissions:** `ecs:Describe*`, `ecs:List*`, `rds:Describe*`, `s3:GetBucket*`, `s3:ListAllMyBuckets`, `sqs:GetQueueAttributes`, `sqs:ListQueues`, `states:Describe*`, `states:List*`, `cloudwatch:GetMetricStatistics`.

**Mutations in runbooks** (require explicit approval + a deploy role):
- ECS: `aws ecs update-service` (task count / task definition rollout)
- RDS: `aws rds reboot-db-instance`

## Resource Inventory

### Compute

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| ECS service (Fargate) | `AWS::ECS::Service` | `orders-api` | `us-east-1` | HTTP API for order creation and status; behind the shared ALB `acme-prod-public` |
| ECS service (Fargate) | `AWS::ECS::Service` | `orders-worker` | `us-east-1` | Async worker; consumes the events queue and starts fulfillment executions |

Both run in ECS cluster `acme-prod`.

### Database

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| RDS instance | `AWS::RDS::DBInstance` | `orders-prod-db` | `us-east-1` | PostgreSQL 15, db.r6g.xlarge, Multi-AZ; stores orders, line items, fulfillment state |
| RDS instance | `AWS::RDS::DBInstance` | `orders-dev-db` | `us-east-1` | PostgreSQL 15, db.t4g.medium, single-AZ; dev/test workloads; tagged `env=dev` |

### Storage

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| S3 bucket | `AWS::S3::Bucket` | `acme-prod-orders-events` (Component `orders-events`) | `us-east-1` | Raw order event payloads retained 90d for replay |
| S3 bucket | `AWS::S3::Bucket` | `acme-prod-orders-archives` (Component `orders-archives`) | `us-east-1` | Fulfilled-order archives retained 7y for compliance (Glacier Deep Archive) |

### Messaging and orchestration

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| SQS queue (standard) | `AWS::SQS::Queue` | `orders-events-queue` | `us-east-1` | Carries `OrderCreated`, `OrderUpdated`, `OrderFulfilled` events; consumers owned by payments and inventory services |
| Step Functions state machine (STANDARD) | `AWS::StepFunctions::StateMachine` | `orders-fulfillment` | `us-east-1` | Fulfillment workflow started by `orders-worker`; ~6M state transitions/month |

## Cost allocation tags

Cost-allocation tags `Service` and `Component` were activated in the Billing console on 2026-02-10, so they appear in Cost Explorer from 2026-02 onward.

| Tag | Value | Applied to |
|-----|-------|-----------|
| `Service` | `orders` | every resource above (Terraform `default_tags`) |
| `Component` | the resource name in the tables above (`orders-api`, `orders-worker`, `orders-prod-db`, `orders-dev-db`, `orders-events`, `orders-archives`, `orders-events-queue`, `orders-fulfillment`) | per resource |
| `env` | `prod`, `dev` | RDS instances |

Tag convention for attribution: filter `Service=orders`, group by `Component`.

## Naming Patterns

Pattern: `orders-{component}`; S3 buckets are prefixed `acme-prod-`.

| Token | Values seen | Source |
|-------|-------------|--------|
| `{service}` | `orders` | `terraform/variables.tf` `service_name` default |
| `{component}` | `api`, `worker`, `prod-db`, `dev-db`, `events`, `archives`, `events-queue`, `fulfillment` | per-resource `name` attribute |
| `{env}` | `prod`, `dev` | tag `env` on RDS instances |

## Dependency Graph

```
orders-api ---------------> orders-prod-db (read/write)
                          > orders-events (S3 write)
                          > orders-events-queue (SQS send)

orders-worker ------------> orders-events-queue (SQS receive)
                          > orders-fulfillment (StartExecution)
                          > orders-prod-db (write fulfillment state)
                          > orders-archives (S3 write on fulfillment)

orders-dev-db <------------  (local dev / CI only; no production traffic path)

Upstream (cross-service, critical path):
  payments-service  <-- orders-events-queue (OrderCreated)
  inventory-service <-- orders-events-queue (OrderFulfilled)
```

Critical path: `orders-api` -> `orders-prod-db` -> `orders-events-queue` -> downstream consumers.

## Signal Envelopes

| Resource | Latency p99 | Error rate | Saturation | Traffic |
|----------|-------------|------------|------------|---------|
| `orders-api` | 350ms (declared SLO) | <0.1% 5xx | CPU <60% per task | ~2,000 req/s peak |
| `orders-worker` | n/a (async) | DLQ depth = 0 target | memory <3 GiB per task | ~500 messages/min |
| `orders-prod-db` | <20ms query p99 | n/a | connections <80% of max | ~1,200 QPS |
| `orders-events-queue` | n/a | oldest message age <60s | n/a | ~20 msg/s average (about 3 SQS requests per message) |
| `orders-fulfillment` | n/a | execution failure rate <1% | n/a | ~2.3 transitions/s average |

## Investigation Runbooks

### Symptom: Order API returning 5xx errors

1. Check ECS service health:
   ```bash
   aws ecs describe-services --cluster acme-prod --services orders-api \
     --query "services[].[serviceName,runningCount,desiredCount,deployments[].rolloutState]"
   ```
2. Check error logs in the `/ecs/orders-api` log group (CloudWatch Logs Insights, `level = "ERROR"`).
3. Is the upstream dependency healthy? Check `orders-prod-db` `CPUUtilization`, `DatabaseConnections` and `FreeableMemory`.
4. **MUTATION - requires explicit approval:** if a bad task definition revision is deployed, roll the service back with `aws ecs update-service --cluster acme-prod --service orders-api --task-definition orders-api:<previous>` (blast radius: all orders-api traffic).

### Symptom: Order fulfillment delayed

1. Check queue depth and age:
   ```bash
   aws sqs get-queue-attributes --queue-url <orders-events-queue-url> \
     --attribute-names ApproximateNumberOfMessages ApproximateAgeOfOldestMessage
   ```
2. Check failed executions of `orders-fulfillment` (`aws stepfunctions list-executions --state-machine-arn <arn> --status-filter FAILED`).
3. Check `orders-worker` task count and logs.

## Stack-Specific Tooling

- AWS commands: `skills/cloud-cost-investigate/examples/aws.md`
- ECS: `aws ecs`
- RDS: `aws rds`
- Step Functions: `aws stepfunctions`

## Assumptions and Caveats

- This catalog was built from Terraform source at commit `a3f9c12` (2026-04-20), not from live account state. Running infrastructure may have drifted - recommend re-running service-discovery before any incident investigation.
- `orders-dev-db` is in the catalog because it is declared in Terraform and carries `env=dev`. It receives no production traffic. Operators responding to production incidents should focus on `orders-prod-db`.
- The SQS queue `orders-events-queue`'s consumers (payments-service, inventory-service) are not in scope for this catalog; they are recorded as dependencies only.
- The shared NAT gateway and the shared ALB `acme-prod-public` belong to the platform VPC, not to `orders`, and are intentionally not listed.
- Signal envelope thresholds are from Terraform SLO declarations and team runbooks as of the cataloging date. Verify against current CloudWatch alarms before relying on them.

## Open Questions

(none raised during this discovery run)
