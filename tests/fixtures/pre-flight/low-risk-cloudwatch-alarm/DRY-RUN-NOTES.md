# Dry-run of `pre-flight` against `low-risk-cloudwatch-alarm`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23; re-run 2026-10-26 against the evidence rule (live health evidence required for GREEN).

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
| L3 target check | `aws sts get-caller-identity` account and `--region us-east-1` match the plan's target |
| L3 resource health | Operator approved the read-only batch. `ecs describe-services` running = desired, no pending; `describe-alarms --state-value ALARM` shows nothing on `orderapi-prod` dimensions → Green (`live:2`, `live:3`) |
| Evidence rule | Category 10 Green cites live evidence; categories 2 and 9 cite the plan |
| Category 11 not triggered | Adding an alarm changes no app-facing attribute → Green from the plan, Q8 not asked |

| Monitoring-only change | The only change is an alarm with no output / export changed, so dependency impact (4), observability readiness (7) and cost impact (8) are Green from the plan without a catalog. Before 2026-10-26 the rules forced 4 = ⚪ and 7 / 8 = Yellow, so this fixture's GREEN was unreachable |
| Fresh eyes on GREEN | A separate reviewer, given the evidence and rules but not the scores, scored all 11 Green. One of its flags (a "missing" `alarm_description`) was rejected by citing `main.tf:10` |
| Not verified (examples the record lists) | The apply identity used by CI (the live check proves only the operator's CLI). Whether an out-of-band alarm with the same name exists (`PutMetricAlarm` upserts). The SNS subscriber protocols: an auto-remediation Lambda or HTTPS endpoint would make the alarm app-affecting |

## Findings and fixes applied

No findings — the skill produced a clean all-Green assessment.

### Variant: alarm with a scaling action

This is the same alarm with an Application Auto Scaling policy ARN added to `alarm_actions`. The alarm now changes the system, so it is app-facing:

- Category 11 triggers and asks Q8. With no source available, it is ⚪.
- The monitoring-only exceptions for categories 4, 7 and 8 no longer apply. Category 4 becomes ⚪. Categories 7 and 8 become Yellow, because cost is now driven by usage.
- Four Yellow / ⚪ scores escalate the verdict to **RED — soft block**.

A simulated run also flagged two real problems:

- The OK action has no scale-in, so capacity can only grow.
- The policy ARN is hard-coded to prod while the alarm name uses `var.env`.

### Variant: SNS protocols not checked

If the L3 subscription-protocol query isn't run, nothing shows the alarm is notify-only. It is treated as app-facing (unsure means triggered), so the verdict can't be GREEN.

### Variant: L3 declined

Same inputs, operator answers "no" to L3. Category 10 → ⚪ (the operator saying "it's fine" is `operator-stated`, not evidence). 1 ⚪ caps the verdict → **YELLOW — proceed with caution**, with the mitigation "approve the L3 health checks to clear ⚪".

## What a produced report would look like

`.culiops/pre-flight/orderapi-add-alarm-20260423-1400.md` would contain:

- Target: account `<plan account>` / `us-east-1`
- Plan hash: `sha256:76e9ec8f3d6c7697eb0d3a6f6a081f9a215ee05a89d8d28c4893a970096185b1` (SHA-256 of `plan-output.txt`)
- Verdict: **GREEN — proceed**
- All 11 categories scored Green, each with its evidence source
- No hard blocks, no acknowledged risks, no mitigations needed
- L1 detail: Terraform plan adds 1 `aws_cloudwatch_metric_alarm`, 0 changes, 0 destroys. Git history shows no recent changes to these files.
- L2 context: normal hours, no incidents, experienced operator
- L3: target check + `ecs describe-services` + firing-alarm check (summarized results)
