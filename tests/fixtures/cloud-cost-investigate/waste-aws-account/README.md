# waste-aws-account - cloud-cost-investigate fixture

Waste-mode fixture for a full account audit across two regions: Compute Optimizer rightsizing, unattached EBS volumes (with detach-time and Kubernetes-PV cases), snapshot orphan checks, commitment coverage, and four items that must stay OUT of the remediation table (untagged spend, a residual charge, an Aurora writer that is memory-bound, and backup snapshots).

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`), a **member** account of an AWS Organization (payer `999988887777`). April 2026 usage spend (the three usage record types at `AmortizedCost`) is $48,000.00 across us-east-1 (62%), eu-west-1 (35%) and global (3%); $8,000.00 of it carries no `Service` tag. Compute Optimizer (14-day lookback, on-demand pricing) returned 3 EC2 rightsizing recommendations (two in us-east-1, one in eu-west-1) and 1 EBS recommendation. There are 12 unattached gp3 volumes, 47 snapshots older than 30 days, one EC2 Instance Savings Plan (m5, us-east-1), and an Aurora writer with low CPU.

Fixture "now" is 2026-05-08; the cost window is the complete month 2026-04-01 to 2026-05-01 (30 days).

## The operator question

> "Run a waste audit on our AWS prod account. What can we delete or rightsize?"

(See `operator-question.md`.)

## What this fixture exercises

- **Mode detection from question phrasing:** "waste audit / delete or rightsize" gives waste mode (suggested at GATE 1).
- **Payer vs member and regions (H1/H2):** the scoping probe (`scoping-probe.json`) shows the caller is NOT the payer (`MasterAccountId` 999988887777), so no `LINKED_ACCOUNT` filter is needed (a payer variant would need it on every CE call). CE by `REGION` gives us-east-1 62.0%, eu-west-1 35.0%, NoRegion 3.0%; sweeps run in BOTH regions, findings exist in both, and the report header lists `Regions covered`.
- **Compute Optimizer is a lead, not a saving (H6):** CO rows start at `low`; after the 30d hourly drill-down (`utilization-metrics.json`) they are `medium`; rate basis is `list-price`.
- **Confidence floors (Law 3):** `high` needs a bill-derived rate, `live:` activity or event evidence, the window met and `Realizable` known. Rows 1-2 meet all four. Rows 3, 4 and 7 have the same evidence with a `list-price` rate: `medium`. Rows 5-6 have a bill-derived but upper-bound rate: `medium`. Rows 8-10 miss the window or the owner: `low`.
- **Realizable states:** `yes` (coverage fetched, none for that service / family / region; EBS and snapshots are not commitment-eligible), `covered until <date>` (row 7), `unknown` (none in this fixture). Only `yes` rows count toward totals.
- **Remediation ladder:** every delete row names its reversible first step (snapshot a volume, hold-tag a snapshot), with the delete last.
- **Tag activation:** `tag-activation.json` shows the `Service` key active before the window, so the untagged-spend figure is not `UNVERIFIED`.
- **Commitment coverage (Principle 4):** the m5 us-east-1 instance is 100% covered by an EC2 Instance Savings Plan until 2027-02-14, so its Realizable is `covered until 2027-02-14` (an owner decision) and it leaves the totals. In the amortized view its cost is the $3,024.00/mo commitment ($4,200.00 at on-demand value); Compute Optimizer's $280.00 is an on-demand figure. Coverage is read for the m5 family in us-east-1, and it is 100%, so no uncovered m5 usage could absorb a freed commitment (a Savings Plan applies hourly to the eligible usage that earns the most; `docs:` cited in the notes). The m5 instance in eu-west-1 is NOT covered (the plan is region-bound); the c5 instance is not covered.
- **EBS unused-since window (H7):** `detach-events.json` gives CloudTrail `DetachVolume` times. 9 volumes were detached 64-88 days ago (eligible, `high`); 1 was detached 3 days ago (`low`, `window-too-short`); 1 has no event in the 90-day history (`low`, `window-unverified`); 1 carries `kubernetes.io/created-for/pvc/name` + `ebs.csi.aws.com/cluster` (Owner `kubernetes-pv`, `low`, data, owner confirm).
- **Dedup (Step 4B):** `vol-0xxxx1234abcd5678` is in both the Compute Optimizer EBS output (resize 1,000 to 250 GB) and the unattached list. The skill keeps ONE row, the delete row, and notes the resize as the alternative; it is not counted twice.
- **Bill-derived rates (Principle 4):** the EBS rate comes from `ebs-cost-by-usage-type.json` (gp3: us-east-1 $0.0800, eu-west-1 $0.0880 per GB-Mo = cost / usage quantity). EC2 figures are Compute Optimizer's on-demand prices, labelled `list-price`.
- **Snapshots are not "older than 30 days" (C2):** all 47 old snapshots are classified by three checks (source volume gone / AMI reference / AWS Backup or DLM marker). 30 are backups (AWS Backup 14, DLM 8, AMI-backed 4, live source volume 4) and go to Informational for retention review; 17 are orphan candidates, priced from the bill per snapshot (incremental), not `VolumeSize x rate`.
- **Informational / excluded section:** untagged spend, the residual extended-support charge, the Aurora binding-constraint exclusion and the backup snapshots are reported with $ and reason, never in the remediation table (Constraint 7).
- **Binding constraint (Principle 3):** the Aurora writer reads 12% average CPU but ~1.7 GB free of 128 GB and rising connections, so it is not downsizeable. The skill fetches `FreeableMemory` / `DatabaseConnections` hourly, not CPU alone.
- **Residual vs recurring (Principle 4):** an RDS extended-support line for an instance deleted on 2026-04-16 is residual / self-clearing, excluded from savings.
- **Cost view:** every CE figure uses the three usage record types at `AmortizedCost`. No commitment applies to EBS, snapshots, RDS or untagged lines, so those numbers equal their unblended charge; only the covered m5 EC2 usage differs.
- **Dollar threshold:** every remaining row is above $5/mo; nothing is dropped.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `scoping-probe.json` | Query 1-4: identity, alias, `describe-organization` (member), CE by `REGION` |
| `compute-optimizer.json` | CO EC2 (3, two regions), EBS (1) and RDS (Aurora, `Optimized`) recommendations |
| `unattached-volumes.json` | `describe-volumes --filters status=available`, both regions (12 gp3 volumes, with tags) |
| `detach-events.json` | CloudTrail `lookup-events` per volume (DetachVolume times, 90-day history) |
| `ebs-cost-by-usage-type.json` | CE EBS gp3 + snapshot usage types by region; the bill-derived rate source |
| `snapshots-older-than-30d.json` | `describe-snapshots --owner-ids self`, 47 snapshots older than 30 days, both regions (replaces the old `orphaned-snapshots.json`, whose name asserted the conclusion) |
| `snapshot-checks.json` | Live volume ids, AMI snapshot references: inputs for the three orphan checks |
| `snapshot-cost-by-resource.json` | CE `get-cost-and-usage-with-resources`, 7 days, per snapshot ARN (bill-derived cost) |
| `commitment-coverage.json` | Savings Plan description, RI list, SP and RI coverage, plus the amortized view of the covered m5 usage |
| `untagged-spend.json` | CE spend with no `Service` tag |
| `tag-activation.json` | `ce list-cost-allocation-tags` for `Service` (status and `LastUpdatedDate`), part of Query 17 |
| `utilization-metrics.json` | 30d hourly CPU for the 3 CO instances (summary envelope over 720 datapoints) + existence checks |
| `db-binding-metrics.json` | Aurora writer CPU + FreeableMemory + DatabaseConnections (hourly summary envelope) |
| `residual-charge.json` | CE extended-support line for a deleted instance + `describe-db-instances` |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step, including the expected report |

## Savings summary (expected output)

| Finding | Source | Rate | Confidence | Est. savings |
|---------|--------|------|------------|-------------|
| Snapshot, then delete 5 unattached EBS volumes, us-east-1 (detached >= 60d) | line-item-computation | bill-derived | high | $80.00/mo |
| Snapshot, then delete 4 unattached EBS volumes, eu-west-1 (detached >= 60d) | line-item-computation | bill-derived | high | $35.20/mo |
| Rightsize EC2 `i-0bbbb` c5.2xlarge to c5.xlarge | compute-optimizer | list-price | medium | $124.00/mo |
| Rightsize EC2 `i-0cccc` m5.xlarge to m5.large (eu-west-1) | compute-optimizer | list-price | medium | $78.00/mo |
| Hold-tag, then delete 12 orphan-candidate snapshots, us-east-1 | line-item-computation | bill-derived | medium | $31.50/mo |
| Hold-tag, then delete 5 orphan-candidate snapshots, eu-west-1 | line-item-computation | bill-derived | medium | $13.50/mo |
| Rightsize EC2 `i-0aaaa` m5.4xlarge to m5.2xlarge | compute-optimizer | list-price | medium | $280.00/mo, **covered until 2027-02-14 (owner decision), excluded from totals** |
| Snapshot, then delete 1,000 GB volume detached 3 days ago (CO resize noted as alternative) | line-item-computation | bill-derived | low | $80.00/mo |
| Confirm owner of Kubernetes PV volume, 500 GB | line-item-computation | bill-derived | low | $40.00/mo |
| Snapshot, then delete 400 GB volume, detach date unverified | line-item-computation | bill-derived | low | $32.00/mo |

**Total estimated savings, per rate basis (no blended figure):** `bill-derived` $115.20/mo high + $45.00/mo medium + $152.00/mo low; `list-price` $202.00/mo medium. The covered row ($280.00/mo at list price) is excluded.

Informational / excluded (no savings claimed, NOT in the remediation table):

| Item | Source of the figure | Amount | Reason |
|------|----------------------|--------|--------|
| Untagged spend (EC2 $5,200.00, EBS $1,800.00, S3 $1,000.00) | line-item-computation | $8,000.00/mo | visibility, not waste; owner unknown |
| RDS extended-support charge, deleted instance `db-legacy-pg13` | line-item-computation (bill-derived $0.10/instance-hour) | $37.20 (April, one-off) | residual / self-clearing |
| Aurora writer `acme-prod-aurora-writer` | compute-optimizer (`Optimized`) | n/a | memory- and connection-bound, not downsizeable |
| 30 backup snapshots (AWS Backup 14, DLM 8, AMI-backed 4, live source volume 4) | line-item-computation (bill-derived) | $175.50/mo billed | backups, retention review; not orphaned |

Why the headline is small: the previous version of this fixture claimed ~$740/mo high-confidence from 11 volumes and 47 "orphaned" snapshots at `VolumeSize x list price`. With bill-derived rates, a real detach window, and the three snapshot checks, the same account yields $115.20/mo high-confidence.
