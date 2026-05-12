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
| Architecture understanding (Step 2) | diagram images | none | proceed with `service-discovery` diagram extraction | $0 | auto (diagrams present) |
| Resource enumeration from IaC | IaC repo | full | not applicable — IaC unavailable; real-discovery fills this | $0 | covered |
| Live resource enumeration (Step 3) | AWS APIs | full | run `service-discovery` real-discovery mode against account 123456789012 in us-east-1 | $0 (read-only) | **needed** |
| Cross-region inventory | Resource Explorer | unknown | covered by runtime-trace Step 4 | $0 | covered |
| Activity baseline + control-plane events (Step 4) | CloudWatch + CloudTrail + CE | full | run `runtime-trace` with scoping primitive `tag:service=payments` | ~$0.05 (Cost Explorer charges) | **needed** |
| CloudTrail availability probe | CloudTrail API | unknown | run `aws cloudtrail describe-trails --region us-east-1` to probe before Step 4 | $0 | **needed** |
| Resource Explorer availability probe | RE API | unknown | run `aws resource-explorer-2 list-indexes` before Step 4 | $0 | **needed** |
| Tribal knowledge (Step 5) | Outgoing team | full | emit questionnaire; share with Pay Team via Slack | $0 | proceeds at Step 5 |
| Readiness assessment (Step 6) | All prior artifacts | full | auto-mark from artifacts; manual on un-evidenceable items | $0 | proceeds at Step 6 |
| Handoff package (Step 7) | All prior artifacts | full | assemble README + snapshots | $0 | proceeds at Step 7 |

## Proposed invocations

### For Step 2 (diagram extraction) — to run after this plan is approved

```
Invoke service-discovery with:
  - mode: real-discovery
  - inputs: ~/handoff/payments-arch.png, ~/handoff/payments-flows.png
  - scoping: tag service=payments
  - output: .culiops/service-discovery/payments-diagrams-catalog.md
```

### For Step 3 (live discovery) — to run after Step 2

```
Invoke service-discovery with:
  - mode: real-discovery
  - inputs: AWS live APIs (account 123456789012, region us-east-1)
  - scoping: tag service=payments
  - output: .culiops/service-discovery/payments-live-catalog.md
```

### For Step 4 (runtime profile) — to run after Step 3

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

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** _pending_

**Approval timestamp:** _pending_

**Operator notes (optional):** _none_
