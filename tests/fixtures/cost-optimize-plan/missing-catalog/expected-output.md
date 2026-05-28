**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-staging-waste-20260528-1130.md
**Mode of upstream:** waste
**Scope:** 987654321098 / acme-staging (single)
**Catalog used:** none — Dimension 4 conservative scoring
**Date:** 2026-05-28 11:36
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-staging-waste-20260528-1130.md` (waste mode, single-cloud aws).
- 2 items above $5/mo floor; 0 filtered below floor.
- Catalog: none — `.culiops/service-discovery/` does not exist. No IaC tree accessible. Dimension 4 (Dependency) will score ⚪ for all items; treated as 🟡-equivalent per tier rules.
- Region: us-east-1.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete vol-0bbbb1 | ec2:DescribeVolumes | ec2:Describe* | ok | state=available; 200 GB gp3; no Attachments |
| 2 | Delete vol-0bbbb1 | ec2:DescribeSnapshots | ec2:Describe* | ok | 1 snapshot (snap-0cccc2def3456789a, completed 2026-05-08, weekly-backup) |
| 3 | Delete vol-0bbbb1 | cloudtrail:LookupEvents (AttachVolume/DetachVolume, 90d) | cloudtrail:LookupEvents | ok | 0 events — no attach/detach in 90d |
| 4 | Add lifecycle policy logs-archive-bucket | s3:GetBucketLifecycleConfiguration | s3:GetBucketLifecycleConfiguration | ok | NoSuchLifecycleConfiguration — no existing policy |
| 5 | Add lifecycle policy logs-archive-bucket | s3:ListBucketIntelligentTieringConfigurations | s3:ListBucketIntelligentTieringConfigurations | ok | IntelligentTieringConfigurationList=[] — no existing IT config |
| 6 | Add lifecycle policy logs-archive-bucket | cloudwatch:GetMetricStatistics (BucketSizeBytes, StandardStorage) | cloudwatch:GetMetricStatistics | ok | 3,968,054,599,680 bytes (~3.70 TB) StandardStorage — within ±5% of upstream 3.6 TB estimate |

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 2 | $232/mo |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 0 | — |

**Total plan savings:** $232/mo (both items high-confidence, both in 🟡 due to Dependency ⚪)

## 🟢 Fast wins

No items in this tier (Dimension 4 scored ⚪ for all items due to missing catalog — ⚪ is treated as 🟡-equivalent, preventing 🟢 Fast win qualification).

## 🟡 Coordinated

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 2 | Add S3 lifecycle policy (Standard → Glacier after 90d) | logs-archive-bucket | $180/mo | 🟢 | 🟢 | 🟢 | ⚪ | line-item-computation (high) | Remove policy rule via IaC revert; objects already transitioned to Glacier re-transition to Standard on next access |
| 1 | Delete unattached EBS volume | vol-0bbbb1 | $52/mo | 🟡 | 🟢 | 🟢 | ⚪ | line-item-computation (high) | Snapshot exists (snap-0cccc2def3456789a, 2026-05-08); restore from snapshot then attach |

**Item #2 — Add lifecycle policy logs-archive-bucket**

**Dimension detail:**
- **Reversibility 🟢** — Lifecycle policy add is a reversible config change; removing the policy rule returns the bucket to its prior state. Objects already transitioned to Glacier are retrievable via restore and re-transition automatically. (Playbook: lifecycle-s3.)
- **Blast radius 🟢** — Single-bucket policy add; no shared namespace touched; no other resources disrupted.
- **Evidence of no-use 🟢** — No existing lifecycle policy (query #4: NoSuchLifecycleConfiguration) and no Intelligent-Tiering config (query #5). CloudWatch confirms ~3.70 TB StandardStorage (query #6), consistent with upstream estimate. Policy-only change does not delete data.
- **Dependency footprint ⚪** — Dimension 4 ⚪ — no catalog and no IaC tree access. Operator should manually verify no consumers before applying. Catalog can be regenerated with `service-discovery` skill. ⚪ treated as 🟡-equivalent per tier rules → item placed in 🟡 Coordinated (not 🔴 Risky).

**Item #1 — Delete unattached EBS volume vol-0bbbb1**

**Dimension detail:**
- **Reversibility 🟡** — EBS volume deletion is irreversible. However, snapshot snap-0cccc2def3456789a (weekly-backup, completed 2026-05-08) exists and is 20 days old — recent enough to mitigate risk but not a same-day backup. Snapshot restore is the rollback path; volume object cannot be recovered post-delete. (Playbook: delete-ebs-volume.) Scored 🟡 rather than 🔴 because a recent snapshot is present (playbook threshold: snapshot <30d old → 🟡; no snapshot or snapshot >90d → 🔴).
- **Blast radius 🟢** — Volume is unattached (Attachments=[], query #1). No EC2 instance, no service, no data pipeline currently mounted to it. Single-resource delete with no shared-namespace impact.
- **Evidence of no-use 🟢** — Volume has been in state=available (unattached) since 2026-02-20 per upstream report. CloudTrail confirms 0 AttachVolume/DetachVolume events in the last 90 days (query #3). The volume has been dormant for 97 days.
- **Dependency footprint ⚪** — Dimension 4 ⚪ — no catalog and no IaC tree access. Operator should manually verify no consumers before applying. Catalog can be regenerated with `service-discovery` skill. ⚪ treated as 🟡-equivalent per tier rules → item placed in 🟡 Coordinated (not 🔴 Risky).

> **Ordering hint: take snapshot before deleting.** The existing snapshot (snap-0cccc2def3456789a, 2026-05-08) is 20 days old. The EBS playbook recommends creating a fresh snapshot immediately before delete to minimize recovery RPO. Use `iac-change-execution` to sequence the snapshot step before the destroy step.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

No items in this tier.

## ❔ Manual review

No items in this tier.

## Gaps

Service-discovery catalog absent at `.culiops/service-discovery/`. Dimension 4 (Dependency footprint) scored ⚪ for all items; conservative tier rules placed otherwise-fast-win items in 🟡 Coordinated. Operator can regenerate the catalog and re-run for tighter tiering.

## Next steps (informational)

- For item #2 (🟡 logs-archive-bucket lifecycle): low coordination overhead for the policy change itself, but verify no downstream consumers depend on current storage class before applying. Add `aws_s3_bucket_lifecycle_configuration` via `iac-change-execution`.
- For item #1 (🟡 vol-0bbbb1 delete): sequence (a) create fresh EBS snapshot, then (b) destroy vol-0bbbb1. Treat as irreversible — confirm contents not needed before proceeding.
- **Run `service-discovery` first for a tighter triage.** With a catalog in place, Dimension 4 can score 🟢 or 🟡 based on actual consumers rather than ⚪ unknown — both items may qualify for 🟢 Fast win after catalog-based scoring.
- `iac-change-execution` will call `pre-flight` for full risk clearance before any apply. This plan's tier badge does not short-circuit pre-flight.
