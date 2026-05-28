**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-05-28 09:21
**Items considered:** 3   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md` (waste mode, single-cloud aws).
- 3 items above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) will score ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete vol-0xxxxxxxxxxxxxxx1 | ec2:DescribeVolumes | ec2:Describe* | ok | state=available; 200 GB gp3; no Attachments |
| 2 | Delete vol-0xxxxxxxxxxxxxxx1 | ec2:DescribeSnapshots | ec2:Describe* | ok | 1 snapshot (snap-0abcdef0123456789, completed 2026-05-13, weekly-backup) |
| 3 | Delete vol-0xxxxxxxxxxxxxxx1 | cloudtrail:LookupEvents (AttachVolume/DetachVolume, 90d) | cloudtrail:LookupEvents | ok | 0 events — no attach/detach in 90d |
| 4 | Rightsize i-0a1b2c3d4e5f67890 | ec2:DescribeInstances | ec2:Describe* | ok | m5.4xlarge, state=running, Name=prod-api, Service=payments |
| 5 | Rightsize i-0a1b2c3d4e5f67890 | cloudwatch:GetMetricStatistics (CPUUtilization, 14d) | cloudwatch:GetMetricStatistics | ok | avg 4.0% / max 13.8% over 14d |
| 6 | Rightsize i-0a1b2c3d4e5f67890 | cloudwatch:GetMetricStatistics (NetworkIn, 14d) | cloudwatch:GetMetricStatistics | ok | sum <70 MB/day — no sustained traffic burst |
| 7 | Rightsize i-0a1b2c3d4e5f67890 | compute-optimizer:GetEC2InstanceRecommendations | compute-optimizer:GetEC2InstanceRecommendations | ok | OVER_PROVISIONED; m5.4xlarge → m5.2xlarge; performanceRisk=1.0 (low); projectedCPUavg=8.04% |
| 8 | Rightsize i-0a1b2c3d4e5f67890 | elasticloadbalancing:DescribeTargetHealth (prod-api-tg) | elasticloadbalancing:DescribeTargetHealth | ok | 2 healthy targets (i-0a1b2c3d4e5f67890 + i-0b2c3d4e5f6789012) — redundancy present |
| 9 | Add lifecycle policy logs-bucket-app | s3:GetBucketLifecycleConfiguration | s3:GetBucketLifecycleConfiguration | ok | NoSuchLifecycleConfiguration — no existing policy |
| 10 | Add lifecycle policy logs-bucket-app | s3:ListBucketIntelligentTieringConfigurations | s3:ListBucketIntelligentTieringConfigurations | ok | IntelligentTieringConfigurationList=[] — no existing IT config |
| 11 | Add lifecycle policy logs-bucket-app | cloudwatch:GetMetricStatistics (BucketSizeBytes, StandardStorage) | cloudwatch:GetMetricStatistics | ok | 4,621,440,819,200 bytes (~4.30 TB) StandardStorage — within ±5% of upstream 4.2 TB estimate |

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 1 | $200/mo |
| 🟡 Coordinated | 1 | $280/mo |
| 🔴 Risky | 1 | $48/mo |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 0 | — |

**Total plan savings:** $528/mo ($200/mo high-confidence fast win + $280/mo medium-confidence coordinated + $48/mo high-confidence risky)

## 🟢 Fast wins

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 2 | Add S3 lifecycle policy (Standard → Glacier after 90d) | logs-bucket-app | $200/mo | 🟢 | 🟢 | 🟢 | 🟢 | line-item-computation (high) | Remove policy rule via IaC revert; objects already transitioned to Glacier re-transition to Standard on next access (Glacier restore) |

**Dimension detail:**
- **Reversibility 🟢** — Lifecycle policy add is a reversible config change; removing the policy rule returns the bucket to its prior state. Objects already transitioned to Glacier are retrievable via restore and re-transition automatically. (Playbook: lifecycle-s3.)
- **Blast radius 🟢** — Single-bucket policy add; no shared namespace touched; no other resources disrupted.
- **Evidence of no-use 🟢** — No existing lifecycle policy (query #9: NoSuchLifecycleConfiguration) and no Intelligent-Tiering config (query #10). CloudWatch confirms ~4.30 TB StandardStorage (query #11), consistent with upstream estimate. Policy-only change does not delete data.
- **Dependency footprint 🟢** — No catalog; IaC grep finds no other resource referencing logs-bucket-app ARN or name in a way that would break if a lifecycle policy is added.

> Ordering hint: none — lifecycle policy addition is independent of other items in this plan.

## 🟡 Coordinated

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 1 | Rightsize prod-api m5.4xlarge → m5.2xlarge | i-0a1b2c3d4e5f67890 | $280/mo | 🟢 | 🟡 | 🟢 | 🟡 | compute-optimizer (medium) | Re-apply old IaC (instance_type = "m5.4xlarge"); instance restart required |

**Dimension detail:**
- **Reversibility 🟢** — Instance type change is reversible by re-applying IaC with old type. Requires a stop/start cycle each direction. Data preserved on EBS root volume. (Playbook: rightsize-ec2.)
- **Blast radius 🟡** — Instance is registered as a target in ALB target group prod-api-tg (query #8: 2 healthy targets). During the stop/start cycle one target is briefly removed from rotation; ALB continues serving from the second target. Redundancy is present but the change touches a shared load-balancer namespace → 🟡 (not 🔴 because ≤1 other target).
- **Evidence of no-use 🟢** — Compute Optimizer confirms OVER_PROVISIONED with 14d avg CPU 4.0% / max 13.8% (queries #5, #7). Projected CPU after resize: avg 8.04% / max ~27% — well within m5.2xlarge headroom. NetworkIn confirms no sustained traffic burst (query #6). performanceRisk=1.0 (low, CO scale).
- **Dependency footprint 🟡** — No service-discovery catalog. IaC grep finds 1 consumer: the ALB target group registration for prod-api-tg references this instance ID. Single consumer → 🟡.

> Ordering hint: perform outside peak hours. prod-api serves payments traffic; schedule the stop/start during a low-traffic window (consult team for current peak window — catalog not present to read it automatically).

## 🔴 Risky

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 3 | Delete unattached EBS volume | vol-0xxxxxxxxxxxxxxx1 | $48/mo | 🔴 | 🟢 | 🟢 | 🟢 | line-item-computation (high) | Snapshot exists (snap-0abcdef0123456789, 2026-05-13); restore from snapshot then attach |

**Dimension detail:**
- **Reversibility 🔴** — EBS volume deletion is irreversible. Snapshot snap-0abcdef0123456789 (weekly-backup, completed 2026-05-13) exists and can serve as restore point, but the volume object itself cannot be recovered post-delete. Irreversibility alone forces 🔴 regardless of other dimension scores. (Playbook: delete-ebs-volume.)
- **Blast radius 🟢** — Volume is unattached (Attachments=[], query #1). No EC2 instance, no service, no data pipeline currently mounted to it. Single-resource delete with no shared-namespace impact.
- **Evidence of no-use 🟢** — Volume has been in state=available (unattached) since 2026-02-14 per upstream report. CloudTrail confirms 0 AttachVolume/DetachVolume events in the last 90 days (query #3). The volume has been dormant for 104 days.
- **Dependency footprint 🟢** — No catalog. IaC grep finds no resource referencing vol-0xxxxxxxxxxxxxxx1. No IaC data blocks targeting this volume ID.

> **Ordering hint: take snapshot before deleting.** A recent snapshot exists (snap-0abcdef0123456789, 2026-05-13), but it is 15 days old. The EBS playbook recommends creating a fresh snapshot immediately before delete to minimize recovery RPO. Use `iac-change-execution` to sequence the snapshot step before the destroy step.

## Gaps

None — all 11 verification queries succeeded. No failed queries, no IAM denials, no throttling.

## Next steps (informational)

- Pick an item and open `iac-change-execution`, passing this plan path and the item number.
- For item #2 (🟢): add `aws_s3_bucket_lifecycle_configuration` for logs-bucket-app with a `transition` block (days=90, storage_class=GLACIER). Low coordination overhead — can proceed independently.
- For item #1 (🟡): update `instance_type` in IaC for i-0a1b2c3d4e5f67890. Coordinate with the payments team on a low-traffic window before applying; ALB will continue serving from the second target during the stop/start.
- For item #3 (🔴): sequence (a) create fresh EBS snapshot, then (b) destroy vol-0xxxxxxxxxxxxxxx1. `iac-change-execution` + `pre-flight` will enforce the snapshot step before delete. Treat as irreversible — confirm the volume contents are not needed before proceeding.
- `iac-change-execution` will call `pre-flight` for full risk clearance before any apply. This plan's tier badge does not short-circuit pre-flight.
