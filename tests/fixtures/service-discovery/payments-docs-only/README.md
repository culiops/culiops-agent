# payments — docs-only / AWS fixture (real-discovery path)

A synthetic repo used to validate the `service-discovery` skill's real-discovery path. Contains no IaC files — only documentation and diagrams. The skill must detect the absence of IaC, parse the documents for resource hints, and then use cloud APIs (read-only) to build the same service catalog it would produce from IaC.

## What's modelled

`payments` is a fictional payment processing API on AWS.

- **Frontend:** an Application Load Balancer (`payments-alb`) routing HTTPS traffic.
- **Compute:** ECS Fargate service (`payments-api`) on cluster `payments-prod`.
- **Database:** RDS PostgreSQL 15 (`payments-db`), Multi-AZ.
- **Cache:** ElastiCache Redis 7 (`payments-cache`) for session and rate-limit data.
- **Cloud-only (not in docs):** SQS dead-letter queue (`payments-dlq`) — exists in the AWS account but is not referenced in any document. Exercises the `undocumented` confidence flag.
- **Documented but decommissioned:** EC2 instance (`payments-legacy-worker`, `i-0abc123def456789a`) — mentioned in the runbook and `flows.mmd` as "being migrated to ECS" but no longer exists in the cloud. Exercises the `documented-not-found` flag, classified `not-found (queried 123456789012/us-east-1)`.
- **Cloud-only, no membership signal:** an RDS instance `analytics-db` returned by a region-wide describe — no `service=payments` tag, name outside the confirmed pattern, not referenced by any confirmed resource. Goes to "Unattributed — operator assigns", not the inventory.
- **Region not stated:** `flows.mmd` shows no region, `runbook.md` names two (`us-east-1` normal, `us-west-2` failover drills) without saying which is serving, and the AWS profile has no default region. The skill must ask the operator.
- **Doc drift:** the runbook says the image is `payments-api:latest`; the live task definition uses tag `2026.04.1`.

## What this fixture exercises in the skill

| Principle | Exercised by |
|-----------|--------------|
| Detection routing | No IaC files → doc signatures detected → real-discovery path |
| Mermaid parsing | `flows.mmd` parsed via `doc-detectors/mermaid.md` — flowchart nodes, edges (incl. a dotted edge), one external node, no subgraph, no region |
| Structured diagram parsing | `architecture.drawio` parsed via `doc-detectors/drawio.md` — explicit nodes, edges, and region container |
| Text keyword extraction | `runbook.md` parsed via `doc-detectors/markdown.md` — resource names, account ID, two candidate regions, CloudWatch references |
| Image vision (simulated) | `infra-overview.png` detected via `doc-detectors/image.md` — placeholder image; DRY-RUN-NOTES describes what vision would extract |
| Cloud context resolution | Account `123456789012` from `runbook.md`; region unknown (two candidates, profile has none) → operator asked; probe batch shown and approved before it runs (`sts get-caller-identity`, `configure get region`) |
| Converging discovery merge | Document hints (Seed A, capped at Medium) merged with simulated cloud query results (Seed B) — membership signals, `undocumented`, `documented-not-found`, and the Unattributed list |
| Confidence flags | `undocumented` (DLQ and 3 read replicas, cloud only, each with a membership signal), `name-match-only` (ALB and cache: docs name them, but no document determines the cloud identifier), `documented-not-found` (legacy worker in docs only), Unattributed (`analytics-db`) |
| Owner column | `aws:cloudformation:stack-name` tag on the ALB and the DLQ → `cloudformation (<stack>)`; other rows `unknown` |
| Secrets by projection | Enrichment uses projected `--query` fields only; the DB credentials secret is recorded by name `payments/prod/db-credentials`, never fetched; SNS subscription endpoints are withheld |
| Same catalog output format | Real-discovery produces the same `.culiops/service-discovery/payments.md` format as IaC path |

## Files

| File | Purpose |
|------|---------|
| `architecture.drawio` | Valid Draw.io XML diagram with AWS resource nodes and relationship edges |
| `flows.mmd` | Mermaid flowchart of the request flow (same AWS components, plus the legacy worker); no region |
| `runbook.md` | Markdown operations runbook with resource names, account context, an ambiguous region statement, and incident procedures |
| `infra-overview.png` | 1x1 pixel placeholder PNG — simulates an architecture diagram image for vision analysis |
