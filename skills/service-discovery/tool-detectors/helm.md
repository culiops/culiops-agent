---
name: helm
url: https://helm.sh
deploys: Kubernetes resources via templated charts
---

## File signatures
- `Chart.yaml` that is NOT under another chart's `charts/` directory (vendored subcharts are dependencies, not stacks)
- `templates/*.yaml` / `templates/*.yml`
- `values.yaml` (chart defaults)
- `values-<env>.yaml` (per-environment overrides — convention, not enforced)
- `requirements.yaml` (Helm 2 dependency file — legacy)
- Instance signals (they hold the values and chart version actually deployed):
  - `helmfile.yaml` (releases with `chart:`, `version:`, `values:`)
  - Argo CD `Application` (`spec.source.chart` / `spec.source.helm`)
  - Flux `HelmRelease` (`spec.chart`, `spec.values`, `spec.valuesFrom`)

## Stack boundary
One *chart* = one directory containing a `Chart.yaml` outside any other chart's `charts/`. One *instance* = one Helm release (one cluster + namespace + release name).

The base `values.yaml` is the chart's defaults — NOT an instance. An instance is a helmfile release, an Argo CD `Application`, a Flux `HelmRelease`, or (failing those) a `values-<env>.yaml` file the operator names.

## Secret-bearing files
- NEVER run `helm get values`, `helm get manifest` or any `helm get *` (they print release Secrets and merged values); NEVER run `sops -d`.
- Values files and helmfile `values:`: read key NAMES and non-secret values only. A value is withheld, recorded as `<set in <file>:<line>>`, when the key contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert`.
- `secrets*.yaml`, `*.sops.*`, `*.enc.*` and helm-secrets files are not opened at all; record the file name as a reference.
- Rendered `Secret` objects: record name and keys only, never `data` / `stringData` values.

## Parameter sources (highest to lowest priority)
- `--set key=value` and `--set-string key=value` on the CLI
- `--values <file>` / `-f <file>` (typically `values-<env>.yaml`), or the helmfile / `HelmRelease` / `Application` values
- `values.yaml` (chart defaults)
- Sub-chart values referenced via the parent's `values.yaml` (key path = sub-chart name)

Apply the Secret-bearing files rule to every source above.

## Resource extraction
- Rendering: `helm template` is allowed ONLY as a local, read-only render with the instance's values files; its output is projected before use (kind / name / namespace + non-secret fields; Secret objects names and keys only). `helm get *`, `helm install`, `helm upgrade`, `helm rollback` and `helm uninstall` are forbidden.
- If `helm template` is unavailable or not approved, extract statically from `templates/` and mark every `{{ }}`-dependent field unresolved.
- Each rendered Kubernetes resource → one inventory entry; raw type is `<apiVersion>/<kind>` (e.g., `apps/v1/Deployment`, `v1/Service`)
- `Chart.yaml` `dependencies:` (Helm 3) or `requirements.yaml` (Helm 2) → sub-chart references; chase only if the sub-chart is bundled in `charts/`
- `tpl` and `include` directives → resolve against the values being applied for the target instance (only when rendered)

## Naming pattern hints
Resource names commonly use `{{ include "<chart>.fullname" . }}` which evaluates to `<release-name>-<chart-name>` (or just `<release-name>` if it contains the chart name). Record the helper used and the resolved form.

## Typical cross-stack dependencies
- ConfigMaps and Secrets in the cluster (referenced by name in pod specs)
- ServiceAccounts and RBAC bindings (IRSA: `eks.amazonaws.com/role-arn` annotation)
- External secret stores via External Secrets Operator, sealed-secrets, or Vault Agent (record references, NEVER read)
- Persistent Volumes / StorageClasses provisioned outside the chart
- Ingress controller and cert-manager (cluster-wide infrastructure)
