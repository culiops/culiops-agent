---
name: markdown
extensions: ".md, .txt, .adoc, .rst, .docx, .html, .pdf"
type: text
---

## File signatures
- `*.md`, `*.txt`, `*.adoc`, `*.rst`, `*.docx`, `*.html`, `*.pdf`
- Filename patterns that increase relevance (prioritize these during file selection):
  - `*arch*` (architecture)
  - `*infra*` (infrastructure)
  - `*runbook*` (runbook, run-book)
  - `*oncall*`, `*on-call*` (on-call)
  - `*deploy*` (deployment)
  - `*topology*` (network topology)
  - `*overview*` (system overview)
  - `*design*` (design document)
  - `*adr*`, `*decision*` (architecture decision record)
  - `runbook*`, `ops/`, `docs/ops*`, `oncall*` (operations; do not match a bare `*ops*`, which hits nearly any file)
  - `*network*` (network)
  - `*disaster*`, `*dr-*`, `*recovery*` (disaster recovery)
  - `*sla*`, `*slo*`, `*sli*` (service level)
  - `*incident*`, `*postmortem*`, `*post-mortem*` (incident review)

## Parsing method
Keyword and pattern extraction from prose text.

1. **Cloud resource type keywords**: scan for mentions of cloud resource types. AWS keywords plus generic technologies:
   - **AWS**: RDS, Aurora, DynamoDB, ElastiCache, Redshift, S3, ECS, EKS, EC2, Lambda, Fargate, ALB, NLB, CLB, API Gateway, CloudFront, Route 53, SQS, SNS, Kinesis, EventBridge, Step Functions, CodePipeline, CodeBuild, IAM, KMS, Secrets Manager, Parameter Store, VPC, WAF, ACM, EFS, EBS, ECR, MSK, MQ, AppSync, Cognito, SES, CloudWatch, X-Ray, OpenSearch
   - **Generic**: PostgreSQL, MySQL, Redis, Memcached, Elasticsearch, Kafka, RabbitMQ, MongoDB, Cassandra, NGINX, HAProxy, Consul, Vault, Terraform, Kubernetes, Docker
2. **Resource names**: look for names adjacent to resource type keywords, especially:
   - Backtick-quoted: `` `orders-db` ``
   - Bold: `**orders-db**`
   - Following a type keyword: "RDS instance orders-db", "the ALB `api-lb`"
   - In headings near resource discussions
3. **ARNs**: match the regex `arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:(\d{12}|aws)?:.+` (region and account may be empty, as for S3 ARNs; the account may be the literal `aws` for AWS-managed policies) — ARNs provide resource type, region, account, and name in a single string
4. **Account IDs**: match 12-digit AWS account IDs
5. **Regions**: match AWS region identifiers (e.g., `us-east-1`, `eu-west-1`)
6. **Relationships from prose**: phrases indicating dependencies:
   - "connects to", "talks to", "calls", "invokes"
   - "depends on", "requires", "backed by", "fronted by"
   - "reads from", "writes to", "publishes to", "subscribes to"
   - "proxies to", "routes to", "load balances across"
   - "deployed in", "runs on", "hosted on"

## Output
**Output: hints only** — `source=doc`, confidence capped at Medium; only live evidence can raise it.

## What to extract
- **Resource types**: from keyword matches in prose
- **Resource names**: from backtick-quoted or bold text adjacent to type keywords, from ARNs
- **Account context**: from AWS account IDs
- **Region context**: from region identifiers mentioned in text
- **Relationships**: from dependency phrases linking two named resources or services
- **ARNs**: full ARN strings provide type, region, account, and resource name simultaneously

## Extraction examples

**Raw markdown prose:**

```markdown
## Infrastructure Overview

The order service runs on **ECS Fargate** in `us-east-1`. It connects to
the `orders-db` RDS PostgreSQL instance (arn:aws:rds:us-east-1:123456789012:db:orders-db)
for persistent storage and reads session data from the `session-cache`
ElastiCache Redis cluster.

Traffic enters through the `api-alb` Application Load Balancer, which
routes to the ECS service. Static assets are served from the `assets-cdn`
CloudFront distribution backed by the `static-assets` S3 bucket.
```

**Extracted hints:**

- Resource: type=ECS Fargate, name="order service" (from prose)
- Resource: type=RDS, name="orders-db", engine=PostgreSQL, region=us-east-1, account=123456789012 (from ARN + prose)
- Resource: type=ElastiCache, name="session-cache", engine=Redis (from prose)
- Resource: type=ALB, name="api-alb" (from backtick-quoted name + type keyword)
- Resource: type=CloudFront, name="assets-cdn" (from backtick-quoted name)
- Resource: type=S3, name="static-assets" (from backtick-quoted name)
- Relationship: api-alb → order service ("routes to")
- Relationship: order service → orders-db ("connects to")
- Relationship: order service → session-cache ("reads session data from")
- Relationship: assets-cdn → static-assets ("backed by")
- Context: region=us-east-1, account=123456789012

## Limitations
- **Prose ambiguity**: natural language is imprecise; "the database" may refer to any database in scope — attach resource hints only when a specific name or type is mentioned
- **Informal names**: documents may use nicknames, abbreviations, or team-internal jargon that don't match actual resource names; mark these as low confidence
- **Planned vs actual**: architecture documents may describe planned (future) infrastructure that doesn't exist yet; there is no reliable way to distinguish planned from deployed — present all findings and let the operator filter
- **PDF and DOCX formatting loss**: text extraction from binary formats may lose structure, tables, and formatting; extracted text is best-effort
- **Embedded diagrams**: documents may contain inline images of architecture diagrams; the `image.md` detector handles those separately — this detector processes only the text layer
- **Stale documentation**: documents may be outdated and describe infrastructure that has been decommissioned or modified; treat all document-sourced hints as lower confidence than IaC-sourced data
