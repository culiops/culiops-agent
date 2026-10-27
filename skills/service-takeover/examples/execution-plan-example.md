# Example — Step 1.5 Execution Plan Output

This is an illustrative example of what the skill emits at Step 1.5 to `.culiops/service-takeover/<service>/execution-plan.md`. It is NOT consumed by the skill — it's a reference for implementers and future maintainers.

---

# Execution Plan — payments

**Run:** payments, account 123456789012, region us-east-1
**Operator:** arn:aws:iam::123456789012:user/alice
**Generated:** 2026-05-12T14:00:00Z
**Intent:** takeover from Pay Team, scheduled for 2026-06-15

## What we have

| Source | State | Path | Age |
|---|---|---|---|
| Diagram images | provided | `~/handoff/payments-arch.png`, `~/handoff/payments-flows.png` | n/a |
| IaC repo | none | — | — |
| AWS credentials | configured | env vars present | live |
| service-discovery catalog | none | — | — |
| runtime-trace profile | none | — | — |
| Tag scoping primitive | `service=payments` | provided by operator | n/a |

## What we need (per planned step)

| Need | Source | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Operator identity matches intake | AWS STS | unknown | run `aws sts get-caller-identity --profile {p} --query Account`; the result must equal intake account `123456789012` (stop on mismatch) | unknown (no pricing source read) | **needed** |
| Discovery (Steps 2–3, one delegation) | diagram images + AWS APIs | full | no IaC supplied → run `service-discovery` real-discovery (docs + live) with the diagrams as docs, against account 123456789012 in us-east-1 | $0 (read-only) | **needed** |
| Resource enumeration from IaC | IaC repo | full | not applicable — IaC unavailable; real-discovery fills this. (If IaC were supplied: `service-discovery` IaC path with its live cross-check, Step 2V.) | $0 | covered |
| Cross-region inventory | Resource Explorer | unknown | covered by runtime-trace Step 4 | $0 | covered |
| Activity baseline + control-plane events (Step 4) | CloudWatch + CloudTrail + CE | full | run `runtime-trace` with scoping primitive `tag:service=payments` | priced at runtime-trace's own cost gate (the Cost Explorer API bills per request: docs: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/) | **needed** |
| CloudTrail Event history probe | CloudTrail API | unknown | run `aws cloudtrail lookup-events --max-results 1 --profile {p} --region us-east-1 --query 'Events[0].EventTime'` before Step 4 (Event history needs no trail). Record only the derived fact, e.g. "Event history readable: yes" | $0 (docs: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html — no charge for viewing Event history) | **needed** |
| Resource Explorer availability probe | RE API | unknown | run `aws resource-explorer-2 list-indexes --profile {p} --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` before Step 4. Record only the derived fact | $0 (docs: https://aws.amazon.com/resourceexplorer/pricing/) | **needed** |
| Tribal knowledge (Step 5) | Outgoing team | full | emit questionnaire; share with Pay Team | $0 | proceeds at Step 5 |
| Readiness assessment (Step 6) | All prior artifacts | full | auto-mark from artifacts; ◐ items get an optional read-only verification batch; attested only for items 3, 11, 12 | $0 | proceeds at Step 6 |
| Handoff package (Step 7) | All prior artifacts | full | assemble README + snapshots | $0 | proceeds at Step 7 |

## Proposed invocations

### For Steps 2–3 (discovery) — to run after this plan is approved

One delegation. No IaC repo, so `service-discovery` runs real-discovery (docs, then live).

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

## Approval block

**Recording rule:** targeted CLI commands above are always projected with `--query`. After the operator runs one, this file and `state.md` record only the derived fact (e.g. "Event history readable: yes", "caller account matches intake: yes"), never the pasted output.

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** _pending_

**Approval timestamp:** _pending_

**Operator notes (optional):** _none_
