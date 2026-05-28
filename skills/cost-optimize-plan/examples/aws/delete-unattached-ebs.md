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
- `cloudtrail:LookupEvents` (optional, for last-attach-time history beyond `Attachments[]`)

## Queries

1. `aws ec2 describe-volumes --volume-ids <vol-id>` — confirms `State=available` (unattached).
2. `aws ec2 describe-snapshots --filters Name=volume-id,Values=<vol-id>` — confirms snapshots exist (rollback path).
3. (Optional, opt-in at GATE 2) `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<vol-id> --start-time <now-90d>` — confirms volume has not been re-attached in last 90d.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| `Volumes[0].State` | `available` | `in-use` or `creating` |
| `Volumes[0].Attachments` | `[]` (empty) | non-empty |
| Most recent `AttachVolume` event in CloudTrail (if opted in) | none within 90d | any within 90d |
| Snapshot exists for rollback | ≥ 1 snapshot newer than 30d | none — bump tier 🔴 (no rollback) |

## Reversibility classification
- **Default:** 🔴 irreversible. Volume deletion is permanent; only the snapshot survives.
- **Mitigated:** if a snapshot < 30d old exists → 🟡 (rollback path: restore from snapshot, ~5–15 min RTO).

## Blast radius classification
- **Default:** 🟢 — single volume, no shared dependencies in the `State=available` precondition.

## Rollback note (informational, shown in plan)
"Take a final snapshot before deletion if not already present. Restore time from snapshot is ~5–15 min depending on volume size. If no snapshot exists, deletion is irreversible."
