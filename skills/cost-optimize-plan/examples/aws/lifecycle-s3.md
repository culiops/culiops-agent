---
cloud: aws
action: lifecycle-policy
resource_type: s3-bucket
applies_when: action == "lifecycle-policy" AND resource matches "arn:aws:s3:::*"
---

# Verify: Add lifecycle policy to S3 bucket

## Required IAM
- s3:GetLifecycleConfiguration
- s3:GetBucketVersioning
- s3:GetBucketLocation
- s3:GetBucketTagging
- s3:GetIntelligentTieringConfiguration
- s3:GetAnalyticsConfiguration
- s3:GetMetricsConfiguration
- s3:ListBucket (inventory / sampling, optional)
- cloudwatch:GetMetricData

## Queries

0. **Target check + ownership probe** (`examples/aws.md`). Bucket tags: `aws s3api get-bucket-tagging --bucket <name>` (`NoSuchTagSet` = none). In Terraform the rule may be inline (`lifecycle_rule` on the bucket) or a standalone lifecycle-configuration resource — cite whichever exists as `code:<path:line>`; both at once is drift.
1. `aws s3api get-bucket-lifecycle-configuration --bucket <name>` (`NoSuchLifecycleConfiguration` = none). Record each existing rule (ID, filter, actions, status). **`PutBucketLifecycleConfiguration` replaces the whole configuration** — the change must extend the existing rule set, never replace it, or it silently deletes the other rules.
2. `aws s3api get-bucket-versioning --bucket <name>` — versioned buckets: current-version rules (`Transition`, `Expiration`) do not touch noncurrent versions (`NoncurrentVersionTransition` / `NoncurrentVersionExpiration`). If the bytes the report counts sit in noncurrent versions (S3 Storage Lens or an Inventory report with `IsLatest` shows the split), a current-version rule saves less than claimed → flag in `Realizable`.
3. `aws s3api list-bucket-intelligent-tiering-configurations --bucket <name>` and the Intelligent-Tiering storage classes in Query 4 — overlap check. Objects already in Intelligent-Tiering are not Standard, so a Standard→X saving computed on total bytes is overstated. Flag it; do not score 🚫.
4. `aws cloudwatch get-metric-data` — `AWS/S3` `BucketSizeBytes` per `StorageType` (`StandardStorage`, plus any `IntelligentTiering*Storage`, `StandardIAStorage`, `GlacierStorage`, …) and `NumberOfObjects` (`StorageType=AllStorageTypes`), dimension `BucketName`; **daily** metrics (period 86400, the exception to hourly). Confirms the size in the source class and gives average object size = bytes ÷ objects.
5. **Access-pattern evidence — do objects older than the transition age still get read?** First available source, same mechanics as `delete-s3-bucket.md` Query 3:
   - **5a. S3 Storage Class Analysis** — `aws s3api list-bucket-analytics-configurations --bucket <name>` / `get-bucket-analytics-configuration --bucket <name> --id <id>`. The API returns the *configuration*; results are the daily CSV export to the configured `DataExport` destination, read with `get-object`. A newly created configuration has no history and needs its own observation period before it says anything (verify the minimum in S3 docs).
   - **5b. Request metrics / server access logs** (`list-bucket-metrics-configurations`, `get-bucket-logging`). Request metrics scoped to the rule's prefix/tag filter give `GetRequests` but not object age: any `GetRequests` there is ⚪ unless access logs let you match the read keys to objects older than the transition age. Access logs give keys, so reads of old objects can be counted directly. Window ≥ 30d for transitions; 60–180d for any `Expiration` (delete-class, Principle 3).
   - **None available** → access-pattern signal ⚪ `activity-unobservable`.
   - `cloudtrail lookup-events` is not a source (management events only).
6. **Cost direction (Principle 2).** Per rule, from the Query 4 size and object count, plus object-size distribution (S3 Inventory if `aws s3api list-bucket-inventory-configurations --bucket <name>` shows one; otherwise a labelled **sample** — `list-objects-v2` is key-ordered, so it is biased, not a distribution):
   `net = eligible_bytes × (source_rate − target_rate) × months  −  eligible_objects × transition_request_rate  −  archive-class per-object metadata overhead  −  early-deletion exposure (bytes below the target class's minimum storage duration × target_rate × remaining days)  −  expected retrieval fees`
   Rates: bill-derived (Principle 4) or Pricing API for the region — never list-price memory. Small objects are the trap: per-object transition request fees and per-object metadata overhead (billed in both Standard and the archive class) dominate, and IA / Glacier Instant Retrieval bill a minimum object size. S3 by default does not transition objects < 128 KB unless the rule overrides it. Show the interim cost and payback time (Principle 2: model the transition).

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Reads of objects older than the transition age (Query 5) — target Glacier Flexible Retrieval / Deep Archive | required | 0 | ≥ 1 — those reads fail with `InvalidObjectState` until the object is restored |
| Reads of objects older than the transition age — target Standard-IA / One Zone-IA / Glacier Instant Retrieval / Intelligent-Tiering | optional | 0 | (no restore needed; retrieval fees are priced in the cost-direction row) |
| Reads of objects older than the expiration age (rules with `Expiration` / `NoncurrentVersionExpiration`) | required | 0 over 60–180d | ≥ 1 — the application still reads data the rule would delete |
| Cost direction (Query 6), net saving per rule | required | net > 0 after transition fees, overhead, minimum-duration and retrieval costs | net ≤ 0 — that rule raises cost (Principle 2) |
| Source-class size vs the report's "bytes to transition" (Query 4) | required | within ±20% | — (> 50% mismatch → ⚪ `stale-upstream`: report is stale; 20–50% → recompute savings from observed size) |

A ⚪ on a `required` row forces Evidence ⚪ (→ 🔴). A rule containing only `AbortIncompleteMultipartUpload` needs none of the read evidence (no read can depend on an incomplete upload).

## Attachment / configuration (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Existing lifecycle rules overlap the same scope | 1 | any → Dependency 🟡 (merge into the existing rule set, do not replace) |
| Existing rule already transitions to the same or a colder class | 1 | any → savings overlap; reduce `Realizable` |
| Intelligent-Tiering configured / objects already in IT classes | 3, 4 | any → savings overstated; flag in `Realizable`, Evidence unchanged |
| Versioned bucket, savings sit in noncurrent versions | 2 | current-version-only rule → flag in `Realizable` |
| IaC references to the bucket (`code:`) | 0 | 1–2 → Dependency 🟡; ≥ 3 → Dependency 🔴 |

## Reversibility classification
- **`AbortIncompleteMultipartUpload`-only rule:** 🟢 — config-only, no effect on stored objects.
- **`Transition` / `NoncurrentVersionTransition` to an instantly readable class** (Standard-IA, One Zone-IA, Glacier Instant Retrieval, Intelligent-Tiering): 🟢 — no data loss and reads keep working; removing the rule stops further transitions. Objects already moved stay in the colder class (moving them back is an optional copy, with retrieval / early-deletion fees). One Zone-IA lowers durability: also Blast 🟡.
- **`Transition` to Glacier Flexible Retrieval / Deep Archive:** 🟡 — reads fail until each object is restored. Reverting means restore + copy to a hotter class, paying retrieval and early-deletion fees.
- **Any `Expiration` / `NoncurrentVersionExpiration`:** 🔴 — deletes data.
- A rule with several actions takes the worst row. Owner `unmanaged` removes the "re-apply old IaC" basis; the abort-only 🟢 stands because it has no data effect.

## Blast radius classification
- **Default:** 🟢 — single bucket, single configuration object — **provided** the change extends the existing rule set (Query 1). A replace-style apply that drops existing rules is out of this playbook's scope: raise Blast to 🔴 and say so.

## Rollback note (informational, shown in plan)
"Removing the lifecycle rule stops further transitions or expirations but does not undo them: objects already moved to a colder class stay there until restored and copied back (Glacier Flexible Retrieval / Deep Archive objects must be restored first; retrieval and early-deletion fees apply), and expired objects are gone unless a noncurrent version or backup exists. To roll back safely, remove the rule via IaC before the first transition date and verify no application reads objects of that age."
