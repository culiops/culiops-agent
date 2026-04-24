# payments — docs-only / AWS fixture (real-discovery path)

A synthetic repo used to validate the `service-discovery` skill's real-discovery path. Contains no IaC files — only documentation and diagrams. The skill must detect the absence of IaC, parse the documents for resource hints, and then use cloud APIs (read-only) to build the same service catalog it would produce from IaC.

## What's modelled

`payments` is a fictional payment processing API on AWS.

- **Frontend:** an Application Load Balancer (`payments-alb`) routing HTTPS traffic.
- **Compute:** ECS Fargate service (`payments-api`) on cluster `payments-prod`.
- **Database:** RDS PostgreSQL 15 (`payments-db`), Multi-AZ.
- **Cache:** ElastiCache Redis 7 (`payments-cache`) for session and rate-limit data.
- **Cloud-only (not in docs):** SQS dead-letter queue (`payments-dlq`) — exists in the AWS account but is not referenced in any document. Exercises the `undocumented` confidence flag.
- **Documented but decommissioned:** EC2 instance (`payments-legacy-worker`) — mentioned in the runbook as "being migrated to ECS" but no longer exists in the cloud. Exercises the `documented-not-found` flag.

## What this fixture exercises in the skill

| Principle | Exercised by |
|-----------|--------------|
| Detection routing | No IaC files → doc signatures detected → real-discovery path |
| Structured diagram parsing | `architecture.drawio` parsed via `doc-detectors/drawio.md` — explicit nodes, edges, and region container |
| Text keyword extraction | `runbook.md` parsed via `doc-detectors/markdown.md` — resource names, account ID, region, CloudWatch references |
| Image vision (simulated) | `infra-overview.png` detected via `doc-detectors/image.md` — placeholder image; DRY-RUN-NOTES describes what vision would extract |
| Cloud context resolution | Account `123456789012`, region `us-east-1` extracted from documents, cross-referenced with simulated `aws sts get-caller-identity` |
| Converging discovery merge | Document hints (Seed A) merged with simulated cloud query results (Seed B) — exercises all three confidence outcomes |
| Confidence flags | `undocumented` (DLQ found in cloud only), `documented-not-found` (legacy worker in docs only) |
| Same catalog output format | Real-discovery produces the same `.culiops/service-discovery/payments.md` format as IaC path |

## Files

| File | Purpose |
|------|---------|
| `architecture.drawio` | Valid Draw.io XML diagram with AWS resource nodes and relationship edges |
| `runbook.md` | Markdown operations runbook with resource names, account/region context, and incident procedures |
| `infra-overview.png` | 1x1 pixel placeholder PNG — simulates an architecture diagram image for vision analysis |
