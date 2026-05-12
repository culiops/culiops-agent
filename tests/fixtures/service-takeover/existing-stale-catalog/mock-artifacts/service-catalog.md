---
service-discovery-schema: 1
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T14:30:00Z
discovery-mode: real-discovery
scoping-primitive: "tag:service=payments"
---

# Service Catalog — payments

## Overview

- **Service:** payments
- **Account:** 123456789012 (alias: prod-main)
- **Primary region:** us-east-1
- **Scoping primitive:** `tag:service=payments`
- **Discovery mode:** real-discovery (AWS CLI, live APIs)
- **Generated:** 2026-05-12T14:30:00Z
- **Operator:** arn:aws:iam::123456789012:user/alice

This catalog was produced by `service-discovery` real-discovery mode. It reflects live AWS state at generation time.

---

## Resource Inventory

| # | Resource type | Name / ARN fragment | Tags | Notes |
|---|---|---|---|---|
| 1 | Lambda | `payments-authorizer` | service=payments, env=prod | Authorizes payment requests; runtime Node.js 20.x, 256 MB, timeout 10s |
| 2 | Lambda | `payments-capture` | service=payments, env=prod | Captures authorized payments; runtime Node.js 20.x, 512 MB, timeout 30s |
| 3 | Lambda | `payments-reconciler` | service=payments, env=prod | Async reconciliation of daily settlement; runtime Python 3.12, 256 MB, timeout 300s |
| 4 | SQS | `payments-capture-queue` | service=payments, env=prod | Standard queue; triggers payments-capture Lambda; DLQ: payments-capture-dlq |
| 5 | SQS | `payments-capture-dlq` | service=payments, env=prod | Dead-letter queue for payments-capture-queue; max receive count 3 |
| 6 | DynamoDB | `payments-ledger` | service=payments, env=prod | On-demand billing; PITR enabled; TTL attr: expires_at |
| 7 | Secrets Manager | `payments/stripe-api-key` | service=payments, env=prod | Stripe secret key; ref only — value not captured |
| 8 | Secrets Manager | `payments/db-encryption-key` | service=payments, env=prod | KMS CMK ARN ref for DynamoDB encryption at rest |

---

## Dependency Map

### Inbound (callers of payments)

| Caller | Type | Protocol | Notes |
|---|---|---|---|
| `checkout-service` | Internal microservice | HTTPS REST → API Gateway | Places authorization requests via POST /authorize |
| `billing-service` | Internal microservice | HTTPS REST → API Gateway | Queries payment status via GET /status/{id} |

### Outbound (services payments calls)

| Dependency | Type | Protocol | Notes |
|---|---|---|---|
| Stripe API | External API | HTTPS REST | Payment gateway; key in Secrets Manager payments/stripe-api-key |
| `fraud-detection` | Internal microservice | SQS | Publishes fraud-check request before authorization |
| `notifications-service` | Internal microservice | SNS topic | Publishes capture-succeeded and capture-failed events |

---

## Secrets References

All secrets are references only — values are never stored in this catalog.

| Secret name | Store | IAM principals with read access | Rotation |
|---|---|---|---|
| `payments/stripe-api-key` | AWS Secrets Manager | `arn:aws:iam::123456789012:role/payments-lambda-exec` | Manual; Pay Team owns |
| `payments/db-encryption-key` | AWS Secrets Manager | `arn:aws:iam::123456789012:role/payments-lambda-exec` | KMS auto-rotation enabled |

---

## Naming Patterns

- Lambda functions: `payments-<function-name>` (all lowercase, hyphen-separated)
- SQS queues: `payments-<purpose>[-dlq]`
- DynamoDB tables: `payments-<table-name>`
- Secrets Manager paths: `payments/<secret-name>`

---

## Assumptions and Caveats

- Discovery scope limited to resources tagged `service=payments` in us-east-1. Resources in other regions or with missing tags may be absent.
- API Gateway front-end not directly tagged — discovered via Lambda triggers. ARN: `arn:aws:apigateway:us-east-1::/restapis/abc123def456`.
- SNS topic `payments-events` owned by notifications-service team; listed as dependency, not in scope.
