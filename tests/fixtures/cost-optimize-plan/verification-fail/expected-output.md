**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-05-28 10:22
**Items considered:** 1   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-bucket-only-20260528-1015.md` (waste mode, single-cloud aws).
- 1 item above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) will score ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete bucket bucket-logs-active | s3:GetBucketLocation | s3:GetBucketLocation | ok | LocationConstraint=ap-southeast-1 — bucket exists in expected region |
| 2 | Delete bucket bucket-logs-active | s3:GetBucketPolicy | s3:GetBucketPolicy | ok | Policy present but Statement=[] — no resource-based policy granting external access |
| 3 | Delete bucket bucket-logs-active | s3:GetBucketLogging | s3:GetBucketLogging | ok | LoggingEnabled=null — bucket is not a logging target for another bucket |
| 4 | Delete bucket bucket-logs-active | s3:GetBucketReplication | s3:GetBucketReplication | ok | ReplicationConfigurationNotFoundError — no replication config; bucket is not a replication source |
| 5 | Delete bucket bucket-logs-active | s3:GetBucketVersioning | s3:GetBucketVersioning | ok | Status=Suspended — versioning not active; no pending delete markers to drain |
| 6 | Delete bucket bucket-logs-active | cloudtrail:LookupEvents (GetObject, 30d) | cloudtrail:LookupEvents | ok | **1,247 GetObject events in last 30d. Last event: 2026-05-27 14:32 UTC. Principal: AssumedRole/lambda-export-fn. Consistent traffic across full window (earliest sampled event: 2026-04-29). Active consumer detected — DISQUALIFYING.** |
| 7 | Delete bucket bucket-logs-active | s3:ListObjectsV2 | s3:ListObjectsV2 | ok | KeyCount=47; most-recent object modified 2026-05-27 15:01 UTC |

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 1 | ($400/mo claimed — NOT realized) |
| ❔ Manual review | 0 | — |

**Total plan savings:** $0/mo — the single candidate item is disqualified. No actionable items.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Savings claimed | Disqualifying evidence |
|---|--------|----------|-----------------|------------------------|
| 1 | Delete bucket bucket-logs-active | bucket-logs-active | $400/mo | cloudtrail:LookupEvents → 1,247 GetObject events in last 30d (last: 2026-05-27 14:32 UTC, principal: AssumedRole/lambda-export-fn). Suggests an active log-processing pipeline reads from this bucket. |

**Dimension detail:**
- **Evidence of use 🚫** — Query #6 (`cloudtrail:LookupEvents`, GetObject, 30d) returned 1,247 events distributed across the full 30-day window (earliest sampled: 2026-04-29, most-recent: 2026-05-27 14:32 UTC). The consistent frequency and single principal (`AssumedRole/lambda-export-fn`) indicate a scheduled or event-driven pipeline reading from this bucket regularly. Active read traffic disqualifies this item from all actionable tiers. Iron Law #3 requires the disqualifying signal to be shown — it is quoted above.
- **Reversibility** — Not scored. Item disqualified at Evidence dimension before reversibility triage.
- **Blast radius** — Not scored. Item disqualified at Evidence dimension.
- **Dependency footprint** — Not scored; the CloudTrail principal (`lambda-export-fn`) itself confirms at least one active dependency.

> **Item is NOT silently dropped.** It remains in the plan in this section with the full evidence record so the operator can investigate and correct the upstream waste analysis.

## Gaps

None — all 7 verification queries succeeded.

## Next steps (informational)

- Item #1 should **NOT** be deleted. The `lambda-export-fn` function reads from `bucket-logs-active` on a recurring schedule — deleting the bucket would break that pipeline.
- Operator should investigate the `lambda-export-fn` dependency: determine what it reads, how frequently, and whether the bucket can be consolidated or archived rather than deleted.
- Update the upstream waste-mode analysis to exclude buckets with active CloudTrail data events (GetObject count > 0 in last 30d). Re-run `cloud-cost-investigate` after adding that exclusion to avoid re-flagging active buckets as waste candidates.
- If the bucket's cost is still a concern after investigation, consider S3 Intelligent-Tiering or a lifecycle policy to reduce StandardStorage costs without deleting the bucket.
