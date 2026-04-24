# Dry-run of `iac-change-execution` against `simple-alarm-addition`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Research

**Input:** operator request — "Add a CloudWatch CPU utilization alarm for paymentapi in prod."

**Expected behaviour:**

| Check | Expected outcome |
|-------|-----------------|
| Catalog lookup | No `.culiops/service-discovery/paymentapi-prod.md` found — skill proceeds without catalog |
| Tool detection | Finds `main.tf`, `variables.tf`, `outputs.tf` → identifies Terraform |
| Naming pattern | Scans existing resource names: `paymentapi-cluster-${var.env}`, `paymentapi-svc-${var.env}`, `paymentapi-alerts-${var.env}` → infers `paymentapi-*-${var.env}` |
| SNS topic discovery | Reads `aws_sns_topic.paymentapi_alerts` → alarm should reuse `aws_sns_topic.paymentapi_alerts.arn` |
| ECS identifiers | Records `ClusterName = "paymentapi-cluster-${var.env}"`, `ServiceName = "paymentapi-svc-${var.env}"` for alarm dimensions |
| tfvars location | Finds `envs/prod.tfvars` — notes `-var-file=envs/prod.tfvars` for plan command |

## Step 2 — Plan

**Expected output:**

```
Phase 1 (of 1):
  Add: aws_cloudwatch_metric_alarm.paymentapi_cpu_high
  Modify: (none)
  Destroy: (none)

Execution path: PR (default)
Pre-flight: required before merge
```

**Alarm spec the skill should propose:**

```hcl
resource "aws_cloudwatch_metric_alarm" "paymentapi_cpu_high" {
  alarm_name          = "paymentapi-cpu-high-${var.env}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU utilization above 80% for paymentapi ${var.env}"

  dimensions = {
    ClusterName = "paymentapi-cluster-${var.env}"
    ServiceName = "paymentapi-svc-${var.env}"
  }

  alarm_actions = [aws_sns_topic.paymentapi_alerts.arn]
  ok_actions    = [aws_sns_topic.paymentapi_alerts.arn]

  tags = {
    Service     = "paymentapi"
    Environment = var.env
  }
}
```

## Step 3 — Implement

**Expected behaviour:**

- Appends the alarm block to `main.tf` (no new files created)
- Follows the `paymentapi-*-${var.env}` convention → names alarm `paymentapi-cpu-high-${var.env}`
- Uses `aws_sns_topic.paymentapi_alerts.arn` (resource reference, not hardcoded ARN)
- Tags match existing resources (`Service = "paymentapi"`, `Environment = var.env`)
- Does NOT create a `plan-output.txt` — that is produced by the operator running `terraform plan`

## Step 4 — Code review gate

**Expected behaviour:**

- Skill surfaces the diff for operator review before proceeding
- Operator approves (no changes requested in this dry-run)

## Step 5 — Pre-flight

**Expected behaviour:**

- Skill invokes `pre-flight` skill with context: Terraform, 1 resource add, CloudWatch alarm, paymentapi, ap-southeast-1
- Expected verdict: **Green** — alarm addition is low-risk, reversible, non-data-path
- Skill reads the produced `.culiops/pre-flight/paymentapi-add-alarm-*.md` and confirms Green before proceeding

## Step 6 — Execute (PR path)

**Expected behaviour:**

- Skill opens a GitHub PR (or prints the git commands to do so)
- PR title: something like `feat(paymentapi): add cpu-high alarm for prod`
- PR description references the pre-flight record
- Skill does NOT run `terraform apply` directly

## Gaps surfaced

_(to be filled during actual dry-run)_

## Fixes applied

_(to be filled during actual dry-run)_
