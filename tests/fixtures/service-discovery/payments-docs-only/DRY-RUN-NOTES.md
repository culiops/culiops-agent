# Dry-run of `service-discovery` against `payments-docs-only`

Simulated run of the real-discovery path against this fixture. Recorded on 2026-04-24.

## Goal

Validate the real-discovery workflow end-to-end: no IaC in the repo, only documentation and diagrams. The skill must detect the absence of IaC, parse three document formats (structured diagram, text, image), extract resource hints, simulate cloud API queries, merge both seeds with confidence flags, and produce the same catalog format as the IaC path.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detection routing (no IaC → docs → real-discovery) | No `*.tf`, `Chart.yaml`, `*.bicep`, `ecspresso.yml`, or other IaC files present; doc signatures detected instead |
| Structured diagram parsing | `architecture.drawio` matched by `doc-detectors/drawio.md` — 4 resource nodes, 3 relationship edges, 1 region container parsed from XML |
| Text keyword extraction | `runbook.md` matched by `doc-detectors/markdown.md` — 5 resource mentions, account ID, region, CloudWatch alarm names, incident procedures |
| Image vision (simulated) | `infra-overview.png` matched by `doc-detectors/image.md` — placeholder 1x1 PNG; vision would extract resource boxes and arrows from a real diagram |
| Cloud context resolution | Account `123456789012` and region `us-east-1` extracted from `runbook.md`, cross-referenced with simulated `aws sts get-caller-identity` |
| Converging discovery merge | Document hints (Seed A: 5 unique resources) merged with simulated cloud results (Seed B: 5 cloud resources); exercises all three confidence outcomes |
| Confidence flags: `undocumented` | SQS DLQ (`payments-dlq`) found in cloud but not referenced in any document → Medium confidence, `undocumented` flag |
| Confidence flags: `documented-not-found` | EC2 instance (`payments-legacy-worker`) mentioned in `runbook.md` but not found in cloud → Low confidence, `documented-not-found` flag |
| Same catalog output format | Real-discovery produces `.culiops/service-discovery/payments.md` with the same section order and structure as the IaC path |

## Step-by-step simulation

### Step 1: Detection

**IaC detector scan:** loaded all `tool-detectors/*.md` files. No file in the repo matched any IaC detector's `## File signatures` section. Zero IaC tools detected.

**Document detector scan:** loaded all `doc-detectors/*.md` files. Three matches:

| File | Format | Detected by |
|------|--------|-------------|
| `architecture.drawio` | Draw.io diagram | `doc-detectors/drawio.md` |
| `runbook.md` | Markdown documentation | `doc-detectors/markdown.md` |
| `infra-overview.png` | Architecture image | `doc-detectors/image.md` |

**Presentation:**

> "No IaC files found in this directory. However, I found documentation and diagrams that may describe the infrastructure:
>
> | File | Format | Detected by |
> |------|--------|-------------|
> | `architecture.drawio` | Draw.io diagram | `doc-detectors/drawio.md` |
> | `runbook.md` | Markdown documentation | `doc-detectors/markdown.md` |
> | `infra-overview.png` | Architecture image | `doc-detectors/image.md` |
>
> I can switch to **real-infrastructure discovery mode** — I'll extract resource hints from these documents, then verify against live cloud APIs (read-only) to build the same service catalog.
>
> **GATE: Switch to real-discovery mode?**"

**Operator response:** confirmed.

### Step 2R: Document parsing and resource hint extraction

**Parse order (reliability):** structured → text → image.

**Structured diagram — `architecture.drawio` (High confidence):**

Parsed the `mxfile` XML. Extracted:

| Element | Type | ID | Value | Details |
|---------|------|----|-------|---------|
| Region container | grouping | `region-1` | "AWS us-east-1" | Placement context |
| Node | ALB | `alb-1` | "payments-alb / Application Load Balancer" | AWS ELB shape |
| Node | ECS | `ecs-1` | "payments-api / ECS Fargate" | AWS ECS shape |
| Node | RDS | `rds-1` | "payments-db / RDS PostgreSQL 15" | AWS RDS shape |
| Node | ElastiCache | `cache-1` | "payments-cache / ElastiCache Redis 7" | AWS ElastiCache shape |

Edges:
- `alb-1` → `ecs-1` (label: "HTTPS")
- `ecs-1` → `rds-1` (label: "JDBC")
- `ecs-1` → `cache-1` (label: "Redis protocol")

Result: 4 resources, 3 relationships, 1 region context. All High confidence — explicitly named with identifiers in structured XML format.

**Text document — `runbook.md` (Medium confidence):**

Keyword scan extracted:

| Resource | Type | Confidence | Details |
|----------|------|------------|---------|
| `payments-alb` | ALB | Medium | Listed under "Load Balancer" section with listener and target group details |
| `payments-api` | ECS Fargate | Medium | Listed under "Compute" with cluster `payments-prod`, desired count 4 |
| `payments-db` | RDS PostgreSQL 15 | Medium | Listed under "Database" with Multi-AZ, `db.r6g.xlarge`, endpoint |
| `payments-cache` | ElastiCache Redis 7 | Medium | Listed under "Cache" with `cache.r6g.large`, port 6379 |
| `payments-legacy-worker` | EC2 (t3.medium) | Medium | Listed under "Compute" with note "being migrated to ECS" |

Cloud context clues:
- Account: `123456789012` (from "runs in AWS account `123456789012`")
- Region: `us-east-1` (from "region `us-east-1`")
- ECS cluster: `payments-prod`
- CloudWatch alarms: `payments-*` prefix (6 alarms enumerated)
- SNS topic: `payments-alerts`
- Secrets Manager: `payments/prod/db-credentials`

**Image — `infra-overview.png` (Low confidence, simulated):**

The fixture contains a 1x1 pixel placeholder PNG. In a real run, the skill would use vision to extract resource labels, arrows, and grouping boundaries from the image. For simulation purposes, assume vision would extract:
- A box labelled "ALB" connected to a box labelled "ECS" (Low confidence — label text partially obscured)
- A box labelled "PostgreSQL" and a box labelled "Redis" both connected from the ECS box
- A dashed boundary labelled "us-east-1"

Result: corroborates the same 4 resources as the other two sources, adding no new information. All Low confidence due to image source.

**Hint consolidation (deduplication):**

Cross-referencing all three sources, 5 unique resource hints:

| # | Hint | Type | Sources | Confidence |
|---|------|------|---------|------------|
| 1 | `payments-alb` | ALB | drawio (High) + runbook (Medium) + image (Low) | **High** |
| 2 | `payments-api` | ECS Fargate | drawio (High) + runbook (Medium) + image (Low) | **High** |
| 3 | `payments-db` | RDS PostgreSQL 15 | drawio (High) + runbook (Medium) + image (Low) | **High** |
| 4 | `payments-cache` | ElastiCache Redis 7 | drawio (High) + runbook (Medium) + image (Low) | **High** |
| 5 | `payments-legacy-worker` | EC2 | runbook (Medium) only | **Medium** |

Cloud context:
- Provider: AWS
- Account: `123456789012`
- Region: `us-east-1`

**GATE: Confirm resource hints.** Operator confirmed.

### Step 3R: Cloud context resolution

**Credential probe (simulated):**

| Provider | Command | Result |
|----------|---------|--------|
| AWS | `aws sts get-caller-identity` | Account `123456789012`, user `arn:aws:iam::123456789012:user/operator`, region `us-east-1` |

**Cross-reference with document hints:**

| Provider | Identity Source | Value | Doc Hint | Match? |
|----------|----------------|-------|----------|--------|
| AWS | `aws sts get-caller-identity` | Account `123456789012`, `us-east-1` | Account `123456789012`, region `us-east-1` | Full match |

**GATE: Is this the correct target environment?** Operator confirmed.

### Step 4R: Converging discovery

**Seed A:** 5 confirmed document hints from Step 2R.

**Seed B:** Loaded `cloud-discovery/aws.md` templates. Proposed 2 broad discovery queries:

| # | Query | Scope | Source |
|---|-------|-------|--------|
| 1 | `aws resourcegroupstaggingapi get-resources --tag-filters Key=service,Values=payments` | All resources tagged `service=payments` | `cloud-discovery/aws.md` |
| 2 | `aws resourcegroupstaggingapi get-resources --resource-type-filters ... --tag-filters Key=Name,Values=payments-*` | Resources with Name prefix `payments-*` | `cloud-discovery/aws.md` |

**GATE 4a: Approve discovery queries.** Operator approved both.

**Simulated cloud query results (Seed B):**

| # | Resource | Type | ARN / ID |
|---|----------|------|----------|
| 1 | `payments-alb` | ALB | `arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/payments-alb/abc123` |
| 2 | `payments-api` | ECS Service | `arn:aws:ecs:us-east-1:123456789012:service/payments-prod/payments-api` |
| 3 | `payments-db` | RDS Instance | `arn:aws:rds:us-east-1:123456789012:db:payments-db` |
| 4 | `payments-cache` | ElastiCache | `arn:aws:elasticache:us-east-1:123456789012:cluster:payments-cache` |
| 5 | `payments-dlq` | SQS Queue | `arn:aws:sqs:us-east-1:123456789012:payments-dlq` |

Note: `payments-legacy-worker` (EC2) was NOT found in cloud results. `payments-dlq` (SQS) was NOT referenced in any document.

**Merge seeds and assign confidence:**

| # | Resource | Type | Source | Confidence | Flag |
|---|----------|------|--------|------------|------|
| 1 | `payments-alb` | ALB | docs + cloud | **High** | |
| 2 | `payments-api` | ECS Fargate | docs + cloud | **High** | |
| 3 | `payments-db` | RDS PostgreSQL 15 | docs + cloud | **High** | |
| 4 | `payments-cache` | ElastiCache Redis 7 | docs + cloud | **High** | |
| 5 | `payments-dlq` | SQS Queue | cloud only | **Medium** | `undocumented` |
| 6 | `payments-legacy-worker` | EC2 | docs only | **Low** | `documented-not-found` |

**GATE 4b: Confirm resource list.** Operator confirmed. Noted that `payments-legacy-worker` is expected to be absent (decommissioned). `payments-dlq` is a legitimate resource belonging to this service — likely a dead-letter queue for failed async processing.

### Step 5R: Detailed resource enrichment

**Enrichment (simulated) per resource:**

| Resource | Key findings |
|----------|-------------|
| `payments-alb` | HTTPS listener (443), target group `payments-api-tg` (8080), 4 healthy targets, idle timeout 60s |
| `payments-api` | Cluster `payments-prod`, 4 running tasks, Fargate, CPU 1024 / Memory 2048, image tag `2026.04.1` |
| `payments-db` | PostgreSQL 15.4, `db.r6g.xlarge`, Multi-AZ enabled, 500 GB gp3, encrypted (KMS), **3 read replicas** |
| `payments-cache` | Redis 7.0, `cache.r6g.large`, cluster mode disabled, 1 replica, automatic failover enabled |
| `payments-dlq` | Standard queue, retention 14 days, **14,200 messages currently in queue**, no redrive policy back to source |

**Surprises:**

- **`payments-db` has 3 read replicas** — the runbook mentions only "Multi-AZ: enabled" without listing replicas. The read replicas are a relevant enrichment finding.
- **`payments-dlq` has 14,200 messages** — the DLQ is not empty, which is a potential operational concern. This is informational only — no gate required, but recorded in the catalog.
- **SNS topic `payments-alerts`** was discovered via the ALB alarm actions. The topic references a PagerDuty endpoint outside the service boundary — recorded as a boundary dependency.

**Dependency walking:**

- ALB → ECS service (target group membership): critical path
- ECS → RDS (security group rule allowing 5432): critical path
- ECS → ElastiCache (security group rule allowing 6379): critical path
- ECS → Secrets Manager (task definition secret reference): critical path (startup dependency)
- ECS → ECR (image pull): critical path (deployment dependency)
- All resources → same VPC `vpc-payments-prod`
- ALB → public subnet; ECS + RDS + ElastiCache → private subnets
- CloudWatch alarms → SNS topic `payments-alerts` → PagerDuty (boundary)

**Runbooks built:** 3 investigation trees covering "payment requests slow/timing out", "payment requests returning errors", and "background processing delayed" (the DLQ finding prompted this third tree). Upstream-first branches in all three.

**GATE: Validate runbooks.** Operator validated.

### Step 6R: Write catalog

Catalog written to `.culiops/service-discovery/payments.md`.

**GATE: Review catalog.** Operator approved.

## Findings

### F1 — Detection routing works correctly for docs-only repos

The skill correctly detected zero IaC tools, scanned doc-detectors, matched three document formats, and prompted for real-discovery mode. The gate structure (confirm before switching) prevents accidental cloud queries when the operator intended to provide IaC files.

### F2 — Hint deduplication across three source types works

The same 4 core resources appeared in all three sources (drawio, runbook, image). The consolidation step correctly merged them into 4 unique hints with the highest confidence from any source. The legacy worker appeared in only one source and was correctly kept at Medium confidence.

### F3 — `documented-not-found` handling works as designed

`payments-legacy-worker` was mentioned in `runbook.md` with a note about decommissioning. The cloud query did not find it. The merge correctly flagged it `documented-not-found` with Low confidence. It appears in the catalog's `## Unresolved References` section, not in the main inventory. The caveats section includes the standard real-discovery note about documents potentially being outdated.

### F4 — `undocumented` handling works as designed

`payments-dlq` was found via the cloud tag/name queries but was not mentioned in any document. The merge correctly flagged it `undocumented` with Medium confidence. It appears in the main inventory with the note: "Discovered via cloud API only — not referenced in any source document. Verify this resource belongs to this service." The operator confirmed it belongs to this service at Gate 4b.

### F5 — All 6 gates fire correctly

| Gate | Step | Fired? | Purpose |
|------|------|--------|---------|
| Switch to real-discovery | Step 1 | Yes | Prevents accidental cloud queries |
| Confirm resource hints | Step 2R | Yes | Operator reviews parsed hints before cloud queries |
| Confirm target environment | Step 3R | Yes | Prevents querying wrong account/region |
| Approve discovery queries | Step 4R (4a) | Yes | Operator sees exact queries before execution |
| Confirm resource list | Step 4R (4b) | Yes | Operator reviews merged list with confidence flags |
| Validate runbooks | Step 5R | Yes | Operator validates investigation trees |

## What a produced doc would look like

`.culiops/service-discovery/payments.md` would contain:

- Header: discovery source=real-discovery, date=2026-04-24, cloud context=AWS / `123456789012` / `us-east-1`, documents used=`architecture.drawio`, `runbook.md`, `infra-overview.png`.
- `## Overview` — payment processing API, discovered via real-discovery (documents + live cloud APIs), runs on ECS Fargate in us-east-1.
- `## Prerequisites` — `aws` CLI v2; auth via `aws sso login` or IAM credentials; least-privilege: `ReadOnlyAccess` (or scoped to ECS, RDS, ElastiCache, SQS, ELBv2, CloudWatch); mutations listed (ECS service update, RDS failover — both flagged `MUTATION`).
- `## Resource Inventory` — 5 rows (4 High confidence, 1 Medium/undocumented), grouped by category:

  | Category | Type | Name | Confidence | Flag | Source |
  |----------|------|------|------------|------|--------|
  | network | ALB | `payments-alb` | High | | docs + cloud |
  | compute | ECS Fargate | `payments-api` | High | | docs + cloud |
  | database | RDS PostgreSQL 15 | `payments-db` | High | | docs + cloud |
  | database | ElastiCache Redis 7 | `payments-cache` | High | | docs + cloud |
  | messaging | SQS Queue | `payments-dlq` | Medium | `undocumented` | cloud only |

- `## Naming Patterns` — `payments-<component>` detected from actual resource names.
- `## Identifying Dimensions` — ECS cluster name, RDS Multi-AZ status, Fargate task revision, image tag.
- `## Dependency Graph` — ALB → ECS (critical path), ECS → RDS (critical path), ECS → ElastiCache (critical path), ECS → Secrets Manager (startup), CloudWatch → SNS (boundary). `payments-dlq` has no inbound edge from any confirmed resource — recorded as isolated.
- `## Signal Envelopes` — populated from CloudWatch alarm thresholds found in enrichment (5xx rate > 1%, p99 > 2000ms, DB connections > 80%, DB CPU > 80%, cache memory > 75%, cache evictions > 100/min).
- `## Investigation Runbooks` — 3 trees: "payment requests slow", "payment requests erroring", "DLQ messages accumulating".
- `## Stack-Specific Tooling` — `examples/aws.md`; PagerDuty as "ask the team."
- `## Unresolved References` — `payments-legacy-worker` (EC2): "Referenced in `runbook.md` under Compute section as 'being migrated to ECS'. Not found in the live environment. Likely decommissioned."
- `## Assumptions and Caveats` — mandatory real-discovery caveats: catalog built from documents + live cloud APIs (not IaC); documents may be outdated; `documented-not-found` resources listed in Unresolved References; `undocumented` resources may belong to a different service; no drift detection without IaC; DLQ has 14,200 messages (operational concern); 3 read replicas on RDS not mentioned in runbook.
- `## Open Questions` — "Is `payments-dlq` fed by a source queue not captured in this service? The DLQ has no visible redrive policy linking it to a source."
