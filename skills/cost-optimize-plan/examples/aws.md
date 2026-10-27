# AWS — cost-optimize-plan examples

Read-only verification queries per playbook. All commands are `Get*` / `Describe*` / `List*` / `Lookup*` / `Simulate*` only — no mutations. The one non-`Get/Describe/List` read is CloudTrail Lake `StartQuery` / `GetQueryResults` (read-only data access, but billed per GB scanned): itemize it at GATE 2 and run it only against an event data store that already exists.

Every playbook's **Query 0** is the shared `## Target check` (0a) + `## Ownership probe` (0b) below. `## Metrics rule` and `## Secrets rule` apply to every query that reads CloudWatch or secrets-bearing output.

## Prerequisites

**CLI:** `aws-cli` v2.13+.

**Authentication:** `aws sso login` (preferred) or static credentials via `~/.aws/credentials`.

**Baseline IAM (read-only):** AWS managed policy `arn:aws:iam::aws:policy/ReadOnlyAccess` covers most playbooks. Notes:
- `iam:SimulatePrincipalPolicy` (S3 delete's optional IAM principal sweep) — in `ReadOnlyAccess`; re-add explicitly if you use a narrower custom viewer role.
- CloudTrail Lake queries need `cloudtrail:StartQuery` + `cloudtrail:GetQueryResults` (and `cloudtrail:ListEventDataStores` to find the store) — check them on a custom role.
- `tag:GetResources` (ownership probe fallback) and `ce:Get*` (commitment coverage) — in `ReadOnlyAccess`; check on a custom role.

**Never** use `*Admin`, `Owner`, `PowerUserAccess` for this skill — read-only only.

**API costs to itemize at GATE 2:**

| API | Cost | Notes |
|-----|------|-------|
| `cloudtrail:LookupEvents` | Free (Event history) | 2 TPS per account per region — pace batches > 20 queries. Management + Insights events only, last 90 days. **No data events** (S3 `GetObject`/`PutObject`, Lambda data events): it cannot prove an S3 bucket is idle. |
| `cloudtrail:StartQuery` (CloudTrail Lake) | Billed per GB scanned | Only against an **existing** event data store; itemize estimated scan size at GATE 2. See CloudTrail pricing for the region. |
| `ce:Get*` (Cost Explorer) | $0.01 per request | Commitment-coverage checks and cost lookups. |
| `cloudwatch:GetMetricData` | Billed per metric requested | See CloudWatch pricing for the region. Prefer it over many `GetMetricStatistics` calls (see Metrics rule). `GetMetricStatistics` has its own per-request pricing — see CloudWatch pricing. |
| `s3api:List*` / `Get*` (incl. reading access-log objects) | Per-request S3 pricing | Small for single-bucket verification; reading months of server access logs is the exception — itemize it. |
| `iam:SimulatePrincipalPolicy`, `ec2:Describe*`, `elasticloadbalancing:Describe*`, `route53:List*`, `lambda:Get*`/`List*`, `tag:GetResources` | Free | |

**Throttling notes:**
- `cloudtrail:LookupEvents` is 2 TPS per account per region.
- `iam:SimulatePrincipalPolicy` rate-limit is region-dependent; batching > 50 principals triggers throttling.

## Target check

Run first in every batch (Query 0a), before any other query.

```bash
aws sts get-caller-identity --output json
```

**IAM:** `sts:GetCallerIdentity`. **API cost:** none.

- `Account` MUST equal the item's account: the upstream report's `Scope` account, or for an `org-wide` report the account in the item's ARN / line item (run the check once per account). Mismatch → **STOP the batch** (not ⚪): nothing queried so far means anything.
- Region = the resource's own region (from its ARN or the report). Pass `--region` explicitly on every call. LookupEvents and CloudWatch are **regional**; global services are queried in `us-east-1` (Route53, CloudFront, IAM) — Global Accelerator's API endpoint is `us-west-2`.
- Record `live:0a` with account ID, region and timestamp.

## Ownership probe

Run per item (Query 0b), before the playbook's own queries. It decides who owns the resource, so what "rollback" and "remediate" mean.

1. **Tags.** From the resource's own describe call (preferred), or `aws resourcegroupstaggingapi get-resources --resource-arn-list <arn> --region <region>` (tagging API for global services: `us-east-1`).
2. **IaC grep.** Grep the operator-supplied IaC repo(s) for the resource ID / name / ARN.

Owner values (record exactly one):

| Owner | Detected by | Effect |
|-------|-------------|--------|
| `terraform` | IaC match; cite `code:<path:line>` of the resource block | Normal path. "Re-apply old IaC" rollback available. |
| `lambroll` | `function.json` match; cite `code:<path:line>` | Normal path (Lambda). |
| `ecspresso` | `ecspresso.yml` / task definition match; cite `code:<path:line>` | Normal path. |
| `k8s` | tags `kubernetes.io/created-for/pvc/name`, `ebs.csi.aws.com/cluster`, `elbv2.k8s.aws/cluster`, `service.k8s.aws/stack`, `kubernetes.io/cluster/<name>` | Remediation target is the owner (PVC / StatefulSet, Service / Ingress), not the raw AWS resource → ❔ `owned-by-k8s`. |
| `asg` | `aws:autoscaling:groupName` | Target is the launch template / ASG → ❔ `owned-by-asg`. |
| `eks-nodegroup` | `eks:nodegroup-name` | Target is the nodegroup → ❔ `owned-by-eks-nodegroup` (unless the playbook is `rightsize-eks-nodegroup`). |
| `karpenter` | `karpenter.sh/nodepool` | Target is the NodePool → ❔ `owned-by-karpenter`. |
| `cloudformation` | `aws:cloudformation:stack-name` (also covers Serverless / SAM / CDK) | Outside the supported stack → ❔ `unsupported-owner`; the skill stops on that item. |
| `unmanaged` | IaC repo(s) supplied and searched with no match, AND the full tag set was read and none names a controller or automation | "Re-apply old IaC" rollback is **not** available; Reversibility cannot be 🟢 on that basis. |
| `unknown` | Probe could not run (IaC repo not supplied, tagging API denied), or a tag looks like a controller / automation tag that is not in the rows above | Treat as `unmanaged` for Reversibility; Dimension 4 scores ⚪. If it is a delete, say which tag was unrecognized. |

**Drift:** if an IaC value differs from the live value (e.g. instance type, memory size), record a drift row (`code:<path:line>` vs `live:<query #>`); never resolve it silently.

## Metrics rule

- `GetMetricStatistics` returns **at most 1,440 datapoints per call** (CLI help). 90 days at `--period 3600` = 2,160 → API error. Use `aws cloudwatch get-metric-data` (one call, many queries, hourly) or split the window into ≤ 60-day chunks.
- **Hourly granularity** for activity windows (Principle 3); a daily period hides bursts. Exception: metrics the service emits only daily (S3 `BucketSizeBytes` / `NumberOfObjects`).
- **Retention:** 1-minute data 15 days, 5-minute 63 days, 1-hour 455 days. A request for finer data than retained returns nothing.
- **Empty ≠ zero.** `Datapoints: []` (or an empty `MetricDataResults.Values`) counts as zero activity ONLY if all three hold: (a) the Target check passed; (b) the resource's own describe call in the same account/region succeeded; (c) namespace, metric and dimension values were taken from that describe output, and the metric exists for that resource type. Otherwise the signal is ⚪.
- Read the temporal distribution (Principle 3), not just the total.

## Secrets rule

Never record raw output that can carry secrets; use `--query` projections and record a summary + the query number.

- Never record `Environment.Variables`, presigned URLs (`Code.Location`), task-definition `environment` / `secrets` values, or Terraform state.
- Never run `terraform state pull` or `terraform show -json`.
- Server access logs and CloudTrail records carry requester IPs and principals: record counts and time distribution, not rows.

## Playbook index

| Playbook | Action | Resource type |
|----------|--------|---------------|
| `aws/delete-unattached-ebs.md` | delete | EBS volume |
| `aws/delete-orphaned-snapshot.md` | delete | EBS snapshot |
| `aws/delete-idle-elastic-ip.md` | delete | Elastic IP |
| `aws/delete-idle-ec2.md` | delete | EC2 instance |
| `aws/delete-s3-bucket.md` | delete | S3 bucket |
| `aws/delete-unused-load-balancer.md` | delete | ALB / NLB / CLB |
| `aws/delete-nat-gateway.md` | delete | NAT Gateway |
| `aws/delete-lambda.md` | delete | Lambda function |
| `aws/delete-kinesis-stream.md` | delete | Kinesis data stream |
| `aws/rightsize-ec2.md` | rightsize | EC2 instance |
| `aws/rightsize-rds.md` | rightsize | RDS instance |
| `aws/rightsize-dynamodb.md` | rightsize | DynamoDB table |
| `aws/rightsize-eks-nodegroup.md` | rightsize | EKS managed nodegroup |
| `aws/rightsize-kinesis-stream.md` | rightsize | Kinesis data stream |
| `aws/lifecycle-s3.md` | lifecycle-policy | S3 bucket |

Unsupported in v1 (graceful degradation → `❔ Manual review required`): Aurora, RDS snapshot delete, ECS/Fargate rightsize, Kubernetes workloads.
