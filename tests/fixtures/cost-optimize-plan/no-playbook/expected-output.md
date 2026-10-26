**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-aurora-20260528-1100.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Target:** account 123456789012 (from `Scope`; no queries run, so not sts-verified), region(s) ap-southeast-1
**IaC repo(s):** none
**Catalog used:** none
**Date:** 2026-05-28 11:05
**Items considered:** 1   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-aurora-20260528-1100.md` (waste mode, single-cloud aws, fresh).
- 1 item above $5/mo floor; 0 filtered below floor.
- Target: account `123456789012` (from `Scope`), region `ap-southeast-1` (from the resource ARN).
- Catalog: none. IaC repo: none supplied (and not needed: no verification batch is built).
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

No queries run - the only item has no matching playbook (`delete` + Aurora cluster; Aurora is listed as unsupported in `examples/aws.md`), so the verification batch is empty and Step 3 is skipped. That includes Query 0: with nothing to verify, no target check or ownership probe is issued, and no ownership is claimed for the item.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 1 | $420/mo (not assessed) |

**Total plan savings:** $0/mo actionable - the single candidate item requires manual review before any action can be taken.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

No items in this tier.

## ❔ Manual review required

| # | Action | Resource | Savings | Source | Confidence | Reason |
|---|--------|----------|---------|--------|------------|--------|
| 1 | Delete Aurora cluster legacy-orders-aurora | arn:aws:rds:ap-southeast-1:123456789012:cluster:legacy-orders-aurora | $420/mo | line-item-computation | medium | `manual-review-required`: no `delete-aurora-cluster` playbook (Aurora is not covered; a writer class change is a failover and Serverless v2 is ACU-based, so `rightsize-rds` does not apply either). Operator should verify, after authenticating against account 123456789012 / ap-southeast-1: (a) 0 `DatabaseConnections`, `SelectThroughput` and `DMLThroughput` over 90d at hourly granularity via `cloudwatch get-metric-data` (extend the upstream 30d window to catch quarterly jobs; 90d x 24 h exceeds the 1,440-point cap of `get-metric-statistics`); (b) no Secrets Manager / SSM Parameter Store entries reference the cluster endpoint; (c) no read replicas (`rds describe-db-clusters --query Clusters[].DBClusterMembers`) and no cross-region replication / global cluster membership (`rds describe-global-clusters`); (d) no ECS task definition / Lambda environment / EC2 user-data references the endpoint hostname (inspect names and references only; do not copy env values anywhere); (e) who owns it: tags, IaC repo and any `aws:cloudformation:stack-name` tag (a CloudFormation-owned cluster is outside the supported stack). **Pre-delete: take a final cluster snapshot** - deleting with `--skip-final-snapshot` is irreversible. |

## Drift

None - no verification ran.

## Gaps

Verification step skipped because no actionable item has a matching playbook. No ownership, activity or dependency evidence was gathered for the Aurora cluster; the manual review above is required before any cost action.

## Next steps (informational)

v1.1+ may ship a delete-aurora-cluster playbook; until then, follow the checklist in the Reason column. If after manual review the item is safe to delete, open `iac-change-execution` directly with the resource ARN - without a cost-optimize-plan tier badge, `iac-change-execution` and `pre-flight` run their normal assessment from scratch.
