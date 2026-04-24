# simple-alarm-addition — iac-change-execution fixture

A single-phase Terraform change that adds a CloudWatch CPU utilization alarm to an existing ECS Fargate service.

## What's modelled

`paymentapi` — a fictional ECS Fargate service in `ap-southeast-1`. The service already exists and is stable. The change adds a `aws_cloudwatch_metric_alarm` resource for CPU utilization.

## The proposed change

Add one `aws_cloudwatch_metric_alarm` resource wired to the existing SNS topic (`paymentapi-alerts-${var.env}`). No other resources are modified or destroyed.

## What this fixture exercises

- **Research without catalog:** no `.culiops/service-discovery/` entry exists; skill must inspect the repo directly to determine tooling, naming conventions, and existing resources
- **Convention matching:** skill detects the `paymentapi-*-${var.env}` naming pattern from existing resources and applies it to the new alarm
- **SNS topic discovery:** skill finds the existing `paymentapi-alerts-${var.env}` SNS topic and reuses it rather than creating a new one
- **Single-phase plan:** the change is purely additive (1 resource added, 0 modified, 0 destroyed) — no multi-phase logic required
- **PR path (default):** no direct-apply override is present; skill defaults to the PR workflow
- **Code review gate:** skill surfaces the generated Terraform for operator review before proceeding to plan/apply
- **Pre-flight integration:** skill invokes pre-flight before execution; expected verdict is Green (single alarm, no data-path impact, reversible)

## Files in this fixture

| File | Purpose |
|------|---------|
| `main.tf` | Existing Terraform for paymentapi (cluster, service, task def, SG, ALB TG, log group, SNS topic). The alarm is **absent** — it is what the skill would add. |
| `variables.tf` | Input variables |
| `outputs.tf` | Outputs |
| `envs/prod.tfvars` | Prod-environment variable values |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |
