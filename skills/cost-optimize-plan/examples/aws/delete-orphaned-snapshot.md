---
cloud: aws
action: delete
resource_type: ebs-snapshot
applies_when: action == "delete" AND resource matches "snap-*"
---

# Verify: Delete orphaned EBS snapshot

## Required IAM
- `ec2:DescribeSnapshots`
- `ec2:DescribeVolumes`
- `ec2:DescribeImages`

## Queries

1. `aws ec2 describe-snapshots --snapshot-ids <snap-id>` — confirms snapshot state and source `VolumeId`.
2. `aws ec2 describe-volumes --volume-ids <volume-id>` — confirms whether the source volume still exists (orphan check).
3. `aws ec2 describe-images --filters Name=block-device-mapping.snapshot-id,Values=<snap-id>` — checks whether any AMI references this snapshot in its `BlockDeviceMappings`.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| `Snapshots[0].State` | `completed` | `pending` or `error` |
| Source `VolumeId` still exists | volume absent from `describe-volumes` output (orphaned) | volume still exists and `State` is not `deleted` |
| Snapshot age | > 30d | ≤ 30d (may still be a routine backup) |
| Referenced as `BlockDeviceMappings[].Ebs.SnapshotId` in `describe-images` | none | any — snapshot is a build artifact |

## Reversibility classification
- **Default:** 🔴 irreversible. Snapshot deletion is permanent; no super-snapshot exists.

## Blast radius classification
- **Default:** 🟢 — single snapshot. Blast radius widens to 🔴 if an AMI references this snapshot (caught by the `describe-images` query above).

## Rollback note (informational, shown in plan)
"Snapshot deletion is permanent — no super-snapshot exists. The source volume (if not already deleted) is the only path back. Before deleting, confirm no AMI references this snapshot in `BlockDeviceMappings` via `ec2:DescribeImages`."
