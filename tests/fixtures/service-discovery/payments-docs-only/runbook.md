# Payments Service — Operations Runbook

## Service Overview

The payments service handles all payment processing for the platform. It runs in AWS account `123456789012`, region `us-east-1`.

## Infrastructure Components

### Load Balancer

- **payments-alb** — Application Load Balancer
  - Listener: HTTPS (443), TLS termination
  - Target group: `payments-api-tg` (port 8080, HTTP health check on `/healthz`)
  - Idle timeout: 60s

### Compute

- **payments-api** — ECS Fargate service
  - Cluster: `payments-prod`
  - Desired count: 4 tasks
  - CPU: 1024 (1 vCPU), Memory: 2048 MB
  - Container port: 8080
  - Image: `123456789012.dkr.ecr.us-east-1.amazonaws.com/payments-api:latest`

- **payments-legacy-worker** — EC2 instance (t3.medium)
  - **Status: being migrated to ECS.** This worker processes batch reconciliation jobs. Migration target date: 2026-Q2. Do not scale or modify — it will be decommissioned once the ECS-based worker is validated.
  - Instance ID: `i-0abc123def456789a`
  - Security group: `payments-legacy-sg`

### Database

- **payments-db** — RDS PostgreSQL 15
  - Multi-AZ: enabled
  - Instance class: `db.r6g.xlarge`
  - Storage: 500 GB gp3, encrypted (KMS)
  - Endpoint: `payments-db.c9abc123.us-east-1.rds.amazonaws.com`
  - Port: 5432
  - Database name: `payments`
  - Credentials: stored in AWS Secrets Manager (`payments/prod/db-credentials`)

### Cache

- **payments-cache** — ElastiCache Redis 7
  - Node type: `cache.r6g.large`
  - Cluster mode: disabled
  - Replicas: 1 (automatic failover enabled)
  - Endpoint: `payments-cache.abc123.0001.use1.cache.amazonaws.com`
  - Port: 6379
  - Used for: session tokens, rate-limit counters, idempotency keys

## Monitoring

CloudWatch alarms are configured on the `payments-*` prefix:

- `payments-api-5xx-rate` — triggers if 5xx rate exceeds 1% over 5 minutes
- `payments-api-p99-latency` — triggers if p99 latency exceeds 2000ms over 5 minutes
- `payments-db-connections` — triggers if active connections exceed 80% of max
- `payments-db-cpu` — triggers if CPU utilization exceeds 80% for 10 minutes
- `payments-cache-memory` — triggers if Redis memory usage exceeds 75%
- `payments-cache-evictions` — triggers if eviction rate exceeds 100/min

All alarms route to SNS topic `payments-alerts` which fans out to PagerDuty.

## Incident Response

### Payment processing slow or timing out

1. Check ALB target group health: are all ECS tasks healthy?
2. Check ECS service events: any task failures or OOM kills?
3. Check RDS metrics: CPU, connections, read/write latency
4. Check ElastiCache metrics: memory, evictions, connection count
5. Check CloudWatch Logs for error patterns in `/ecs/payments-prod`

### Payment processing returning errors

1. Check ALB 5xx metrics — is the ALB itself returning errors or forwarding from targets?
2. Check ECS task logs for exception stack traces
3. Check RDS connectivity — can tasks reach the database?
4. Check Secrets Manager — has the DB credential rotation completed successfully?
5. If errors mention "duplicate key" or "constraint violation" — check idempotency key cache (Redis) health

### Database failover

1. Check RDS events for failover notifications
2. Verify new primary endpoint is responsive
3. Check application connection pool recovery — ECS tasks may need 30-60s to reconnect
4. Monitor error rate during reconnection window — some 5xx is expected

## Contacts

- **On-call rotation:** PagerDuty service `payments-prod`
- **Team Slack:** `#payments-eng`
- **Database team:** `#platform-data` (for RDS escalations)
- **Security team:** `#security-oncall` (for credential rotation issues)
