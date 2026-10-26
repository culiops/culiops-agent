---
cloud: aws
action: delete
resource_type: ebs-snapshot
applies_when: action == "delete" AND resource matches "snap-*"
---

# Verify: Delete orphaned EBS snapshot

## Required IAM
- `ec2:DescribeSnapshots`
- `ec2:DescribeSnapshotAttribute`
- `ec2:DescribeVolumes`
- `ec2:DescribeImages`
- `rbin:ListRules`, `rbin:GetRule` (Recycle Bin retention rules)
- `cloudtrail:LookupEvents` (optional, snapshot-use history)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). `cloudformation` → ❔ `unsupported-owner`. `unmanaged` → no IaC to re-apply (irrelevant to a delete's rollback, but record it). **Backup-policy owner check (below, Query 1)** is part of the ownership probe for snapshots.
1. `aws ec2 describe-snapshots --snapshot-ids <snap-id>` — captures `State`, `VolumeId`, `VolumeSize`, `StartTime`, `StorageTier` (`standard` / `archive`), `Description`, `Tags`.
   - **AWS Backup / DLM managed → ❔ `owned-by-backup-policy` and stop.** Signals: tag `aws:backup:source-resource` (AWS Backup), tag `dlm:managed=true` or a DLM `Description` ("Created for policy: …"), or a Description stating it was created by AWS Backup. The remedy is changing the backup plan / lifecycle policy (retention) or, for AWS Backup, deleting the *recovery point* in its vault — a direct `delete-snapshot` fights the policy (backup tooling errors or re-creates it) and needs the policy owner's approval.
2. `aws ec2 describe-volumes --volume-ids <volume-id>` — whether the source volume still exists (orphan check). `InvalidVolume.NotFound` = orphaned.
3. `aws ec2 describe-images --owners self --filters Name=block-device-mapping.snapshot-id,Values=<snap-id>` — AMIs whose `BlockDeviceMappings` reference this snapshot. (A snapshot behind a *deregistered* AMI is the classic true orphan.)
4. `aws ec2 describe-snapshot-attribute --snapshot-id <snap-id> --attribute createVolumePermission` — is it shared with other accounts or public (`Group=all`)?
5. **Recycle Bin:** `aws rbin list-rules --resource-type EBS_SNAPSHOT`, then `aws rbin get-rule --identifier <id>` for each: `RetentionPeriod`, `ResourceTags`, `ExcludeResourceTags`, `LockConfiguration`. A rule with no `ResourceTags` is region-level (covers all snapshots unless excluded); a tag-level rule applies only if the snapshot carries a matching tag. No matching rule → not covered.
6. (Optional, opt-in at GATE 2) `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<snap-id> --start-time <now-90d>` — management events only, last 90 days; look for `CreateVolume`, `CopySnapshot`, `CreateImage`, `RunInstances`. **Activity signal** (the snapshot being used as a source). Anything older than 90d is ⚪.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Snapshot age (`StartTime`; creation is the latest activity event) | required | ≥ 60d (Principle 3 delete window floor) | < 30d — recently created, may still be a routine backup |
| Use of the snapshot as a source in the last 90d (Query 6) | optional | none | `CreateVolume` / `CopySnapshot` / `CreateImage` / `RunInstances` in the last 30d |

Values between the thresholds (age 30–60d) → row not 🟢 (a delete needs Evidence 🟢 to land anywhere but 🔴 / 🔵). `State` must be `completed`: `pending` → defer and re-check; `error` → the snapshot is unusable (no value in keeping it), proceed.

## Attachment (Dimension 2 / 4 input)

These are references, never activity (Principle 1). None produces 🚫.

| Signal | Query | Effect |
|--------|-------|--------|
| An AMI references this snapshot | 3 | ≥ 1 → Blast 🔴 (the AMI becomes unlaunchable; deregister the AMI first, then the snapshot — an ordering hint, separate item) |
| Shared with other accounts or public | 4 | any → Blast 🔴 |
| Source volume still exists | 2 | this snapshot is a backup of a live volume → Blast 🔴 unless a newer snapshot of the same volume exists (then 🟡). It is not an orphan; confirm the intent |
| IaC / catalog references to the snapshot ID (Dim 4 grep: launch templates, `aws_ebs_volume.snapshot_id`) | `code:` | per Dimension 4 thresholds |

## Reversibility classification
- **Default:** 🔴 irreversible. Snapshot deletion is permanent.
- **Recycle Bin covers it → 🟡:** a matching rule (Query 5) retains the deleted snapshot for the rule's `RetentionPeriod`; recoverable via `aws ec2 list-snapshots-in-recycle-bin` / `restore-snapshot-from-recycle-bin` within that period. Retained snapshots are still billed; a `LockConfiguration` means the rule itself cannot be removed early.

## Blast radius classification
- **Default:** 🟢 — single snapshot. Widens per the Attachment table (AMI reference, sharing, live source volume).

## Rollback note (informational, shown in plan)
"Snapshot deletion is permanent unless a Recycle Bin rule covers it (then restorable until the retention period ends). Before deleting, confirm no AMI references this snapshot (`ec2:DescribeImages`) and it is not shared.

**Cost-accuracy (Principle 4):** snapshots are incremental, so deleting one frees only the blocks no other snapshot in the chain references — the saving is usually far below `VolumeSize`. Derive it from the bill (usage by snapshot tag/ID) or by estimating unique blocks, not from the volume size.

**Principle 2 fallback (cheaper, reversible):** move it to the **archive tier** (`aws ec2 modify-snapshot-tier --snapshot-id <snap-id> --storage-tier archive`). Restore takes hours to days (verify current documentation), and a minimum archive period (90 days; verify) applies, so early removal still bills the remainder. Archive stores a **full** copy, not incremental — for a snapshot in a long incremental chain it can cost *more* than standard, so run the Principle 2 cost-direction check (bill-derived or Pricing API rates, at real snapshot size) before proposing it."
