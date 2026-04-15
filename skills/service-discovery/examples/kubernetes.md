# Examples: Kubernetes & Helm CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the stack is Kubernetes and/or Helm. Use this file in any of these cases — the cluster's hosting location is orthogonal:

- **On-prem / self-managed** Kubernetes (kubeadm, Rancher/RKE, OpenShift, k3s, Talos, bare-metal).
- **Managed** Kubernetes (EKS / GKE / AKS) — use this file **alongside** the matching cloud examples file. The cloud file covers the control-plane / node-pool / cloud-integration commands (`aws eks describe-cluster`, `gcloud container clusters describe`, `az aks show`); this file covers everything inside the cluster once `kubectl` is wired up.
- **Helm releases** deployed anywhere — this file is the source of truth for Helm commands.

Replace placeholders (`{namespace}`, `{deployment}`, `{release}`, etc.) with the values resolved in Step 2.

## Prerequisites

**CLI tools:** `kubectl` (≥ 1.28 recommended — keep within the [±1 minor version skew](https://kubernetes.io/releases/version-skew-policy/) of the cluster's control plane). `helm` (≥ 3.12) if Helm is in scope. Optional but useful: `stern` (multi-pod log tailing), `kubectx`/`kubens` (context and namespace switching).

**Authentication:** `kubectl` reads `~/.kube/config` by default (override with `KUBECONFIG` env var). For on-prem clusters, the kubeconfig typically comes from the cluster admin (client-cert + embedded CA, or an OIDC provider). For managed clusters it comes from the cloud CLI:

- EKS: `aws eks update-kubeconfig --name {cluster} --region {region}`
- GKE: `gcloud container clusters get-credentials {cluster} --region {region}`
- AKS: `az aks get-credentials --name {cluster} --resource-group {rg}`

Before running anything, confirm the active context so you don't act on the wrong cluster:

```
kubectl config current-context
kubectl config get-contexts
kubectl auth can-i --list --namespace={namespace}
```

**Least-privilege Kubernetes RBAC — every command below is read-only.** Kubernetes RBAC is orthogonal to cloud IAM; on managed clusters you may need both (IAM to reach the API server, RBAC to do anything once inside). Grant the operator either:

- **Baseline (simplest):** the built-in `view` `ClusterRole` bound at the relevant namespace(s) via a `RoleBinding`, or cluster-wide via a `ClusterRoleBinding` if multiple namespaces are in scope. Covers `get`/`list`/`watch` on the standard resource kinds the runbooks reference.
- **Tighter (recommended):** a custom `Role` listing only the resource kinds + verbs actually needed (`deployments`, `statefulsets`, `pods`, `pods/log`, `services`, `ingresses`, `events`, `configmaps`, `horizontalpodautoscalers`, `persistentvolumeclaims`, `jobs`, `cronjobs` + verbs `get`/`list`/`watch`).
- **Secrets are *not* included in the `view` role by design.** If a runbook step needs Secret metadata, bind a separate tighter Role that grants `get`/`list` on `secrets` in the specific namespace only, with explicit team approval.
- **Never use `cluster-admin`, `admin`, or `edit`** for read-only investigation — those include write verbs on the whole API surface.
- On managed clusters, bind the RBAC subject to the IAM principal using the cluster's aws-auth ConfigMap (EKS), Google group sync (GKE), or Azure AD group (AKS).

**Mutations are flagged inline.** Most commands here are read-only. State-changing commands (any `kubectl scale|rollout restart|rollout undo|apply|delete|edit|patch|replace|drain|cordon`, `helm install|upgrade|rollback|uninstall`, `argocd app sync|rollback`, `flux suspend|resume|reconcile`) are labeled explicitly. `kubectl exec` and `kubectl port-forward` are *not* technically mutations but give direct pod access and expose local ports — treat them as sensitive: label, justify, and require approval. **Never run a mutation without explicit team approval and an elevated role.**

**Cost awareness:** `kubectl` calls to the API server are free, but the *observability backend* the cluster forwards to is often metered — Prometheus/Grafana/Loki self-hosted is free; Grafana Cloud, Amazon Managed Prometheus, Azure Managed Prometheus, and GCP Managed Service for Prometheus all meter query volume. Check with the platform team which backend is in use before running large time-range queries.

---

## How to use this file

Each section maps one Kubernetes/Helm resource category to status/config + the four golden signals where applicable. On-prem clusters rely on what's installed — `kubectl top` needs [metrics-server](https://github.com/kubernetes-sigs/metrics-server); rich metrics need Prometheus + Grafana; logs need a backend (Loki, ELK, OpenSearch, or the cloud-managed equivalent). If the cluster lacks these, note the gap in the runbook and fall back to `kubectl describe` / `kubectl get events` / `kubectl logs`.

---

## Cluster & Nodes

- Cluster info: `kubectl cluster-info`
- Control-plane health: `kubectl get --raw /healthz` / `kubectl get --raw /readyz?verbose`
- Nodes list: `kubectl get nodes -o wide`
- Node details: `kubectl describe node {node}`
- Node resource pressure (CPU/memory/disk/PID): visible in `kubectl describe node` → `Conditions`
- Node CPU / memory usage: `kubectl top nodes` (requires metrics-server)
- API server version: `kubectl version`

## Namespaces

- List namespaces: `kubectl get ns`
- Namespace details: `kubectl describe ns {namespace}`
- Resource quotas: `kubectl get resourcequota -n {namespace}` / `kubectl describe resourcequota -n {namespace}`
- Limit ranges: `kubectl get limitrange -n {namespace} -o yaml`

## Workloads (Deployments / StatefulSets / DaemonSets)

- List: `kubectl get deploy,sts,ds -n {namespace}`
- Deployment details: `kubectl describe deploy/{deployment} -n {namespace}`
- StatefulSet details: `kubectl describe sts/{statefulset} -n {namespace}`
- Rollout status: `kubectl rollout status deploy/{deployment} -n {namespace}`
- Rollout history: `kubectl rollout history deploy/{deployment} -n {namespace}`
- Replica count & readiness: `kubectl get deploy/{deployment} -n {namespace} -o wide`
- Full spec (yaml): `kubectl get deploy/{deployment} -n {namespace} -o yaml`

## Jobs & CronJobs

- List: `kubectl get jobs,cronjobs -n {namespace}`
- CronJob schedule & history: `kubectl describe cronjob/{cronjob} -n {namespace}`
- Completed / failed jobs: `kubectl get jobs -n {namespace} --field-selector status.successful=1` / `status.successful=0`

## Pods

- List: `kubectl get pods -n {namespace} -o wide`
- By label (e.g., owning service): `kubectl get pods -n {namespace} -l app={service}`
- Pod details (status, events, restart count, conditions, containers): `kubectl describe pod/{pod} -n {namespace}`
- Pending / failed pods: `kubectl get pods -n {namespace} --field-selector status.phase=Pending` / `=Failed`
- Per-pod CPU / memory: `kubectl top pods -n {namespace}` (requires metrics-server)
- Per-container resources (requests/limits): in `kubectl describe pod` → `Containers:` block

## Services, Endpoints & Ingress

- Services: `kubectl get svc -n {namespace}`
- Service details: `kubectl describe svc/{service} -n {namespace}`
- Endpoints (what the service is actually routing to): `kubectl get endpoints {service} -n {namespace}`
- EndpointSlice (newer API): `kubectl get endpointslices -n {namespace} -l kubernetes.io/service-name={service}`
- Ingresses: `kubectl get ingress -n {namespace}` / `kubectl describe ingress/{ingress} -n {namespace}`
- Ingress class & controller: `kubectl get ingressclass`

## ConfigMaps & Secrets

- ConfigMaps: `kubectl get cm -n {namespace}` / `kubectl get cm/{configmap} -n {namespace} -o yaml`
- Secrets (**metadata only; don't dump values unless required + approved**): `kubectl get secret -n {namespace}` / `kubectl describe secret/{secret} -n {namespace}`
- Secret value fetch (sensitive — treat as mutation-adjacent): `kubectl get secret/{secret} -n {namespace} -o jsonpath='{.data.{key}}' | base64 -d` — requires explicit team approval.

## Autoscaling (HPA / VPA)

- HPAs: `kubectl get hpa -n {namespace}`
- HPA details (current vs. target metric, min/max replicas): `kubectl describe hpa/{hpa} -n {namespace}`
- VPAs (if installed): `kubectl get vpa -n {namespace}` / `kubectl describe vpa/{vpa} -n {namespace}`

## Persistent Storage (PV / PVC / StorageClass)

- PVCs in namespace: `kubectl get pvc -n {namespace}`
- PVC details (bound PV, size, storage class): `kubectl describe pvc/{pvc} -n {namespace}`
- PVs (cluster-scoped): `kubectl get pv`
- StorageClasses: `kubectl get storageclass`

## Events

- Namespace events sorted by most recent: `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`
- Events for a specific object: `kubectl describe {kind}/{name} -n {namespace}` (bottom of the output)
- Cluster-wide events: `kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -50`

## Logs

- Pod logs (single container): `kubectl logs {pod} -n {namespace}`
- Multi-container pod: `kubectl logs {pod} -c {container} -n {namespace}`
- Previous instance (if pod restarted): `kubectl logs {pod} -n {namespace} --previous`
- Follow: `kubectl logs -f {pod} -n {namespace}` — **label as interactive; don't chain into the next step**
- By label across pods: `kubectl logs -n {namespace} -l app={service} --tail=200`
- Multi-pod tailing: `stern {service} -n {namespace} --since 15m` (if `stern` installed)

## Metrics (on-cluster Prometheus)

- `kubectl top` works if metrics-server is installed. For deeper signals the cluster needs Prometheus. Common patterns:
  - Port-forward to the Prometheus service: `kubectl port-forward -n monitoring svc/prometheus 9090:9090` — **opens a local port; label as interactive and approve before running**
  - Then query via the UI at `http://localhost:9090` or via `curl 'http://localhost:9090/api/v1/query?query=...'`
- Typical PromQL signals (adjust label selectors to your cluster's conventions):
  - Request rate (histogram): `sum(rate(http_requests_total{namespace="{namespace}",service="{service}"}[5m]))`
  - p99 latency: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="{namespace}",service="{service}"}[5m])) by (le))`
  - Error rate: `sum(rate(http_requests_total{namespace="{namespace}",service="{service}",code=~"5.."}[5m]))`
  - Pod CPU saturation: `sum(rate(container_cpu_usage_seconds_total{namespace="{namespace}",pod=~"{service}-.*"}[5m])) by (pod)`

## Helm

- List releases in namespace: `helm list -n {namespace}`
- All releases across namespaces: `helm list -A`
- Release status (revision, notes, last deployed): `helm status {release} -n {namespace}`
- Rendered manifests for a release: `helm get manifest {release} -n {namespace}`
- Resolved values: `helm get values {release} -n {namespace}` (add `-a` / `--all` for computed defaults)
- Release history (rollback candidates): `helm history {release} -n {namespace}`
- Release hooks & notes: `helm get hooks {release} -n {namespace}` / `helm get notes {release} -n {namespace}`
- Chart source (if the chart is a dependency in the repo): inspect `Chart.yaml` and `charts/` subdir

## GitOps (ArgoCD / Flux)

If the cluster is managed by ArgoCD or Flux, the **desired state** lives in Git, not in `helm`/`kubectl apply`. Inspect both the GitOps controller and the cluster state.

- ArgoCD: `argocd app list` / `argocd app get {app}` / `argocd app history {app}` (requires ArgoCD CLI + login)
- ArgoCD in-cluster (no CLI): `kubectl get applications -n argocd` / `kubectl describe application/{app} -n argocd`
- Flux: `flux get kustomizations -A` / `flux get helmreleases -A`
- Flux per-resource: `flux describe kustomization/{name} -n {namespace}` / `flux describe helmrelease/{name} -n {namespace}`

## Ingress controllers & service mesh

Common on-prem / portable choices. Use whichever is actually installed; grep the cluster for CRDs (`kubectl get crd | grep -E 'istio|linkerd|traefik|ambassador|contour'`).

- ingress-nginx logs: `kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=200`
- Traefik dashboard / routes: `kubectl describe ingressroute -A` (Traefik CRDs) or `kubectl get ingress -A`
- Istio: `istioctl proxy-status` / `istioctl analyze -n {namespace}`
- Linkerd: `linkerd check` / `linkerd viz stat deploy -n {namespace}`
- cert-manager: `kubectl get certificate,certificaterequest,order,challenge -n {namespace}` / `kubectl describe certificate/{cert} -n {namespace}`

## Common mutations (FLAGGED — require approval)

Listed here so runbooks can reference a known mutation by name. **Each is `MUTATION — requires explicit approval`; runbook must state blast radius and elevated permission inline.**

- `kubectl scale deploy/{deployment} --replicas={n}` — changes capacity
- `kubectl rollout restart deploy/{deployment}` — rolls all pods
- `kubectl rollout undo deploy/{deployment} --to-revision={n}` — reverts to prior version
- `kubectl delete pod/{pod}` — evicts a single pod (blast radius usually small, but approve)
- `kubectl drain {node}` — evicts all pods from a node
- `kubectl cordon {node}` / `uncordon {node}` — pause/resume scheduling
- `kubectl apply -f ...` / `kubectl edit ...` / `kubectl patch ...` — any spec change
- `helm upgrade {release} {chart} -f values.yaml` — rolls a release
- `helm rollback {release} {revision}` — reverts a release
- `helm uninstall {release}` — deletes a release
- `argocd app sync {app}` / `argocd app rollback {app} {revision}` — GitOps sync/rollback
- `flux suspend` / `flux resume` / `flux reconcile` — pause or force reconciliation

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{namespace}` | Kubernetes namespace | `widgetapi-prod` |
| `{deployment}`, `{statefulset}`, `{daemonset}`, `{cronjob}`, `{job}` | Workload name | `widgetapi-web` |
| `{pod}` | Pod name | `widgetapi-web-7d9b-x7k2p` |
| `{service}`, `{ingress}`, `{hpa}`, `{vpa}`, `{pvc}`, `{configmap}`, `{secret}`, `{cert}` | Resource names | `widgetapi-web` |
| `{container}` | Container name inside a multi-container pod | `app` |
| `{release}` | Helm release name | `widgetapi` |
| `{chart}` | Helm chart (repo/name or local path) | `bitnami/postgresql` |
| `{node}` | Node name | `ip-10-0-1-42.ec2.internal` |
| `{context}` | kubeconfig context | `prod-eu-west-1` |
| `{cluster}` | Cluster name (from cloud side, if managed) | `widgetapi-prod` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
