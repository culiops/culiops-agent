# Dry-run of `cloud-cost-investigate` against `waste-aws-account`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

Note: `get-rds-database-recommendations` and `get-idle-recommendations` are now in `examples/aws.md` (Step 2B), so Q7 (RDS recommendations) is part of the plan. `get-idle-recommendations` is not modelled here (the fixture has no idle findings).

Cost view: every Cost Explorer figure below is the three usage record types (`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`) at `AmortizedCost`. No commitment applies to EBS, snapshots, RDS or the untagged lines, so those numbers equal their unblended charge; only the covered m5 EC2 usage differs.

## Step 1 - Detect & Scope

- Reads `operator-question.md`. Heuristic: "waste audit / delete or rightsize" gives **waste mode** (suggested).
- Detects AWS from `AWS_PROFILE` / `~/.aws/` (simulated for the fixture).
- **Scoping probe (GATE 1a)**, 4 read-only calls, 1 CE request, about $0.01 (`scoping-probe.json`):

  | # | API | Result |
  |---|-----|--------|
  | 1 | `sts get-caller-identity` | account `123456789012` |
  | 2 | `iam list-account-aliases` | `acme-prod` |
  | 3 | `organizations describe-organization` | `MasterAccountId` = `999988887777`, not the caller: **member account**. CE returns only this account, so no `LINKED_ACCOUNT` filter. (Payer variant: caller == `MasterAccountId` would require `LINKED_ACCOUNT` = `123456789012` on EVERY CE call, otherwise the figures are organization-wide.) |
  | 4 | `ce get-cost-and-usage` MONTHLY 2026-04, usage record types (`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`), `AmortizedCost`, group `REGION` | us-east-1 $29,760.00 (62.0%), eu-west-1 $16,800.00 (35.0%), NoRegion $1,440.00 (3.0%); total $48,000.00 |

- Sweep regions: every region above the 1% noise floor that is a real region: **us-east-1 and eu-west-1**. NoRegion (global: IAM, Route 53, CloudFront) has no regional sweep; it is a Gap, not "clean".
- Time range: previous complete month 2026-04-01 to 2026-05-01 for cost; utilization 30d hourly (2026-04-08 to 2026-05-08). Catalog: none (waste mode allows this). IaC repo: none, so Owner comes from tags only.
- Scoping summary: mode=waste, account=`123456789012` (`acme-prod`, member), scope=single, regions=us-east-1 (62.0%) + eu-west-1 (35.0%).

**GATE 1:** operator confirms scope, mode, regions and time range.

## Step 2B - Waste mode query plan (GATE 2 batch)

Regional calls run once per sweep region and are shown as one row. Queries 1-4 are the probe above.

| # | API | Scope | Region(s) | Time | IAM | Est. cost | Why |
|---|-----|-------|-----------|------|-----|-----------|-----|
| 5 | `compute-optimizer get-ec2-instance-recommendations` | account | us-east-1, eu-west-1 | 14d lookback | `compute-optimizer:GetEC2InstanceRecommendations` | $0 | rightsize leads (priced at on-demand) |
| 6 | `compute-optimizer get-ebs-volume-recommendations` | account | both | 14d | `compute-optimizer:GetEBSVolumeRecommendations` | $0 | EBS leads |
| 7 | `compute-optimizer get-rds-database-recommendations` | account | both | 14d | `compute-optimizer:GetRDSDatabaseRecommendations` | $0 | DB findings (Optimized / not) |
| 8 | `ec2 describe-volumes --filters status=available` (with Tags) | account | both | now | `ec2:DescribeVolumes` | $0 | unattached volumes + owner tags |
| 9 | `cloudtrail lookup-events` (ResourceName = each of 12 volume ids) | account | both | last 90d | `cloudtrail:LookupEvents` | $0 | DetachVolume time = unused-since |
| 10 | `ec2 describe-snapshots --owner-ids self` | account | both | now | `ec2:DescribeSnapshots` | $0 | snapshots + policy markers |
| 11 | `ec2 describe-volumes` (all ids) | account | both | now | `ec2:DescribeVolumes` | $0 | orphan check (a): source volume live? |
| 12 | `ec2 describe-images --owners self` | account | both | now | `ec2:DescribeImages` | $0 | orphan check (b): AMI reference? |
| 13 | `savingsplans describe-savings-plans` + `ec2 describe-reserved-instances` | account | global / both | now | `savingsplans:DescribeSavingsPlans`, `ec2:DescribeReservedInstances` | $0 | commitments and end dates |
| 14 | `ce get-savings-plans-coverage` + `ce get-reservation-coverage` | EC2 | global | 2026-04 | `ce:GetSavingsPlansCoverage`, `ce:GetReservationCoverage` | $0.02 (2 requests) | `Realizable` |
| 15 | `ce get-cost-and-usage` (EBS usage types, group `REGION` x `USAGE_TYPE`) | usage record types, `AmortizedCost` | global | 2026-04 | `ce:GetCostAndUsage` | $0.01 (1 page) | bill-derived $/GB-Mo |
| 16 | `ce get-cost-and-usage-with-resources` (snapshot usage group, group `RESOURCE_ID`) | account | global | 2026-04-24..2026-05-01 (7d; resource-level data covers the last 14d, opt-in) | `ce:GetCostAndUsageWithResources` | $0.01 (1 page) | per-snapshot bill cost |
| 17 | `ce get-cost-and-usage` (group `TAG:Service` x `SERVICE`) | usage record types, `AmortizedCost` | global | 2026-04 | `ce:GetCostAndUsage` | $0.01 (1 page) | untagged spend |

**Total estimated API cost:** $0.05 for the batch (plus $0.01 probe). CloudTrail `LookupEvents` is throttled (2 requests/s per region): 12 lookups are spaced out.
**IAM permissions needed:** the consolidated list of the IAM column plus the probe's `sts:GetCallerIdentity`, `iam:ListAccountAliases`, `organizations:DescribeOrganization`.

**GATE 2:** operator approves.

## Step 3 - Execute the batch

- Q5-Q7 return `compute-optimizer.json` (one combined fixture file for three calls): 3 EC2 recs (two us-east-1, one eu-west-1), 1 EBS rec, 1 RDS rec (`Optimized`).
- Q8 returns `unattached-volumes.json` (12 volumes: 8 us-east-1, 4 eu-west-1; 3,300 GB).
- Q9 returns `detach-events.json`; Q10 returns `snapshots-older-than-30d.json` (47); Q11 + Q12 return `snapshot-checks.json`.
- Q13 + Q14 return `commitment-coverage.json`; Q15 returns `ebs-cost-by-usage-type.json`; Q16 returns `snapshot-cost-by-resource.json`; Q17 returns `untagged-spend.json` ($8,000.00).
- Every query status `ok`. Rows: Q5 3, Q6 1, Q7 1, Q8 12, Q9 12 lookups (11 with a DetachVolume event), Q10 47, Q11 40 live volume ids, Q12 4 AMI snapshot refs.

## Step 4 - Drill-down decision (GATE 3 batch)

Gaps in the first batch: CO rows rest on a 14-day lookback and no activity data (Principle 1/3); the Aurora writer needs its binding constraint; an RDS extended-support line needs a recurring-vs-residual check. Proposed batch (each metric query is paired with its `list-metrics` existence check in the SAME batch):

| # | API | Region | Time | Est. cost | Why |
|---|-----|--------|------|-----------|-----|
| 18 | `cloudwatch get-metric-statistics` AWS/EC2 `CPUUtilization`, **`--period 3600`**, Average + Maximum, 3 instances | us-east-1 (2), eu-west-1 (1) | 30d (720 hourly datapoints per instance, under the 1,440 cap) | $0 | confirm resize over >= 30d at hourly granularity |
| 19 | `cloudwatch list-metrics` (AWS/EC2, `InstanceId`) x3 | same | - | $0 | an empty series is only "zero" if the metric exists |
| 20 | `cloudwatch get-metric-statistics` AWS/RDS `CPUUtilization`, `FreeableMemory`, `DatabaseConnections`, `--period 3600`, `acme-prod-aurora-writer` | us-east-1 | 30d hourly | $0 | binding constraint of a database |
| 21 | `cloudwatch list-metrics` (AWS/RDS, `DBInstanceIdentifier`) x3 | us-east-1 | - | $0 | existence check for Q20 |
| 22 | `rds describe-db-instances --query 'DBInstances[].DBInstanceIdentifier'` | both | now | $0 | does `db-legacy-pg13` still exist? |
| 23 | `ce get-cost-and-usage` (RDS service, usage type `USE1-RDS:PostgreSQL-ExtendedSupport`) | global | 2026-04 | $0.01 | rate and quantity of the extended-support line |

7 queries (<= 10), $0.01 estimated. **GATE 3:** operator approves.

Execute: Q18/Q19 return `utilization-metrics.json`; Q20/Q21 return `db-binding-metrics.json`; Q22/Q23 return `residual-charge.json`. **The fixture represents the hourly series as a summary envelope** (`datapointCount`: 720, average / p50 / p99 of the hourly averages, max of the hourly maximums, plus a 5-point sample); the real call returns all 720 points per metric and instance.

| Instance | Region | 30d hourly CPU avg | p50 | p99 | max | Hours < 10% | CO lookback metrics |
|----------|--------|--------------------|-----|-----|-----|-------------|---------------------|
| `i-0aaaa1111bbbb2222` | us-east-1 | 3.8% | 3.6% | 9.4% | 14.9% | 99% | avg 3.8% / max 14.2% (14d) |
| `i-0bbbb3333cccc4444` | us-east-1 | 4.1% | 3.9% | 8.8% | 13.1% | 99% | avg 4.1% / max 12.8% (14d) |
| `i-0cccc5555dddd6666` | eu-west-1 | 2.6% | 2.5% | 5.7% | 8.3% | 100% | avg 2.6% / max 8.1% (14d) |

Steady low use with no burst in the temporal distribution: the resize signal is confirmed, so the three CO rows move from `low` to `medium`, subject to coverage below.

## Step 4B - Waste analysis

### Commitment coverage (Realizable)

- Q13: one active plan, EC2 Instance Savings Plan, family m5, **us-east-1**, $4.20/hr, ends **2027-02-14**. No RIs in either region.
- Q14: m5 us-east-1 100.0% covered ($4,200.00 on-demand equivalent; the plan's own commitment bills $4.20 x 720 h = $3,024.00); c5 us-east-1 0.0% ($2,640.00 on-demand); m5 **eu-west-1** 0.0% ($1,860.00 on-demand, the plan is region-bound).
- Amortized view (the skill's cost view): covered m5 usage is billed as `SavingsPlanCoveredUsage` at the effective rate, $3,024.00/mo (the commitment, fully used, no unused amount), against $4,200.00 at on-demand value (`commitment-coverage.json` `amortizedView`). Compute Optimizer's $280.00 is priced at on-demand, so it is not a saving on this bill while the plan runs.
- Result: `i-0aaaa` (m5, us-east-1) is fully covered, so downsizing it saves about $0 until 2027-02-14: its row shows `covered until 2027-02-14` and leaves the totals. `i-0bbbb` (c5) and `i-0cccc` (m5, eu-west-1) are not covered: realizable.

### Dedup

`vol-0xxxx1234abcd5678` is in Q6 (CO resize 1,000 to 250 GB, $60.00/mo at list price) and Q8 (available). The skill keeps ONE row, the **delete** row, and notes the resize as the alternative. After dedup there are 12 unattached volumes, each counted once, and the CO EBS recommendation is not a separate row. (CO evaluated the volume while it was still attached; it was detached 2026-05-05.)

### Unattached EBS: window and ownership (Principle 3, H7)

Rate (Q15, bill-derived): us-east-1 gp3 $3,300.00 / 41,250 GB-Mo = **$0.0800/GB-Mo**; eu-west-1 gp3 $1,980.00 / 22,500 GB-Mo = **$0.0880/GB-Mo**. All 12 volumes are at the gp3 baseline (3000 IOPS, 125 MB/s), so there is no IOPS/throughput add-on.

| Volume | Region | GB | Last DetachVolume | Days ago | Owner tags | Verdict |
|--------|--------|----|-------------------|----------|------------|---------|
| `vol-0xxxx1234abcd5678` | us-east-1 | 1000 | 2026-05-05 | 3 | none | LOW: detached 3 days ago (`window-too-short`); also the CO resize overlap |
| `vol-0aaaa0001bbbb0001` | us-east-1 | 500 | 2026-02-22 | 75 | PV/CSI tags | LOW: `kubernetes-pv`, holds data, owner confirm |
| `vol-0aaaa0002bbbb0002` | us-east-1 | 400 | none in 90d | - | none | LOW: `window-unverified` (no DetachVolume event in 90 days) |
| `vol-0aaaa0003bbbb0003` | us-east-1 | 300 | 2026-02-26 | 71 | none | eligible (>= 60d since detach), row 1 |
| `vol-0aaaa0004bbbb0004` | us-east-1 | 250 | 2026-03-03 | 66 | none | eligible (>= 60d since detach), row 1 |
| `vol-0aaaa0005bbbb0005` | us-east-1 | 200 | 2026-02-12 | 85 | none | eligible (>= 60d since detach), row 1 |
| `vol-0aaaa0006bbbb0006` | us-east-1 | 200 | 2026-03-01 | 68 | none | eligible (>= 60d since detach), row 1 |
| `vol-0aaaa000bbbbb000b` | us-east-1 | 50 | 2026-02-27 | 70 | none | eligible (>= 60d since detach), row 1 |
| `vol-0aaaa0007bbbb0007` | eu-west-1 | 150 | 2026-02-18 | 79 | none | eligible (>= 60d since detach), row 2 |
| `vol-0aaaa0008bbbb0008` | eu-west-1 | 100 | 2026-03-05 | 64 | none | eligible (>= 60d since detach), row 2 |
| `vol-0aaaa0009bbbb0009` | eu-west-1 | 100 | 2026-02-09 | 88 | none | eligible (>= 60d since detach), row 2 |
| `vol-0aaaa000abbbb000a` | eu-west-1 | 50 | 2026-03-02 | 67 | none | eligible (>= 60d since detach), row 2 |

Eligible set: us-east-1 1,000 GB x $0.0800 = **$80.00**; eu-west-1 400 GB x $0.0880 = **$35.20**.

### Snapshots: three orphan checks (C2)

Q10 returns every snapshot older than 30 days (47 = 35 us-east-1 + 12 eu-west-1). Age is not orphaned. Each snapshot is classified in this order: (c) policy marker (AWS Backup tag/description, DLM tag/description) -> (b) referenced by an AMI (Q12) -> (a) source volume still exists (Q11) -> otherwise orphan candidate.

| Class | Count | Report section |
|-------|-------|----------------|
| AWS Backup-managed | 14 (9 us-east-1, 5 eu-west-1) | Informational: backup retention review |
| DLM-managed | 8 (us-east-1) | Informational: backup retention review |
| AMI-backed (source volume already gone) | 4 (3 us-east-1, 1 eu-west-1) | Informational: backup retention review |
| Live source volume (unattached volume still exists) | 4 (3 us-east-1, 1 eu-west-1) | Informational: backup retention review |
| **Orphan candidates** (volume gone, no AMI, no policy) | **17** (12 us-east-1, 5 eu-west-1) | Remediation rows 5 and 6 |

Total 14 + 8 + 4 + 4 + 17 = 47. The 4 live-source snapshots belong to volumes `vol-0aaaa0003`, `0004`, `0005` and `0007`, all of which are delete candidates in rows 1-2: if those volumes are deleted, these 4 snapshots become orphan candidates (re-run after the cleanup; not counted now).

Cost of the orphan candidates is **bill-derived and incremental**, from Q16 (7-day resource-level cost per snapshot ARN, x 30/7):

| Region | Candidates | 7-day bill cost | Monthly (x 30/7) | Naive `VolumeSize x rate` (rejected) |
|--------|-----------|-----------------|------------------|--------------------------------------|
| us-east-1 | 12 | $7.35 | **$31.50** | 3,400 GB x $0.05 = $170.00 |
| eu-west-1 | 5 | $3.15 | **$13.50** | 1,050 GB x $0.055 = $57.75 |

The naive figures ($227.75) would overstate the saving about 5.1x. Snapshot storage is incremental and chained, so the bill-attributed cost is an upper bound for what deletion frees: confidence `medium`, not `high`.

Orphan candidate ids, us-east-1: `snap-27a485a3f00fee560`, `snap-ecbf2e34c4af15f20`, `snap-641a84044143aa063`, `snap-4feb5435ab632479f`, `snap-76521964b030fc89c`, `snap-7e0d92bd7b1e72a1b`, `snap-f5eb794f3d1919b7c`, `snap-174754ad1ac539316`, `snap-7051f0c8c2ca4b004`, `snap-a985f263b75a2cf25`, `snap-e8d2fd878e6ca39af`, `snap-b82f7a29b191e86af`.
Orphan candidate ids, eu-west-1: `snap-d4215ab346b413872`, `snap-4dd27b8bbe72fcfe9`, `snap-6e928f48a6d73c35d`, `snap-b0dc1d5f0f70fcae8`, `snap-de07ed407d029fcde`.

Backups, for the Informational section: 30 snapshots, bill-attributed $175.50/mo (us-east-1 $135.00 + eu-west-1 $40.50), no savings claimed.

### Aurora writer (Principle 3, binding constraint)

`acme-prod-aurora-writer` (db.r6g.4xlarge, 128 GB): 30d hourly CPU average 12.1%, but `FreeableMemory` minimum ~1.6 GB of 128 GB and `DatabaseConnections` rising (average 1,840, max 2,210) toward the limit. Memory- and connection-bound: NOT downsizeable. Compute Optimizer agrees (`Optimized`, Q7). Not a remediation row; evidence `live:20`, `live:21`, `live:7`.

### Residual charge (Principle 4, recurring vs residual)

Q22: `db-legacy-pg13` is absent from `describe-db-instances` in both regions (deleted 2026-04-16). Q23: `USE1-RDS:PostgreSQL-ExtendedSupport` $37.20 for 372 instance-hours = $0.10/instance-hour (bill-derived). One-off line for hours before deletion; it does not recur. Classified `residual / self-clearing`, not chased, reported in Informational.

### Untagged spend

Q17: $8,000.00 with no `Service` tag (EC2 $5,200.00, EBS $1,800.00, S3 $1,000.00). Untagged is not waste: Informational, owner unknown, no savings.

### Threshold and totals

All 10 rows are above $5/mo (smallest $13.50); nothing is dropped.

| Bucket | Rows | Amount |
|--------|------|--------|
| High | 1, 2 | $80.00 + $35.20 = **$115.20** |
| Medium (counted) | 3, 4, 5, 6 | $124.00 + $78.00 + $31.50 + $13.50 = **$247.00** |
| Medium, covered (excluded) | 7 | $280.00 |
| Low | 8, 9, 10 | $80.00 + $40.00 + $32.00 = **$152.00** |
| **Total counted** | | **$514.20** |

## Step 5 - Compose report

Writes draft to `.culiops/cloud-cost-investigate/acme-prod-waste-<YYYYMMDD-HHmm>.md`.

Header:

```
**Cloud cost investigation**
**Mode:** waste
**Cloud:** aws
**Scope:** 123456789012 (acme-prod) (single) - member
**Regions covered:** us-east-1 (62.0% of spend in the window), eu-west-1 (35.0%); NoRegion/global (3.0%) is not sweepable
**Time range:** 2026-04-01 -> 2026-05-01 (cost); utilization 2026-04-08 -> 2026-05-08
**Catalog used:** none
**IaC repo(s):** none
**Date:** 2026-05-08 10:00
```

Queries run: rows 1-23 as above, each with status `ok` and a row count; extracted results only, no raw output.

### Remediation list (prioritized)

| # | Action | Resource(s) | Owner | Est. savings | Realizable | Source | Rate | Confidence | Evidence |
|---|--------|-------------|-------|--------------|------------|--------|------|------------|----------|
| 1 | Delete 5 unattached EBS volumes (us-east-1) | `vol-0aaaa0003bbbb0003`, `vol-0aaaa0004bbbb0004`, `vol-0aaaa0005bbbb0005`, `vol-0aaaa0006bbbb0006`, `vol-0aaaa000bbbbb000b` | unknown (no IaC repo given) | $80.00/mo | ✓ no commitment applies to EBS (live:13) | line-item-computation | bill-derived | high | available (live:8); last DetachVolume 2026-02-12..2026-03-03, 66-85d ago (live:9); no PV/CSI/CFN tags (live:8); 1,000 GB x $0.0800 = 3,300.00/41,250 GB-Mo (live:15) |
| 2 | Delete 4 unattached EBS volumes (eu-west-1) | `vol-0aaaa0007bbbb0007`, `vol-0aaaa0008bbbb0008`, `vol-0aaaa0009bbbb0009`, `vol-0aaaa000abbbb000a` | unknown (no IaC repo given) | $35.20/mo | ✓ no commitment applies to EBS (live:13) | line-item-computation | bill-derived | high | available (live:8); last DetachVolume 2026-02-09..2026-03-05, 64-88d ago (live:9); no PV/CSI/CFN tags (live:8); 400 GB x $0.0880 = 1,980.00/22,500 GB-Mo (live:15) |
| 3 | Rightsize prod-api-worker-02 c5.2xlarge to c5.xlarge (us-east-1) | `i-0bbbb3333cccc4444` | unknown (no IaC repo given) | $124.00/mo | ✓ c5 us-east-1: 0% SP/RI coverage (live:14) | compute-optimizer | list-price | medium | CO rec (live:5, 14d lookback); 30d hourly CPU avg 4.1%, p99 8.8%, 99% of hours < 10% (live:18, live:19) |
| 4 | Rightsize prod-batch-runner-01 m5.xlarge to m5.large (eu-west-1) | `i-0cccc5555dddd6666` | unknown (no IaC repo given) | $78.00/mo | ✓ m5 eu-west-1: 0% SP/RI coverage; the m5 plan is us-east-1 only (live:13, live:14) | compute-optimizer | list-price | medium | CO rec (live:5); 30d hourly CPU avg 2.6%, p99 5.7%, 100% of hours < 10% (live:18, live:19) |
| 5 | Delete 12 orphan-candidate snapshots (us-east-1) | 12 snapshot ids (listed in the notes) | unknown (no IaC repo given) | $31.50/mo | ✓ no commitment applies | line-item-computation | bill-derived | medium | all 3 orphan checks pass: source volume gone (live:11), no AMI reference (live:12), no AWS Backup/DLM marker (live:10); bill-attributed cost $7.35 over 7d x 30/7 (live:16); upper bound, chain effect |
| 6 | Delete 5 orphan-candidate snapshots (eu-west-1) | 5 snapshot ids (listed in the notes) | unknown (no IaC repo given) | $13.50/mo | ✓ no commitment applies | line-item-computation | bill-derived | medium | all 3 orphan checks pass (live:10, live:11, live:12); bill-attributed cost $3.15 over 7d x 30/7 (live:16); upper bound, chain effect |
| 7 | Rightsize prod-api-worker-01 m5.4xlarge to m5.2xlarge (us-east-1) | `i-0aaaa1111bbbb2222` | unknown (no IaC repo given) | $280.00/mo | **covered until 2027-02-14** (EC2 Instance SP, m5, us-east-1, 100% covered: live:13, live:14); billed at the $3,024.00/mo commitment either way (amortized covered usage; $4,200.00 on-demand value), so the $280.00 list-price saving is not on the bill; excluded from totals | compute-optimizer | list-price | medium | CO rec (live:5); 30d hourly CPU avg 3.8%, p99 9.4%, 99% of hours < 10% (live:18, live:19) |
| 8 | Delete unattached EBS volume (detached 3 days ago) | `vol-0xxxx1234abcd5678` (1,000 GB) | unknown (no IaC repo given) | $80.00/mo | ✓ no commitment applies | line-item-computation | bill-derived | low | `window-too-short`: DetachVolume 2026-05-05 (live:9); 1,000 GB x $0.0800 (live:15). Alternative, not counted: resize 1,000 to 250 GB, CO $60.00/mo list-price (live:6). Re-check on/after 2026-07-04 (60d) |
| 9 | Confirm owner, then delete or snapshot-and-delete the PV volume | `vol-0aaaa0001bbbb0001` (500 GB) | kubernetes-pv (PVC `orders/data-orders-pg-0`, cluster `acme-prod-eks`) | $40.00/mo | ✓ no commitment applies | line-item-computation | bill-derived | low | PV/CSI tags (live:8); DetachVolume 2026-02-22, 75d ago (live:9). A StatefulSet scaled to 0 holds data: owner confirm before any delete. 500 GB x $0.0800 (live:15) |
| 10 | Delete unattached EBS volume, detach date unknown | `vol-0aaaa0002bbbb0002` (400 GB) | unknown (no IaC repo given) | $32.00/mo | ✓ no commitment applies | line-item-computation | bill-derived | low | `window-unverified`: available (live:8) but no DetachVolume event in the 90-day history (live:9), CreateTime 2025-10-17 is not an unused-since date. 400 GB x $0.0800 (live:15) |

**Total estimated savings:** $115.20/mo (high) + $247.00/mo (medium) + $152.00/mo (low) = $514.20/mo. Row 7 ($280.00/mo, `covered until 2027-02-14`) is excluded from the totals.

### Informational / excluded

| Item | Amount | Source / rate | Reason | Evidence |
|------|--------|---------------|--------|----------|
| Untagged spend: EC2 $5,200.00, EBS $1,800.00, S3 $1,000.00 | $8,000.00/mo | line-item-computation | no `Service` tag; owner unknown. Visibility, not waste. No savings claimed | live:17 |
| RDS extended-support charge, deleted instance `db-legacy-pg13` | $37.20 (April, one-off) | line-item-computation, bill-derived $0.10/instance-hour | residual / self-clearing; instance deleted 2026-04-16, charge does not recur | live:22, live:23 |
| Aurora writer `acme-prod-aurora-writer` (db.r6g.4xlarge) | n/a | compute-optimizer (`Optimized`) | 12.1% CPU but ~1.6 GB free of 128 GB and rising connections: memory/connection-bound, not downsizeable | live:7, live:20, live:21 |
| Backup snapshots: AWS Backup 14, DLM 8, AMI-backed 4, live source volume 4 (30) | $175.50/mo billed | line-item-computation, bill-derived | policy-managed, AMI-backed or source volume exists: backups, not orphans. Retention review only. 4 become orphan candidates if their unattached source volumes (rows 1-2) are deleted | live:10, live:11, live:12, live:16 |

### Gaps

- Global / NoRegion spend (3.0%, $1,440.00) is not a region and was not swept.
- Sweeps in this fixture cover Compute Optimizer, EBS and snapshots only; NAT gateways, load balancers, Lambda, DynamoDB, Kinesis and EKS inventories are not part of this batch.
- No IaC repo was given: Owner is `unknown` except the Kubernetes PV (tag-derived).
- Snapshot savings are bill-attributed upper bounds (chained, incremental storage).
- `vol-0aaaa0002bbbb0002`: no DetachVolume event in the 90-day history; unused-since date unknown (`window-unverified`).
- Compute Optimizer savings are on-demand list prices (savings-estimation mode with discounts not enabled); rows 3, 4 and 7 are `list-price`.

### Next steps (informational)

- Triage the table with `cost-optimize-plan` before any change; confirm the owner of the Kubernetes PV volume (row 9) first.
- Re-check row 8 on or after 2026-07-04 (60 days after the detach).
- After rows 1-2 are executed, re-run the snapshot checks: 4 backups lose their source volume.
- Review the 30 backup snapshots' retention with the backup owner.

**GATE 4:** operator approves the report; skill commits only the report file (default-branch / public-remote warning applies).

## Gaps surfaced

(filled during actual dry-run)

## Fixes applied

(filled during actual dry-run)
