# Dry-run notes — missing-catalog

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides path to upstream report (`operator-question.md`). Skill loads `upstream-report.md`, extracts 2-item Remediation list, reads `**Cloud:** aws` (single-cloud), `**Scope:** 987654321098 / acme-staging`. Applies $5/mo floor — both items pass ($52, $180). Checks for `.culiops/service-discovery/` directory — **does not exist**. Checks for IaC tree (`*.tf`, `*.tfvars`, etc.) in working directory — **none found**. Scoping summary shows: `**Catalog:** none — Dimension 4 conservative scoring`. Skill presents scoping summary noting that Dimension 4 will score ⚪ for all items and be treated as 🟡-equivalent. Operator confirms 2 items, $5/mo floor, single-cloud aws. Approved.

2. **GATE 2 (Verification batch)** — Skill looks up playbooks for both items:
   - Item #1 (delete EBS): `examples/aws/delete-ebs-volume.md` → 3 queries (DescribeVolumes, DescribeSnapshots, CloudTrail LookupEvents attach/detach 90d).
   - Item #2 (lifecycle S3): `examples/aws/lifecycle-s3.md` → 3 queries (GetBucketLifecycleConfiguration, ListBucketIntelligentTieringConfigurations, BucketSizeBytes metric).
   Both playbooks present; no manual-review items. Total: 6 queries, 0 deduplication opportunities (no shared resources). Estimated API cost: ~$0.50 (CloudTrail LookupEvents 90d dominates). IAM perms list shown: `ec2:Describe*`, `cloudtrail:LookupEvents`, `cloudwatch:GetMetricStatistics`, `s3:GetBucketLifecycleConfiguration`, `s3:ListBucketIntelligentTieringConfigurations`. Operator approves full batch.

3. **GATE 3 (Plan review)** — Skill executes 6 queries against mock-responses (all succeed). Scoring:
   - **Item #1 (delete vol-0bbbb1):** Reversibility 🟡 (snapshot exists, 20d old — below 30d threshold), Blast 🟢 (unattached, no consumers), Evidence 🟢 (0 events 90d, dormant 97d), Dependency ⚪ (no catalog, no IaC tree).
   - **Item #2 (lifecycle logs-archive-bucket):** Reversibility 🟢 (policy-only change), Blast 🟢 (single-bucket), Evidence 🟢 (no existing policy, ~3.70 TB confirmed), Dependency ⚪ (no catalog, no IaC tree).
   Tier rule evaluation:
   - Rule 1 (🚫): Evidence is 🚫? No → skip.
   - Rule 2 (🔴): Reversibility 🔴 or Blast 🔴 or Dependency 🔴 or Evidence ⚪? No — Dependency is ⚪ but disambiguation rule says ⚪ on Dim 4 = 🟡-equivalent, NOT 🔴. → skip.
   - Rule 3 (🟡): any dimension 🟡 (including ⚪ on dimensions 1/2/4), no 🔴 / 🚫 / Evidence-⚪? Yes — both items have Dependency ⚪ (= 🟡-equivalent) → **both land in 🟡 Coordinated**.
   Ordering hint: snapshot-before-delete emitted for item #1. Draft plan composes with 0 items in 🟢, 2 items in 🟡. Operator reviews — sees dependency-⚪ note per item and in Gaps section, approves. Plan written to `.culiops/cost-optimize-plan/acme-staging-20260528-1136.md`.

## What this fixture validates

- **Conservative ⚪ tier rule: missing catalog does NOT force items to 🔴.** Dimension 4 ⚪ triggers the 🟡-equivalent path in tier rule 3, not the 🔴 path in rule 2. Both items land in 🟡 Coordinated.
- **Dimension 4 ⚪ on ALL items still produces meaningful tier output (🟡 Coordinated).** The plan is not blocked or degraded to all-🚫; it proceeds with a conservative but actionable placement.
- **Plan summary shows 0 🟢 Fast wins.** ⚪ on Dimension 4 prevents Fast win qualification because rule 4 (🟢 Fast win) requires all four dimensions to be 🟢, and ⚪ is not 🟢.
- **Plan compose shows the dependency-unknown explanation per item AND in the Gaps section.** Each item's Dependency dimension detail states "Dimension 4 ⚪ — no catalog and no IaC tree access" and suggests running `service-discovery`. The Gaps section repeats this at plan level with the actionable suggestion to re-run after catalog regeneration.
- **All 6 verification queries succeed (Evidence dimension 🟢 for both items).** The missing catalog is a scoping-step gap, not a verification failure — the queries themselves return good data.
- **Snapshot-before-delete ordering hint emitted for item #1.** The existing snapshot (2026-05-08) is 20 days old; playbook recommends a fresh snapshot to minimize RPO.

## Acceptance check

A reviewer confirms:
(a) The skill does not error on missing catalog — scoping summary acknowledges the absence and proceeds with conservative scoring.
(b) Both items land in 🟡 Coordinated, not 🔴 Risky — the ⚪ disambiguation rule (Dependency ⚪ → 🟡-equivalent) fires correctly.
(c) The Evidence column (and Dimension detail section) for each item explicitly notes the Dimension 4 ⚪ status and explains why — "no catalog and no IaC tree access; operator should manually verify no consumers before applying."
(d) The plan summary table shows 🟢=0, 🟡=2, 🔴=0 — no items were promoted to 🔴 by the ⚪ score.
(e) The Gaps section mentions the missing catalog and the `service-discovery` skill as the remedy.
