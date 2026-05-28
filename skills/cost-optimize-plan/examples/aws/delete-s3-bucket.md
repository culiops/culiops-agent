---
cloud: aws
action: delete
resource_type: s3-bucket
applies_when: action == "delete" AND resource matches "arn:aws:s3:::*"
---

# Verify: Delete S3 bucket

## Required IAM
- s3:GetBucketLocation
- s3:GetBucketPolicy
- s3:GetBucketLogging
- s3:GetBucketReplication
- s3:GetBucketVersioning
- s3:ListBucket (with `--max-keys 1`)
- cloudtrail:LookupEvents
- iam:SimulatePrincipalPolicy
- route53:ListResourceRecordSets

## Queries

1. `aws s3api get-bucket-location --bucket <name>` — confirms account ownership and region.
2. `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<name> --start-time <now-90d> --max-results 100` — recent data events. Note: data events are only captured if a data event trail is configured. If none configured, query returns 0 events but absence-of-evidence ≠ evidence-of-absence; flag as ⚪ in evidence column.
3. `aws s3api list-objects-v2 --bucket <name> --max-keys 1 --query 'Contents[0].LastModified'` — emptiness check + most-recent modify time.
4. `aws s3api get-bucket-logging --bucket <name>` — confirms no other service uses it as a logging target.
5. `aws s3api get-bucket-replication --bucket <name>` — confirms not source/destination of replication.
6. `aws s3api get-bucket-versioning --bucket <name>` — needed for reversibility classification.
7. `aws route53 list-resource-record-sets --hosted-zone-id <each-zone> | grep <name>.s3` — DNS reference sweep (operator may opt-out if 100+ zones to avoid throttling).
8. (Optional, opt-in at GATE 2) IAM principal sweep — for each principal in account, `iam:SimulatePrincipalPolicy` against `s3:GetObject`/`s3:PutObject` on bucket.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger | ⚪ Unknown |
|--------|--------------|-------------|------------|
| CloudTrail data events (GetObject/PutObject/DeleteObject) in last 90d | 0 events AND data-event trail configured | ≥ 1 event | data-event trail not configured |
| Bucket policy referencing external principals | none | any | bucket policy denied |
| DNS records pointing at bucket endpoint | 0 | ≥ 1 | route53 access denied |
| Replication source/destination | none | any | n/a |
| Object count | 0 (or `last-modified` > 365d if non-empty) | < 365d last-modified | bucket access denied |

## Reversibility classification
- **Default:** 🔴 irreversible (objects gone is gone).
- **Mitigated:** if versioning enabled AND MFA-delete NOT enabled AND operator confirms version history → 🟡 (~30d undelete window via S3 version history).

## Blast radius classification
- **Default:** 🟡 — S3 bucket names are GLOBAL namespace; after deletion, the name is released and another AWS customer can claim it. Brand/phishing risk if name was public-facing.

## Rollback note (informational, shown in plan)
"S3 deletion is irreversible. If versioning was enabled and MFA-delete was not, individual object versions within the retention window may be recoverable for up to 30 days. After bucket deletion, the bucket name returns to the global pool — if the name was public-facing (e.g., referenced in a static site or whitelisted by partners), strongly consider keeping the bucket empty rather than deleting."
