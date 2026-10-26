---
service-discovery-schema: 1
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-04-28T15:00:00Z
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
- **Generated:** 2026-04-28T15:00:00Z
- **Operator:** arn:aws:iam::123456789012:user/alice

---

## Resource Inventory

| # | Resource type | Name / ARN fragment | Tags | Notes |
|---|---|---|---|---|
| 1 | Lambda | `payments-authorizer` | service=payments, env=prod | Authorizes payment requests |
| 2 | Lambda | `payments-capture` | service=payments, env=prod | Captures authorized payments |
| 3 | Lambda | `payments-reconciler` | service=payments, env=prod | Async reconciliation |
| 4 | SQS | `payments-capture-queue` | service=payments, env=prod | Triggers payments-capture Lambda |
| 5 | DynamoDB | `payments-ledger` | service=payments, env=prod | On-demand billing; PITR enabled |

---

## Assumptions and Caveats

- Catalog generated 2026-04-28 — 14 days before current run. State may have drifted.
- Secrets Manager secrets were not tagged at discovery time; may be missing from inventory.
- Re-run with current credentials recommended for takeover accuracy.
