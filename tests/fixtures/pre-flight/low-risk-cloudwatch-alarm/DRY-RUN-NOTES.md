# Dry-run of `pre-flight` against `low-risk-cloudwatch-alarm`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Assessor loading | `assessors/iac-change.md` matched Terraform plan output (detected `Plan: 1 to add, 0 to change, 0 to destroy.`) |
| All-Green scoring | Every category scored Green — the skill produced a "GREEN — proceed" verdict |
| L1 blast radius | 1 resource added, single region, resource type is `aws_cloudwatch_metric_alarm` (monitoring, not data-path) → Green |
| L1 reversibility | Addition only, no destroy/replace. Alarm can be removed by reverting the commit → Green |
| L1 change velocity | `git log --since=7.days -- main.tf variables.tf` returned 0 commits → Green |
| L1 dependency impact | CloudWatch alarm has no downstream consumers → Green |
| L1 observability readiness | The change itself adds monitoring — improves observability → Green |
| L1 cost impact | CloudWatch alarm cost: $0.10/month per alarm → negligible → Green |
| L1 security posture | No IAM, network, encryption, or public-access changes → Green |
| L2 timing context | Operator answered: no incident (Q1), no freeze (Q2), not peak (Q3) → Green |
| L2 operator familiarity | Operator answered: changed this service many times (Q4), experienced with Terraform (Q5) → Green |
| L2 cost impact | Operator answered: negligible (Q6) → confirms L1 Green |
| L3 not requested | Operator declined L3 — all categories already scored from L1+L2 |

## Findings and fixes applied

No findings — the skill produced a clean all-Green assessment.

## What a produced report would look like

`.culiops/pre-flight/orderapi-add-alarm-20260423-1400.md` would contain:

- Verdict: **GREEN — proceed**
- All 10 categories scored Green
- No hard blocks, no acknowledged risks, no mitigations needed
- L1 detail: Terraform plan adds 1 `aws_cloudwatch_metric_alarm`, 0 changes, 0 destroys. Git history shows no recent changes to these files.
- L2 context: normal hours, no incidents, experienced operator
- L3: not requested
