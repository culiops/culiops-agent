# Execution Plan — payments

**Run:** payments, account 123456789012, region us-east-1
**Operator:** arn:aws:iam::123456789012:user/alice
**Generated:** 2026-05-12T14:08:00Z
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
| Operator identity matches intake | AWS STS | unknown | run `aws sts get-caller-identity --profile prod-main --query Account`; the result must equal intake account `123456789012` (stop on mismatch) | unknown (no pricing source read) | **needed** |
| Discovery (Steps 2–3, one delegation) | diagram images + AWS APIs | full | no IaC supplied -> run `service-discovery` real-discovery (docs + live) against account 123456789012 in us-east-1 | priced at `service-discovery`'s own cost gate | **needed** |
| Resource enumeration from IaC | IaC repo | full | not applicable — IaC unavailable; real-discovery fills this. (If IaC were supplied: `service-discovery` IaC path with its live cross-check, Step 2V.) | $0 | covered |
| Activity baseline + control-plane events + wiring + cross-Region (Step 4) | runtime-trace | full | **SKIPPED — operator choice** (time constraint: the handoff meeting moved to 2026-05-14). Consequence: no runtime profile; items 5, 7, 8, 9 become `?` and 2, 16, 18, 19, 25 cannot be cross-checked (`◐`). Run it later with the same invocation; it needs no Cost Explorer access to produce these sections. | — | skipped (operator choice, 2026-05-12T14:09:00Z) |
| Tribal knowledge (Step 5) | Outgoing team | full | emit questionnaire; share with Pay Team | $0 | proceeds at Step 5 |
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

### For Step 4 (runtime profile) — SKIPPED

Skipped by operator choice at Gate 1.5 (time constraint). To add it later: re-invoke `service-takeover` and resume at Step 4 with the same scoping (`tag:service=payments`, intent `takeover`).

---

## Approval block

**Recording rule:** targeted CLI commands above are always projected with `--query`. After the operator runs one, this file and `state.md` record only the derived fact (for example "Event history readable: yes", "caller account matches intake: yes"), never the pasted output.

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** approved

**Approval timestamp:** 2026-05-12T14:12:00Z

**Operator notes:** "Skip runtime-trace for now — the meeting moved up to Thursday. I will run it before sign-off. Still do the discovery and the read-only batch. Share the questionnaire with Bob (bob@example.com) at Step 5."

---

## Addendum — Step 6 verification batch

Proposed at Gate 6 for the `◐` items that have a read-only check (10, 24, 15). Approved separately from the Step 1.5 plan.

| Item | Command | Expected derived fact |
|---|---|---|
| 10 | `aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}'` | which of the 5 named alarms exist, what they cover, whether each is enabled with actions, and its state |
| 24 | `aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'` | `ENABLED` / `DISABLED` |
| 15 | `aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}'` | `allowed` / `implicitDeny` per action and function |
| 15 | `aws iam get-context-keys-for-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --query 'ContextKeyNames'` | list of condition keys that need a value (empty = none) |

**Approved:** 2026-05-12T15:14:00Z. Targeted commands are read-only, projected with `--query`, pinned to `--profile prod-main --region us-east-1`, and run after `aws sts get-caller-identity` re-confirms account 123456789012. Only derived facts are recorded in `readiness-scorecard.md`.
