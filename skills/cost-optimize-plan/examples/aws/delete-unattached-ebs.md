---
cloud: aws
action: delete
resource_type: ebs-volume
applies_when: action == "delete" AND resource matches "vol-*"
---

# Verify: Delete unattached EBS volume

## Required IAM
- `ec2:DescribeVolumes`
- `ec2:DescribeSnapshots`
- `cloudtrail:LookupEvents` (free; management events, last 90 days)
- `rbin:ListRules` (Recycle Bin rules for the rollback snapshot)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). `cloudformation` → ❔ `unsupported-owner`. `unmanaged` → no IaC resource to remove (record it). **Ownership `k8s` → ❔ `owned-by-k8s` and stop** (see Query 1): the volume is a PersistentVolume's backing store.
1. `aws ec2 describe-volumes --volume-ids <vol-id>` — `State`, `Attachments`, `CreateTime`, `Size`, `VolumeType`, `Encrypted`/`KmsKeyId`, `SnapshotId`, `Tags`.
   - **Precondition:** `State=available` and `Attachments=[]`. `in-use` or `creating` → item is stale, drop it.
   - **Kubernetes-owned signals (tags):** `kubernetes.io/created-for/pvc/name`, `kubernetes.io/created-for/pv/name`, `ebs.csi.aws.com/cluster` (also in-tree `kubernetes.io/cluster/<name>`). A StatefulSet scaled to 0 (or a pod gone while the PVC remains) leaves its PV's volume `available` — that is **not** an orphan. Deleting it directly breaks the PV and loses the data; the PVC would reattach to nothing. Resolve it through the PVC / PV and the StorageClass `reclaimPolicy` (`Delete` vs `Retain`) — a Kubernetes change, not an EC2 one. A `Released` PV with `Retain` policy is the legitimate orphan case, and only after the owner confirms.
2. `aws ec2 describe-snapshots --filters Name=volume-id,Values=<vol-id> --query 'Snapshots[].[SnapshotId,StartTime,State,Tags,Description]'` — candidate rollback snapshots (see validity rule below).
3. **Attach / detach history (free, 90d max):** `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<vol-id> --start-time <now-90d> --query "Events[?EventName=='AttachVolume'||EventName=='DetachVolume'].[EventTime,EventName]"`. If `ResourceName` does not return these events (verify — depends on the event populating `resources`), fall back to `AttributeKey=EventName,AttributeValue=DetachVolume` and filter client-side: `--query "Events[?contains(CloudTrailEvent, '<vol-id>')]"`. The result gives the **last detach time**.
4. `aws rbin list-rules --resource-type EBS_SNAPSHOT` — whether a Recycle Bin retention rule would cover the rollback snapshot (Reversibility only; see below). `aws rbin get-rule --identifier <id>` for `RetentionPeriod` / `ResourceTags`.

> **Window (Principle 3):** a delete needs 60–180d. CloudTrail covers 90d, so the usable evidence is: no `AttachVolume` / `DetachVolume` in the 90d window ⇒ the volume has been unattached for ≥ 90d (or since `CreateTime` if the volume is younger than 90d). An event in the window gives the exact last-detach time.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Time unattached = now − (last `DetachVolume`, else `CreateTime` if never attached; Query 3) | required | ≥ 60d | `AttachVolume` or `DetachVolume` within the last 30d — recently in use |
| `AttachVolume` events within the 90d window (Query 3) | required | none, or only older than 60d | any within the last 30d (recurring attach/detach, e.g. a periodic restore or batch job, also 🚫) |

A volume whose last detach is more than 90d ago cannot be dated precisely by this playbook; treat "no events in 90d" as ≥ 90d. A volume with a `CreateTime` older than 90d and a query that failed → ⚪ → Evidence 🔴.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Kubernetes PV / PVC tags | 1 | present → ❔ `owned-by-k8s` (not scoreable here) |
| IaC / catalog references to the volume ID (Dim 4 grep, e.g. `aws_volume_attachment`, PV `volumeHandle`) | `code:` | per Dimension 4 thresholds |
| Volume used as a `SnapshotId` source or referenced by launch templates | `code:` | ≥ 1 → Dependency 🟡 |

## Reversibility classification
- **Default:** 🔴 irreversible. Volume deletion is permanent; only a snapshot survives.
- **Mitigated → 🟡: a *valid rollback snapshot* exists.** Valid means: `State=completed`, AND `StartTime` is **after the volume's last detach** (the last `DetachVolume` event, or the volume's `CreateTime` if it was never attached), because only then does the snapshot contain everything the volume held. A snapshot older than the last detach misses the writes made before detaching, regardless of how recent it is — "newer than 30d" is not the test. If the snapshot is older than the 90d CloudTrail window, the last detach cannot be dated → not provably valid → stay 🔴 (or take a fresh final snapshot as step 1).
- **Snapshot durability:** a rollback snapshot managed by DLM or AWS Backup (tags `dlm:managed`, `aws:backup:source-resource`) can expire per policy, and a manual one can be deleted — note its retention. A Recycle Bin rule (Query 4) covering EBS snapshots keeps a *deleted* snapshot recoverable for the rule's retention period; it does not make the volume's deletion recoverable (Recycle Bin does not cover volumes). Prefer a dedicated, tagged final snapshot taken at GATE time.

## Blast radius classification
- **Default:** 🟢 — single volume, no shared dependencies in the `State=available` precondition (K8s-owned volumes are excluded at step 0).

## Rollback note (informational, shown in plan)
"Take a final snapshot before deletion if no valid rollback snapshot (taken after the last detach) exists, and wait for it to reach `completed`. Restoring from a snapshot creates a new volume (new ID) that is usable within minutes, but blocks load lazily from S3 — expect first-read latency unless the volume is initialized or Fast Snapshot Restore is enabled. Anything that referenced the old volume ID must be repointed. If no valid snapshot exists, deletion is irreversible. If Ownership is `unmanaged`, there is no IaC resource to re-apply; restore is manual."
