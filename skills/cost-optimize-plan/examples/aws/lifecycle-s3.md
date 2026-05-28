---
cloud: aws
action: lifecycle-policy
resource_type: s3-bucket
applies_when: action == "lifecycle-policy" AND resource matches "arn:aws:s3:::*"
---

# Verify: Add lifecycle policy to S3 bucket

## Required IAM
- s3:GetBucketLifecycleConfiguration
- s3:GetBucketIntelligentTieringConfiguration
- s3:GetBucketLocation
- cloudwatch:GetMetricStatistics

## Queries

1. `aws s3api get-bucket-lifecycle-configuration --bucket <name>` — does a lifecycle policy already exist? If yes, recommendation is to extend, not replace.
2. `aws s3api list-bucket-intelligent-tiering-configurations --bucket <name>` — if Intelligent-Tiering is configured, lifecycle policy may double-bill — flag as 🚫.
3. `aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name BucketSizeBytes --dimensions Name=BucketName,Value=<name> Name=StorageType,Value=StandardStorage --start-time <now-90d> --end-time <now> --statistics Average --period 86400` — confirms savings projection: the recommendation says X TB will transition; CloudWatch confirms current size.
4. (Optional) `aws s3api list-objects-v2 --bucket <name> --max-keys 1000 --query 'Contents[?LastModified < `<now-90d>`]'` then count results — confirms a meaningful portion of objects will actually meet the transition criterion.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|-------------|
| Existing lifecycle policy | none, or non-conflicting | conflicting (e.g., already transitions to Glacier) |
| Intelligent-Tiering configured | not configured | configured (double-billing risk) |
| Current bucket size in StandardStorage | matches recommendation's "TB to transition" within ±20% | mismatch > 50% — recommendation is stale |

## Reversibility classification
- **Default:** 🟢 reversible — remove the lifecycle rule via IaC. Objects already transitioned to Glacier are still recoverable via restore (cost: $0.03/GB + retrieval time).

## Blast radius classification
- **Default:** 🟢 — single bucket, single configuration object.

## Rollback note (informational, shown in plan)
"Remove the lifecycle rule via IaC. Objects already transitioned to a colder tier remain accessible via restore (Glacier restore: $0.03/GB, expedited = minutes, standard = 3-5h, bulk = 5-12h). Restore cost is one-time per object."
