**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-data-waste-20260602-1020.md
**Mode of upstream:** waste
**Scope:** 111122223333 / acme-data (single)
**Target:** account 111122223333 (sts verified, live:0a), region(s) ap-southeast-1
**IaC repo(s):** ~/acme-infra (simulated for this fixture; code refs illustrative)
**Catalog used:** none
**Date:** 2026-06-02 10:26
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-data-waste-20260602-1020.md` (waste mode, single-cloud aws, fresh).
- 2 items above $5/mo floor; 0 filtered below floor.
- Target: account `111122223333`, region `ap-southeast-1`. Catalog: none. IaC repo supplied: `~/acme-infra`.
- **Ownership gate:** the batch lists each item's playbook queries as conditional on the ownership probe (Query 0b). When the probe routes an item to ❔ (`k8s` / `asg` / `eks-nodegroup` / `karpenter`, Constraint 13), its remaining queries are skipped at execution and listed in this plan.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

Both items were routed to ❔ after the ownership probe; only Query 0 ran. Executed 2026-06-02 10:22-10:23 UTC.

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 111122223333 = `Scope`; region ap-southeast-1 (2026-06-02T10:22Z) |
| 0b-1 | Delete vol-0dddd1 | ec2:DescribeVolumes (tags) + IaC grep | ec2:Describe* | ok | `State=available`, `Attachments=[]`; tags `kubernetes.io/created-for/pvc/name=data-kafka-2`, `kubernetes.io/created-for/pvc/namespace=streaming`, `ebs.csi.aws.com/cluster=true`; no IaC resource for the volume ID → owner **k8s** → ❔ `owned-by-k8s` |
| 0b-2 | Rightsize i-0eeee1 | ec2:DescribeInstances (tags) + IaC grep | ec2:Describe* | ok | tag `aws:autoscaling:groupName=web-asg` (launch template `lt-0123456789abcdef0` v7); no IaC resource for the instance ID; ASG declared at `asg.tf:12` → owner **asg** → ❔ `owned-by-asg` |

**Skipped at execution (conditional on Query 0b; never run, never billed):**
- Item #1 (`delete-unattached-ebs.md`): `ec2:DescribeSnapshots`, `cloudtrail:LookupEvents` (attach/detach history), `rbin:ListRules`.
- Item #2 (`rightsize-ec2.md`): `ec2:DescribeInstanceTypes`, `cloudwatch:GetMetricData` (CPU / network), CloudWatch-agent memory discovery + `GetMetricData`, `compute-optimizer:GetEC2InstanceRecommendations`, `elbv2:DescribeTargetGroups` / `DescribeTargetHealth`, `cloudwatch:DescribeAlarms`, `ce:GetSavingsPlansCoverage` / `GetReservationCoverage`.

Skipping approved queries is a trim of the batch, not an extension (Law 2). The reason: scoring Reversibility, Blast, Evidence or `Realizable` for the raw resource would answer the wrong question, because the remediation target is the owner, not the resource.

**Total estimated API cost:** $0 (two free describe calls and a free `sts` call); the Cost Explorer requests of the rightsize playbook were not issued.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 2 | $130/mo (not assessed) |

**Total plan savings:** $0/mo actionable - 0 actionable items, 2 routed to their owners (❔).

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

No items in this tier.

## ❔ Manual review required

| # | Action | Resource | Savings | Source | Confidence | Reason |
|---|--------|----------|---------|--------|------------|--------|
| 1 | Delete unattached EBS volume | vol-0dddd1 | $40/mo | line-item-computation | high | **`owned-by-k8s`** - the volume is the backing store of PersistentVolume `pvc-7c1e5a62-…` for PVC `streaming/data-kafka-2` (EBS CSI driver tags, live:0b-1). `available` is the expected state when its StatefulSet is scaled to 0 (the chart in `~/acme-infra` shows `replicaCount: 0` at `charts/kafka/values.yaml:21`, illustrative), so it is **not an orphan**. Deleting the volume directly would break the PV and lose the Kafka partition data. The change belongs to the owner: the PVC / PV and the StorageClass `reclaimPolicy` (`Retain`, `charts/kafka/storageclass.yaml:8`). Only a PV in `Released` state under `Retain`, confirmed by the Kafka owners, is a legitimate orphan. |
| 2 | Rightsize web instance m5.2xlarge → m5.xlarge | i-0eeee1 | $90/mo | compute-optimizer | medium | **`owned-by-asg`** - member of Auto Scaling group `web-asg` (live:0b-2). A resize of one instance is reverted at the next scale event or instance refresh. The change belongs in the launch template of `web-asg` (`launch_template.tf:5`, `instance_type` at line 9; ASG at `asg.tf:12`), rolled out by an instance refresh. Fit of the smaller class (CPU p95, memory, network, alarms) was **not** verified here, because the target is the launch template, not this instance. |

## Drift

None - no item reached a code-versus-live comparison.

## Gaps

- Item #1: live cluster state (PVC / PV status, StatefulSet replicas, who last scaled it) is outside this skill (AWS read-only) and was not queried; the `charts/` refs are from the IaC repo, not the live cluster.
- Item #2: no rightsize evidence exists for the new class. There is no launch-template rightsize playbook yet; gather CPU / memory / network evidence across the ASG's members before changing `instance_type`.
- Upstream savings ($40, $90) copied verbatim and not assessed.

## Next steps (informational)

- **Item #1:** ask the Kafka owners whether the `kafka` StatefulSet is retired or paused. If retired, remove the PVC / PV through the cluster's own workflow (the StorageClass `reclaimPolicy` then decides whether the volume is deleted or released); only a `Released` + `Retain` volume is then a candidate for a raw delete, and that is a new triage. If paused, keep it: the cost is the price of the paused workload.
- **Item #2:** change the launch template in IaC (`launch_template.tf`) and roll it with an instance refresh, via `iac-change-execution` + `pre-flight`, after gathering evidence for the target class across all ASG members.
- Manual review items are changed through their owner; `owned-by-<owner>` items do not get a tier badge.
