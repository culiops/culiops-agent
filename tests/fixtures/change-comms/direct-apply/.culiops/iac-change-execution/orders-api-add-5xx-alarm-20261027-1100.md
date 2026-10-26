**IaC change execution for:** `orders-api` / `prod`
**Change:** `Add CloudWatch alarm for orders-api ALB 5xx rate`
**Date:** `2026-10-27 11:00`
**Commit:** `b1c2d3e`
**IaC tool(s):** `Terraform`
**Execution path:** Direct apply
**Pre-flight record:** `invoked inline — verdict: GREEN`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: manual apply (no CI for this repo). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1`. Repo: `github.com/acme/orders-infra`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| No existing 5xx alarm on the orders-api ALB | `code: monitoring.tf` (none) | `live: aws cloudwatch describe-alarms --alarm-name-prefix orders-api-alb-5xx` → 0 alarms | ✅ |

## Change Plan

**Phase 1 of 1: Add 5xx alarm**
- Files: `monitoring.tf`
- Resources affected: 1 to add (`aws_cloudwatch_metric_alarm.orders_api_5xx`), 0 to change, 0 to destroy
- Blast radius: none; the alarm is additive and notifies the existing on-call SNS topic
- Rollback path: `terraform destroy -target=aws_cloudwatch_metric_alarm.orders_api_5xx` or remove the block and re-apply
- Success criteria: re-plan → `No changes`; `aws cloudwatch describe-alarms --alarm-names orders-api-alb-5xx` → `StateValue = OK`

**Execution path:** Direct apply

## Execution Log

### Phase 1: Add 5xx alarm
- Files changed: `monitoring.tf`
- Plan output summary: 1 to add, 0 to change, 0 to destroy
- Plan hash: `sha256:c4d6e8…`
- Pre-flight verdict: GREEN
- Execution: `terraform apply -var-file=envs/prod.tfvars` — Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
- Verification: re-plan: No changes; `aws cloudwatch describe-alarms` → state OK

## Outcome

completed

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
