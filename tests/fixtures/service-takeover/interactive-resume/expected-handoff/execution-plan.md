# Execution Plan — payments

**Run:** payments, account 123456789012, region us-east-1
**Operator:** arn:aws:iam::123456789012:user/alice
**Generated:** 2026-05-05T09:12:00Z
**Intent:** takeover from Pay Team, scheduled for 2026-06-15

---

## What we have

| Source | State | Path | Age |
|---|---|---|---|
| Diagram images | provided | `~/handoff/payments-arch.png`, `~/handoff/payments-flows.png` | n/a |
| IaC repo | none | — | — |
| AWS credentials | configured | profile `prod-main` | live |
| service-discovery catalog | none | — | — |
| runtime-trace profile | none | — | — |
| Tag scoping primitive | `service=payments` | provided by operator | n/a |

---

## What we need (per planned step)

| Need | Source | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Operator identity matches intake | AWS STS | unknown | run `aws sts get-caller-identity --profile prod-main --query Account`; the result must equal intake account `123456789012` (stop on mismatch) | $0 | **needed** |
| Discovery (Steps 2–3, one delegation) | diagram images + AWS APIs | full | no IaC supplied -> run `service-discovery` real-discovery (docs + live) against account 123456789012 in us-east-1 | $0 (read-only) | **needed** |
| Resource enumeration from IaC | IaC repo | full | not applicable — IaC unavailable; real-discovery fills this. (If IaC were supplied: `service-discovery` IaC path with its live cross-check, Step 2V.) | $0 | covered |
| Cross-region inventory | Resource Explorer | unknown | covered by runtime-trace Step 4 | $0 | covered |
| Activity baseline + control-plane events + wiring (Step 4) | CloudWatch + CloudTrail + CE | full | run `runtime-trace` with scoping primitive `tag:service=payments` (tag-attributed spend) | ~$0.03 (Cost Explorer charges) | **needed** |
| CloudTrail Event history probe | CloudTrail API | unknown | run `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region us-east-1 --query 'Events[0].EventTime'` before Step 4 (Event history needs no trail). Record only the derived fact, e.g. "Event history readable: yes" | $0 | **needed** |
| Resource Explorer availability probe | RE API | unknown | run `aws resource-explorer-2 list-indexes --profile prod-main --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` before Step 4. Record only the derived fact | $0 | **needed** |
| Tribal knowledge (Step 5) | Outgoing team | full | emit questionnaire; share with Pay Team via Slack | $0 | proceeds at Step 5 |
| Readiness assessment (Step 6) | All prior artifacts | full | auto-mark from artifacts; `◐` items with a read-only check get a Step 6 verification batch (offered by default; skipping leaves them `◐` and the verdict `partial`); attested only for items 3, 11, 12 | $0 | proceeds at Step 6 |
| Handoff package (Step 7) | All prior artifacts | full | assemble README + snapshots; private-repo reminder before any commit | $0 | proceeds at Step 7 |

---

## Proposed invocations

### For Steps 2–3 (discovery) — to run after this plan is approved

One delegation. No IaC repo, so `service-discovery` runs real-discovery (docs, then live). Its output is the only catalog; there is no separate diagram catalog to overwrite.

```
Invoke service-discovery with:
  - mode: real-discovery
  - inputs: ~/handoff/payments-arch.png, ~/handoff/payments-flows.png (docs);
            AWS live APIs (account 123456789012, region us-east-1)
  - scoping: tag service=payments
  - output: .culiops/service-discovery/payments-catalog.md
```

### For Step 4 (runtime profile) — to run after Steps 2–3

```
Invoke runtime-trace with:
  - service: payments
  - account: 123456789012
  - region: us-east-1
  - scoping-primitive: tag service=payments
  - intent-category: takeover
  - --redact: not set (internal handoff)
  - output: .culiops/runtime-trace/payments-runtime-profile.md
```

---

## Approval block

**Recording rule:** targeted CLI commands above are always projected with `--query`. After the operator runs one, this file and `state.md` record only the derived fact (for example "Event history readable: yes", "caller account matches intake: yes"), never the pasted output.

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** approved

**Approval timestamp:** 2026-05-05T09:20:00Z

**Operator notes:** "Proceed as proposed. Share the questionnaire with Bob (bob@example.com) at Step 5."

---

## Addendum — Day 7 resume (2026-05-12T08:00:00Z)

- `state.md` read first; intake not re-entered. Resume point confirmed by the operator: **Step 4**.
- Identity re-checked on resume (`sts get-caller-identity` = 123456789012).
- Existing artifact: `service-catalog.md`, generated 2026-05-05T10:20:00Z, **7 days old**, `Live verification: performed 2026-05-05`. Offered: (A) use as-is, (B) verify with a thin re-scan, (C) re-run. **Operator chose (A) use as-is.** The age is recorded in `state.md` (same-target table) and in the scorecard notes; the profile's Resource Explorer result (8 of 8, same names) was checked against the catalog inventory after Step 4.
- The `runtime-trace` invocation under "Proposed invocations" above is the one saved on Day 1.

---

## Addendum — Step 6 verification batch

Proposed at Gate 6 (Day 7) for the `◐` items that have a read-only check (10, 24, 15).

| Item | Command | Expected derived fact |
|---|---|---|
| 10 | `aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}'` | which of the 5 named alarms exist, with actions |
| 24 | `aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'` | `ENABLED` / `DISABLED` |
| 15 | `aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}'` | `allowed` / `implicitDeny` per action and function |

**Approved:** 2026-05-12T09:20:00Z. Targeted commands are read-only, projected with `--query`, pinned to `--profile prod-main --region us-east-1`, and run after `aws sts get-caller-identity` re-confirms account 123456789012. Only derived facts are recorded in `readiness-scorecard.md`.
