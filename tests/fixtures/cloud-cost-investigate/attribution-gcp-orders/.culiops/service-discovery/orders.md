**Cataloged from commit:** `a3f9c12`
**Cataloging date:** `2026-04-20`
**Target instance:** `prod` (GCP project `acme-prod`, region `us-central1`)
**IaC tool(s):** Terraform

# orders — Service Discovery Catalog

## Overview

The `orders` service handles order intake, fulfillment queuing, and event publishing for the ACME platform. It runs as two Cloud Run services (API + async worker), persists order records in Cloud SQL (PostgreSQL), exchanges events via Pub/Sub, and enqueues fulfillment jobs via Cloud Tasks. Static/large order data and audit archives are stored in GCS.

Project: `acme-prod`
Instance: `prod`
Region: `us-central1`

## Prerequisites

**CLI:** `gcloud` >= 452.0.0, authenticated as a principal with `roles/viewer` on project `acme-prod`.

**Authentication:**
```bash
gcloud auth login
gcloud config set project acme-prod
```

**Least-privilege read-only role:** `roles/viewer` (project-level) grants read access to all Cloud Run, Cloud SQL, GCS, Pub/Sub, and Cloud Tasks resources listed below.

**Mutations in runbooks** (require explicit approval + `roles/editor` or per-service mutation role):
- Cloud Run: `gcloud run services update` (traffic split / revision rollout)
- Cloud SQL: instance restart via `gcloud sql instances restart`

## Resource Inventory

### Compute

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| Cloud Run service | `run.googleapis.com/Service` | `orders-api` | `us-central1` | HTTP API for order creation and status; receives external traffic via Load Balancer |
| Cloud Run service | `run.googleapis.com/Service` | `orders-worker` | `us-central1` | Async worker; pulls from Pub/Sub and invokes Cloud Tasks |

### Database

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| Cloud SQL instance | `sqladmin.googleapis.com/Instance` | `orders-prod-db` | `us-central1` | PostgreSQL 15 primary + 1 read replica; stores orders, line items, fulfillment state |
| Cloud SQL instance | `sqladmin.googleapis.com/Instance` | `orders-dev-db` | `us-central1` | PostgreSQL 15 single-node; dev/test workloads; labeled `env=dev` |

### Storage

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| GCS bucket | `storage.googleapis.com/Bucket` | `orders-events` | `us-central1` | Raw order event payloads retained 90d for replay |
| GCS bucket | `storage.googleapis.com/Bucket` | `orders-archives` | `us-central1` | Fulfilled-order archives retained 7y for compliance |

### Messaging

| Resource | Type | Name | Region | Description |
|----------|------|------|--------|-------------|
| Pub/Sub topic | `pubsub.googleapis.com/Topic` | `orders.events` | global | Publishes `OrderCreated`, `OrderUpdated`, `OrderFulfilled` events; subscriptions owned by payments and inventory services |
| Cloud Tasks queue | `cloudtasks.googleapis.com/Queue` | `orders-fulfillment` | `us-central1` | Enqueues fulfillment tasks for the orders-worker; max dispatch rate 500/s |

## Naming Patterns

Pattern: `orders-{component}` or `orders.{topic}` (Pub/Sub uses dot separator per AMCE naming convention).

| Token | Values seen | Source |
|-------|-------------|--------|
| `{service}` | `orders` | `terraform/variables.tf` `service_name` default |
| `{component}` | `api`, `worker`, `prod-db`, `dev-db`, `events`, `archives`, `fulfillment` | per-resource `name` attribute |
| `{env}` | `prod`, `dev` | label `env` on Cloud SQL instances |

## Identifying Dimensions

| Dimension | Values | How to filter |
|-----------|--------|---------------|
| Environment | `prod`, `dev` | `labels.env` on Cloud SQL; `--tag env:prod` on Cloud Run revisions |
| Region | `us-central1` | all resources except Pub/Sub topic (global) |
| Cloud Run revision | `orders-api-YYYYMMDD-HHMMSS` | `gcloud run revisions list --service=orders-api` |

## Dependency Graph

```
orders-api ──────────────────────────────► orders-prod-db (read/write)
                                          ► orders-events (GCS write)
                                          ► orders.events (Pub/Sub publish)
                                          ► orders-fulfillment (Cloud Tasks enqueue)

orders-worker ───────────────────────────► orders.events (Pub/Sub subscribe)
                                          ► orders-fulfillment (Cloud Tasks dispatch)
                                          ► orders-prod-db (write fulfillment state)
                                          ► orders-archives (GCS write on fulfillment)

orders-dev-db ◄──────────────────────────  (local dev / CI only; no production traffic path)

Upstream (cross-service, critical path):
  payments-service  ◄── orders.events (OrderCreated)
  inventory-service ◄── orders.events (OrderFulfilled)
```

Critical path: `orders-api` → `orders-prod-db` → `orders.events` → downstream consumers.

## Signal Envelopes

| Resource | Latency p99 | Error rate | Saturation | Traffic |
|----------|-------------|------------|------------|---------|
| `orders-api` | 350ms (declared SLO) | <0.1% 5xx | CPU <60% per revision | ~2,000 req/s peak |
| `orders-worker` | n/a (async) | DLQ depth = 0 target | memory <512MiB | ~500 tasks/min |
| `orders-prod-db` | <20ms query p99 | n/a | connections <80% of max | ~1,200 QPS |
| `orders.events` | n/a | undelivered message age <60s | n/a | ~1,500 msg/s |
| `orders-fulfillment` | n/a | task retry rate <5% | queue depth <10K | ~500 tasks/s max |

## Investigation Runbooks

### Symptom: Order API returning 5xx errors

1. Check Cloud Run service health:
   ```bash
   gcloud run services describe orders-api --region=us-central1
   gcloud run revisions list --service=orders-api --region=us-central1
   ```
2. Check error logs:
   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" resource.labels.service_name="orders-api" severity>=ERROR' --limit=50
   ```
3. Is upstream dependency healthy? Check `orders-prod-db` via Cloud SQL metrics.
4. **MUTATION — requires explicit approval:** If a bad revision is deployed: `gcloud run services update-traffic orders-api --to-revisions=PREV_REV=100 --region=us-central1` (blast radius: all orders-api traffic).

### Symptom: Order fulfillment delayed

1. Check Cloud Tasks queue depth:
   ```bash
   gcloud tasks queues describe orders-fulfillment --location=us-central1
   ```
2. Check orders-worker logs and error rate:
   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" resource.labels.service_name="orders-worker" severity>=ERROR' --limit=50
   ```
3. Check Pub/Sub subscription undelivered message age for `orders.events`.

## Stack-Specific Tooling

- GCP commands: `skills/cloud-cost-investigate/examples/gcp.md`
- Cloud Run: `gcloud run` CLI
- Cloud SQL: `gcloud sql` CLI
- Pub/Sub: `gcloud pubsub` CLI

## Assumptions and Caveats

- This catalog was built from Terraform source at commit `a3f9c12` (2026-04-20). Running infrastructure may have drifted — recommend re-running service-discovery before any incident investigation.
- `orders-dev-db` is in the catalog but carries `env=dev`. It receives no production traffic. Its presence here is for completeness; operators responding to production incidents should focus on `orders-prod-db`.
- The Pub/Sub topic `orders.events` is global; subscribers (payments-service, inventory-service) are not in scope for this catalog — they are recorded as dependencies only.
- Signal envelope thresholds are from Terraform SLO declarations and team runbooks as of the cataloging date. Verify against current Cloud Monitoring alert policies before relying on them.

## Open Questions

(none raised during this discovery run)
