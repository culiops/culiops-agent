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

**Disruption.** For each app-facing changed resource, state what running traffic sees: `none` / `restart` / `failover` / `replace` / `brief unavailability`. Evidence: `plan:` for in-place vs replace; `docs: <URL>` for what that attribute change does (some in-place changes still reboot or fail over a database; a pod-template change rolls pods); `live:` for what softens it (Multi-AZ, replica count, PodDisruptionBudget, rolling-update `maxUnavailable`, ECS deployment configuration). If a calling skill passed a Disruption field, cite it instead of re-deriving. Disruption not established → category 1 is ⚪, never `none`.

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
| Major version upgrade of a managed service: ElastiCache, OpenSearch, MSK, an EKS / Kubernetes control plane | Red until `docs:` shows a downgrade path — treat as one-way |
| Namespace deleted | Red, hard block when it holds PVCs or other stateful objects (everything namespaced in it goes) |
| PVC deleted, or a PV / StorageClass with `reclaimPolicy: Delete` | Red, hard block (the volume and its data are deleted with the claim) |

**The table is not a complete list.** A row can raise a score (cite `assessor:`); it never clears one. An in-place change to an attribute that is not on it is Green only with `docs: <URL>` (or `live:`) showing that re-applying the old value restores the previous state. Without that the category is ⚪. Tags, labels and annotations are exempt.

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

Analyze git history of the changed files on the branch this change merges to (`<base>`; for per-environment branches, the environment's branch):
- `git log --since=7.days --oneline <base> -- <changed-files>` → count recent commits
- Exclude this change's own commits (`git log <base>..HEAD`) — a multi-commit PR doesn't count against itself
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
- Kubernetes: Services and Ingress hosts that others dial, CRDs, `ClusterRole` / `ClusterRoleBinding`s, shared ConfigMaps / Secrets / PVCs, a namespace's ResourceQuota

Cross-reference with service-discovery catalog if available (`.culiops/service-discovery/<service>.md`):
- Check `## Dependency Graph` section for downstream consumers
- Check whether changed resources are marked as critical-path
- If catalog shows 3+ downstream consumers → **Red**
- If catalog shows 1–2 downstream consumers → **Yellow**
- If catalog shows none → **Yellow**, not Green: it is a lead (`catalog:`). Green needs `code` (references to the resource's outputs, ARNs or names in the repo) or `live` (the dependents query in `examples/`) showing nothing consumes it
- If no catalog exists → score as unknown (⚪), suggest running service-discovery. Exception: every changed resource is on the not-app-facing list (see `### Application compatibility`) and the plan changes no output / export → **Green**, citing the plan. Nothing can consume an alarm or a dashboard

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

An alarm counts only if it watches the changed resources (its namespace / metric / dimensions or label selectors point at them), not just because its name contains the service name. An alarm or rule that exists only in code is `code:` evidence and scores Yellow; Green needs `live:` confirmation that it exists and is enabled (CloudWatch `ActionsEnabled`, Prometheus rule loaded).

Classify alerting maturity:
- SLO burn-rate alerting → **Green** (best practice)
- SLI-based threshold alerting → **Green** (acceptable)
- Static threshold alerting (CPU > 80%, memory > 90%) → **Yellow** (prone to false positives)
- No alerting on changed resources → **Red**

Check whether the change itself modifies monitoring:
- Deleting or disabling alarms/monitors → **Red** (reducing observability)
- Adding new alarms/monitors → lowers risk (improving observability)
- **The change only adds or edits not-app-facing monitoring** (alarms, dashboards, metric filters) and changes nothing app-facing → **Green**. This category asks whether a break caused by *this change* would be detected, and such a change gives the app nothing to break. The maturity ladder above scores the monitoring around app-facing changes, not the alarm being added. The mitigation is to confirm after apply that the new alarm leaves `INSUFFICIENT_DATA`

### Cost impact

Detect cost-relevant changes in the plan:
- New resources: check instance types, storage sizes, replica counts
- Instance type changes: flag moves to larger / GPU / high-memory instances
- Replica count increases: multiply by per-unit cost estimate
- Cross-region replication additions: flag data transfer costs
- NAT Gateway additions: flag hourly + per-GB data processing charges
- Usage-based services (API Gateway, Lambda, SQS, SNS): flag if traffic volume is unknown
- Additions that are only alarms, dashboards or metric filters are cost-**Green** when the price is looked up (the pricing page or API for the region, `docs:` or the lookup date) — a remembered "small fixed price" is not evidence. Log groups are not in this exception: ingestion and storage scale with volume
- Decreases (scale-down, rightsizing, deletion) are cost-**Green** only when nothing they leave behind keeps billing: final or retained snapshots and backups, and committed purchases (reservations, savings plans) still bill after the resource is gone. Check `code` / `live`, or cite `docs:`; otherwise **Yellow**. Their capacity risk is scored under blast radius and resource health — don't count it twice
- Kubernetes cost drivers: `Service` of type `LoadBalancer` or a new Ingress (provisions a cloud load balancer), a new PVC (provisions a volume), GPU requests, and replica or resource-request increases that make the autoscaler add nodes. Price the node / volume / load balancer the provider bills, with the lookup date

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

A narrowing (removed action, tighter resource or condition) is Green here only when the full before and after documents are in evidence. A diff with `# (N unchanged attributes hidden)` or a partial hunk cannot show effective access: an added `Deny`, a `NotAction`, or a changed `Principal` or `Condition` can widen it. Compare statement by statement (IAM: Effect, Action / NotAction, Resource, Principal, Condition; RBAC: verbs, resources, subjects, scope). Not comparable → ⚪. Whether the app still needs what was removed is category 11, below.

### Application compatibility

Category 11 is **fail-closed** (`SKILL.md` → Scoring Rules). A changed attribute is **not app-facing** only if it is on this list:

- Tags / labels / annotations that nothing reads at runtime, descriptions, comments
- Dashboards, metric filters, log groups and log retention
- Alarms whose actions only notify: no actions, or SNS topics whose subscriptions are all `email`, `email-json` or `sms`. Check this with the subscription-protocol query in `examples/aws.md`, reading protocols only and never endpoints. An alarm action that scales (Auto Scaling or Application Auto Scaling policy), stops, reboots, terminates or recovers EC2, starts SSM automation, or reaches a `lambda`, `sqs`, `firehose`, `http(s)` or `application` subscriber changes the system, so that alarm is **app-facing**. If the subscriber protocols were not checked, treat the alarm as app-facing (unsure means triggered). Kubernetes equivalent: a `PrometheusRule` is notify-only only when every Alertmanager receiver it routes to is one the operator names as email, chat or paging (receiver types only — never URLs or tokens; `operator-stated`). A webhook, or anything that scales, restarts or remediates, makes it app-facing; receivers not checked → app-facing
- Backup, snapshot and recovery-point schedules (score them under category 2)
- Scaling counts alone: desired count, replicas, min / max size (score them under category 1)
- IAM for humans and CI/CD roles (not a role the workload runs as)
- Cost-only purchase options: reservations, savings plans, spot / on-demand split

**Everything else is app-facing.** The table below shows common app-facing changes and what to search for. It is a set of examples, not the trigger list. A resource type missing from it still triggers category 11.

| Attribute | Terraform | Kubernetes (Helm / Kustomize / manifests) | ecspresso / lambroll | What to search in the app |
|---|---|---|---|---|
| Workload permissions removed or narrowed | task / function / instance-profile role policy, IRSA / Pod Identity role policy, resource policy (bucket, queue, key) | the ServiceAccount's role annotation, RBAC for in-cluster API calls | task role / function role ARN | the SDK call for each removed action (`sqs:SendMessage` → `SendMessage(`), the resource name / ARN |
| Env var / config key removed, renamed, or value format changed | `environment` / `secrets` in task definitions, Lambda `environment`, SSM parameter names | `env`, `envFrom`, ConfigMap / Secret **keys**, mounted file paths | `environment`, `secrets`, Lambda `Environment` names | the old and new names (`Getenv`, `process.env`, `os.environ`, config struct tags); how the value is parsed |
| Endpoint identity: hostname, port, path, protocol | DB / cache endpoint after replace, listener port, target-group health-check path, DNS record, queue / topic / bucket / table rename or replace | `Service` port / port name, `Ingress` path, container port, probe path | `portMappings`, `healthCheck` command / path | the host / port / path the app dials or serves; the health-check handler |
| Engine or runtime version | `engine_version` (major), cache `engine_version`, Lambda `runtime`, OpenSearch / Kafka version | image of a sidecar or dependency chart (DB, broker) | Lambda `runtime` | driver / client library version in the lockfile (`go.mod`, `package-lock.json`, `requirements*.txt`, `pom.xml`); compatibility with the new version is a `docs:` claim (the driver's or engine's support matrix) |
| Limits the app must fit inside | SQS visibility timeout, ALB / NLB idle timeout, DB `max_connections` (parameter group), Lambda timeout / memory / reserved concurrency, API Gateway timeout | CPU / memory limits, `terminationGracePeriodSeconds`, HPA min / max | task CPU / memory, Lambda timeout / memory | processing time, connection pool size, request timeout, shutdown handling |
| CDN, edge and request routing | CloudFront cache behaviors (`path_pattern`, `allowed_methods`), cache policy (cache key: headers / cookies / query strings; TTLs), origin request policy, CloudFront Functions / Lambda@Edge, ALB listener rules, API Gateway routes / authorizers / stage variables, WAF rules | `Ingress` paths, rewrites and annotations, Gateway API routes, service-mesh routing | — | the routes under the pattern; whether each response depends on the user (cookies, `Authorization`, session) or on headers / query strings left out of the cache key; whether the app sets `Cache-Control` / `Vary`; HTTP methods the routes need. A cookie-dependent response under a cache key without that cookie is served to other users: also score it under category 9 |
| Encryption key on data the app reads | KMS key change on bucket / table / queue / secret | — | — | whether the app's role can use the new key (`kms:Decrypt`) — usually an IAM check, not code |

**Scoring** (after Step 3b):
- A use of the old contract is found → **Red**. Name the call site (`app:` citation) and the failure mode. Logged-and-ignored or default-fallback failures are silent: say that health checks, error rate and alarms will not show the break.
- The app degrades but keeps working (e.g. a timeout falls back to a shorter default) → **Yellow**, with the effect.
- All uses found and compatible (e.g. the app already reads both the old and the new name) → **Green**, cite them.
- No use found → **Yellow**, unless `live` evidence also shows the old contract unused (e.g. IAM last-accessed for the service older than the activity window, zero sends / requests over ≥ 30 days) → then **Green**. A text search can miss dynamic names and other consumers.
- No source available → **⚪**.

**Mitigation pattern:** expand–contract. Ship the app change that works with both the old and the new contract, deploy it, verify (live), then make the infra change. Or keep the old contract. Removing a permission the app uses only after the app stops calling it.

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
| Blast radius | Replicas, Multi-AZ, PodDisruptionBudget, rolling-update / deployment settings | Softeners present → `live:` evidence for the Disruption field. Absent → disruption is not softened |
| Dependency impact | Consumers of the changed resource (`examples/` → Disruption and dependents) | Any consumer → at least Yellow. None found → `live:` evidence for Green |
| Observability readiness | Verify alarms/dashboards exist in the live system and are enabled (not just in IaC) | Alarms defined in code but not present live → IaC drift, elevate observability score. Present and enabled → `live:` evidence for Green |
| Timing context | Current request rate vs. baseline — is this peak traffic? | Request rate > 1.5x baseline → peak traffic, elevate timing score |
| Change velocity | Recent deployments in the last 24h; last successful apply | Multiple recent deploys → elevate change velocity score |
| Cost impact | Current spend rate on resources being changed | Use to validate or adjust L1 cost estimate |
| Application compatibility | For a removed permission or resource: role last-accessed, `simulate-principal-policy`, send / publish activity on the resource (`examples/aws.md` → Application Compatibility Checks). For a removed Service port or Ingress path, or narrowed RBAC: traffic on that port / path over ≥ 30 days (`examples/kubernetes.md` → Application Compatibility Checks) | Used recently → supports a Red found in code; unused over ≥ 30 days **and** no use in the source → Green. Live data alone never shows how the app fails |

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
| "This is just a config change, not infrastructure" | STOP — config changes cause more outages than infrastructure changes. Evaluate the same 11 categories. |
| "Scaling down saves money, so cost is Yellow" | STOP — a cost decrease is cost-Green. The risk is lost capacity: score it under blast radius and resource health. |
| "The resource shows 0 errors, so it's healthy and needed" | STOP — 0 errors ≠ used or necessary. A resource can run error-free and still be pure waste (an idle poller). Judge resource health on useful activity, not just the absence of failures. |
| "This attribute isn't in the one-way table, so it's reversible" | STOP — the table is a starting point. Unlisted means unchecked: find the docs for the attribute, or the category is ⚪. |
| "It's a decrease (or a delete), so cost is Green" | STOP — final snapshots, retained backups and committed purchases keep billing. Check what it leaves behind. |
| "The catalog lists no dependents, so nothing consumes it" | STOP — a catalog is a lead from when it was written. Confirm with code or a live query. |
| "Releasing this Elastic IP is safe, nothing internal uses it" | STOP — a partner firewall may allowlist the public IP. Release is irreversible. Run the external-allowlist check (≥ 6mo zero egress + operator confirmation) before scoring Green. |
