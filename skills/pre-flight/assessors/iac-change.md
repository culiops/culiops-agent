---
name: iac-change
description: Evaluates IaC plan/diff outputs for risk before apply
triggers: Terraform plan, Helm diff, Pulumi preview, CloudFormation changeset, Bicep what-if, ecspresso diff, lambroll diff, or operator says "I'm about to apply an IaC change"
---

# IaC Change Assessor

Evaluates infrastructure-as-code changes using plan/diff output as primary input. Covers: Terraform plan/apply, Helm diff/upgrade, Pulumi preview/up, CloudFormation changeset/execute, Bicep what-if/deploy, ecspresso diff/deploy, lambroll diff/deploy.

## Input Recognition

This assessor activates when the operator provides any of:
- Terraform plan output (`terraform plan`, `terraform show`, `tfplan` file) — look for `Plan:` summary line
- Helm diff output (`helm diff upgrade`) — look for `+`, `-`, `~` prefixed YAML lines
- Pulumi preview output (`pulumi preview`) — look for `Resources:` summary
- CloudFormation changeset (`aws cloudformation describe-change-set`) — look for `Changes:` array
- Bicep what-if output (`az deployment group what-if`) — look for `Resource changes:` summary
- ecspresso diff output (`ecspresso diff`) — look for ECS service/task definition diff
- lambroll diff output (`lambroll diff`) — look for Lambda function configuration diff
- Text description: operator says they are about to apply an IaC change and describes what

If no plan output is available, ask the operator to run the relevant plan/diff command first. Score without plan output only if the operator cannot produce one — and flag this in the report.

## L1 — Static Risk Signals

### Blast radius

Count resources in the plan output:
- **Additions only (no modifications/deletions):** lower blast radius, but check if new resources create implicit dependencies (e.g., new security group referenced by existing instances)
- **Modifications:** check what's being modified — tag-only changes are low risk; attribute changes on load balancers, DNS, IAM, or database configs are high risk
- **Deletions / replacements (`destroy`, `replace`, `force_new`):** high blast radius — other resources may depend on the deleted resource
- **Multi-region or multi-account:** any change spanning regions or accounts is automatically elevated

Check whether changed resources are:
- User-facing data path (load balancer, CDN, API gateway, DNS) → elevated
- Shared infrastructure (database, message queue, auth/IAM, networking/VPC) → elevated
- Single-service internal resource (app config, monitoring, logging) → lower

Terraform-specific signals:
- `# forces replacement` in plan output → the resource will be destroyed and recreated
- `~ update in-place` → modification
- `+ create` → addition
- `- destroy` → deletion
- Count of resources: 1–3 = low, 4–10 = medium, 11+ = high

Helm-specific signals:
- Changes to `Deployment`, `StatefulSet`, `DaemonSet` → triggers pod rollout
- Changes to `Service`, `Ingress`, `NetworkPolicy` → affects traffic routing
- Changes to `ConfigMap`, `Secret` referenced by pods → triggers restart if mounted

ecspresso/lambroll-specific signals:
- Task definition changes (image tag, CPU/memory, env vars) → triggers new deployment
- Service definition changes (desired count, load balancer config) → affects capacity/routing

### Reversibility

Detect destructive or irreversible actions in the plan:
- `destroy` / `delete` / `replace` / `force_new` on stateful resources (databases, storage, encryption keys) → **Red: irreversible data loss**
- Schema migrations referenced in the change → **Red: data transformation cannot be undone**
- Encryption key rotation or deletion → **Red: data encrypted with old key becomes inaccessible**
- `destroy` / `replace` on stateless resources (compute, networking rules) → **Yellow: recreatable but may cause downtime**
- `update in-place` → **Green: previous state recoverable via re-apply of old code**

Check rollback mechanisms:
- Git history: is the previous version of these files in version control? (always yes for IaC repos)
- Terraform: can `terraform apply` with the previous commit restore state? (yes for updates, no for destroys of stateful resources)
- Helm: `helm rollback` available? (yes, Helm tracks revision history)
- ecspresso: `ecspresso rollback` available? (yes, ECS tracks task definition revisions)
- lambroll: previous function version available? (check if versioning is enabled)

Estimate MTTR by recovery path:
- Automated rollback (Helm rollback, ecspresso rollback, revert commit + re-apply) → minutes
- Manual rollback with data restore (RDS snapshot restore, S3 versioning) → 30 min to hours
- No known rollback (encryption key deleted, cross-region replication removed) → score as irreversible

### Change velocity

Analyze git history of the changed files:
- `git log --since=7.days --oneline -- <changed-files>` → count recent commits
- 0–1 commits in 7 days → **Green**
- 2–3 commits → **Yellow**
- 4+ commits → **Red** (high churn indicates instability or incomplete prior changes)

Check for stacked changes:
- Are there uncommitted changes to the same files? (`git status`)
- Are there open PRs touching the same files? (if git platform integration available)

Check automation lag:
- When was this stack last successfully applied? If > 90 days → **Yellow** (accumulated drift risk)
- If > 180 days → **Red**

### Dependency impact

From the plan output, identify resources that other services consume:
- Outputs / exported values that change or disappear → downstream consumers may break
- Security groups, IAM roles, VPC components shared across services → scope of impact widens
- Database instances, message queues, caches used by multiple services → shared dependency

Cross-reference with service-discovery catalog if available (`.culiops/service-discovery/<service>.md`):
- Check `## Dependency Graph` section for downstream consumers
- Check whether changed resources are marked as critical-path
- If catalog shows 3+ downstream consumers → **Red**
- If catalog shows 1–2 downstream consumers → **Yellow**
- If no catalog exists → score as unknown (⚪), suggest running service-discovery

Check for backward-incompatible changes:
- Renamed or removed outputs/exports → breaks consumers at their next apply
- Changed resource identifiers that other stacks reference → breaks cross-stack references
- Modified API contracts (changed ports, protocols, paths) → breaks runtime callers

### Observability readiness

Scan the IaC code for monitoring resources related to the changed components:
- CloudWatch alarms / Prometheus rules / Datadog monitors / Grafana alerts → present or absent?
- SLO definitions (error budget configurations, burn-rate alerts) → present or absent?
- Dashboards (CloudWatch, Grafana, Datadog) → present or absent?
- Log group configurations → present or absent?

Classify alerting maturity:
- SLO burn-rate alerting → **Green** (best practice)
- SLI-based threshold alerting → **Green** (acceptable)
- Static threshold alerting (CPU > 80%, memory > 90%) → **Yellow** (prone to false positives)
- No alerting on changed resources → **Red**

Check whether the change itself modifies monitoring:
- Deleting or disabling alarms/monitors → **Red** (reducing observability)
- Adding new alarms/monitors → lowers risk (improving observability)

### Cost impact

Detect cost-relevant changes in the plan:
- New resources: check instance types, storage sizes, replica counts
- Instance type changes: flag moves to larger / GPU / high-memory instances
- Replica count increases: multiply by per-unit cost estimate
- Cross-region replication additions: flag data transfer costs
- NAT Gateway additions: flag per-GB data processing charges
- Usage-based services (API Gateway, Lambda, SQS, SNS): flag if traffic volume is unknown

Known expensive patterns:
- `aws_instance` / `azurerm_virtual_machine` / `google_compute_instance` with GPU types (`p3`, `p4`, `g4`, `Standard_NC`, `n1-standard-*` with GPU)
- `aws_nat_gateway` ($0.045/hr + $0.045/GB)
- `aws_rds_cluster` Aurora pricing (higher per-hour than RDS)
- Cross-region `aws_s3_bucket_replication`, `azurerm_storage_account` GRS
- `aws_elasticsearch_domain` / `aws_opensearch_domain` (often over-provisioned)

### Security posture

Detect security-relevant changes:
- **IAM / RBAC changes:** new roles, policy modifications, permission widening. Flag any `Action: "*"` or `Resource: "*"` as **Red**
- **Network rules:** security group ingress/egress changes, NSG rules, firewall rules. Flag `0.0.0.0/0` ingress as **Red**
- **Encryption:** changes to KMS keys, encryption-at-rest settings, TLS configurations. Flag removal of encryption as **Red**
- **Public access:** S3 bucket policies, storage account public access, CDN origin changes. Flag enabling public access as **Red**
- **Audit logging:** CloudTrail, Azure Activity Log, GCP Audit Logs. Flag disabling as **Red**
- **Secret references:** new or changed secret ARNs, vault paths, key vault references. Flag hardcoded secrets as **Red**

## L2 — Context Questions

Beyond the standard 7 questions (defined in SKILL.md), ask these IaC-specific questions:

1. Have you run the plan/diff command and reviewed the output? (yes / no — if no, ask them to run it)
2. Is this change going through your normal CI/CD pipeline, or is it a manual apply? (pipeline / manual — manual elevates operator familiarity risk)
3. Has this stack been applied successfully recently, or has it been a while? (recent / months ago / unsure)

## L3 — Live Query Hooks

When the operator opts into L3, run these from `examples/<cloud>.md`:

| Category | What to query | How to interpret |
|----------|---------------|-----------------|
| Resource health | Current error rate, CPU/memory saturation for the service being changed | Error rate > baseline or saturation > 70% → elevate resource health score |
| Observability readiness | Verify alarms/dashboards exist in the live system (not just in IaC) | Alarms defined in code but not present live → IaC drift, elevate observability score |
| Timing context | Current request rate vs. baseline — is this peak traffic? | Request rate > 1.5x baseline → peak traffic, elevate timing score |
| Cost impact | Current spend rate on resources being changed | Use to validate or adjust L1 cost estimate |
| Resource health | Recent deployments in the last 24h | Multiple recent deploys → elevate change velocity score |

## Rationalization Prevention

| Thought | Reality |
|---------|---------|
| "This plan only adds resources, so it's safe" | STOP — additions can break existing resources via dependency changes, exhaust quotas, or introduce cost surprises. Score blast radius and dependency impact from the plan. |
| "It's just a tag change" | STOP — tag changes are usually Green, but verify the tag isn't used for routing, cost allocation, or conditional logic. Check whether any `count` or `for_each` uses the tag. |
| "The plan shows 0 destroys, so reversibility is Green" | STOP — `update in-place` on stateful resources can still be irreversible (e.g., changing an RDS engine version, modifying encryption settings). Read the specific attribute being changed. |
| "This is a rollback, so it's inherently safe" | STOP — rollbacks can fail, can conflict with data changes that happened after the original deploy, or can roll back to a state that no longer works with current dependencies. Score normally. |
| "The same change worked in staging" | STOP — staging doesn't have production traffic, production data, or production dependencies. Production risk is independent. |
| "This is just a config change, not infrastructure" | STOP — config changes cause more outages than infrastructure changes. Evaluate the same 10 categories. |
