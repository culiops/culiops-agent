**Pre-flight assessment for:** `notifyapi` / `prod`
**Action:** Increase replica count from 2 to 4
**Date:** 2026-04-24 10:30
**Commit:** `d4e5f6g`
**Assessor used:** iac-change
**Layers evaluated:** L1 (static) + L2 (human)

## Verdict: GREEN — PROCEED

## Risk Scorecard

| # | Category | Score | Finding | Mitigation |
|---|----------|-------|---------|------------|
| 1 | Blast radius | 🟢 | Single deployment, single namespace. Scale-up only — no resource destruction. | — |
| 2 | Reversibility | 🟢 | `helm rollback` or revert PR restores previous replica count within seconds. | — |
| 3 | Change velocity | 🟢 | No changes to this chart in the past 14 days. | — |
| 4 | Dependency impact | 🟢 | No downstream consumers. Upstream SQS and SMTP unaffected by replica count. | — |
| 5 | Timing context | 🟢 | Business hours, no active incident, no traffic freeze. | — |
| 6 | Operator familiarity | 🟢 | Operator has deployed this chart multiple times. Replica scaling is routine. | — |
| 7 | Observability readiness | 🟢 | Deployment rollout observable via `kubectl rollout status`. Readiness probes configured. | — |
| 8 | Cost impact | 🟢 | 2 additional pods at 250m/256Mi. Estimated monthly delta: ~$8 USD. | — |
| 9 | Security posture | 🟢 | No IAM, network policy, secret, or image changes. | — |
| 10 | Resource health | 🟢 | Deployment healthy (2/2 pods ready). Cluster has capacity for 4 replicas. | — |

## Hard Blocks

None.

## Acknowledged Risks

None.

## Mitigations Committed

None.

## Context Provided (L2)

- Helm chart: `notifyapi` v1.2.0, appVersion 3.1.0
- Namespace: `notifyapi-prod`
- Current replicas: 2 (from `values-prod.yaml`), target: 4
- Resource requests per pod: 250m CPU, 256Mi memory
- Cluster node pool: `general-4xl` (8 vCPU / 32 GiB per node, 3 nodes)
- Catalog: `.culiops/service-discovery/notifyapi-prod.md`
- No active incidents. No deployment freeze.

## L1 Analysis Detail

Scanned: `Chart.yaml`, `values.yaml`, `values-prod.yaml`, `templates/deployment.yaml`. Catalog used: `.culiops/service-discovery/notifyapi-prod.md`. Git history: no commits to chart files in 14 days.

## L3 Queries Run

L3 not requested.
