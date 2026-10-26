**Pre-flight assessment for:** `notifyapi` / `prod`
**Action:** Increase replica count from 2 to 4
**Date:** 2026-04-24 10:30
**Commit:** `d4e5f6g`
**Target:** context `prod-cluster` / namespace `notifyapi-prod`
**Plan hash:** `sha256:9f2c4e…` (SHA-256 of the `helm diff upgrade` output assessed)
**Plan source:** `helm diff upgrade notifyapi . -f values-prod.yaml -n notifyapi-prod`
**Delivery model:** CI on merge
**Invoked by:** operator
**Assessor used:** iac-change
**Layers evaluated:** L1 (static) + L2 (human) + L3 (live)

## Verdict: GREEN — PROCEED

## Risk Scorecard

| # | Category | Score | Finding | Evidence | Mitigation |
|---|----------|-------|---------|----------|------------|
| 1 | Blast radius | 🟢 | Single deployment, single namespace. Scale-up only — no resource destruction. | `plan` (1 object changed: `Deployment/notifyapi`) | — |
| 2 | Reversibility | 🟢 | `helm rollback` or revert PR restores previous replica count within seconds. No one-way attributes. | `plan` (`replicas` only) | — |
| 3 | Change velocity | 🟢 | No changes to this chart on the default branch in the past 14 days. | `git log` | — |
| 4 | Dependency impact | 🟢 | No downstream consumers. Upstream SQS and SMTP unaffected by replica count. | `code:.culiops/service-discovery/notifyapi-prod.md` | — |
| 5 | Timing context | 🟢 | Business hours, no active incident, no traffic freeze. | `operator` (Q1–Q3) | — |
| 6 | Operator familiarity | 🟢 | Operator has deployed this chart multiple times. Replica scaling is routine. | `operator` (Q4–Q5) | — |
| 7 | Observability readiness | 🟢 | Deployment rollout observable via `kubectl rollout status`. Readiness probes configured. | `code:templates/deployment.yaml` | — |
| 8 | Cost impact | 🟢 | 2 additional pods at 250m/256Mi. Estimated monthly delta: ~$8 USD. | `code:values-prod.yaml` | — |
| 9 | Security posture | 🟢 | No IAM, network policy, secret, or image changes. | `plan` | — |
| 10 | Resource health | 🟢 | Deployment healthy (2/2 pods ready, 0 restarts). Nodes have room for 2 more pods at 250m/256Mi. | `live:2`, `live:3`, `live:4` | — |

## Evidence

| Fact | Code / plan | Live | Match |
|------|-------------|------|-------|
| Current replicas = 2 | `values-prod.yaml` `replicaCount: 2` | `live:2` 2/2 ready | ✓ |
| Requests 250m / 256Mi | `values-prod.yaml` | — | code-only (not needed live) |

No drift found.

## Hard Blocks

None.

## Acknowledged Risks

None.

## Mitigations Committed

None.

## Context Provided (L2)

- No active incidents. No deployment freeze. Not peak hours. (`operator`)
- Operator has deployed this chart many times; experienced with Helm. (`operator`)
- Expected cost impact: negligible. (`operator-stated`; L1 estimate agrees)

## L1 Analysis Detail

Scanned: `Chart.yaml` (`notifyapi` v1.2.0, appVersion 3.1.0), `values.yaml`, `values-prod.yaml`, `templates/deployment.yaml`. Catalog used: `.culiops/service-discovery/notifyapi-prod.md`. Git history: no commits to chart files on the default branch in 14 days.

## L3 Queries Run

Batch approved by the operator once.

1. `kubectl config current-context` → `prod-cluster` (matches target)
2. `kubectl get deploy/notifyapi -n notifyapi-prod -o jsonpath='{.status.readyReplicas}/{.spec.replicas}'` → `2/2`
3. `kubectl get pods -n notifyapi-prod -l app.kubernetes.io/name=notifyapi -o jsonpath=…restartCount…` → 0 restarts on both pods
4. `kubectl top nodes` → 3 nodes, CPU 31–44%, memory 38–52%
