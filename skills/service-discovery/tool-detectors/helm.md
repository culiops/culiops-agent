---
name: helm
url: https://helm.sh
deploys: Kubernetes resources via templated charts
---

## File signatures
- `Chart.yaml` (chart metadata — required for any chart)
- `templates/*.yaml` / `templates/*.yml`
- `values.yaml` (chart defaults)
- `values-<env>.yaml` (per-environment overrides — convention, not enforced)
- `requirements.yaml` (Helm 2 dependency file — legacy)

## Stack boundary
One *chart* = one directory containing a `Chart.yaml`. One *instance* = one Helm release (one `helm install`/`helm upgrade` invocation against one cluster + namespace + release name).

The base `values.yaml` is the chart's defaults — NOT an instance. Per-environment `values-<env>.yaml` files are the instance-multiplication mechanism in this skill's mental model.

## Parameter sources (highest to lowest priority)
- `--set key=value` and `--set-string key=value` on the CLI
- `--values <file>` / `-f <file>` (typically `values-<env>.yaml`)
- `values.yaml` (chart defaults)
- Sub-chart values referenced via the parent's `values.yaml` (key path = sub-chart name)

## Resource extraction
- Each rendered Kubernetes resource in `templates/` → one inventory entry; raw type is `<apiVersion>/<kind>` (e.g., `apps/v1/Deployment`, `v1/Service`, `networking.k8s.io/v1/Ingress`)
- `Chart.yaml` `dependencies:` (Helm 3) or `requirements.yaml` (Helm 2) → sub-chart references; chase only if the sub-chart is bundled in `charts/`
- `tpl` and `include` directives inside templates → resolve against the values being applied for the target instance

## Naming pattern hints
Resource names commonly use `{{ include "<chart>.fullname" . }}` which evaluates to `<release-name>-<chart-name>` (or just `<release-name>` if it contains the chart name). Record the helper used and the resolved form.

## Typical cross-stack dependencies
- ConfigMaps and Secrets in the cluster (referenced by name in pod specs)
- ServiceAccounts and RBAC bindings
- External secret stores via External Secrets Operator, sealed-secrets, or Vault Agent (record references, NEVER read)
- Persistent Volumes / StorageClasses provisioned outside the chart
- Ingress controller and cert-manager (cluster-wide infrastructure)
