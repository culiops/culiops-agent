# Dry-run of `service-discovery` against `payments-docs-only`

Simulated run of the real-discovery path against this fixture. First recorded 2026-04-24; re-run 2026-10-26 for the membership/absence rules, the Medium cap on document hints, the probe-batch gate, secrets by projection and the Mermaid + unknown-region cases; re-run 2026-10-27 for the same-identifier rule for High, the derived-pattern rule for membership, `declared` vs `observed` envelopes and edge bases.

## Goal

Validate the real-discovery workflow end-to-end: no IaC in the repo, only documentation and diagrams. The skill must detect the absence of IaC, parse four document formats (draw.io, Mermaid, text, image), extract resource hints, ask for a region the documents do not settle, run approved read-only queries, merge both seeds with confidence flags and membership signals, and produce the same catalog format as the IaC path.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detection routing (no IaC → docs → real-discovery) | No `*.tf`, `Chart.yaml`, `ecspresso.yml`, or other IaC files present; doc signatures detected instead |
| Structured diagram parsing (draw.io) | `architecture.drawio` matched by `doc-detectors/drawio.md` — 4 resource nodes, 3 relationship edges, 1 region container parsed from XML |
| Structured diagram parsing (Mermaid) | `flows.mmd` matched by `doc-detectors/mermaid.md` — 5 resource nodes, 1 external `Client` node, 5 edges (one dotted), no subgraph, no region |
| Text keyword extraction | `runbook.md` matched by `doc-detectors/markdown.md` — 5 resource mentions, account ID, two candidate regions, 6 CloudWatch alarm names, 1 SNS topic, 1 secret name, incident procedures |
| Image vision (simulated) | `infra-overview.png` matched by `doc-detectors/image.md` — placeholder 1x1 PNG; vision would extract resource boxes and arrows from a real diagram |
| Document hints capped at Medium | Every doc-derived hint is at most Medium (the draw.io nodes are no longer High); only a live match on the **same identifier** raises a row to High. A match on name or type alone stays Medium with the `name-match-only` flag |
| Region unknown → ask | `flows.mmd` has no region; `runbook.md` names `us-east-1` (normal) and `us-west-2` (failover drills) without saying which serves; the profile has no default region → the skill asks the operator |
| Probe batch approved before running | `sts get-caller-identity` and `configure get region` are listed and approved before any call |
| Converging discovery merge | Document hints (Seed A: 5 unique) merged with cloud results (Seed B); exercises membership signals and every flag |
| `undocumented` + membership signal | SQS DLQ `payments-dlq` (tag `service=payments`) and 3 RDS read replicas (referenced by confirmed `payments-db`) — cloud only, Medium |
| `documented-not-found` | EC2 `payments-legacy-worker` (runbook + `flows.mmd`) — Low, `not-found (queried 123456789012/us-east-1)` |
| Unattributed — operator assigns | RDS `analytics-db` returned by a region-wide describe; no tag, no name match, no reference → not in the inventory |
| Owner column | `aws:cloudformation:stack-name` on the ALB and the DLQ → `cloudformation (<stack>)`, recognition only |
| Secrets by projection | Enrichment commands project fields with `--query`; `payments/prod/db-credentials` recorded by name only; SNS subscription endpoint withheld |
| Same catalog output format | Real-discovery produces `.culiops/service-discovery/payments.md` with the same section order as the IaC path |

## Step-by-step simulation

### Step 1: Detection

**IaC detector scan:** loaded all `tool-detectors/*.md` files. No file in the repo matched any IaC detector's `## File signatures` section. Zero IaC tools detected (also no recognition-only tools: no `template.yaml`, `serverless.yml`, `cdk.json`).

**Document detector scan:** loaded all `doc-detectors/*.md` files. Four matches:

| File | Format | Detected by |
|------|--------|-------------|
| `architecture.drawio` | Draw.io diagram | `doc-detectors/drawio.md` |
| `flows.mmd` | Mermaid diagram | `doc-detectors/mermaid.md` |
| `runbook.md` | Markdown documentation | `doc-detectors/markdown.md` |
| `infra-overview.png` | Architecture image | `doc-detectors/image.md` |

**Presentation:**

> "No IaC files found in this directory. However, I found documentation and diagrams that may describe the infrastructure: *(table above)*
>
> I can switch to **real-infrastructure discovery mode** — I'll extract resource hints from these documents, then verify against live cloud APIs (read-only) to build the same service catalog.
>
> **GATE: Switch to real-discovery mode?**"

**Operator response:** confirmed. *(Gate 1)*

### Step 2R: Document parsing and resource hint extraction

**Parse order (reliability):** structured (draw.io, Mermaid) → text → image.

**`architecture.drawio` (Medium):** 1 region container `region-1` ("AWS us-east-1"); nodes `alb-1` payments-alb, `ecs-1` payments-api, `rds-1` payments-db, `cache-1` payments-cache; edges `alb-1`→`ecs-1` (HTTPS), `ecs-1`→`rds-1` (JDBC), `ecs-1`→`cache-1` (Redis protocol). 4 resources, 3 relationships, 1 region context. Diagrams are intent, not state, so these are Medium even though they are explicitly named.

**`flows.mmd` (Medium):** nodes `ALB` payments-alb, `API` payments-api, `DB` payments-db, `Cache` payments-cache, `Worker` payments-legacy-worker (EC2 batch reconcile), external `Client` (not a resource). Edges: `Client`→`ALB` (HTTPS), `ALB`→`API`, `API`→`DB` (SQL), `API`→`Cache` (session and idempotency keys), `Worker`→`DB` (dotted, nightly reconcile). **No region, no account** anywhere in the file.

**`runbook.md` (Medium):**

| Resource | Type | Details |
|----------|------|---------|
| `payments-alb` | ALB | HTTPS 443 listener, target group `payments-api-tg` (8080, `/healthz`), idle timeout 60s |
| `payments-api` | ECS Fargate | Cluster `payments-prod`, desired 4, CPU 1024 / Memory 2048, image `payments-api:latest` |
| `payments-legacy-worker` | EC2 (t3.medium) | "being migrated to ECS", instance `i-0abc123def456789a`, SG `payments-legacy-sg` |
| `payments-db` | RDS PostgreSQL 15 | Multi-AZ, `db.r6g.xlarge`, 500 GB gp3, KMS, port 5432 |
| `payments-cache` | ElastiCache Redis 7 | `cache.r6g.large`, cluster mode off, 1 replica, failover on, port 6379 |

Cloud context clues: account `123456789012`; **regions `us-east-1` (normal) and `us-west-2` (failover drills), not stated which is serving**; ECS cluster `payments-prod`; 6 CloudWatch alarms with prefix `payments-`; SNS topic `payments-alerts`; Secrets Manager name `payments/prod/db-credentials` (a name, recorded as a reference, never fetched).

**Image — `infra-overview.png` (Low, simulated):** 1x1 placeholder. A real run would extract an "ALB" box connected to an "ECS" box, "PostgreSQL" and "Redis" boxes connected from ECS, and a dashed boundary labelled "us-east-1". It corroborates the same four resources and adds nothing new.

**Hint consolidation (5 unique resource hints):**

| # | Hint | Type | Sources | Confidence |
|---|------|------|---------|------------|
| 1 | `payments-alb` | ALB | drawio + flows.mmd + runbook (Medium each) + image (Low) | **Medium** |
| 2 | `payments-api` | ECS Fargate | drawio + flows.mmd + runbook + image | **Medium** |
| 3 | `payments-db` | RDS PostgreSQL 15 | drawio + flows.mmd + runbook + image | **Medium** |
| 4 | `payments-cache` | ElastiCache Redis 7 | drawio + flows.mmd + runbook + image | **Medium** |
| 5 | `payments-legacy-worker` | EC2 | runbook + flows.mmd | **Medium** |

Cloud context: provider AWS; account `123456789012`; region **unresolved** (see Step 3R).

**GATE: Confirm resource hints.** Operator confirmed. *(Gate 2)*

### Step 3R: Cloud context resolution

**Probe batch (shown first; no call is made until approved):**

| # | Command | Purpose |
|---|---------|---------|
| P1 | `aws sts get-caller-identity --profile payments-ro --query '{Account:Account,Arn:Arn}'` | which account the profile points at (STS returns no region) |
| P2 | `aws configure get region --profile payments-ro` | which region the profile would use |

**GATE: Approve probe batch.** Operator approved. *(Gate 3)*

| Probe | Result |
|-------|--------|
| P1 | Account `123456789012`, `arn:aws:iam::123456789012:user/operator` |
| P2 | *(empty — no region configured on the profile)* |

**Cross-reference with document hints:**

| Item | Live | Doc hint | Match? |
|------|------|----------|--------|
| Account | `123456789012` | `123456789012` (runbook) | Match |
| Region | *(not set)* | `us-east-1` (drawio container, runbook hostnames, runbook "normally"), `us-west-2` (runbook failover drills), none in `flows.mmd` | **Unresolved — ask** |

**Region resolution (asked, not guessed):**

> "The profile has no default region, and the documents name two: `us-east-1` (normal) and `us-west-2` (failover drills). `flows.mmd` names none. Which region should I query?"

**Operator response:** `us-east-1`; failover region is not built, do not query it.

**GATE: Is this the correct target environment?** Operator confirmed: account `123456789012`, region `us-east-1`; every later command carries `--profile payments-ro --region us-east-1`. *(Gate 4)*

### Step 4R: Converging discovery

**Seed A:** 5 confirmed document hints from Step 2R.

**Seed B:** loaded `cloud-discovery/aws.md` templates. Proposed 3 queries (all with `--profile payments-ro --region us-east-1`, all projected):

| # | Query | Scope | Source |
|---|-------|-------|--------|
| 1 | `aws resourcegroupstaggingapi get-resources --tag-filters Key=service,Values=payments --query "ResourceTagMappingList[].{arn:ResourceARN,owner:Tags[?Key=='aws:cloudformation:stack-name'].Value\|[0]}"` | Resources tagged `service=payments` (regional; tagged only) | `cloud-discovery/aws.md` |
| 2 | `aws rds describe-db-instances --query 'DBInstances[].{id:DBInstanceIdentifier,src:ReadReplicaSourceDBInstanceIdentifier}'` | All RDS instances in the region (to see replicas) | `cloud-discovery/aws.md` |
| 3 | `aws ec2 describe-instances --instance-ids i-0abc123def456789a --query 'Reservations[].Instances[].State.Name'` | The one documented EC2 instance, by its ID from `runbook.md` (the Tagging API cannot prove absence) | `cloud-discovery/aws.md` |

**GATE 4a: Approve discovery queries.** Operator approved all three. *(Gate 5)*

**Simulated cloud results (Seed B):**

| # | Resource | Type | ARN / ID | Found by | Owner (from tags) |
|---|----------|------|----------|----------|-------------------|
| 1 | `payments-alb` | ALB | `arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/payments-alb/abc123` | Q1 | cloudformation (`payments-edge`) |
| 2 | `payments-api` | ECS Service | `arn:aws:ecs:us-east-1:123456789012:service/payments-prod/payments-api` | Q1 | unknown |
| 3 | `payments-db` | RDS Instance | `arn:aws:rds:us-east-1:123456789012:db:payments-db` | Q1, Q2 | unknown |
| 4 | `payments-cache` | ElastiCache | `arn:aws:elasticache:us-east-1:123456789012:cluster:payments-cache` | Q1 | unknown |
| 5 | `payments-dlq` | SQS Queue | `arn:aws:sqs:us-east-1:123456789012:payments-dlq` | Q1 | cloudformation (`payments-async`) |
| 6-8 | `payments-db-ro-1`, `-ro-2`, `-ro-3` | RDS read replicas | `arn:aws:rds:us-east-1:123456789012:db:payments-db-ro-{1,2,3}` | Q2 (`src=payments-db`) | unknown |
| 9 | `analytics-db` | RDS Instance | `arn:aws:rds:us-east-1:123456789012:db:analytics-db` | Q2 (`src=null`) | unknown |
| — | `i-0abc123def456789a` | EC2 | `InvalidInstanceID.NotFound` | Q3 | — |

**Membership signals** (cloud-only results join the inventory only with one):

| Resource | Signal | Result |
|----------|--------|--------|
| `payments-dlq` | tag `service=payments` (the service tag key) | joins inventory, `undocumented` |
| `payments-db-ro-1..3` | referenced by confirmed `payments-db` (`ReadReplicaSourceDBInstanceIdentifier`) | join inventory, `undocumented` |
| `analytics-db` | none: no `service` tag, name outside the `payments-<component>` pattern (derived only from rows 1-5, which carry the `service=payments` tag found by Q1), no reference from a confirmed resource | **Unattributed — operator assigns** (not in the inventory) |

**Absence classification:**

| Resource | Class | Why |
|----------|-------|-----|
| `payments-legacy-worker` | `not-found (queried 123456789012/us-east-1)` | Q3 can see EC2 instances in this account/region and returned `InvalidInstanceID.NotFound` for the documented ID. The failover region was not queried, so the note says "not found in us-east-1", not "decommissioned" |

**Merge seeds and assign confidence:**

| # | Resource | Type | Source | Confidence | Flag |
|---|----------|------|--------|------------|------|
| 1 | `payments-alb` | ALB | docs + cloud | **Medium** | `name-match-only` |
| 2 | `payments-api` | ECS Fargate | docs + cloud | **High** | |
| 3 | `payments-db` | RDS PostgreSQL 15 | docs + cloud | **High** | |
| 4 | `payments-cache` | ElastiCache Redis 7 | docs + cloud | **Medium** | `name-match-only` |
| 5 | `payments-dlq` | SQS Queue | cloud only (tag) | **Medium** | `undocumented` |
| 6-8 | `payments-db-ro-1..3` | RDS read replica | cloud only (reference) | **Medium** | `undocumented` |
| 9 | `payments-legacy-worker` | EC2 | docs only | **Low** | `documented-not-found` |

Identifier check behind the confidence column. The documents give names, never ARNs, so a match counts as the same identifier only where the document's parts plus the confirmed account and region determine the ARN:

| Row | Determined ARN | Cloud ARN | Result |
|-----|----------------|-----------|--------|
| `payments-api` | `arn:aws:ecs:us-east-1:123456789012:service/payments-prod/payments-api` (account, cluster and name from `runbook.md`; region confirmed at Gate 4) | same | High |
| `payments-db` | `arn:aws:rds:us-east-1:123456789012:db:payments-db` (account and name from `runbook.md`) | same | High |
| `payments-alb` | not determined: the ARN ends in a hash no document states | `…loadbalancer/app/payments-alb/abc123` | Medium, `name-match-only` |
| `payments-cache` | not determined: the runbook describes a replication group, Q1 returned a cache-cluster ARN | `…:cluster:payments-cache` | Medium, `name-match-only` |

Unattributed — operator assigns: `analytics-db` (RDS, `arn:aws:rds:us-east-1:123456789012:db:analytics-db`).

**GATE 4b: Confirm resource list.** Operator confirmed. Noted that `payments-legacy-worker` is expected to be absent. Operator said `payments-dlq` belongs to this service and that `analytics-db` belongs to the data team: it stays out of the catalog (listed under Assumptions as "seen, not attributed"). *(Gate 6)*

### Step 5R: Detailed resource enrichment

Every command is projected (`--query`) and carries `--profile payments-ro --region us-east-1`. No `get-secret-value`, no `describe-task-definition` environment values, no full-object output.

| Resource | Command (projected) | Key findings |
|----------|---------------------|--------------|
| `payments-alb` | `aws elbv2 describe-listeners --load-balancer-arn <arn> --query 'Listeners[].{port:Port,proto:Protocol}'`; `aws elbv2 describe-target-groups --load-balancer-arn <arn> --query 'TargetGroups[].{name:TargetGroupName,port:Port,hc:HealthCheckPath}'`; `aws elbv2 describe-target-health --target-group-arn <tg-arn> --query 'TargetHealthDescriptions[].TargetHealth.State'`; `aws elbv2 describe-load-balancer-attributes --load-balancer-arn <arn> --query "Attributes[?Key=='idle_timeout.timeout_seconds'].Value"` | HTTPS listener (443), target group `payments-api-tg` (8080, `/healthz`), 4 targets `healthy`, idle timeout 60s |
| `payments-api` | `aws ecs describe-services --cluster payments-prod --services payments-api --query 'services[].{running:runningCount,desired:desiredCount,td:taskDefinition}'`; `aws ecs describe-task-definition --task-definition <td> --query 'taskDefinition.{cpu:cpu,memory:memory,images:containerDefinitions[].image,secretNames:containerDefinitions[].secrets[].name}'` | Cluster `payments-prod`, 4 running / 4 desired, Fargate, CPU 1024 / Memory 2048, **image tag `2026.04.1`**, secret **names** only: `DB_PASSWORD` |
| `payments-db` | `aws rds describe-db-instances --db-instance-identifier payments-db --query 'DBInstances[].{engine:EngineVersion,class:DBInstanceClass,multiAz:MultiAZ,storage:AllocatedStorage,type:StorageType,encrypted:StorageEncrypted,replicas:ReadReplicaDBInstanceIdentifiers}'` | PostgreSQL 15.4, `db.r6g.xlarge`, Multi-AZ, 500 GB gp3, encrypted, **3 read replicas** |
| `payments-cache` | `aws elasticache describe-replication-groups --replication-group-id payments-cache --query 'ReplicationGroups[].{nodes:MemberClusters,failover:AutomaticFailover,clusterMode:ClusterEnabled}'`; `aws elasticache describe-cache-clusters --query "CacheClusters[?ReplicationGroupId=='payments-cache'].{type:CacheNodeType,engine:EngineVersion}"` | Redis 7.0, `cache.r6g.large`, cluster mode off, 2 nodes (1 replica), automatic failover on |
| `payments-dlq` | `aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/payments-dlq --attribute-names ApproximateNumberOfMessages MessageRetentionPeriod RedriveAllowPolicy` | Standard queue, retention 14 days, **14,200 messages**, no `RedriveAllowPolicy` back to a source |
| alarms | `aws cloudwatch describe-alarms --alarm-name-prefix payments- --query 'MetricAlarms[].{name:AlarmName,metric:MetricName,threshold:Threshold,period:Period,actions:AlarmActions}'` | 6 alarms, thresholds match the runbook; all actions → SNS `payments-alerts` |
| SNS `payments-alerts` | `aws sns list-subscriptions-by-topic --topic-arn <arn> --query 'Subscriptions[].Protocol'` | 1 subscription, protocol `https`. The endpoint URL is **withheld**: it points at PagerDuty and such URLs embed an integration key. Recorded as a boundary dependency |

**Surprises (informational, no gate):**

- **Doc drift: image tag.** `runbook.md:23` says the container image is `payments-api:latest`; the live task definition runs tag `2026.04.1` (from the `describe-task-definition` projection above). The runbook is stale; the catalog records the live tag and cites both.
- **`payments-db` has 3 read replicas** — the runbook mentions only "Multi-AZ: enabled". They are now inventory rows 6-8.
- **`payments-dlq` holds 14,200 messages** and nothing allows a redrive back to a source queue.
- **SNS `payments-alerts` → PagerDuty** (HTTPS subscription): outside the service boundary, recorded as a boundary dependency.

**Dependency walking** (each edge is `live:` from the enrichment commands above; whether an edge is on the synchronous request path is labelled `inferred` until the operator confirms it, and the operator confirmed the trees at Gate 7):

- ALB → ECS service (target group membership): critical path, `inferred`
- ECS → RDS (security group rule allowing 5432): critical path, `inferred` (a rule shows allowed traffic, not a call)
- ECS → ElastiCache (security group rule allowing 6379): critical path, `inferred`
- ECS → Secrets Manager (task-definition secret reference `payments/prod/db-credentials`, value never read): critical path (startup dependency)
- ECS → ECR (image pull): critical path (deployment dependency)
- RDS primary → 3 read replicas
- All resources → same VPC `vpc-payments-prod`; ALB in public subnets; ECS + RDS + ElastiCache in private subnets
- CloudWatch alarms → SNS `payments-alerts` → PagerDuty (boundary)

**Runbooks built:** 3 investigation trees: "payment requests slow/timing out", "payment requests returning errors", "background processing delayed" (the DLQ finding prompted the third). Upstream-first branches in all three.

**GATE: Validate runbooks.** Operator validated. *(Gate 7)*

### Step 6R: Write catalog

Catalog written to `.culiops/service-discovery/payments.md`.

**GATE: Review catalog.** Operator approved. *(Gate 8)*

## Findings

### F1 — Detection routing works correctly for docs-only repos

Zero IaC tools, four document formats matched, real-discovery offered at a gate. The gate prevents accidental cloud queries when the operator meant to supply IaC.

### F2 — Hint deduplication across four source types works

The four core resources appear in all four sources (draw.io, Mermaid, runbook, image) and the legacy worker in two (runbook, Mermaid). The consolidation yields **5 unique hints**: four core at Medium (documents alone never reach High) and the legacy worker at Medium. After the cloud merge, two of the four reach High (same identifier) and two stay Medium (`name-match-only`).

### F3 — `documented-not-found` handling works as designed

`payments-legacy-worker` is in `runbook.md` and `flows.mmd`. Q3 queried the documented instance ID in the confirmed account/region and got `InvalidInstanceID.NotFound`, so the class is `not-found (queried 123456789012/us-east-1)`; flagged `documented-not-found`, Low, listed under `## Unresolved References`, not in the inventory. The caveat says "not found in us-east-1", not "decommissioned".

### F4 — `undocumented` needs a membership signal

`payments-dlq` joined via the `service=payments` tag; the three replicas via a reference from confirmed `payments-db`. Each carries "Discovered via cloud API only — not referenced in any source document. Verify this resource belongs to this service." `analytics-db`, with no signal, stayed out of the inventory and went to the Unattributed list for the operator.

### F5 — Region is asked, not inferred

No source settles the region (profile empty, `flows.mmd` silent, runbook names two). The skill asked once at Step 3R and then pinned `--region us-east-1` on every command. The unqueried `us-west-2` is stated in Assumptions ("failover region not queried at the operator's direction").

### F6 — Secrets stayed out of the catalog

`payments/prod/db-credentials` appears as a name; the SNS endpoint is withheld; no `get-secret-value`, no task-definition environment values. Acceptance check: the catalog contains no `https://events.pagerduty.com/...` URL and no connection string.

### F7 — All 8 gates fire correctly

| # | Gate | Step | Purpose |
|---|------|------|---------|
| 1 | Switch to real-discovery | Step 1 | Prevents accidental cloud queries |
| 2 | Confirm resource hints | Step 2R | Operator reviews parsed hints before any cloud call |
| 3 | Approve probe batch | Step 3R | Operator sees the identity probes before they run |
| 4 | Confirm target environment | Step 3R | Account + region pinned (the region was asked first) |
| 5 | Approve discovery queries (4a) | Step 4R | Operator sees exact queries before execution |
| 6 | Confirm resource list (4b) | Step 4R | Operator reviews merged list, flags, and the Unattributed list |
| 7 | Validate runbooks | Step 5R | Operator validates investigation trees |
| 8 | Review catalog | Step 6R | Operator approves before write/commit |

## What a produced doc would look like

`.culiops/service-discovery/payments.md` would contain:

- Header: discovery source=real-discovery, date=2026-10-26, cloud context=AWS / `123456789012` / `us-east-1`, documents used=`architecture.drawio`, `flows.mmd`, `runbook.md`, `infra-overview.png`.
- `## Overview` — payment processing API, discovered via real-discovery (documents + live cloud APIs), runs on ECS Fargate in us-east-1.
- `## Prerequisites` — `aws` CLI v2; auth via `aws sso login` or IAM credentials; least-privilege: scoped read (ECS, RDS, ElastiCache, SQS attributes, ELBv2, CloudWatch, EC2 describe, SNS list) **without** `secretsmanager:GetSecretValue`; mutations listed (ECS service update, RDS failover — both flagged `MUTATION`).
- `## Resource Inventory` — 8 rows (2 High, 6 Medium: 2 `name-match-only`, 4 `undocumented`):

  | Category | Type | Name | Confidence | Flag | Source | Owner |
  |----------|------|------|------------|------|--------|-------|
  | network | ALB | `payments-alb` | Medium | `name-match-only` | docs + cloud | cloudformation (`payments-edge`) |
  | compute | ECS Fargate | `payments-api` | High | | docs + cloud | unknown |
  | database | RDS PostgreSQL 15 | `payments-db` | High | | docs + cloud | unknown |
  | database | ElastiCache Redis 7 | `payments-cache` | Medium | `name-match-only` | docs + cloud | unknown |
  | database | RDS read replica | `payments-db-ro-1`, `-ro-2`, `-ro-3` | Medium | `undocumented` | cloud only | unknown |
  | messaging | SQS Queue | `payments-dlq` | Medium | `undocumented` | cloud only | cloudformation (`payments-async`) |

  (The three replicas are separate rows in the written catalog; shown grouped here: 4 + 3 + 1 = 8.)

- `## Naming Patterns` — `payments-<component>` detected from actual resource names.
- `## Identifying Dimensions` — ECS cluster name, RDS Multi-AZ status and replica number, Fargate task revision, image tag.
- `## Dependency Graph` — ALB → ECS (critical path, `inferred`), ECS → RDS (critical path, `inferred`), ECS → ElastiCache (critical path, `inferred`), ECS → Secrets Manager `payments/prod/db-credentials` (startup, name only), RDS → 3 replicas, CloudWatch → SNS → PagerDuty (boundary). `payments-dlq` has no inbound edge from any confirmed resource — recorded as isolated.
- `## Signal Envelopes` — `declared`: the CloudWatch alarm definitions read in enrichment (5xx rate > 1%, p99 > 2000ms, DB connections > 80%, DB CPU > 80%, cache memory > 75%, cache evictions > 100/min). No `observed` entries: enrichment read configuration and alarm definitions, not metric statistics, so there is no baseline to record.
- `## Investigation Runbooks` — 3 trees: "payment requests slow", "payment requests erroring", "DLQ messages accumulating".
- `## Stack-Specific Tooling` — `examples/aws.md`; PagerDuty as "ask the team".
- `## Unresolved References` — `payments-legacy-worker` (EC2): "Referenced in `runbook.md` and `flows.mmd` as 'being migrated to ECS'. `not-found (queried 123456789012/us-east-1)`: the documented instance ID `i-0abc123def456789a` does not exist there. May be decommissioned, renamed, or in another account/region."
- `## Assumptions and Caveats` — mandatory real-discovery caveats: built from documents + live cloud APIs (not IaC); documents may be outdated (the runbook's `:latest` image tag vs live `2026.04.1`); no drift detection without IaC; `undocumented` resources may belong to a different service; **seen, not attributed:** RDS `analytics-db` (no membership signal; operator says data team); region `us-east-1` chosen by the operator, `us-west-2` (failover) not queried; owners recognised from the `aws:cloudformation:stack-name` tag, stacks not inspected; DLQ has 14,200 messages (operational concern); 3 read replicas not mentioned in the runbook; SNS endpoint withheld.
- `## Open Questions` — "Is `payments-dlq` fed by a source queue not captured in this service? It has no visible redrive link to a source." "Who owns `analytics-db`?"
