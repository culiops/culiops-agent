# Dry-run notes — happy-path

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides path to upstream report (`operator-question.md`). Skill loads `upstream-report.md`, extracts 3-item Remediation list, reads `**Cloud:** aws` (single-cloud), `**Scope:** 123456789012 / acme-prod`. Applies $5/mo floor — all 3 items pass ($280, $200, $48). No catalog at `.culiops/service-discovery/` — Dimension 4 will score ⚪ (treated as 🟡-equivalent). Skill presents scoping summary. Operator confirms 3 items, $5/mo floor, single-cloud aws. Approved.

2. **GATE 2 (Verification batch)** — Skill looks up playbooks for all 3 items:
   - Item #1 (rightsize EC2): `examples/aws/rightsize-ec2.md` → 5 queries (DescribeInstances, CPU metrics, NetworkIn metrics, CO recommendation, DescribeTargetHealth).
   - Item #2 (lifecycle S3): `examples/aws/lifecycle-s3.md` → 3 queries (GetBucketLifecycleConfiguration, ListBucketIntelligentTieringConfigurations, BucketSizeBytes metric).
   - Item #3 (delete EBS): `examples/aws/delete-ebs-volume.md` → 3 queries (DescribeVolumes, DescribeSnapshots, CloudTrail LookupEvents attach/detach 90d).
   All playbooks present; no manual-review items. Total: 11 queries, 0 deduplication opportunities (no shared resources). Estimated API cost: $1.20 (CloudTrail LookupEvents 90d dominates). IAM perms list shown: `ec2:Describe*`, `cloudtrail:LookupEvents`, `cloudwatch:GetMetricStatistics`, `compute-optimizer:GetEC2InstanceRecommendations`, `elasticloadbalancing:DescribeTargetHealth`, `s3:GetBucketLifecycleConfiguration`, `s3:ListBucketIntelligentTieringConfigurations`. Operator approves full batch.

3. **GATE 3 (Plan review)** — Skill executes 11 queries against mock-responses (all succeed), scores 4 dimensions for each item, assigns tiers (lifecycle=🟢, rightsize=🟡, delete-EBS=🔴), detects ordering hint (snapshot-before-delete on item #3), composes draft plan. Operator reviews — no revisions requested. Approved. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-0921.md`.

## What this fixture validates

- **Positive path with all queries succeeding.** Gaps section reads "None." No partial plan, no ⚪ Evidence scores.
- **Three actionable tiers produced (🟢/🟡/🔴), no 🚫 or ❔.** Lifecycle policy scores all 🟢 dimensions → Fast win. Rightsize scores blast 🟡 (ALB target, 2 healthy = redundancy but shared namespace) + dependency 🟡 (1 IaC consumer) → Coordinated. EBS delete scores reversibility 🔴 (irreversible, dominates) with all other dimensions 🟢 → Risky.
- **Ordering hint: snapshot-before-delete callout on item #3.** A snapshot exists (snap-0abcdef0123456789, 2026-05-13) but is 15 days old; playbook recommends a fresh snapshot before delete to minimize RPO. Emitted as a callout in the 🔴 section.
- **Reversibility 🔴 dominates other 🟢 dimensions → item #3 lands in 🔴 not 🟢.** Tier rule 2 fires (Reversibility is 🔴) before rule 4 can fire. Even though blast, evidence, and dependency are all 🟢, the item stays 🔴.
- **No catalog does not silently produce 🟢 Dependency scores.** Item #1 gets Dependency 🟡 because IaC grep finds 1 consumer (ALB TG). Item #3 gets Dependency 🟢 because grep finds none. No item claims 🟢 on Dependency from catalog absence alone.
- **Plan summary savings total $528/mo** ($200 + $280 + $48), matching the upstream report's combined estimate.

## Acceptance check

A reviewer steps through `upstream-report.md` + each `mock-responses/*.json` and confirms the skill would produce `expected-output.md` with representative results (allowing for run-specific timestamps). The tier assignments, dimension scores, ordering hints, and Gaps text must match exactly. Note: emoji rendering in tier columns must be visible; if a markdown renderer strips 4-byte UTF-8 characters, the test is incomplete.
