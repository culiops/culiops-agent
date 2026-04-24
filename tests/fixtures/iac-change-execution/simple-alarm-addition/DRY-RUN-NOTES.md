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

## Step 4 — Execute

### 4a: Generate plan output

- Skill presents: `terraform plan -var-file=envs/prod.tfvars -out=tfplan`
- Operator runs the command (or skill runs with approval)
- Expected plan: 1 to add, 0 to change, 0 to destroy

### 4b: Pre-flight gate

- No existing pre-flight record — skill invokes `pre-flight` inline
- Context: Terraform, 1 resource add, CloudWatch alarm, paymentapi, ap-southeast-1
- Expected verdict: **Green** — alarm addition is low-risk, reversible, non-data-path
- GATE 3: Green → proceed

### 4c: Execute (PR path)

- Skill presents PR action and waits for GATE 4 approval
- Creates branch `iac-change/paymentapi-cpu-alarm`, commits, opens PR
- PR description references the pre-flight record
- Reports PR URL to operator
- Skill does NOT run `terraform apply` directly

## Step 5 — Verify & Record

- PR path: "PR created. Pipeline will handle apply and verification."
- Writes execution record to `.culiops/iac-change-execution/paymentapi-cpu-alarm-<timestamp>.md`
- GATE 5: offers to commit the record

## Gaps surfaced

_(to be filled during actual dry-run)_

## Fixes applied

_(to be filled during actual dry-run)_
