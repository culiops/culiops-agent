---
name: iac-change
description: Evaluates IaC plan/diff outputs for risk before apply
triggers: Terraform plan, Helm diff, kubectl diff (raw manifests or Kustomize), ecspresso diff, lambroll diff, Argo CD / Flux diff, or operator says "I'm about to apply an IaC change"
---

# IaC Change Assessor

Evaluates infrastructure-as-code changes using plan/diff output as primary input. Covers: Terraform plan/apply, Helm diff/upgrade, Kustomize and raw manifests (`kubectl diff` / `kubectl apply`), GitOps-delivered Kubernetes changes (Argo CD / Flux), ecspresso diff/deploy, lambroll diff/deploy.

Not covered: CloudFormation change sets, Serverless Framework, CDK, Pulumi, Bicep, GCP, Azure. If the input is one of these, stop (see `SKILL.md` → Supported stack).

## Input Recognition

This assessor activates when the operator provides any of:
- Terraform plan output (`terraform plan`, `terraform show -no-color tfplan`) — look for the `Plan:` summary line, or `No changes.`
- Helm diff output (`helm diff upgrade`) — look for `+`, `-`, `~` prefixed YAML lines. helm-diff masks Secret data by default; never ask for `--show-secrets`
- kubectl diff output (`kubectl diff -f <dir>` for raw manifests, `kubectl diff -k <dir>` for Kustomize) — unified diff per object. kubectl masks Secret data
- GitOps diff (`argocd app diff <app>`, `flux diff kustomization <name> --path <dir>`) — read-only
- ecspresso diff output (`ecspresso diff`) — look for ECS service/task definition diff. **Prints task-definition environment values in plaintext:** summarize changed variable names, never copy values
- lambroll diff output (`lambroll diff`) — look for Lambda function configuration diff. Same plaintext-environment warning
- Text description: operator says they are about to apply an IaC change and describes what

If no plan output is available, ask the operator to run the relevant plan/diff command first. Score without plan output only if the operator cannot produce one — and flag this in the report.

## L1 — Static Risk Signals

### Plan hygiene & drift

Check these before scoring — they decide whether the plan can be trusted at all:
- **Drift:** Terraform's "Objects have changed outside of Terraform" / "Note: Objects have changed" block → someone changed live state outside IaC. List each object as a drift row in `## Evidence` and ask the operator whether the plan should overwrite it.
- **Partial or stale plan:** ask whether the plan was made with `-target`, `-refresh=false`, or a non-default var-file / workspace. A targeted or unrefreshed plan doesn't show everything apply will touch → blast radius and reversibility are ⚪ at best.
- **Unexpected "No changes"** while the operator expects changes → likely the wrong workspace / var-file / context. Stop and re-check the target.
- **Unexpected resources** in the plan that the operator didn't intend → surface before scoring.

### Blast radius

Count resources in the plan output:
- **Additions only (no modifications/deletions):** lower blast radius, but check if new resources create implicit dependencies (e.g., new security group referenced by existing instances)
- **Modifications:** check what's being modified — tag-only changes are low risk; attribute changes on load balancers, DNS, IAM, or database configs are high risk
- **Deletions / replacements (`destroy`, `replace`, `force_new`):** high blast radius — other resources may depend on the deleted resource
- **Capacity reductions** (lower desired count / replicas / min size, smaller instance class): reduced headroom and redundancy → at least **Yellow**. Score the capacity risk here, not under cost
- **Multi-region or multi-account:** any change spanning regions or accounts is automatically elevated

Check whether changed resources are:
- User-facing data path (load balancer, CDN, API gateway, DNS) → elevated
- Shared infrastructure (database, message queue, auth/IAM, networking/VPC) → elevated
- Single-service internal resource (app config, monitoring, logging) → lower

Terraform-specific signals:
- `# forces replacement` / `must be replaced` in plan output → the resource will be destroyed and recreated
- `-/+` = destroy then create (gap in between); `+/-` = create before destroy
- "will be recreated" on `aws_security_group_rule` and similar → delete then create → brief traffic gap on that rule
- `~ update in-place` → modification
- `+ create` → addition
- `- destroy` → deletion
- `moved` / `removed` / `import` blocks → state surgery; confirm intent with the operator
- Count of resources: 1–3 = low, 4–10 = medium, 11+ = high

Kubernetes signals (Helm, Kustomize, raw manifests, GitOps):
- Changes to `Deployment`, `StatefulSet`, `DaemonSet` pod templates → triggers pod rollout
- Changes to `Service`, `Ingress`, `NetworkPolicy` → affects traffic routing
- Changes to `ConfigMap`, `Secret` referenced by pods → triggers restart if mounted
- Changes to immutable fields (StatefulSet `volumeClaimTemplates`, `selector`, Job templates) → apply fails or forces delete + recreate
- `CustomResourceDefinition` changes → affect every custom resource of that kind cluster-wide

ecspresso/lambroll-specific signals:
- Task definition changes (image tag, CPU/memory, env vars, container `healthCheck`) → triggers new deployment. A container `healthCheck` change decides whether ECS keeps or kills tasks; the ALB target-group health check is a separate (usually Terraform) setting
- Service definition changes (desired count, load balancer config, deployment configuration) → affects capacity/routing

### Reversibility

Detect destructive or irreversible actions in the plan:
- `destroy` / `delete` / `replace` / `force_new` on stateful resources (databases, storage, encryption keys) → **Red: irreversible data loss**. Before scoring, gather evidence on recovery: `deletion_protection`, `skip_final_snapshot` / `final_snapshot_identifier`, `lifecycle.prevent_destroy` in code (for a resource removed from config, these come from state, not the plan — mark `UNVERIFIED` unless confirmed live), and live backups / snapshots (L3). A snapshot reduces the loss but restore creates a new resource (new endpoint, downtime, data after the snapshot lost) — the hard block stands until the operator justifies it
- Schema migrations referenced in the change → **Red: data transformation cannot be undone**
- Encryption key deletion, disable, or scheduled deletion → **Red: data encrypted with that key becomes inaccessible**
- `destroy` / `replace` on stateless resources (compute, networking rules) → **Yellow: recreatable but may cause downtime**
- `update in-place` → **Green only after checking the changed attribute is reversible.** Re-applying the old code does not undo these one-way updates:

| One-way in-place update | Score |
|---|---|
| `backup_retention_period` → 0 (RDS / Aurora: deletes automated backups, ends point-in-time recovery) | Red, hard block |
| S3 `versioning` Enabled → Suspended; new or shortened lifecycle `expiration` / `noncurrent_version_expiration` | Red, hard block (objects deleted on schedule) |
| `retention_in_days` lowered on a CloudWatch log group | Red, hard block (older logs deleted) |
| DynamoDB `point_in_time_recovery` disabled | Red, hard block (recovery window lost) |
| RDS / Aurora `engine_version` major upgrade | Red (no in-place downgrade; rollback = restore from snapshot) |
| CRD version removed / CRD deleted | Red, hard block (deleting a CRD deletes every resource of that kind) |
| `deletion_protection` → false, `skip_final_snapshot` → true, `prevent_destroy` removed | Yellow alone; Red if this plan or a queued follow-up destroys the resource |
| RDS `allocated_storage` increase, EBS volume size increase, PVC storage request increase | Yellow (cannot shrink; no data loss) |
| KMS key change on an existing encrypted resource | Read the plan — often forces replacement; score as replacement |

**External allowlist check (IP / EIP / NAT / egress-address release).** Any `destroy` / `release` of a public IP — `aws_eip`, an EIP association, a NAT gateway (which releases its EIP), or any change that frees a public egress address — is **irreversible if a partner or external system has allowlisted that IP** in a firewall. A released EIP returns to the AWS pool; you cannot get the same address back. Before scoring this Green, confirm no external reliance: check egress history over ≥ 6 months (0 egress ⇒ no external caller depends on the source IP) and ask the operator whether any partner allowlists this address. Treat unknown as a **hard-block (Red)** until confirmed — the cost of a wrong release is a broken partner integration with no rollback.

Check rollback mechanisms — and what each one does **not** undo:
- **Terraform:** rollback = `git revert` → plan → apply. Never "apply an old state file". Doesn't restore destroyed data or undo one-way attributes.
- **Helm:** `helm rollback` restores a previous revision's manifests. It doesn't undo PVC data, CRDs (Helm never upgrades or deletes CRDs from `crds/`), migrations run by hooks, or resources annotated `helm.sh/resource-policy: keep`.
- **Kustomize / raw manifests:** re-apply the previous manifests from git. `kubectl rollout undo` reverts only a Deployment / StatefulSet / DaemonSet pod template. Never `kubectl delete -f` as a rollback — it deletes objects that existed before the change.
- **GitOps (Argo CD / Flux):** rollback = `git revert` and let the controller sync. Check whether auto-sync and prune are on — prune deletes objects removed from git.
- **ecspresso:** `ecspresso rollback` reverts the task definition only. Service settings (desired count, LB config, deployment configuration) need the previous service definition re-deployed from git.
- **lambroll:** `lambroll rollback` needs published versions and an alias; without versioning, rollback = redeploy the previous code from git.

Estimate MTTR by recovery path:
- Automated rollback (Helm rollback, ecspresso rollback, revert commit + re-apply) → minutes
- Manual rollback with data restore (RDS snapshot restore, S3 versioning) → 30 min to hours
- No known rollback (encryption key deleted, cross-region replication removed, backups deleted) → score as irreversible

### Change velocity

Analyze git history of the changed files on the default branch:
- `git log --since=7.days --oneline <default-branch> -- <changed-files>` → count recent commits
- Exclude this change's own commits (`git log <default-branch>..HEAD`) — a multi-commit PR doesn't count against itself
- 0–1 commits in 7 days → **Green**
- 2–3 commits → **Yellow**
- 4+ commits → **Red** (high churn indicates instability or incomplete prior changes)

Check for stacked changes:
- Are there uncommitted changes to the same files? (`git status`)
- Are there open PRs / MRs touching the same files? (read-only forge CLI, if available)

Check automation lag:
- When was this stack last successfully applied? Evidence sources: CI pipeline history; S3 backend `aws s3api head-object --bucket <bucket> --key <state-key>` → `LastModified` (metadata only); `helm history` last deployed; ECS deployment `createdAt`. **Never `terraform state pull` or download the state file** — state holds secrets in plaintext.
- If > 90 days → **Yellow** (accumulated drift risk)
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

An alarm counts only if it watches the changed resources (its namespace / metric / dimensions or label selectors point at them), not just because its name contains the service name.

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
- NAT Gateway additions: flag hourly + per-GB data processing charges
- Usage-based services (API Gateway, Lambda, SQS, SNS): flag if traffic volume is unknown
- Decreases (scale-down, rightsizing, deletion) are cost-**Green**. Their capacity risk is scored under blast radius and resource health — don't count it twice

Look prices up for the target region (AWS Price List API, the pricing calculator) and record the lookup date. Never use a remembered price — prices change and differ by region.

Known expensive patterns:
- `aws_instance` / launch templates / node groups with GPU or accelerator types (`p*`, `g*`, `inf*`, `trn*`)
- `aws_nat_gateway` (hourly charge + per-GB processing)
- `aws_rds_cluster` Aurora pricing (higher per-hour than RDS; I/O-Optimized vs Standard)
- Cross-region `aws_s3_bucket_replication`
- `aws_elasticsearch_domain` / `aws_opensearch_domain` (often over-provisioned)

### Security posture

Detect security-relevant changes:
- **IAM changes:** new roles, policy modifications, permission widening. Flag any `Action: "*"` or `Resource: "*"` as **Red**
- **Kubernetes RBAC & pod security:** new `ClusterRoleBinding` to `cluster-admin`, wildcard verbs/resources, `privileged: true`, `hostNetwork` / `hostPath`, removed `NetworkPolicy` → **Red**
- **Network rules:** security group ingress/egress changes. Flag `0.0.0.0/0` or `::/0` ingress as **Red**
- **Encryption:** changes to KMS keys, encryption-at-rest settings, TLS configurations. Flag removal of encryption as **Red**
- **Public access:** S3 bucket policies / Block Public Access, CDN origin changes, new public `LoadBalancer` Services or Ingress hosts. Flag enabling public access as **Red**
- **Audit logging:** CloudTrail, EKS control-plane logging. Flag disabling as **Red**
- **Secret references:** new or changed Secrets Manager / SSM ARNs, Kubernetes Secret references. Flag hardcoded secrets as **Red** — and name the location, never repeat the value

## L2 — Context Questions

Beyond the standard 7 questions (defined in SKILL.md), ask these IaC-specific questions:

1. Have you run the plan/diff command and reviewed the output? (yes / no — if no, ask them to run it)
2. How is this change delivered: CI/CD pipeline, GitOps controller, or manual apply? (manual elevates operator familiarity risk; GitOps means merging is the apply)
3. Was the plan made with `-target`, `-refresh=false`, or a non-default workspace / var-file? (yes / no / unsure)
4. Has this stack been applied successfully recently, or has it been a while? (recent / months ago / unsure — `operator-stated`; verify per Change velocity → automation lag)

## L3 — Live Query Hooks

When the operator opts into L3, run these from `examples/aws.md` / `examples/kubernetes.md`, after the target check:

| Category | What to query | How to interpret |
|----------|---------------|-----------------|
| Resource health | Current error rate, CPU/memory saturation, alarms / alerts in firing state on the changed resources | Error rate > baseline, saturation > 70%, or a firing alarm → elevate resource health score. This is the only evidence that can make category 10 Green |
| Reversibility | Backups / snapshots / versioning / PITR for stateful resources being destroyed or changed one-way | No recent recovery point → keep Red; recovery point exists → record it, the hard block still needs justification |
| Observability readiness | Verify alarms/dashboards exist in the live system (not just in IaC) | Alarms defined in code but not present live → IaC drift, elevate observability score |
| Timing context | Current request rate vs. baseline — is this peak traffic? | Request rate > 1.5x baseline → peak traffic, elevate timing score |
| Change velocity | Recent deployments in the last 24h; last successful apply | Multiple recent deploys → elevate change velocity score |
| Cost impact | Current spend rate on resources being changed | Use to validate or adjust L1 cost estimate |

## Rationalization Prevention

| Thought | Reality |
|---------|---------|
| "This plan only adds resources, so it's safe" | STOP — additions can break existing resources via dependency changes, exhaust quotas, or introduce cost surprises. Score blast radius and dependency impact from the plan. |
| "It's just a tag change" | STOP — tag changes are usually Green, but verify the tag isn't used for routing, cost allocation, or conditional logic. Check whether any `count` or `for_each` uses the tag. |
| "The plan shows 0 destroys, so reversibility is Green" | STOP — `update in-place` can still be one-way (backup retention to 0, engine major version, lifecycle expiration). Check the one-way table. |
| "There's a final snapshot, so the destroy is reversible" | STOP — restore creates a new resource with a new endpoint, takes time, and loses data written after the snapshot. Still Red; the hard block needs justification. |
| "The plan says 'No changes', nothing to assess" | STOP — if the operator expected changes, the plan probably ran against the wrong workspace / var-file / context. Re-check the target. |
| "This is a rollback, so it's inherently safe" | STOP — rollbacks can fail, can conflict with data changes that happened after the original deploy, or can roll back to a state that no longer works with current dependencies. Score normally. |
| "The same change worked in staging" | STOP — staging doesn't have production traffic, production data, or production dependencies. Production risk is independent. |
| "This is just a config change, not infrastructure" | STOP — config changes cause more outages than infrastructure changes. Evaluate the same 10 categories. |
| "Scaling down saves money, so cost is Yellow" | STOP — a cost decrease is cost-Green. The risk is lost capacity: score it under blast radius and resource health. |
| "The resource shows 0 errors, so it's healthy and needed" | STOP — 0 errors ≠ used or necessary. A resource can run error-free and still be pure waste (an idle poller). Judge resource health on useful activity, not just the absence of failures. |
| "Releasing this Elastic IP is safe, nothing internal uses it" | STOP — a partner firewall may allowlist the public IP. Release is irreversible. Run the external-allowlist check (≥ 6mo zero egress + operator confirmation) before scoring Green. |
