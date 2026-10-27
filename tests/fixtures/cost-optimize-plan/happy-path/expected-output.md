**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Target:** account 123456789012 (sts verified, live:0a), region(s) ap-southeast-1
**IaC repo(s):** ~/acme-infra (simulated for this fixture; code refs illustrative)
**Catalog used:** none
**Date:** 2026-05-28 09:21
**Items considered:** 3   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md` (waste mode, single-cloud aws, dated 2026-05-28 — fresh).
- 3 items above $5/mo floor; 0 filtered below floor.
- Target: account `123456789012` (from `Scope`), region `ap-southeast-1` (from the resource IDs/ARNs).
- Catalog: none — Dimension 4 scored from the IaC grep only; where neither a catalog nor a grep hit resolves it, it would be ⚪.
- IaC repo supplied: `~/acme-infra`. The ownership probe and Dimension 4 grep run there.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

All queries executed 2026-05-28 09:18-09:20 UTC. Row numbering: `0a` = target check, `0b-<item>` = ownership probe for that item, then `1..N` in batch order. Evidence below is summarized (Constraint 14); no raw output recorded.

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 123456789012 = `Scope`; region ap-southeast-1 (2026-05-28T09:18Z) |
| 0b-1 | Rightsize i-0a1b2c3d4e5f67890 | ec2:DescribeInstances (tags) + IaC grep | ec2:Describe* | ok | no `aws:autoscaling:groupName` / `eks:` / `karpenter.sh` tag; IaC match `ec2.tf:17` → owner **terraform**; `instance_type = "m5.4xlarge"` = live (no drift) |
| 0b-2 | Lifecycle logs-bucket-app | s3:GetBucketTagging + IaC grep | s3:GetBucketTagging | ok | no controller / CloudFormation tag; bucket resource `s3.tf:42`, no lifecycle config in code → owner **terraform** |
| 0b-3 | Delete vol-0xxxxxxxxxxxxxxx1 | ec2:DescribeVolumes (tags) + IaC grep | ec2:Describe* | ok | `State=available`, `Attachments=[]`; no `kubernetes.io/*` / `ebs.csi.aws.com/*` tag; full tag set read (`Environment` only), none names a controller or automation; `~/acme-infra` searched, no IaC match → owner **unmanaged** |
| 1 | Rightsize i-0a1b2c3d4e5f67890 | ec2:DescribeInstanceTypes | ec2:Describe* | ok | m5.4xlarge 16 vCPU / 64 GiB → m5.2xlarge 8 vCPU / 32 GiB; same arch (x86_64); not burstable; **target RAM < current → memory row required** |
| 2 | Rightsize i-0a1b2c3d4e5f67890 | cloudwatch:GetMetricData (CPU Avg/Max/p95, NetworkIn/Out; 30d @ 3600s) | cloudwatch:GetMetricData | ok | CPU mean 4.0%, hourly max 13.8%, max hourly p95 9.1%; peak NetworkIn 2.6 KB/s, NetworkOut 5.8 KB/s; 720 points/series, dimensions from the describe call |
| 3 | Rightsize i-0a1b2c3d4e5f67890 | cloudwatch:ListMetrics + GetMetricData (CWAgent `mem_used_percent`; 30d @ 3600s) | cloudwatch:ListMetrics, GetMetricData | ok | agent installed; `mem_used_percent` mean 18.7%, max 34.5% (dimension set copied from ListMetrics) |
| 4 | Rightsize i-0a1b2c3d4e5f67890 | compute-optimizer:GetEC2InstanceRecommendations | compute-optimizer:GetEC2InstanceRecommendations | ok | OVER_PROVISIONED; m5.4xlarge → m5.2xlarge; lookback 14d (< 30d, so thresholds use rows 2-3, not CO) |
| 5 | Rightsize i-0a1b2c3d4e5f67890 | elbv2:DescribeTargetGroups + DescribeTargetHealth | elasticloadbalancing:Describe* | ok | member of `prod-api-tg` with 1 other healthy target (i-0b2c3d4e5f6789012): 2 healthy |
| 6 | Rightsize i-0a1b2c3d4e5f67890 | cloudwatch:DescribeAlarms (ALARM, filtered on InstanceId) | cloudwatch:DescribeAlarms | ok | 0 alarms in ALARM state reference the instance |
| 7 | Rightsize i-0a1b2c3d4e5f67890 | ce:GetSavingsPlansCoverage + ce:GetReservationCoverage (30d) | ce:Get* | ok | 0% Savings Plans coverage, 0 reserved hours of 720: on-demand |
| 8 | Lifecycle logs-bucket-app | s3:GetBucketLifecycleConfiguration | s3:GetLifecycleConfiguration | ok | `NoSuchLifecycleConfiguration`: no rule to overlap or replace |
| 9 | Lifecycle logs-bucket-app | s3:GetBucketVersioning | s3:GetBucketVersioning | ok | versioning never enabled: current-version rule covers all bytes |
| 10 | Lifecycle logs-bucket-app | s3:ListBucketIntelligentTieringConfigurations | s3:GetIntelligentTieringConfiguration | ok | none: no Intelligent-Tiering overlap |
| 11 | Lifecycle logs-bucket-app | cloudwatch:GetMetricData (`BucketSizeBytes`, `NumberOfObjects`; daily, 90d) | cloudwatch:GetMetricData | ok | Standard 4,621,440,819,200 B (4.20 TiB) / 541,000 objects (avg 8.5 MB); no bytes in any other storage class |
| 12 | Lifecycle logs-bucket-app | s3:ListBucketAnalyticsConfigurations + s3:GetObject (SCA export, `acme-analytics-exports`) | s3:GetAnalyticsConfiguration, s3:GetObject | ok | Storage Class Analysis `logs-all`, 115 days of history; objects aged >= 90d: 489,089 (3,891 GiB), **0 GET requests**; younger objects read normally |
| 13 | Lifecycle logs-bucket-app | s3:ListBucketInventoryConfigurations + s3:GetObject (inventory report) | s3:GetInventoryConfiguration, s3:GetObject | ok | objects aged >= 90d: p5 = 410 KiB, none < 128 KiB (the transition-size floor) |
| 14 | Lifecycle logs-bucket-app | ce:GetCostAndUsage (S3 storage line items, 30d) | ce:GetCostAndUsage | ok | bill-derived Standard rate for the cost-direction check; Standard-IA rates from the Pricing API fallback (no Standard-IA usage in the bill; pricing get-products, AmazonS3, ap-southeast-1, read 2026-05-28) |
| 15 | Delete vol-0xxxxxxxxxxxxxxx1 | ec2:DescribeSnapshots | ec2:Describe* | ok | 1 snapshot `snap-0abcdef0123456789`, completed 2026-02-08, manual |
| 16 | Delete vol-0xxxxxxxxxxxxxxx1 | cloudtrail:LookupEvents (AttachVolume/DetachVolume, 90d; management events) | cloudtrail:LookupEvents | ok | 0 events in 2026-02-27 → 2026-05-28: unattached for the whole window; last detach predates it and cannot be dated |
| 17 | Delete vol-0xxxxxxxxxxxxxxx1 | rbin:ListRules (EBS_SNAPSHOT) | rbin:ListRules | ok | no Recycle Bin rule for EBS snapshots (rules for `EBS_VOLUME` not queried) |
| d1 | Rightsize i-0a1b2c3d4e5f67890 | docs read: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/change-instance-type-of-ebs-backed-instance.html (read 2026-05-28) | none (public page) | ok | a type change needs the instance stopped; it is down while stopped (duration varies); a non-Elastic public IPv4 changes on stop/start |
| d2 | Lifecycle logs-bucket-app | docs read: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html (read 2026-05-28) | none (public page) | ok | S3 Standard-IA objects are available for millisecond access (retrieval fee applies; 128 KB / 30-day minimums) |

**Total estimated API cost:** ce:Get* (3 requests, billed per request) plus a handful of S3 GETs and GetMetricData calls — well under $0.25 at GATE 2 itemization; CloudTrail LookupEvents is free; the two documentation reads (`d1`, `d2`) cost $0.

### Principle 2 cost-direction computation (item #2, `lifecycle-s3.md` Query 6)

Rates: **bill-derived** Standard (row 14, fictional account); Standard-IA storage, transition-request and retrieval rates from the Pricing API fallback. Fixture values, not AWS list prices.

| Component | Value |
|---|---|
| Eligible bytes (aged >= 90d, row 12) | 3,891 GiB / 489,089 objects (none < 128 KiB, row 13: no minimum-size penalty) |
| Gross storage saving: 3,891 GiB x (Standard 0.0540 − Standard-IA 0.0290) per GiB-month | +$97.3/mo |
| Per-object overhead (IA has no archive-class metadata overhead) | $0 |
| Early-deletion exposure (no `Expiration`; IA 30-day minimum is met by objects already >= 90d old) | $0 |
| Expected retrieval fees (0 reads of aged objects, row 12) | $0 |
| **Net steady-state saving** | **+$97.3/mo** (upstream: $100/mo, −2.7%) |
| One-time transition requests (489,089 x 0.01 per 1,000) | −$4.9 once; payback about 1.5 days |

Result: `$210/mo (eligible 3,891 GiB in Standard) → ≈ $113/mo in Standard-IA`; direction confirmed positive. Because every eligible object is already older than 90 days, the **entire 3,891 GiB transitions on the first lifecycle run**. Reads keep working (IA is instantly readable); only retrieval fees would apply, and the access evidence says there are none.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 1 | $100/mo |
| 🟡 Coordinated | 1 | $280/mo |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 1 | $48/mo |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 0 | — |

**Total plan savings:** $428/mo ($100/mo high-confidence fast win + $280/mo medium-confidence coordinated + $48/mo high-confidence risky). Upstream numbers copied verbatim; recomputation for #2 agrees within 3%. Totals count only `Realizable ✓` rows; all three are ✓.

## 🟢 Fast wins

| # | Action | Resource | Owner | Savings | Realizable | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|------------|---------------|-------|----------|------------|--------|----------|
| 2 | Add lifecycle rule Standard → Standard-IA at 90d (no expiration) | logs-bucket-app | terraform `code:s3.tf:42` | $100/mo | ✓ cost direction net +$97/mo after fees (live:11,13,14) | 🟢 code:s3.tf:42, docs:https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html (d2) | 🟢 | 🟢 live:11,12,13,14 | 🟢 code:none outside module | line-item-computation (high) | Remove the rule via IaC revert; objects already in Standard-IA stay readable (an optional copy back costs retrieval / early-deletion fees) |

**Dimension detail:**
- **Reversibility 🟢** — `lifecycle-s3.md`: a `Transition` to an instantly readable class (Standard-IA) is 🟢: no data loss, reads keep working (millisecond access, docs d2), removing the rule stops further transitions. The IaC was found by the ownership probe (`code:s3.tf:42`, live:0b-2), so "re-apply old IaC" is a real rollback. (A transition to Glacier Flexible / Deep Archive would be 🟡; an `Expiration` 🔴.)
- **Blast 🟢** — single bucket, extends an empty rule set (live:8), nothing replaced.
- **Evidence 🟢** — every `required` row passes: cost direction net +$97.3/mo after transition requests, no minimum-size or early-deletion penalty (live:13,14; computation above); observed Standard size 4.20 TiB vs the report's 4.2 TB (live:11). The access-pattern row is `optional` for an instantly readable target and was run anyway: 0 GET requests on objects aged >= 90d across 115 days of Storage Class Analysis history (live:12), so it passes. No Intelligent-Tiering overlap (live:10), not versioned (live:9).
- **Dependency 🟢** — no consumer of the bucket resource outside its own module in the IaC grep.
- Not idle-ambiguous; tier rule 5 (all four 🟢). Rules 1-4 do not fire.

> Ordering hint: none - #2 is independent of #1 and #3.

## 🟡 Coordinated

| # | Action | Resource | Owner | Savings | Realizable | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|------------|---------------|-------|----------|------------|--------|----------|
| 1 | Rightsize prod-api m5.4xlarge → m5.2xlarge | i-0a1b2c3d4e5f67890 | terraform `code:ec2.tf:17` | $280/mo | ✓ on-demand, 0% SP/RI coverage (live:7) | 🟢 code:ec2.tf:17, docs:https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/change-instance-type-of-ebs-backed-instance.html (d1) | 🟡 live:5 | 🟢 live:2,3,6 | 🟡 code:alb.tf:64 | compute-optimizer (medium) | Re-apply old IaC (`instance_type = "m5.4xlarge"`); stop/start each way (the instance is down while stopped; d1) |

**Dimension detail:**
- **#1 Reversibility 🟢** — reversible resize on a terraform-owned instance; the IaC (`code:ec2.tf:17`) was found by the ownership probe (live:0b-1), so "re-apply old IaC" (reverting through the repo's own delivery path) is a real rollback; the stop/start behaviour is confirmed by docs (d1). **Blast 🟡** — registered in `prod-api-tg` with 1 other healthy target (live:5); the stop/start removes one target while the instance is stopped (d1). No catalog, so it is not bumped to 🟢 (the playbook bumps only on catalog confirmation). **Evidence 🟢** — every required row of `rightsize-ec2.md` passes over the 30d hourly window: mean CPU 4.0% (< 30%); p95 9.1% → 18.2% on the target (< 60%); max 13.8% → 27.6% (< 75%); peak network ≈ 0.05 Mbps vs "Up to 10 Gigabit" (< 50%); memory is **required** because target RAM (32 GiB) < current (64 GiB): max 34.5% → 69.0% on the target (< 75%); 0 alarms (live:2,3,6). Compute Optimizer's own 14d lookback (live:4) is not used for thresholds. **Dependency 🟡** — one IaC consumer: the target-group attachment at `code:alb.tf:64`.
- **Why not 🟢:** Blast 🟡 + Dependency 🟡. Tier rule 4 (any 🟡, no 🔴 / 🚫 / 🔵 / Evidence ⚪).

> Ordering hint: #1 outside peak hours; prod-api serves payments traffic (no catalog to read the peak window from - confirm with the owning team).

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

| # | Action | Resource | Owner | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|---------------|-------|----------|------------|--------|----------|
| 3 | Delete unattached EBS volume | vol-0xxxxxxxxxxxxxxx1 | unmanaged | $48/mo | 🔴 no provably valid rollback snapshot (live:15,16) | 🟢 | 🟢 live:0b-3,16 | 🟢 code:no hits | line-item-computation (high) | Take a fresh final snapshot first; restore from it (new volume ID) |

**Dimension detail:**
- **Reversibility 🔴** — the only snapshot (`snap-0abcdef0123456789`, 2026-02-08, live:15) predates the volume's detach and is older than the 90d CloudTrail window (live:16), so the last detach cannot be dated and the snapshot cannot be shown to contain the volume's final writes. `delete-unattached-ebs.md` keeps this 🔴 until a fresh final snapshot exists. No Recycle Bin rule for snapshots (live:17); whether an `EBS_VOLUME` rule exists is unknown, not "no rule" (not queried). Owner is `unmanaged`: no IaC to re-apply.
- **Blast 🟢** — unattached, single resource, not Kubernetes-owned (live:0b-3).
- **Evidence 🟢** — both required rows pass: no Attach/Detach event in the 90d window (live:16) so it has been unattached >= 60d (upstream dates it 2026-02-14, 103 days). The Evidence is 🟢, so tier rule 3's "delete AND Evidence not 🟢" clause does not fire; the 🔴 comes from Reversibility (first clause).
- **Dependency 🟢** — IaC grep for the volume ID returns no hit in `~/acme-infra`, the only repo searched (`iac-grep-simulated.json`); no catalog. Repos not supplied are not covered (Gaps).
- **Realizable ✓** — gp3 storage, no commitment applies.

> **Ordering hint: take a fresh final snapshot before deleting**, wait for `completed`, and only then delete. A snapshot taken after this point would be a valid rollback and re-score Reversibility 🟡. Use `iac-change-execution` to sequence it (it has no IaC resource to destroy: owner is `unmanaged`, so the delete is a manual step it will plan).

## 🚫 Do not act

No items in this tier.

## ❔ Manual review required

No items in this tier.

## Drift

| # | Resource | Code (`code:`) | Live (`live:`) | Note |
|---|----------|----------------|----------------|------|
| 1 | i-0a1b2c3d4e5f67890 | `instance_type = "m5.4xlarge"` (`ec2.tf:17`) | m5.4xlarge (live:0b-1) | none — matches |
| 2 | logs-bucket-app | no lifecycle configuration in code (`s3.tf:42`) | `NoSuchLifecycleConfiguration` (live:8) | none — matches |

## Gaps

None blocking — every query succeeded and every `required` signal was observed.
- Item #1: Compute Optimizer's lookback is 14d (live:4), shorter than the 30d rightsize requirement; tier thresholds rest on the skill's own 30d CloudWatch series (live:2,3).
- Item #2: recomputed net saving (+$97/mo) vs upstream $100/mo — within 3%, no disagreement to resolve; upstream figure kept in the plan.
- Item #2: optional access-pattern row ran (Storage Class Analysis) and passed; no optional row was declined.
- Item #3: dependency "no hit" covers `~/acme-infra` only; other repos were not supplied. Recycle Bin `EBS_VOLUME` rules were not queried (unknown, not "no rule").

## Next steps (informational)

- Pick an item and open `iac-change-execution`, passing this plan path and the item number. Each item carries its target, owner + `code:` address and `live:` evidence rows; `iac-change-execution` re-verifies live state itself (this plan may be days old), and `pre-flight` clearance is still mandatory.
- #2 (🟢): add `aws_s3_bucket_lifecycle_configuration` for `logs-bucket-app` with a single `transition` (days = 90, `STANDARD_IA`). The first run moves all 3,891 GiB at once; reads keep working, so the only exposure is retrieval fees if something reads old logs (none seen in 115 days).
- #1 (🟡): update `instance_type` at `ec2.tf:17`; coordinate a low-traffic window with the payments team.
- #3 (🔴): create and verify a fresh final snapshot, then delete the volume. Treat as irreversible once the snapshot is the only copy.
- `iac-change-execution` will call `pre-flight` for full risk clearance before any apply. This plan's tier badge does not short-circuit pre-flight.
