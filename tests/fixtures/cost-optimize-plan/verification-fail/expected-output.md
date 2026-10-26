**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Target:** account 123456789012 (sts verified, live:0a), region(s) ap-southeast-1
**IaC repo(s):** ~/acme-infra (simulated for this fixture; code refs illustrative)
**Catalog used:** none
**Date:** 2026-05-28 10:22
**Items considered:** 1   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md` (waste mode, single-cloud aws, fresh).
- 1 item above $5/mo floor; 0 filtered below floor.
- Target: account `123456789012`, region `ap-southeast-1`.
- Catalog: none. IaC repo supplied: `~/acme-infra`.
- Activity source: S3 `lookup-events` is NOT a source (management events only; it never returns `GetObject`). `delete-s3-bucket.md` order applies: request metrics, then server access logs, then CloudTrail Lake.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

All queries executed 2026-05-28 10:18-10:21 UTC. Evidence is summarized: access-log rows, requester IPs and object keys are not recorded (Constraint 14).

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 123456789012 = `Scope`; region ap-southeast-1 (2026-05-28T10:18Z) |
| 0b | Delete bucket-logs-active | s3:GetBucketTagging + IaC grep | s3:GetBucketTagging | ok | no CloudFormation / controller tag; `aws_s3_bucket` at `s3.tf:88` → owner **terraform**; one other IaC reference (`lambda.tf:140`, the export role's read policy) |
| 1 | Delete bucket-logs-active | s3:GetBucketLocation | s3:GetBucketLocation | ok | `ap-southeast-1`: bucket exists in this account/region (Metrics rule precondition) |
| 2 | Delete bucket-logs-active | s3:GetBucketVersioning + s3:GetBucketLifecycleConfiguration | s3:GetBucketVersioning, s3:GetLifecycleConfiguration | ok | versioning `Suspended`; no lifecycle rule |
| 3 | Delete bucket-logs-active | s3:ListBucketMetricsConfigurations (source 3a) | s3:GetMetricsConfiguration | ok | none configured: CloudWatch request metrics unavailable, fall through to 3b |
| 4 | Delete bucket-logs-active | s3:GetBucketLogging + s3:ListObjectsV2 / s3:GetObject on `acme-s3-access-logs` (source 3b, 90d) | s3:GetBucketLogging, s3:ListBucket, s3:GetObject (log bucket) | ok | logging enabled since 2025-11-10 (covers the window). **90d: 3,694 `REST.GET.OBJECT`, of which 1,247 in the last 30d; last GET 2026-05-27 14:32 UTC; every day has GETs (daily min 31 / median 41 / max 52); all by `assumed-role/lambda-export-fn`.** 2,311 PUTs by `log-shipper`; 0 DELETE |
| 5 | Delete bucket-logs-active | cloudwatch:GetMetricData (`NumberOfObjects`, `BucketSizeBytes`; daily, 90d) + `list-objects-v2 --max-keys 1 --query KeyCount` | cloudwatch:GetMetricData, s3:ListBucket | ok | objects 38,100 → 41,200 (+8.1%): writes persisted; bucket non-empty |
| 6 | Delete bucket-logs-active | s3:GetBucketPolicy | s3:GetBucketPolicy | ok | `NoSuchBucketPolicy`: no cross-account or service principals |
| 7 | Delete bucket-logs-active | s3:GetBucketReplication | s3:GetReplicationConfiguration | ok | none: not a replication source |
| 8 | Delete bucket-logs-active | log-target sweep (cloudtrail:DescribeTrails, elbv2/elb attributes, cloudfront:GetDistributionConfig, ec2:DescribeFlowLogs, config:DescribeDeliveryChannels) | see `delete-s3-bucket.md` | ok | not the destination of any trail, LB access log, CloudFront log, flow log or Config channel |
| 9 | Delete bucket-logs-active | route53:ListResourceRecordSets (all records, client-side match) | route53:List* | ok | 1 zone, 38 records, no record points at the bucket |

Not run, by design: activity source 3c (CloudTrail Lake) because 3b already covers the window; optional Query 9 IAM principal sweep (not selected at GATE 2).

**Total estimated API cost:** about 90 S3 LIST and about 3,800 S3 GET requests against the access-log bucket (per-request S3 pricing, itemized at GATE 2; small), plus free describe calls. No CloudTrail Lake scan.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 1 | ($400/mo claimed — NOT realized) |
| ❔ Manual review | 0 | — |

**Total plan savings:** $0/mo — the single candidate item is disqualified. No actionable items.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Savings claimed | Disqualifying evidence |
|---|--------|----------|-----------------|------------------------|
| 1 | Delete bucket bucket-logs-active | bucket-logs-active | $400/mo | S3 server access logs → 3,694 GET in 90d, 1,247 in the last 30d, every day of the window (daily 31-52), last 2026-05-27 14:32 UTC, all by `assumed-role/lambda-export-fn` (live:4). Steady recurring reads of an active bucket; plus object count growing +8.1% (live:5). |

**Dimension detail:**
- **Evidence 🚫** — the required activity row of `delete-s3-bucket.md` (GET/PUT/DELETE/HEAD over >= 60d, hourly-or-daily distribution) is triggered by a recurring, recent pattern (Principle 3: this is steady use, not one old burst). The source is S3 server access logs (live:4) because no request-metrics configuration exists (live:3); the optional growth row also fires (live:5). Tier rule 1 → 🚫.
- **Owner:** terraform (`code:s3.tf:88`). `lambda.tf:140` shows the exporting function's IAM role reads this bucket, which independently corroborates the log evidence (attachment, not scored as Evidence).
- **Reversibility / Blast radius / Dependency** — not scored: the item is disqualified at Evidence. (For reference: versioning is Suspended, so a delete would not be recoverable.)

> **Item is NOT silently dropped.** It stays in the plan with the full disqualifying record so the operator can correct the upstream waste analysis.

## Drift

None — no item reached a code-versus-live comparison (the item was disqualified on Evidence).

## Gaps

- Server access logs are best-effort delivery and history begins 2025-11-10; the counts are a lower bound. That does not weaken the 🚫 (any recurring access disqualifies); it would matter only for a 🟢 reading.
- Log-target sweep did not cover S3 Inventory / Storage Lens / Athena result locations or Macie / Security Lake / GuardDuty exports (`delete-s3-bucket.md` Query 8 limits). Moot for this item.
- Optional IAM principal sweep not selected at GATE 2.

## Next steps (informational)

- Item #1 should **NOT** be deleted. `lambda-export-fn` reads from `bucket-logs-active` every day; deleting the bucket would break that export pipeline.
- Investigate the `lambda-export-fn` dependency (what it reads, how often, whether the data can be consolidated or archived rather than deleted).
- Update the upstream waste analysis so it does not flag buckets with recurring access. S3 request data is not in `lookup-events`: use request metrics, access logs or CloudTrail Lake.
- If the bucket's cost is still a concern, a lifecycle or Intelligent-Tiering change (run through `cost-optimize-plan` as its own item, with access-pattern evidence) reduces cost without deleting.
