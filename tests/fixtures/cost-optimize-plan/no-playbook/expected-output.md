**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-lambda-20260528-1100.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-05-28 11:05
**Items considered:** 1   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-lambda-20260528-1100.md` (waste mode, single-cloud aws).
- 1 item above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) will score ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

No queries run — all items routed to manual review (see below). No `delete-lambda` playbook exists in v1; the skill cannot construct a verification batch for this action type.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 0 | — |
| ❔ Manual review | 1 | $35/mo (not assessed) |

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
| 1 | Delete Lambda function idle-worker | arn:aws:lambda:ap-southeast-1:123456789012:function:idle-worker | $35/mo | line-item-computation | medium | No `delete-lambda` playbook in v1. Operator should verify: (a) 0 invocations in last 90d via cloudwatch:GetMetricStatistics on Lambda.Invocations; (b) no EventBridge rules reference the function via events:ListRules with target filter; (c) no API Gateway integrations via apigateway:GetIntegrations sweep; (d) no other services trigger it (SQS, S3 events, Cognito). |

## Gaps

Verification step skipped because no actionable items have matching playbooks. The operator's manual review of the ❔ item is required before any cost action.

## Next steps (informational)

v1.1+ may ship a delete-lambda playbook; until then, operator should follow the playbook stub in the Reason column above. If after manual review the item is safe to delete, open `iac-change-execution` directly with the resource ARN — without a cost-optimize-plan tier badge, iac-change-execution will run its normal pre-flight assessment from scratch.
