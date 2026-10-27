**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-staging-waste-20260528-1130.md
**Mode of upstream:** waste
**Scope:** 987654321098 / acme-staging (single)
**Target:** account 987654321098 (sts verified, live:0a), region(s) us-east-1
**IaC repo(s):** none - ownership from tags only
**Catalog used:** none - Dimension 4 conservative scoring
**Date:** 2026-05-28 11:36
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-staging-waste-20260528-1130.md` (waste mode, single-cloud aws, fresh).
- 2 items above $5/mo floor; 0 filtered below floor.
- Target: account `987654321098`, region `us-east-1`.
- Catalog: none - `.culiops/service-discovery/` does not exist. **IaC repo: none supplied**, so the ownership grep cannot run: owners resolve to `unknown` and Dimension 4 scores ⚪ for both items (🟡-equivalent for the lifecycle change; a delete with Dimension 4 ⚪ goes to 🔴 `dependency-unknown` per tier rule 3). `unmanaged` cannot be proven, so Reversibility never gets the "re-apply old IaC" basis.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

All queries executed 2026-05-28 11:31-11:34 UTC. Row numbering: `0a` target check, `0b-<item>` ownership probe, then `1..N`. Evidence is summarized.

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 987654321098 = `Scope`; region us-east-1 (2026-05-28T11:31Z) |
| 0b-1 | Delete vol-0bbbb1 | ec2:DescribeVolumes (tags) | ec2:Describe* | ok | `State=available`, `Attachments=[]`, 200 GB gp3; no `kubernetes.io/*` / `ebs.csi.aws.com/*` tag; no IaC repo → owner **unknown** |
| 0b-2 | Lifecycle logs-archive-bucket | s3:GetBucketTagging | s3:GetBucketTagging | ok | no CloudFormation / controller tag; no IaC repo → owner **unknown** |
| 1 | Delete vol-0bbbb1 | ec2:DescribeSnapshots | ec2:Describe* | ok | 1 snapshot `snap-0cccc2def3456789a`, completed 2026-05-08, DLM-managed |
| 2 | Delete vol-0bbbb1 | cloudtrail:LookupEvents (AttachVolume/DetachVolume, 90d; management events) | cloudtrail:LookupEvents | ok | 0 events in 2026-02-27 → 2026-05-28: unattached for the whole window |
| 3 | Delete vol-0bbbb1 | rbin:ListRules (EBS_SNAPSHOT) | rbin:ListRules | ok | no Recycle Bin rule |
| 4 | Lifecycle logs-archive-bucket | s3:GetBucketLifecycleConfiguration | s3:GetLifecycleConfiguration | ok | `NoSuchLifecycleConfiguration` |
| 5 | Lifecycle logs-archive-bucket | s3:GetBucketVersioning | s3:GetBucketVersioning | ok | versioning never enabled |
| 6 | Lifecycle logs-archive-bucket | s3:ListBucketIntelligentTieringConfigurations | s3:GetIntelligentTieringConfiguration | ok | none |
| 7 | Lifecycle logs-archive-bucket | cloudwatch:GetMetricData (`BucketSizeBytes`, `NumberOfObjects`; daily, 90d) | cloudwatch:GetMetricData | ok | Standard 3,968,054,599,680 B (3.61 TiB) / 661,000 objects (avg 6.0 MB); nothing in other classes |
| 8 | Lifecycle logs-archive-bucket | s3:ListBucketAnalyticsConfigurations + s3:GetObject (SCA export) | s3:GetAnalyticsConfiguration, s3:GetObject | ok | Storage Class Analysis, 98 days of history; objects aged >= 90d: 641,000 (3,584 GiB), **0 GET requests** |
| 9 | Lifecycle logs-archive-bucket | s3:ListBucketInventoryConfigurations + s3:GetObject (inventory report) | s3:GetInventoryConfiguration, s3:GetObject | ok | objects aged >= 90d: p5 = 480 KiB, none < 128 KiB |
| 10 | Lifecycle logs-archive-bucket | ce:GetCostAndUsage (S3 storage line items, 30d) | ce:GetCostAndUsage | ok | bill-derived Standard rate; target-class rates from the Pricing API fallback (pricing get-products, AmazonS3, us-east-1, read 2026-05-28; fictional fixture values) |
| d1 | Lifecycle logs-archive-bucket | docs read: https://docs.aws.amazon.com/AmazonS3/latest/API/API_RestoreObject.html (read 2026-05-28) | none (public page) | ok | objects archived to Glacier Flexible Retrieval are not accessible in real time: a restore request and a wait come first |

**Total estimated API cost:** one Cost Explorer request (billed per request) plus a few S3 GETs and free describe/list calls; CloudTrail LookupEvents is free; the documentation read (`d1`) costs $0.

### Principle 2 cost-direction computation (item #2)

Fixture rates (bill-derived Standard, Pricing-API-fallback Glacier Flexible Retrieval; not AWS list prices): gross 3,584 GiB x (0.0540 − 0.0036) = +$180.6/mo; archive per-object overhead (641,000 x 40 KiB) −$0.3/mo; early-deletion exposure $0 (no expiration); retrieval fees $0 (0 reads of aged objects). **Net +$180.3/mo** (upstream $180/mo, +0.2%). One-time transition requests (641,000 x 0.06 per 1,000) −$38.5; payback about 6 days. Direction confirmed positive.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 1 | $180/mo |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 1 | $52/mo |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 0 | — |

**Total plan savings:** $232/mo ($180/mo high-confidence coordinated + $52/mo high-confidence risky). Totals count only `Realizable ✓` rows; both rows are ✓.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

| # | Action | Resource | Owner | Savings | Realizable | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|------------|---------------|-------|----------|------------|--------|----------|
| 2 | Add S3 lifecycle rule (Standard → Glacier Flexible Retrieval after 90d, no expiration) | logs-archive-bucket | unknown | $180/mo | ✓ cost direction net +$180/mo after fees (live:7,8,9,10) | 🟡 any `Transition`; docs: https://docs.aws.amazon.com/AmazonS3/latest/API/API_RestoreObject.html (d1) | 🟢 | 🟢 live:8,9 | ⚪ no catalog, no IaC repo | line-item-computation (high) | Removing the rule does NOT move objects back; restore + copy needed (fees apply). No IaC to revert (owner unknown) |

**Dimension detail - #2 lifecycle logs-archive-bucket:**
- **Reversibility 🟡** - `lifecycle-s3.md`: a `Transition` to Glacier Flexible Retrieval is 🟡 (reads fail until restore). Independently, owner `unknown` removes the IaC-revert basis, so even an instantly readable target could not be 🟢 here.
- **Blast radius 🟢** - single bucket, adds the only rule on an empty rule set (live:4).
- **Evidence 🟢** - every `required` row passes: 0 GET requests on objects aged >= 90d across 98 days of Storage Class Analysis (live:8; Glacier Flexible target); net +$180.3/mo after fees (live:10 inputs, computation above); observed 3.61 TiB vs the report's 3.6 TB (live:7); no Intelligent-Tiering overlap (live:6); not versioned (live:5).
- **Dependency footprint ⚪** - no catalog and no IaC repo: nothing to scan. For this non-delete change, ⚪ on Dimension 4 is 🟡-equivalent (it does not force 🔴; a delete with ⚪ on Dimension 4 or Blast radius does, see #1). Operator should confirm no consumer reads objects of that age (e.g. quarterly pulls) before applying. Running `service-discovery` replaces the ⚪ with a real score.

**Why #2 is not 🟢:** Reversibility is 🟡 and Dimension 4 is ⚪. Tier rule 4 (any 🟡 including ⚪ on Dimension 4 for a non-delete, no 🔴 / 🚫 / 🔵 / Evidence-⚪). A catalog alone would not make it a Fast win.

> Ordering hint: #2 is independent of #1.

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

| # | Action | Resource | Owner | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|---------------|-------|----------|------------|--------|----------|
| 1 | Delete unattached EBS volume (`dependency-unknown`) | vol-0bbbb1 | unknown | $52/mo | 🟡 valid rollback snapshot (live:1,2) | 🟢 | 🟢 live:2 | ⚪ no catalog, no IaC repo | line-item-computation (high) | Restore from `snap-0cccc2def3456789a` (new volume ID); take a fresh final snapshot first |

**Dimension detail - #1 delete vol-0bbbb1:**
- **Reversibility 🟡** - a *valid* rollback snapshot exists: `snap-0cccc2def3456789a` is `completed`, started 2026-05-08, after the volume's last detach (which predates the 90d window, live:2) and inside the window. It is DLM-managed, so its retention is not guaranteed (Gap). Without it this would be 🔴. The playbook queried Recycle Bin rules for `EBS_SNAPSHOT` only (live:3): whether an `EBS_VOLUME` rule exists is unknown, not "no rule".
- **Blast radius 🟢** - unattached, not Kubernetes-owned (live:0b-1).
- **Evidence 🟢** - no Attach/Detach event in 90d (live:2): unattached >= 60d (upstream dates it 2026-02-20, 97 days).
- **Dependency footprint ⚪** - no catalog and no IaC repo, so no repo was searched and nothing can be said about who references the volume. **Tier rule 3 (last clause):** the action is a delete and Dimension 4 is ⚪ → 🔴 `dependency-unknown`. Unknown is not safe. Evidence 🟢 and Reversibility 🟡 do not offset it. Supplying the IaC repo or running `service-discovery` replaces the ⚪ with a real score and can move the item to 🟡.

> Ordering hint: take a fresh final snapshot before deleting #1 (the existing one is 20 days old and DLM-managed).

## 🚫 Do not act

No items in this tier.

## ❔ Manual review required

No items in this tier.

## Drift

None - no IaC repo was supplied, so no code-versus-live comparison was possible.

## Gaps

- Service-discovery catalog absent at `.culiops/service-discovery/` and no IaC repo supplied: Dimension 4 scored ⚪ for both items and owners are `unknown`. Supply the IaC repo path and/or run `service-discovery`, then re-run for tighter scoring (Dependency and ownership; #1 can then leave 🔴, #2 stays 🟡 because of Reversibility).
- Item #1: Dimension 4 is ⚪, so the delete is held in 🔴 `dependency-unknown` until the IaC repo is searched or a catalog exists. Recycle Bin `EBS_VOLUME` rules were not queried (unknown, not "no rule").
- Item #1: the DLM policy's retention for `snap-0cccc2def3456789a` is not queried by the playbook; use a dedicated, tagged final snapshot taken at execution time.

## Next steps (informational)

- #2 (🟡): add the lifecycle rule through whichever IaC owns the bucket (find it first: owner is `unknown`). Every eligible object is already older than 90 days, so the whole 3,584 GiB transitions on the first run; confirm nobody reads that data. Merge into the existing rule set (there is none today).
- #1 (🔴 `dependency-unknown`): first supply the IaC repo or run `service-discovery` and re-run; then sequence (a) fresh final snapshot, then (b) delete `vol-0bbbb1`. Owner `unknown`: there may be no IaC resource to remove; `iac-change-execution` will establish that.
- **Run `service-discovery` and supply the IaC repo for a tighter triage.**
- `iac-change-execution` will call `pre-flight` for full risk clearance before any apply. This plan's tier badge does not short-circuit pre-flight.
