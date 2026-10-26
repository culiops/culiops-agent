# Examples: Kubernetes CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer for in-cluster Kubernetes workloads. Use it alongside `aws.md` when the cluster is EKS, or on its own for any other conformant cluster.

Replace placeholders (`{namespace}`, `{deploy}`, `{selector}`, `{pod}`, etc.) with values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** `kubectl` (>= 1.28 recommended). `helm` (>= 3.12) if change is Helm-based. `argocd` / `flux` CLI if delivery is GitOps.

**Authentication:**
- EKS: `aws eks update-kubeconfig --name {cluster} --region {region}` (run the `aws.md` target check first)
- Other clusters: kubeconfig file (`KUBECONFIG` or `~/.kube/config`)

Confirm access: `kubectl auth can-i list pods -n {namespace}`

**Least-privilege RBAC.** The built-in `view` ClusterRole covers every command below **except the ones marked "beyond `view`"**. `view` deliberately cannot read Secrets, `exec` into pods, port-forward, or proxy to services. Never use `cluster-admin` for pre-flight checks. A command marked "beyond `view`" is shown to the operator with the extra permission it needs; the operator decides, and it is never the default.

**Secrets:** never run `kubectl get secret -o yaml`, `helm get values --all`, `helm get manifest`, or `helm diff --show-secrets`. `kubectl get deploy -o yaml` can contain inline `env[].value` secrets — use `jsonpath` for the fields you need.

**Metrics-server required for `kubectl top`.** If not installed, CPU/memory checks will fail — note in report and proceed.

---

## Target Check (run first)

The live context must match the target recorded in Step 1. If it doesn't, stop L3.

- Context: `kubectl config current-context`
- API server: `kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'` → must be the plan's cluster
- Namespace exists: `kubectl get namespace {namespace}`

## Find the workload's own labels

Don't assume an `app=` label convention. Read the selector from the workload and use it as `{selector}`:

- `kubectl get deploy/{deploy} -n {namespace} -o jsonpath='{.spec.selector.matchLabels}'` → a JSON map; turn it into `key=value,key=value` for `-l`
- Same for `statefulset/{name}` / `daemonset/{name}`

---

## Resource Health Checks

### Deployments / StatefulSets / DaemonSets

- Status: `kubectl get deploy/{deploy} -n {namespace} -o wide`
- Rollout status: `kubectl rollout status deploy/{deploy} -n {namespace} --timeout=5s` (non-zero exit while a rollout is in progress — that is itself a signal)
- Replica health: `kubectl get deploy/{deploy} -n {namespace} -o jsonpath='{.status.readyReplicas}/{.spec.replicas}'`
- Recent rollout history: `kubectl rollout history deploy/{deploy} -n {namespace}`

### Pods

- Pod status: `kubectl get pods -n {namespace} -l {selector} -o wide`
- Restart counts: `kubectl get pods -n {namespace} -l {selector} -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.restartCount}{"\t"}{end}{"\n"}{end}'`
- CPU/memory usage: `kubectl top pods -n {namespace} -l {selector}`
- OOMKilled detection: `kubectl get pods -n {namespace} -l {selector} -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.lastState.terminated.reason}{"\t"}{end}{"\n"}{end}'`
- Recent events: `kubectl get events -n {namespace} --field-selector involvedObject.name={pod} --sort-by='.lastTimestamp'`

### Services / Ingress

- Service endpoints: `kubectl get endpointslices -n {namespace} -l kubernetes.io/service-name={service}`
- Ingress status: `kubectl get ingress -n {namespace} -o wide`

### HPA (Horizontal Pod Autoscaler)

- Current status: `kubectl get hpa -n {namespace} -o wide`
- Target utilization vs actual: `kubectl describe hpa/{hpa} -n {namespace}`

### PodDisruptionBudget

- Allowed disruptions: `kubectl get pdb -n {namespace}` (0 allowed → a rollout or node drain will stall)

### Nodes

- Node status: `kubectl get nodes -o wide`
- Node resource usage: `kubectl top nodes`
- Node conditions: `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.conditions[?(@.status=="True")]}{.type}{" "}{end}{"\n"}{end}'`

---

## Reversibility Checks

- PVCs and their storage class: `kubectl get pvc -n {namespace}`
- Can the volume be expanded / is reclaim `Delete`: `kubectl get storageclass {sc} -o jsonpath='{.allowVolumeExpansion}{"\t"}{.reclaimPolicy}'` (`Delete` → deleting the PVC deletes the data)
- Objects Helm will keep on uninstall: look for `helm.sh/resource-policy: keep` in the chart templates (L1, code)

---

## Observability Checks

### Prometheus (if available)

Query Prometheus over its HTTP API from wherever the operator can reach it (`$PROM_URL` = the Prometheus or Thanos / Mimir query endpoint, often behind Grafana or an internal ingress). Metric and recording-rule names below are examples — adapt them to the names your stack uses (the service-discovery catalog may list them).

- Current error rate: `curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=sum(rate(http_requests_total{service="{service}",code=~"5.."}[5m]))'`
- Current request rate: `curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=sum(rate(http_requests_total{service="{service}"}[5m]))'`
- Same hour last week (baseline): add `offset 1w` inside the `rate(...)` selector
- SLO burn rate (if configured): `curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=slo:burn_rate:5m{service="{service}"}'`

If Prometheus is reachable only from inside the cluster: `kubectl port-forward` needs `pods/portforward` and `kubectl exec` needs `pods/exec` — both **beyond `view`** (exec is a shell in the pod). Show the operator what's needed; don't request it by default.

### Alerts

- Currently firing alerts: `curl -s "$PROM_URL/api/v1/alerts" | jq '.data.alerts[] | select(.state=="firing")'`
- Or from Alertmanager: `amtool alert query --alertmanager.url="$AM_URL"`

---

## GitOps Checks (Argo CD / Flux)

- Argo CD app sync + health: `argocd app get {app} -o json | jq '{sync:.status.sync.status, health:.status.health.status, autoSync:.spec.syncPolicy.automated}'` (`automated.prune: true` → objects removed from git are deleted)
- Argo CD live diff: `argocd app diff {app}`
- Flux: `flux get kustomizations -A` / `flux get helmreleases -A` (ready, suspended, last applied revision)

---

## Timing Context Checks

### Recent Changes

- Recent deployments: `kubectl rollout history deploy/{deploy} -n {namespace} | tail -5`
- Helm release history: `helm history {release} -n {namespace} --max 5` — **beyond `view`**: Helm stores releases in Secrets, so this needs `secrets` get/list in the namespace, which also exposes every other Secret there. Prefer the CI or GitOps deploy history; if the operator runs it, record only revision, status and date
- Recent namespace events: `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -20`
