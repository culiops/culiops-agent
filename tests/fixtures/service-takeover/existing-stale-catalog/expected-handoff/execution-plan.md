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
| AWS credentials | configured | env vars present | live |
| service-discovery catalog | **stale** | `.culiops/service-discovery/payments-catalog.md` | **14 days (generated-at 2026-04-28T15:00:00Z)** |
| runtime-trace profile | none | — | — |
| Tag scoping primitive | `service=payments` | provided by operator | n/a |

---

## Capability probe results

| Probe | Result |
|---|---|
| AWS access | ✓ alice verified in account 123456789012 |
| CloudTrail | ✓ available, ManagementEvents enabled in us-east-1 |
| Resource Explorer | ✓ view configured in us-east-1 |
| Cost Explorer | ✓ ce:GetCostAndUsage permitted |
| Existing catalog | detected — `.culiops/service-discovery/payments-catalog.md` (14 days old) |

---

## What we need (per planned step)

| Need | Source | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Architecture understanding (Step 2) | diagram images | none | proceed with `service-discovery` diagram extraction (image mode) | $0 | auto (diagrams present) |
| Resource enumeration from IaC | IaC repo | full | not applicable — IaC unavailable; real-discovery fills this | $0 | covered by Step 3 |
| Existing service-discovery catalog (Step 2) | `.culiops/service-discovery/payments-catalog.md` | **stale (14 days)** | **Options: (A) use as-is — skip re-run, accept 14-day-old data; (B) verify with thin re-scan — re-run resource enumeration only, merge with existing; (C) re-run from scratch — rename old catalog with timestamp suffix, run full service-discovery.** Operator selected: **re-run (C)**. Old catalog renamed to `payments-catalog.20260428-stale.md`. | $0 (read-only) | **operator selected C at Gate 1.5** |
| Live resource enumeration (Step 3) | AWS APIs | full | run `service-discovery` real-discovery mode against account 123456789012 in us-east-1 | $0 (read-only) | **needed** |
| Cross-region inventory | Resource Explorer | none | covered by runtime-trace Step 4 (RE available) | $0 | covered |
| Activity baseline + control-plane events (Step 4) | CloudWatch + CloudTrail + CE | full | run `runtime-trace` with scoping primitive `tag:service=payments` | ~$0.04 (Cost Explorer charges) | **needed** |
| CloudTrail availability | CloudTrail API | resolved | probe confirmed ManagementEvents enabled | $0 | resolved |
| Resource Explorer availability | RE API | resolved | probe confirmed view configured | $0 | resolved |
| Tribal knowledge (Step 5) | Outgoing team (Pay Team) | full | emit questionnaire; share with Pay Team via Slack | $0 | proceeds at Step 5 |
| Readiness assessment (Step 6) | All prior artifacts | full | auto-mark from artifacts; manual on un-evidenceable items | $0 | proceeds at Step 6 |
| Handoff package (Step 7) | All prior artifacts | full | assemble README + snapshots | $0 | proceeds at Step 7 |

---

## Proposed invocations

### For Step 2 (diagram extraction) — to run after this plan is approved

```
Invoke service-discovery with:
  - mode: real-discovery (image mode)
  - inputs: ~/handoff/payments-arch.png, ~/handoff/payments-flows.png
  - scoping: tag service=payments
  - output: .culiops/service-discovery/payments-diagrams-catalog.md
```

Note: old catalog preserved as `.culiops/service-discovery/payments-catalog.20260428-stale.md` per operator re-run choice.

### For Step 3 (live discovery) — to run after Step 2

```
Invoke service-discovery with:
  - mode: real-discovery
  - inputs: AWS live APIs (account 123456789012, region us-east-1)
  - scoping: tag service=payments
  - output: .culiops/service-discovery/payments-live-catalog.md (merge with diagrams catalog)
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

---

## Approval block

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** approved

**Approval timestamp:** 2026-05-12T14:10:00Z

**Operator notes:** "Proceed as proposed. Re-run service-discovery from scratch — 14-day-old catalog is too stale for a takeover. Cost Explorer access confirmed. Share questionnaire with Bob (bob@example.com) at Step 5."
