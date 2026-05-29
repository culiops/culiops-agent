**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-aurora-20260528-1100.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-05-28 11:05
**Items considered:** 1   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-aurora-20260528-1100.md` (waste mode, single-cloud aws).
- 1 item above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) will score ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

No queries run — all items routed to manual review (see below). No `delete-aurora-cluster` playbook exists in v1; the skill cannot construct a verification batch for this action type.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 1 | $420/mo (not assessed) |

**Total plan savings:** $0/mo actionable — the single candidate item requires manual review before any action can be taken.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

No items in this tier.

## ❔ Manual review required

| # | Action | Resource | Savings | Source | Confidence | Reason |
|---|--------|----------|---------|--------|------------|--------|
| 1 | Delete Aurora cluster legacy-orders-aurora | arn:aws:rds:ap-southeast-1:123456789012:cluster:legacy-orders-aurora | $420/mo | line-item-computation | medium | No `delete-aurora-cluster` playbook in v1. Operator should verify: (a) 0 DatabaseConnections + 0 SelectThroughput + 0 DMLThroughput in last 90d via cloudwatch:GetMetricStatistics (extend the 30d window from the upstream report to catch quarterly jobs); (b) no Secrets Manager / SSM Parameter Store entries reference the cluster endpoint via secretsmanager:ListSecrets + ssm:DescribeParameters scans; (c) no read replicas in the cluster (`rds:DescribeDBClusters --query Clusters[].DBClusterMembers`) or cross-region replication targets (`rds:DescribeGlobalClusters`); (d) no ECS task definition / Lambda env var / EC2 user-data references the cluster endpoint hostname. **Pre-delete: take a final cluster snapshot** (`rds:CreateDBClusterSnapshot`) for compliance / accidental-deletion recovery — Aurora cluster deletion with `--skip-final-snapshot` is irreversible. |

## Gaps

Verification step skipped because no actionable items have matching playbooks. The operator's manual review of the ❔ item is required before any cost action.

## Next steps (informational)

v1.1+ may ship a delete-aurora-cluster playbook; until then, operator should follow the playbook stub in the Reason column above. If after manual review the item is safe to delete, open `iac-change-execution` directly with the resource ARN — without a cost-optimize-plan tier badge, iac-change-execution will run its normal pre-flight assessment from scratch.
