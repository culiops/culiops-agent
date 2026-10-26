# direct-apply

## Scenario

One-phase Terraform change applied directly from the operator's machine: add a CloudWatch 5xx alarm for `orders-api` (prod). The record `orders-api-add-5xx-alarm-20261027-1100.md` has Execution path `Direct apply`, so the outcome and verification come from the record, not from the operator. The operator does not know the apply time and skips it. Platform is Slack.

Exercises: the direct-apply source rule (record is authoritative for outcome and verification), citation of extracted facts, Slack formatting, missing apply time handled as a TODO, and the record `Date` never being shown as the apply time.

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md` | Execution `terraform apply -var-file=envs/prod.tfvars — Apply complete! Resources: 1 added, 0 changed, 0 destroyed.`; Verification `re-plan: No changes; aws cloudwatch describe-alarms → state OK`; Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |

## MUST

- The result draft uses Slack formatting (`*bold*`, no wiki markup).
- The verification text in the fact table is cited as `record: .culiops/iac-change-execution/orders-api-add-5xx-alarm-20261027-1100.md#Execution Log`.
- The outcome (apply complete, 1 added) is taken from the record and may be stated, since this is a direct apply.
- The apply time is omitted, or shown as `<TODO: apply time>`, and the TODO is listed under Open TODOs.
- Result and ticket-close drafts are produced.

## MUST-NOT

- The string `11:00` shown as the apply time (the record `Date` is when the record was written).
- An invented apply time.
