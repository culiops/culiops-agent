# AWS — cost-optimize-plan examples

Read-only verification queries per playbook. All commands are `Get*` / `Describe*` / `List*` / `Lookup*` / `Simulate*` only — no mutations.

## Prerequisites

**CLI:** `aws-cli` v2.13+ (LookupEvents requires recent CloudTrail SDK).

**Authentication:** `aws sso login` (preferred) or static credentials via `~/.aws/credentials`.

**Baseline IAM (read-only):** AWS managed policy `arn:aws:iam::aws:policy/ReadOnlyAccess` is sufficient for every v1 playbook EXCEPT:
- `iam:SimulatePrincipalPolicy` (used by `delete-s3-bucket.md` IAM principal sweep) — included in `ReadOnlyAccess`, but if you've narrowed to a tighter custom viewer role, re-add this permission explicitly.
- `cloudtrail:LookupEvents` — included in `ReadOnlyAccess`.

**Never** use `*Admin`, `Owner`, `PowerUserAccess` for this skill — read-only only.

**API costs to itemize at GATE 2:**

| API | Per-request cost | Notes |
|-----|-----------------|-------|
| `cloudtrail:LookupEvents` | $0 for events ≤ 7d; older = $2.00 per 100K events returned | The skill caps lookup windows to playbook defaults (mostly 90d). Surfaces in GATE 2 batch. |
| `iam:SimulatePrincipalPolicy` | $0 | Free. |
| `ec2:Describe*` | $0 | Free. |
| `s3api:Get*` | $0.0004 per 1K LIST, $0.005 per 10K HEAD | Small for single-bucket verification. |
| `cloudwatch:GetMetricData` | $0.01 per 1K metric data points scanned | Used by rightsize playbooks. |
| `route53:ListResourceRecordSets` | $0 | Free. |

**Throttling notes:**
- `cloudtrail:LookupEvents` is rate-limited to 2 TPS per account. Batches >20 queries should pace.
- `iam:SimulatePrincipalPolicy` rate-limit is region-dependent; batching >50 principals triggers throttling.

## Authentication probe

```bash
aws sts get-caller-identity --output json
```

**IAM:** `sts:GetCallerIdentity` (default for any IAM principal).
**API cost:** none.

## Playbook index

| Playbook | Action | Resource type |
|----------|--------|---------------|
| `aws/delete-unattached-ebs.md` | delete | EBS volume |
| `aws/delete-orphaned-snapshot.md` | delete | EBS / RDS snapshot |
| `aws/delete-idle-elastic-ip.md` | delete | Elastic IP |
| `aws/delete-idle-ec2.md` | delete | EC2 instance |
| `aws/delete-s3-bucket.md` | delete | S3 bucket |
| `aws/delete-unused-load-balancer.md` | delete | ALB / NLB / CLB |
| `aws/rightsize-ec2.md` | rightsize | EC2 instance |
| `aws/rightsize-rds.md` | rightsize | RDS instance |
| `aws/lifecycle-s3.md` | lifecycle-policy | S3 bucket |

Unsupported in v1 (graceful degradation → `❔ Manual review required`): NAT Gateway, Lambda delete, DynamoDB rightsize, EKS nodegroup rightsize, GCP, Azure, Kubernetes.
