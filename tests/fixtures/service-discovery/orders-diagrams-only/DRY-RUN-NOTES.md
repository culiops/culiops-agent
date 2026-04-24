# Dry-run of `service-discovery` against `orders-diagrams-only`

Simulated run of the real-discovery path against this fixture. Recorded on 2026-04-24.

## Goal

Validate the real-discovery workflow with **diagrams only** — no text documentation at all. This exercises a narrower input surface than `payments-docs-only`: the skill has only a Mermaid file and a placeholder image, with no supporting runbook or text docs to provide account IDs, credentials paths, or operational context. Also validates GCP as the target cloud, exercising `cloud-discovery/gcp.md` templates.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detection routing (no IaC → diagrams → real-discovery) | No IaC files present; `.mmd` + `.png` doc signatures detected |
| Diagrams-only (no text documents) | No markdown, runbook, or text files — only structured diagram and image |
| Mermaid structured parsing | `system-architecture.mmd` matched by `doc-detectors/mermaid.md` — flowchart with `subgraph` groupings, node labels, and edge annotations |
| Image vision fallback | `network-topology.png` matched by `doc-detectors/image.md` — placeholder; simulated vision extraction |
| GCP cloud context | Project `orders-prod` extracted from Mermaid subgraph label; `cloud-discovery/gcp.md` templates used |
| Missing region in diagrams | No region specified in any diagram — skill correctly asked operator at Step 3R |
| Cloud Load Balancing as implicit resource | Mermaid shows `Cloud Load Balancing` as an external node — Cloud Run has implicit LB; skill handles this correctly |
| All resources found in cloud | No `documented-not-found` or `undocumented` flags — all 5 diagram resources match cloud results |

## Step-by-step simulation

### Step 1: Detection

**IaC detector scan:** loaded all `tool-detectors/*.md` files. No file in the repo matched any IaC detector's `## File signatures` section. Zero IaC tools detected.

**Document detector scan:** loaded all `doc-detectors/*.md` files. Two matches:

| File | Format | Detected by |
|------|--------|-------------|
| `system-architecture.mmd` | Mermaid diagram | `doc-detectors/mermaid.md` |
| `network-topology.png` | Architecture image | `doc-detectors/image.md` |

**Presentation:**

> "No IaC files found in this directory. However, I found diagrams that may describe the infrastructure:
>
> | File | Format | Detected by |
> |------|--------|-------------|
> | `system-architecture.mmd` | Mermaid diagram | `doc-detectors/mermaid.md` |
> | `network-topology.png` | Architecture image | `doc-detectors/image.md` |
>
> I can switch to **real-infrastructure discovery mode** — I'll extract resource hints from these diagrams, then verify against live cloud APIs (read-only) to build the same service catalog.
>
> **GATE: Switch to real-discovery mode?**"

**Operator response:** confirmed.

### Step 2R: Document parsing and resource hint extraction

**Parse order (reliability):** structured → image. No text documents to parse.

**Structured diagram — `system-architecture.mmd` (High confidence):**

Parsed the Mermaid flowchart syntax. Extracted:

| Element | Type | Node ID | Value | Details |
|---------|------|---------|-------|---------|
| Subgraph (outer) | project context | — | "GCP project: orders-prod" | Project identifier |
| Subgraph | grouping | — | "Cloud Run" | Compute layer |
| Node | Cloud Run Service | `API` | "orders-api / Cloud Run Service" | Compute |
| Subgraph | grouping | — | "Data Layer" | Data layer |
| Node | Cloud SQL | `DB` | "orders-db / Cloud SQL PostgreSQL 15" | Database |
| Node | Memorystore | `Cache` | "orders-cache / Memorystore Redis" | Cache |
| Subgraph | grouping | — | "Async" | Async layer |
| Node | Pub/Sub | `Events` | "orders-events / Pub/Sub Topic" | Messaging |
| Subgraph | grouping | — | "Storage" | Storage layer |
| Node | Cloud Storage | `Files` | "orders-attachments / Cloud Storage" | Object storage |
| Node (external) | Load Balancer | `LB` | "Cloud Load Balancing" | Entry point, outside project subgraph |

Edges:
- `LB` → `API` (no label — implicit HTTPS)
- `API` → `DB` (label: "SQL")
- `API` → `Cache` (label: "Redis")
- `API` → `Events` (label: "publish")
- `API` → `Files` (label: "upload")

Result: 5 resources inside the project boundary, 1 external entry point (Cloud LB), 5 relationships, 1 project context (`orders-prod`). All High confidence — explicitly named with identifiers in structured Mermaid syntax.

Note: Cloud Load Balancing is shown as an external node, but for Cloud Run services the load balancer is implicit (managed by the platform). The skill records it as an entry point annotation, not as a separate discoverable resource.

**Image — `network-topology.png` (Low confidence, simulated):**

The fixture contains a 1x1 pixel placeholder PNG. In a real run, the skill would use vision to extract network topology details. For simulation purposes, assume vision would extract:
- A cloud boundary labelled "GCP" containing boxes for "Cloud Run", "Cloud SQL", "Redis", "Pub/Sub", and "GCS"
- Arrows showing traffic flow from an internet icon through the Cloud Run box to the data services
- No additional resources beyond what the Mermaid diagram shows

Result: corroborates the same 5 resources. All Low confidence due to image source.

**Hint consolidation:**

Cross-referencing both sources, 5 unique resource hints:

| # | Hint | Type | Sources | Confidence |
|---|------|------|---------|------------|
| 1 | `orders-api` | Cloud Run Service | mermaid (High) + image (Low) | **High** |
| 2 | `orders-db` | Cloud SQL PostgreSQL 15 | mermaid (High) + image (Low) | **High** |
| 3 | `orders-cache` | Memorystore Redis | mermaid (High) + image (Low) | **High** |
| 4 | `orders-events` | Pub/Sub Topic | mermaid (High) + image (Low) | **High** |
| 5 | `orders-attachments` | Cloud Storage Bucket | mermaid (High) + image (Low) | **High** |

Cloud context:
- Provider: GCP
- Project: `orders-prod` (from Mermaid subgraph label)
- Region: **unknown** — no region specified in any diagram

**GATE: Confirm resource hints.** Operator confirmed.

### Step 3R: Cloud context resolution

**Credential probe (simulated):**

| Provider | Command | Result |
|----------|---------|--------|
| GCP | `gcloud config get project` | `orders-prod` |
| GCP | `gcloud config get compute/region` | *(not set)* |

**Cross-reference with document hints:**

| Provider | Identity Source | Value | Doc Hint | Match? |
|----------|----------------|-------|----------|--------|
| GCP | `gcloud config get project` | `orders-prod` | Project: `orders-prod` (from Mermaid) | Full match |
| GCP | region | *(not set)* | Region: unknown | No region in either source |

**Region resolution:** Neither the diagrams nor the gcloud config specified a region. The skill asked the operator:

> "No region found in diagrams or local gcloud config. Which GCP region should I use for discovery queries?"

**Operator response:** `us-central1`.

**GATE: Is this the correct target environment?** Operator confirmed: project `orders-prod`, region `us-central1`.

### Step 4R: Converging discovery

**Seed A:** 5 confirmed document hints from Step 2R.

**Seed B:** Loaded `cloud-discovery/gcp.md` templates. Proposed 2 broad discovery queries:

| # | Query | Scope | Source |
|---|-------|-------|--------|
| 1 | `gcloud asset search-all-resources --scope=projects/orders-prod --query="name:orders"` | All resources in project with "orders" in name | `cloud-discovery/gcp.md` |
| 2 | `gcloud asset search-all-resources --scope=projects/orders-prod --asset-types="run.googleapis.com/Service,sqladmin.googleapis.com/Instance,redis.googleapis.com/Instance,pubsub.googleapis.com/Topic,storage.googleapis.com/Bucket"` | All resources of hinted types in project | `cloud-discovery/gcp.md` |

**GATE 4a: Approve discovery queries.** Operator approved both.

**Simulated cloud query results (Seed B):**

| # | Resource | Type | Resource Name |
|---|----------|------|---------------|
| 1 | `orders-api` | Cloud Run Service | `projects/orders-prod/locations/us-central1/services/orders-api` |
| 2 | `orders-db` | Cloud SQL Instance | `projects/orders-prod/instances/orders-db` |
| 3 | `orders-cache` | Memorystore Redis | `projects/orders-prod/locations/us-central1/instances/orders-cache` |
| 4 | `orders-events` | Pub/Sub Topic | `projects/orders-prod/topics/orders-events` |
| 5 | `orders-attachments` | Cloud Storage Bucket | `projects/orders-prod/buckets/orders-attachments` |

All 5 document hints matched cloud resources. No cloud-only resources found. No document-only resources missing from cloud.

**Merge seeds and assign confidence:**

| # | Resource | Type | Source | Confidence | Flag |
|---|----------|------|--------|------------|------|
| 1 | `orders-api` | Cloud Run Service | docs + cloud | **High** | |
| 2 | `orders-db` | Cloud SQL PostgreSQL 15 | docs + cloud | **High** | |
| 3 | `orders-cache` | Memorystore Redis | docs + cloud | **High** | |
| 4 | `orders-events` | Pub/Sub Topic | docs + cloud | **High** | |
| 5 | `orders-attachments` | Cloud Storage Bucket | docs + cloud | **High** | |

**GATE 4b: Confirm resource list.** Operator confirmed. All resources matched cleanly — no flags needed.

### Step 5R: Detailed resource enrichment

**Enrichment (simulated) per resource:**

| Resource | Key findings |
|----------|-------------|
| `orders-api` | Cloud Run, gen2, CPU 2 / Memory 1Gi, max instances 10, min instances 1, region `us-central1`, revision `orders-api-00042-abc`, concurrency 80, ingress "all", authenticated via IAM |
| `orders-db` | PostgreSQL 15.3, `db-custom-4-16384` (4 vCPU, 16 GB RAM), HA enabled, `us-central1`, private IP only, automated backups daily, storage 100 GB SSD |
| `orders-cache` | Redis 7.0, 5 GB, Standard tier (HA), `us-central1-a`, private endpoint, `AUTH` enabled |
| `orders-events` | Pub/Sub topic, 2 subscriptions (`orders-events-processor`, `orders-events-analytics`), message retention 7 days |
| `orders-attachments` | Standard storage class, `us-central1`, uniform bucket-level access, versioning enabled, lifecycle rule (delete after 365 days) |

**Dependency walking:**

- Cloud LB (implicit) → `orders-api` (Cloud Run managed): entry point
- `orders-api` → `orders-db` (VPC connector + private IP): critical path
- `orders-api` → `orders-cache` (VPC connector + private endpoint): critical path
- `orders-api` → `orders-events` (Pub/Sub publish, IAM role `roles/pubsub.publisher`): async
- `orders-api` → `orders-attachments` (GCS upload, IAM role `roles/storage.objectCreator`): async
- Two Pub/Sub subscriptions (`orders-events-processor`, `orders-events-analytics`) consume from `orders-events` — these are boundary dependencies (different services consuming the topic)

**Runbooks built:** 2 investigation trees covering "order requests slow/timing out" and "order requests returning errors". Upstream-first branches check Cloud SQL and Memorystore before narrowing on Cloud Run instance health.

**GATE: Validate runbooks.** Operator validated.

### Step 6R: Write catalog

Catalog written to `.culiops/service-discovery/orders.md`.

**GATE: Review catalog.** Operator approved.

## Findings

### F1 — Diagrams-only works: no text documentation required

The skill successfully completed the full real-discovery workflow with only a Mermaid file and a placeholder image. The Mermaid diagram provided enough structured data (5 resource nodes, 5 edges, project context from subgraph label) to seed the cloud discovery queries. Text documents are helpful (they provide account IDs, operational context, alarm names) but are not required.

### F2 — Missing region handled correctly

No diagram included a region. The gcloud config also had no region set. The skill correctly identified the gap at Step 3R and asked the operator rather than guessing. This is the expected behavior: "NO ASSUMPTIONS. IF UNCLEAR, ASK THE HUMAN."

### F3 — Cloud Load Balancing handled correctly as implicit resource

The Mermaid diagram shows `Cloud Load Balancing` as an external node connected to the Cloud Run service. The skill correctly treated this as an entry-point annotation rather than a separate discoverable resource. Cloud Run services have an implicit load balancer managed by the platform — there is no standalone `google_compute_forwarding_rule` or similar resource to discover. The catalog records the entry point in the dependency graph without adding a phantom resource to the inventory.

### F4 — GCP Cloud Asset Inventory queries work for discovery

The `cloud-discovery/gcp.md` template's `gcloud asset search-all-resources` queries correctly scoped by project and asset type. All 5 resources were found. The scope-based approach (project-level) is the GCP equivalent of the AWS tag-based approach — both are broad enough to catch undocumented resources while still being scoped to the operator-confirmed environment.

### F5 — Clean match (no flags) is a valid outcome

Unlike `payments-docs-only` which exercised both `undocumented` and `documented-not-found` flags, this fixture has a 1:1 match between document hints and cloud resources. This validates that the merge logic does not force-generate flags when none are warranted.

## What a produced doc would look like

`.culiops/service-discovery/orders.md` would contain:

- Header: discovery source=real-discovery, date=2026-04-24, cloud context=GCP / `orders-prod` / `us-central1`, documents used=`system-architecture.mmd`, `network-topology.png`.
- `## Overview` — order management API, discovered via real-discovery (diagrams + live cloud APIs), runs on Cloud Run in GCP project `orders-prod`, region `us-central1`.
- `## Prerequisites` — `gcloud` CLI; auth via `gcloud auth login`; least-privilege: `roles/viewer` on project (or scoped to Cloud Run, Cloud SQL, Memorystore, Pub/Sub, Cloud Storage); mutations listed (Cloud Run traffic splitting, Cloud SQL failover — both flagged `MUTATION`).
- `## Resource Inventory` — 5 rows, all High confidence:

  | Category | Type | Name | Confidence | Source |
  |----------|------|------|------------|--------|
  | compute | Cloud Run Service | `orders-api` | High | docs + cloud |
  | database | Cloud SQL PostgreSQL 15 | `orders-db` | High | docs + cloud |
  | database | Memorystore Redis | `orders-cache` | High | docs + cloud |
  | messaging | Pub/Sub Topic | `orders-events` | High | docs + cloud |
  | storage | Cloud Storage Bucket | `orders-attachments` | High | docs + cloud |

- `## Naming Patterns` — `orders-<component>` detected from actual resource names.
- `## Identifying Dimensions` — GCP project, region, Cloud Run revision, Cloud SQL HA status.
- `## Dependency Graph` — Cloud LB (implicit) → `orders-api` (entry point), `orders-api` → `orders-db` (critical path, SQL), `orders-api` → `orders-cache` (critical path, Redis), `orders-api` → `orders-events` (async, Pub/Sub publish), `orders-api` → `orders-attachments` (async, GCS upload). Boundary: `orders-events-processor` and `orders-events-analytics` subscriptions (external consumers).
- `## Signal Envelopes` — none declared (no text docs with alarm thresholds); all recorded as "not declared — establish baseline."
- `## Investigation Runbooks` — 2 trees: "order requests slow", "order requests erroring."
- `## Stack-Specific Tooling` — `examples/gcp.md`.
- `## Unresolved References` — none.
- `## Assumptions and Caveats` — mandatory real-discovery caveats; region `us-central1` was provided by operator (not in any document); no signal envelopes found (diagrams-only input lacks alarm thresholds); Pub/Sub subscriptions `orders-events-processor` and `orders-events-analytics` are outside the service boundary.
- `## Open Questions` — "Who owns the `orders-events-processor` and `orders-events-analytics` subscriptions? If they belong to different teams, the `orders-events` topic is a shared contract."
