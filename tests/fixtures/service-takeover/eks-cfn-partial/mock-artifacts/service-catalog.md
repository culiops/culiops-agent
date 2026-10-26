---
service-discovery-schema: 1
service: search-api
account: "123456789012"
region: eu-west-1
generated-at: 2026-05-12T14:28:00Z
discovery-mode: real-discovery
scoping-primitive: "namespace:search + tag:service=search-api"
---

# Service Catalog — search-api

**Cataloging date:** 2026-05-12
**Target instance:** prod (123456789012 / eu-west-1, kube context `platform-eks`, namespace `search`)
**Discovery source:** real-discovery (documents + live cloud APIs + live Kubernetes API)
**Documents used:** `search-api-architecture.png`
**Live verification:** performed 2026-05-12 against 123456789012/eu-west-1, context platform-eks (real-discovery: every inventory row below was read live)

## Overview

- **Service:** search-api (full-text product search API)
- **Account:** 123456789012 (alias: prod-main); **Region:** eu-west-1; **Cluster:** `platform-eks`, namespace `search`
- **Membership signal:** namespace `search` for Kubernetes objects; tag `service=search-api` for AWS resources

## Resource Inventory

Live column: query number from GATE 4a (K = kubectl read, Q = AWS CLI read).

| # | Category | Type | Resolved name | Source | Confidence | Owner | Live | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | compute | Kubernetes Deployment | `search/search-api` | docs + cloud | High | helm `search-api` | ✓ matches (K1) | 3 replicas; ServiceAccount `search/search-api` (IRSA) |
| 2 | network | Kubernetes Ingress | `search/search-api` | docs + cloud | High | helm `search-api` | ✓ matches (K2) | provisions the ALB below |
| 3 | network | ALB | `k8s-search-searchapi-4f3a2b1c9d` | cloud | Medium (`undocumented`) | kubernetes ingress `search/search-api` (aws-load-balancer-controller) | ✓ matches (Q2) | internet-facing; created from the Ingress |
| 4 | messaging | SQS queue | `search-reindex-queue` | docs + cloud | High | cloudformation (`search-data-stack`) | ✓ matches (Q3) | Standard queue |
| 5 | cache | ElastiCache replication group | `search-cache` | docs + cloud | High | cloudformation (`search-data-stack`) | ✓ matches (Q4) | Redis, 2 nodes; snapshot retention 7 days |
| 6 | storage | S3 bucket | `search-index-snapshots-123456789012` | docs + cloud | High | cloudformation (`search-data-stack`) | ✓ matches (Q5) | versioning on; lifecycle expires objects after 30 days |
| 7 | observability | CloudWatch log group | `/search/search-api` | cloud | Medium (`undocumented`) | kubernetes (fluent-bit DaemonSet) | ✓ matches (Q6) | retention 14 days |
| 8 | identity | IAM role | `search-api-irsa` | docs + cloud | High | cloudformation (`search-iam-stack`) | ✓ matches (Q7) | trusted by ServiceAccount `search/search-api` |
| 9 | identity | Secrets Manager secret | `search/redis-auth` | docs + cloud | High | cloudformation (`search-data-stack`) | ✓ matches (Q8) | reference only; value never read |
| 10 | identity | Kubernetes Secret | `search/search-api-env` | cloud | Medium (`undocumented`) | helm `search-api` | ✓ matches (K3) | key names only: `REDIS_AUTH_TOKEN`; values never read |

**Unattributed — operator assigns:** none.

## Secret References

References only. Names and ARNs, never values.

| Secret | Reference | Store | Read by | Rotation |
|---|---|---|---|---|
| `search/redis-auth` | `arn:aws:secretsmanager:eu-west-1:123456789012:secret:search/redis-auth-MnOpQr` | AWS Secrets Manager | `arn:aws:iam::123456789012:role/search-api-irsa` | rotation not enabled in Secrets Manager |
| `search/search-api-env` | Kubernetes Secret, namespace `search`, key `REDIS_AUTH_TOKEN` | Kubernetes | ServiceAccount `search/search-api` | follows `search/redis-auth` |

## Dependency Graph

**Inbound:** `web-frontend` and `mobile-api` via ALB `k8s-search-searchapi-4f3a2b1c9d` (from the diagram; the clients are not observable from AWS).

**Outbound:** ElastiCache `search-cache`; SQS `search-reindex-queue`; S3 `search-index-snapshots-123456789012`. No external APIs.

**Critical path:** ALB -> Ingress -> Deployment `search/search-api` -> ElastiCache `search-cache`.

## Unresolved References

None.

## Assumptions and Caveats

- Built from real-discovery (documents + live cloud and Kubernetes APIs), not from IaC. Ownership comes from live tags and Helm release metadata: five AWS rows are owned by CloudFormation stacks (`cloudformation (<stack>)`), so later changes to them must go through the stack, not the console (pre-import ownership check).
- Kubernetes Secret values and Helm values were never read; only key names and release names are recorded.
- Pod-level state (restarts, HPA, node placement) is not part of this catalog.

## Open Questions

- Is the EKS access entry for `platform-team-eks` read-only or `edit`? (Kubernetes RBAC is outside the AWS reads used here.)
