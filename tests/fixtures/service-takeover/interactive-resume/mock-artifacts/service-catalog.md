---
service-discovery-schema: 1
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-05T10:20:00Z
discovery-mode: real-discovery
scoping-primitive: "tag:service=payments"
---

# Service Catalog — payments

**Cataloging date:** 2026-05-05
**Target instance:** prod (123456789012 / us-east-1)
**Discovery source:** real-discovery (documents + live cloud APIs; no IaC supplied)
**Documents used:** `payments-arch.png`, `payments-flows.png`
**Live verification:** performed 2026-05-05 against 123456789012/us-east-1 (real-discovery: every inventory row below was read from the live account)

## Overview

- **Service:** payments
- **Account:** 123456789012 (alias: prod-main)
- **Primary region:** us-east-1
- **Membership signal:** tag `service=payments` (key confirmed by the operator at GATE 4b); every inventory row carries it
- **Operator:** arn:aws:iam::123456789012:user/alice
- **Purpose (from the operator):** payment authorization and capture for the e-commerce checkout flow

## Resource Inventory

Source: `docs + cloud` = in the diagrams and found live; `cloud` = found live only (flag `undocumented`). Live column: query number from GATE 4a (Q1 Tagging API, Q2 Lambda, Q3 SQS, Q4 DynamoDB, Q5 Secrets Manager).

| # | Category | Type | Resolved name | Source | Confidence | Owner | Live | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | serverless | Lambda | `payments-authorizer` | docs + cloud | High | none identified | ✓ matches (Q2) | Node.js 20.x, 256 MB, timeout 10s; authorizes payment requests |
| 2 | serverless | Lambda | `payments-capture` | docs + cloud | High | none identified | ✓ matches (Q2) | Node.js 20.x, 512 MB, timeout 30s; captures authorized payments |
| 3 | serverless | Lambda | `payments-reconciler` | docs + cloud | High | none identified | ✓ matches (Q2) | Python 3.12, 256 MB, timeout 300s; daily settlement reconciliation |
| 4 | messaging | SQS queue | `payments-capture-queue` | docs + cloud | High | none identified | ✓ matches (Q3) | Standard queue; triggers `payments-capture`; redrive to `payments-capture-dlq` after 3 receives |
| 5 | messaging | SQS queue | `payments-capture-dlq` | docs + cloud | High | none identified | ✓ matches (Q3) | Dead-letter queue for `payments-capture-queue` |
| 6 | database | DynamoDB table | `payments-ledger` | docs + cloud | High | none identified | ✓ matches (Q4) | On-demand billing; PITR enabled; TTL enabled on attribute `expires_at`; KMS CMK encryption |
| 7 | identity | Secrets Manager secret | `payments/stripe-api-key` | cloud | Medium (`undocumented`) | none identified | ✓ matches (Q5) | Reference only; value never read |
| 8 | identity | Secrets Manager secret | `payments/db-encryption-key` | cloud | Medium (`undocumented`) | none identified | ✓ matches (Q5) | Reference only; value never read |

**Unattributed — operator assigns:**

- API Gateway REST API `abc123def456` (`payments-api`): in the diagrams and named in `payments-authorizer`'s resource policy, but it carries no `service` tag and fronts routes of other services. The operator recorded it as an inbound dependency, not inventory (GATE 4b).
- SNS topic `payments-events`: name fits the pattern, no `service` tag; owned by the notifications-service team per the diagram. Recorded as an outbound dependency, not inventory.

## Secret References

References only. Names and ARNs, never values.

| Secret | ARN | Store | Read by (execution-role policy, Q5) | Rotation |
|---|---|---|---|---|
| `payments/stripe-api-key` | `arn:aws:secretsmanager:us-east-1:123456789012:secret:payments/stripe-api-key-AbCdEf` | AWS Secrets Manager | `arn:aws:iam::123456789012:role/payments-lambda-exec` | rotation not enabled in Secrets Manager |
| `payments/db-encryption-key` | `arn:aws:secretsmanager:us-east-1:123456789012:secret:payments/db-encryption-key-GhIjKl` | AWS Secrets Manager | `arn:aws:iam::123456789012:role/payments-lambda-exec` | KMS key auto-rotation enabled |

## Naming Patterns

- Lambda functions: `payments-<function>`; SQS queues: `payments-<purpose>[-dlq]`; DynamoDB tables: `payments-<table>`; secrets: `payments/<name>`. Detected from live names, not from an IaC template.

## Dependency Graph

**Inbound (from the diagrams; the callers behind the gateway are not observable from AWS):**

| Caller | Via | Notes |
|---|---|---|
| `checkout-service` | API Gateway `abc123def456`, `POST /authorize` | authorization requests |
| `billing-service` | API Gateway `abc123def456`, `GET /status/{id}` | payment status queries |

**Outbound:**

| Dependency | Type | Notes |
|---|---|---|
| Stripe API | external API | payment gateway; key in `payments/stripe-api-key` |
| `fraud-detection` | internal service (SQS) | fraud-check request before authorization |
| `notifications-service` | internal service (SNS topic `payments-events`) | capture-succeeded / capture-failed events |

**Critical path:** API Gateway `abc123def456` → `payments-authorizer` → `payments-capture-queue` → `payments-capture` → Stripe API; `payments-ledger` is written on both Lambdas.

## Unresolved References

None. Every resource named in the diagrams was found live (Q1–Q5).

## Assumptions and Caveats

- This catalog was built from real-discovery (documents + live cloud APIs), not from infrastructure-as-code. Resources may exist that are not managed by any IaC tool; no drift detection is possible without IaC.
- Resources marked `undocumented` were found live with a membership signal but are not in the diagrams. Resources with no membership signal are listed as Unattributed and are not part of this catalog unless the operator assigns them.
- Scope was one account and one region (us-east-1). Resources in other Regions or without the `service` tag are not covered here; see the runtime profile's cross-Region footprint.

## Open Questions

- Who owns API Gateway REST API `abc123def456`, and which other services' routes does it carry?
