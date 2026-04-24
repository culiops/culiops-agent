# helm-config-update — iac-change-execution fixture

A single-phase Helm values change: increase the replica count for `notifyapi` from 2 to 4 in the prod environment.

## What's modelled

`notifyapi` — a fictional Kubernetes notification service running on EKS in `ap-southeast-1`. A service catalog entry and a pre-flight record both exist under `.culiops/`.

## The proposed change

Update `values-prod.yaml`: change `replicaCount` from `2` to `4`. No other values are modified.

## What this fixture exercises

- **Helm tool support:** skill detects `Chart.yaml` and recognises this as a Helm-managed service (not Terraform)
- **Catalog consumption:** `.culiops/service-discovery/notifyapi-prod.md` exists; skill reads it for upstream dependencies and naming pattern
- **Pre-flight record reuse:** `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md` exists with a Green verdict for this exact change; skill REUSES it rather than re-invoking `pre-flight`
- **Values file targeting:** skill modifies `values-prod.yaml` (not `values.yaml`) because `values-prod.yaml` holds env-specific overrides
- **PR path (default):** no direct-apply override; skill produces a PR

## Files in this fixture

| File | Purpose |
|------|---------|
| `Chart.yaml` | Helm chart metadata |
| `values.yaml` | Base defaults (replicaCount: 1) |
| `values-prod.yaml` | Prod overrides (replicaCount: 2 — the value to be changed) |
| `templates/deployment.yaml` | Deployment template |
| `templates/configmap.yaml` | ConfigMap template |
| `templates/service.yaml` | Service template |
| `.culiops/service-discovery/notifyapi-prod.md` | Service catalog entry |
| `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md` | Existing Green pre-flight record |
| `DRY-RUN-NOTES.md` | Expected skill behaviour |
