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
- s3:GetReplicationConfiguration
- s3:GetBucketVersioning
- s3:GetBucketTagging
- s3:GetLifecycleConfiguration
- s3:GetMetricsConfiguration
- s3:ListBucket
- s3:GetObject (on the **log** bucket only, and only if activity source 2 is used)
- cloudwatch:GetMetricData
- cloudtrail:ListEventDataStores, cloudtrail:GetEventDataStore, cloudtrail:StartQuery, cloudtrail:GetQueryResults (activity source 3 only)
- cloudtrail:DescribeTrails, elasticloadbalancing:DescribeLoadBalancers, elasticloadbalancing:DescribeLoadBalancerAttributes, cloudfront:ListDistributions, cloudfront:GetDistributionConfig, ec2:DescribeFlowLogs, config:DescribeDeliveryChannels (log-target sweep)
- route53:ListHostedZones, route53:ListResourceRecordSets
- iam:SimulatePrincipalPolicy (optional)

## Queries

0. **Target check + ownership probe** (`examples/aws.md`). Bucket tags: `aws s3api get-bucket-tagging --bucket <name>` (`NoSuchTagSet` = no tags). Region from query 1; pass it to every regional call.
1. `aws s3api get-bucket-location --bucket <name>` — confirms the bucket exists in this account and gives its region (`null` = `us-east-1`). A failure here means every metric below is ⚪ (Metrics rule: empty ≠ zero).
2. `aws s3api get-bucket-versioning --bucket <name>` and `aws s3api get-bucket-lifecycle-configuration --bucket <name>` (`NoSuchLifecycleConfiguration` = none) — Reversibility inputs (versioning state, MFA delete, noncurrent-version expiry).
3. **Request activity — use the first source that is available and covers the window.** `cloudtrail lookup-events` is NOT a source: it returns management and Insights events only, never `GetObject` / `PutObject`, so it always reads zero for S3 object activity.
   - **3a. CloudWatch S3 request metrics** — `aws s3api list-bucket-metrics-configurations --bucket <name>`. If a configuration exists, read it with `aws cloudwatch get-metric-data` (namespace `AWS/S3`, metrics `GetRequests`, `PutRequests`, `DeleteRequests`, `HeadRequests`, `PostRequests`; dimensions `BucketName` + `FilterId` = the configuration's `Id`; hourly; window per Principle 3). `ListRequests` is informational only — this skill's own calls land there. Request metrics are **not retroactive**: history starts at the configuration's creation, and a shorter history than the window → `window-too-short` ⚪.
   - **3b. S3 server access logs** — only if THIS bucket has logging enabled: `aws s3api get-bucket-logging --bucket <name>` → `LoggingEnabled.TargetBucket` / `TargetPrefix`. Read the log objects for the window with read-only `aws s3api list-objects-v2 --bucket <log-bucket> --prefix <prefix><YYYY-MM-DD>` (keys are date-prefixed) and `aws s3api get-object`; filter on the bucket-name field if the prefix is shared. Count `REST.GET.OBJECT` / `REST.PUT.OBJECT` / `REST.DELETE.OBJECT` / `REST.HEAD.OBJECT` by day, excluding the verifying principal and AWS log-delivery / inventory requesters. Log delivery is best-effort (not guaranteed complete), history starts when logging was enabled, and the log bucket may sit in another account (⚪ if unreadable). **Itemize the LIST/GET request cost at GATE 2**; record counts and distribution only (Secrets rule).
   - **3c. CloudTrail Lake** — `aws cloudtrail list-event-data-stores` (in the bucket's region), then `aws cloudtrail get-event-data-store --event-data-store <arn>` and confirm its advanced event selectors capture S3 data events (`resources.type` = `AWS::S3::Object`) and that the store is old enough to cover the window. Only against such an **existing** store: `aws cloudtrail start-query --query-statement "SELECT eventName, COUNT(*) AS n, MIN(eventTime) AS first_seen, MAX(eventTime) AS last_seen FROM <event-data-store-id> WHERE eventTime > '<now-90d>' AND eventSource = 's3.amazonaws.com' AND element_at(requestParameters, 'bucketName') = '<name>' GROUP BY eventName"`, then `aws cloudtrail get-query-results --query-id <id>`. Verify the `requestParameters` accessor syntax against CloudTrail Lake SQL docs before first use; group by day to get the distribution. **Billed per GB scanned — itemize at GATE 2.**
   - **None available** → the required activity signal is ⚪ `activity-unobservable` → Evidence ⚪ → 🔴. Do not substitute LookupEvents or object listings.
4. `aws cloudwatch get-metric-data` — `AWS/S3` `NumberOfObjects` (`StorageType=AllStorageTypes`) and `BucketSizeBytes` (`StorageType=StandardStorage`, plus other classes in use), dimension `BucketName`; these are **daily** metrics (period 86400). Trend over the window. Net growth = writes happened. Flat is inconclusive: reads leave no trace here. **Do not use `list-objects-v2 --max-keys 1` for "newest object"** — it returns the lexicographically first key, not the most recent; no last-modified claim can be made from it. Emptiness only: `aws s3api list-objects-v2 --bucket <name> --max-keys 1 --query KeyCount` (and `list-object-versions --max-items 1` if versioned).
5. `aws s3api get-bucket-policy --bucket <name>` (`NoSuchBucketPolicy` = none) — record the principals (cross-account, service principals) as a summary.
6. `aws s3api get-bucket-replication --bucket <name>` (`ReplicationConfigurationNotFoundError` = none) — this bucket as replication **source**. As **destination**: needs each other bucket's replication config (`aws s3api list-buckets`, then `get-bucket-replication` per bucket, match the destination ARN) — optional, opt-in at GATE 2 (one call per bucket).
7. **Log-target sweep** — is this bucket the destination of another service's logs? Services write without reading, so activity metrics miss them.
   - `aws cloudtrail describe-trails --include-shadow-trails` — `S3BucketName == <name>` (org trails: run from the management account).
   - ALB/NLB (bucket's region): `aws elbv2 describe-load-balancers` then per LB `aws elbv2 describe-load-balancer-attributes --load-balancer-arn <arn>` — `access_logs.s3.bucket` (ALB also `connection_logs.s3.bucket`). CLB: `aws elb describe-load-balancer-attributes --load-balancer-name <n>` — `AccessLog.S3BucketName`.
   - CloudFront (`us-east-1`): `aws cloudfront list-distributions` then `aws cloudfront get-distribution-config --id <id>` — `Logging.Bucket` and S3 origins naming the bucket. Standard logging v2 destinations: `aws logs describe-delivery-destinations` (verify output field before relying on it).
   - `aws ec2 describe-flow-logs` — `LogDestination` ARN contains the bucket (per region where flow logs exist).
   - `aws configservice describe-delivery-channels` — `s3BucketName` (per region).
   - Other buckets' access-log targets: `get-bucket-logging` per bucket, match `TargetBucket` — optional, opt-in at GATE 2.
   - Not swept (record as Gap): S3 Inventory / Storage Lens / Athena result locations, Macie / Security Lake / GuardDuty exports.
8. **DNS reference sweep** — per hosted zone, list ALL records (paginate: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id>`, no server-side filter) and match client-side, case-insensitive, for `<name>.s3`, `<name>.s3-website`, and a record whose name equals the bucket name (website hosting requires it). Opt-out allowed for 100+ zones; then DNS is ⚪ (Gap).
9. (Optional, opt-in at GATE 2) IAM principal sweep — `iam:SimulatePrincipalPolicy` per principal against `s3:GetObject` / `s3:PutObject` on the bucket. Answers "who *could*", not "who does" — attachment only.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| GET / PUT / DELETE / HEAD requests (Query 3, hourly) over ≥ 60d, excluding the verifying principal and AWS log delivery | required | 0 requests AND source history covers the window | requests in the window, judged on temporal distribution (Principle 3: one old burst is not steady use; any recent or recurring access is) |
| Net object-count / size trend (Query 4) | optional | flat or falling | net growth (writes persisted) |

⚪: no activity source available (`activity-unobservable`), source history shorter than the window (`window-too-short`), log bucket unreadable, or Target check / Query 1 failed. ⚪ on the required signal forces Evidence ⚪ (→ 🔴).

## Attachment (Dimension 2 / 4 input)

Attachment never produces 🚫 (Principle 1).

| Signal | Query | Effect |
|--------|-------|--------|
| Bucket policy with external / cross-account principals | 5 | any → Blast 🔴 |
| Bucket policy with log-delivery service principals (`logging.s3`, `delivery.logs`, `cloudtrail`, ELB log-delivery) | 5 | any → Blast 🔴 (probable log target) |
| This bucket is a log target (trail, ALB/NLB/CLB, CloudFront, flow logs, Config, other buckets) | 7 | any → Blast 🔴 |
| Replication source or destination | 6 | any → Blast 🔴 |
| DNS records or website hosting pointing at the bucket | 8 | any → Blast 🔴 (deleting frees the name: subdomain-takeover risk) |
| IAM principals with S3 access | 9 | any → Dependency 🟡 |
| IaC references to the bucket name / ARN | 0 | 1–2 → Dependency 🟡; ≥ 3 → Dependency 🔴 |

## Reversibility classification
- **Default:** 🔴 irreversible (objects gone is gone). `unmanaged` owner changes nothing here.
- **Mitigated to 🟡:** versioning enabled AND MFA delete NOT enabled AND the plan stages the delete (delete markers first; permanent version removal and bucket delete only after an agreed hold). The recovery window is that hold plus whatever the noncurrent-version lifecycle rule (Query 2) leaves — not a fixed number of days. A bucket can only be deleted once all versions are gone, so bucket deletion itself ends recoverability.

## Blast radius classification
- **Default:** 🟡 — S3 bucket names are GLOBAL namespace; after deletion, the name is released and another AWS customer can claim it. Brand/phishing risk if the name was public-facing.
- **Raised to 🔴:** any Attachment row above that says so.

## Rollback note (informational, shown in plan)
"S3 deletion is irreversible. In a versioned bucket (no MFA delete), noncurrent versions can be restored only while they still exist — the window is set by the noncurrent-version lifecycle rule and any hold you agree, and ends when the versions are purged or the bucket is deleted. After bucket deletion the name returns to the global pool: if it was public-facing (static site, partner allowlist, log-delivery destination), strongly consider keeping the bucket empty rather than deleting."
