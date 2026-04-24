# Examples: Kubernetes CLI Templates for `iac-change-execution`

Reference command templates for the `iac-change-execution` skill when the target workloads are managed by Kubernetes tooling — Helm, Kustomize, or raw manifests. These templates apply regardless of where the cluster runs: EKS, GKE, AKS, or on-premises. Use alongside the matching cloud file (`aws.md`, `gcp.md`, `azure.md`) for cluster-level cloud operations.

Replace placeholders (`{namespace}`, `{release}`, `{chart}`, `{image-tag}`, `{values-file}`, etc.) with the values resolved in Step 1 research or detected from the plan output.

## Prerequisites

**CLI tools:**
- `kubectl` — must be within ±1 minor version of the cluster's Kubernetes version. Verify: `kubectl version --client`.
- `helm` >= 3.x for Helm-managed releases. Verify: `helm version`.
- `kustomize` for Kustomize-managed overlays (standalone CLI preferred over `kubectl kustomize`). Verify: `kustomize version`.

**Authentication (kubeconfig):** The operator must have a valid kubeconfig context pointing to the target cluster before running any command.

- EKS: `aws eks update-kubeconfig --name {cluster} --region {region}`
- GKE: `gcloud container clusters get-credentials {cluster} --region {region} --project {project}`
- AKS: `az aks get-credentials --name {cluster} --resource-group {rg}`
- On-premises / other: obtain kubeconfig from the cluster administrator.

Confirm active context: `kubectl config current-context`.

**Least-privilege RBAC — TWO tiers are required for this skill.**

- **Tier 1 (Steps 1 and 5 — read-only):** Kubernetes `ClusterRole` named `view` (built-in) bound to the operator's identity, or a namespace-scoped `Role` with `get`, `list`, `watch` on the relevant resource types. Never use `cluster-admin` or any `*` verb binding for read-only operations.
- **Tier 2 (Step 4 — mutation only):** a namespace-scoped `Role` or `ClusterRole` with only the `create`, `update`, `patch`, `delete` verbs on the specific resource types the change modifies (e.g., `deployments`, `configmaps`, `services`). Elevated binding must cover only the target namespace. Drop the elevated binding after the mutation completes.

**Helm releases:** Helm stores release metadata as Kubernetes Secrets in the target namespace. Read access to Secrets in that namespace is required for `helm status`, `helm get`, and `helm history`.

---

## Research Queries (Step 1 — Read-Only)

### Deployment — current config

- Deployment details: `kubectl get deploy {deploy} -n {namespace} -o yaml`
- Deployment summary: `kubectl describe deploy/{deploy} -n {namespace}`
- Deployment strategy: `kubectl get deploy {deploy} -n {namespace} -o jsonpath='{.spec.strategy}'`
- Replica count: `kubectl get deploy {deploy} -n {namespace} -o jsonpath='{.spec.replicas}'`

### Service and Ingress — current network config

- Service details: `kubectl get svc {service} -n {namespace} -o yaml`
- Ingress details: `kubectl get ingress {ingress} -n {namespace} -o yaml`
- Endpoints backing the service: `kubectl get endpoints {service} -n {namespace}`

### ConfigMap — current configuration

- ConfigMap contents: `kubectl get configmap {configmap} -n {namespace} -o yaml`
- List ConfigMaps in namespace: `kubectl get configmaps -n {namespace}`

### HPA — current autoscaling config

- HPA details: `kubectl get hpa {hpa} -n {namespace} -o yaml`
- HPA status (current vs min/max replicas): `kubectl describe hpa/{hpa} -n {namespace}`

### Current image — running version

- Current image in deployment: `kubectl get deploy {deploy} -n {namespace} -o jsonpath='{.spec.template.spec.containers[*].image}'`
- Pod images currently running: `kubectl get pods -n {namespace} -l app={service} -o jsonpath='{.items[*].spec.containers[*].image}'`

### Helm release — values and history

- Current release values: `helm get values {release} -n {namespace}`
- All values (including defaults): `helm get values {release} -n {namespace} --all`
- Release metadata and chart version: `helm status {release} -n {namespace}`
- Release history: `helm history {release} -n {namespace}`
- Rendered manifests for the current release: `helm get manifest {release} -n {namespace}`

---

## Verification Checks (Step 5 — Read-Only)

### Deployment rollout status — post-apply health

- Rollout status (blocks until complete or timeout): `kubectl rollout status deploy/{deploy} -n {namespace} --timeout=5m`
- Ready replicas vs desired: `kubectl get deploy {deploy} -n {namespace} -o jsonpath='{.status.readyReplicas}/{.spec.replicas}'`
- Rollout history: `kubectl rollout history deploy/{deploy} -n {namespace}`

### Pod status — individual pod health

- Pod list with status: `kubectl get pods -n {namespace} -l app={service} -o wide`
- Pod details (events, conditions): `kubectl describe pod/{pod} -n {namespace}`
- Recent events for namespace: `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`

### Helm release status — post-upgrade state

- Release status (expect `deployed`): `helm status {release} -n {namespace}`
- Manifest diff from previous revision: `helm diff revision {release} {prev-revision} {new-revision} -n {namespace}` (requires `helm-diff` plugin)

### Endpoints — traffic routing health

- Endpoint readiness (expect all addresses populated): `kubectl get endpoints {service} -n {namespace}`
- Ingress backend health: `kubectl describe ingress {ingress} -n {namespace}`

### Pod logs — error detection

- Recent logs for a pod: `kubectl logs {pod} -n {namespace} --tail=100`
- Logs filtered for errors: `kubectl logs {pod} -n {namespace} --tail=200 | grep -i error`
- Previous pod logs (if pod restarted): `kubectl logs {pod} -n {namespace} --previous --tail=100`

### Resource usage — saturation check

- Pod CPU and memory (requires metrics-server): `kubectl top pods -n {namespace} -l app={service}`
- Node resource usage: `kubectl top nodes`

---

## Apply Commands (Step 4c — MUTATION)

Each command below changes cluster state. The skill presents each command to the operator and waits for explicit approval before running. Assume Tier 2 elevated RBAC permissions are active.

### Helm — upgrade an existing release

**MUTATION** — `helm upgrade {release} {chart} -n {namespace} -f {values-file} --version {chart-version} --atomic --timeout 5m`
- Blast radius: all Kubernetes resources managed by the release (Deployments, Services, ConfigMaps, etc.); running pods in the namespace are restarted according to the deployment strategy.
- Elevated permission required: namespace-scoped `Role` with `create`, `update`, `patch`, `delete` on `deployments`, `services`, `configmaps`, and any other resource types the chart manages.
- Rollback path: `helm rollback {release} {prev-revision} -n {namespace}` — rolls back to the specified previous revision. `--atomic` flag auto-rolls back if the upgrade fails before `--timeout` elapses.
- Note: always run `helm diff upgrade {release} {chart} -f {values-file}` (Step 4a) and review before approving the upgrade.

### Helm — install a new release

**MUTATION** — `helm install {release} {chart} -n {namespace} -f {values-file} --version {chart-version} --create-namespace`
- Blast radius: new Kubernetes resources created by the chart; no existing resources are modified. Namespace is created if it does not exist (when `--create-namespace` is used).
- Elevated permission required: namespace-scoped `Role` (or `ClusterRole` if the chart creates cluster-scoped resources) with `create` on the resource types the chart installs.
- Rollback path: `helm uninstall {release} -n {namespace}` to remove the release entirely. Note: PersistentVolumeClaims are not deleted by `helm uninstall` by default.

### Kustomize — apply an overlay

**MUTATION** — `kubectl apply -k {overlay-path}`
- Blast radius: all resources in the Kustomize overlay; existing resources with matching names are patched in-place. Review `kubectl diff -k {overlay-path}` (Step 4a) before approving.
- Elevated permission required: namespace-scoped `Role` with `create`, `update`, `patch` on the resource types in the overlay (typically `deployments`, `configmaps`, `services`, `ingresses`).
- Rollback path: apply the previous version of the overlay (`kubectl apply -k {prev-overlay-path}`), or revert the overlay files in the repo and re-apply. No built-in rollback mechanism.

### Raw manifest — apply a single manifest

**MUTATION** — `kubectl apply -f {manifest-file} -n {namespace}`
- Blast radius: only the resources defined in the manifest file. Review `kubectl diff -f {manifest-file}` (Step 4a) before approving.
- Elevated permission required: namespace-scoped `Role` with `create`, `update`, `patch` on the specific resource types in the manifest.
- Rollback path: apply the previous version of the manifest (`kubectl apply -f {prev-manifest-file}`), or `kubectl delete -f {manifest-file}` to remove newly created resources. No built-in rollback for in-place updates.

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{namespace}` | Kubernetes namespace | `production` |
| `{deploy}` | Deployment name | `widgetapi-web` |
| `{service}` | Service name (and label selector value) | `widgetapi-web` |
| `{ingress}` | Ingress name | `widgetapi-web-ingress` |
| `{configmap}` | ConfigMap name | `widgetapi-config` |
| `{hpa}` | HorizontalPodAutoscaler name | `widgetapi-web-hpa` |
| `{pod}` | Pod name (from `kubectl get pods`) | `widgetapi-web-abc12-xyz34` |
| `{release}` | Helm release name | `widgetapi-web` |
| `{chart}` | Helm chart reference | `oci://registry.example.com/charts/widgetapi` |
| `{chart-version}` | Helm chart version | `1.4.2` |
| `{values-file}` | Path to Helm values file | `./helm/values-prod.yaml` |
| `{overlay-path}` | Path to Kustomize overlay directory | `./k8s/overlays/prod` |
| `{manifest-file}` | Path to a raw Kubernetes manifest | `./k8s/manifests/deployment.yaml` |
| `{image-tag}` | Container image tag | `sha256:abc123` or `v1.4.2` |
| `{prev-revision}` | Previous Helm revision number | `3` |
| `{new-revision}` | New Helm revision number | `4` |
| `{cluster}`, `{region}`, `{project}`, `{rg}` | Cloud-specific identifiers (see cloud examples file) | — |
