# Examples: Kubernetes CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer for in-cluster Kubernetes workloads. This file is orthogonal to the cloud provider — use it alongside `aws.md`, `gcp.md`, or `azure.md` when the change targets Kubernetes resources.

Replace placeholders (`{namespace}`, `{deploy}`, `{service}`, `{pod}`, etc.) with values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** `kubectl` (>= 1.28 recommended). `helm` (>= 3.12) if change is Helm-based.

**Authentication:** depends on cluster provider:
- EKS: `aws eks update-kubeconfig --name {cluster} --region {region}`
- GKE: `gcloud container clusters get-credentials {cluster} --zone {zone} --project {project}`
- AKS: `az aks get-credentials --name {cluster} --resource-group {rg}`
- On-prem: kubeconfig file (`KUBECONFIG` or `~/.kube/config`)

Confirm access: `kubectl auth can-i list pods -n {namespace}`

**Least-privilege RBAC — every command below is read-only.** The built-in `view` ClusterRole is sufficient. Never use `cluster-admin` for pre-flight checks.

**Metrics-server required for `kubectl top`.** If not installed, CPU/memory checks will fail — note in report and proceed.

---

## Resource Health Checks

### Deployments / StatefulSets / DaemonSets

- Status: `kubectl get deploy/{deploy} -n {namespace} -o wide`
- Rollout status: `kubectl rollout status deploy/{deploy} -n {namespace} --timeout=5s`
- Replica health: `kubectl get deploy/{deploy} -n {namespace} -o jsonpath='{.status.readyReplicas}/{.spec.replicas}'`
- Recent rollout history: `kubectl rollout history deploy/{deploy} -n {namespace}`

### Pods

- Pod status: `kubectl get pods -n {namespace} -l app={service} -o wide`
- Restart counts: `kubectl get pods -n {namespace} -l app={service} -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.restartCount}{"\t"}{end}{"\n"}{end}'`
- CPU/memory usage: `kubectl top pods -n {namespace} -l app={service}`
- OOMKilled detection: `kubectl get pods -n {namespace} -l app={service} -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.lastState.terminated.reason}{"\t"}{end}{"\n"}{end}'`
- Recent events: `kubectl get events -n {namespace} --field-selector involvedObject.name={pod} --sort-by='.lastTimestamp'`

### Services / Ingress

- Service endpoints: `kubectl get endpoints/{service} -n {namespace}`
- Ingress status: `kubectl get ingress -n {namespace} -o wide`

### HPA (Horizontal Pod Autoscaler)

- Current status: `kubectl get hpa -n {namespace} -o wide`
- Target utilization vs actual: `kubectl describe hpa/{hpa} -n {namespace}`

### Nodes

- Node status: `kubectl get nodes -o wide`
- Node resource usage: `kubectl top nodes`
- Node conditions: `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.conditions[?(@.status=="True")]}{.type}{" "}{end}{"\n"}{end}'`

---

## Observability Checks

### Prometheus (if available)

- Current error rate: `kubectl exec -n {prometheus-ns} {prometheus-pod} -- curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{service="{service}",code=~"5.."}[5m])'`
- Current request rate: `kubectl exec -n {prometheus-ns} {prometheus-pod} -- curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{service="{service}"}[5m])'`
- SLO burn rate (if configured): `kubectl exec -n {prometheus-ns} {prometheus-pod} -- curl -s 'http://localhost:9090/api/v1/query?query=slo:burn_rate:5m{service="{service}"}'`

### Alerts

- Currently firing alerts: `kubectl exec -n {prometheus-ns} {prometheus-pod} -- curl -s 'http://localhost:9090/api/v1/alerts' | jq '.data.alerts[] | select(.state=="firing")'`

---

## Timing Context Checks

### Recent Changes

- Recent deployments: `kubectl rollout history deploy/{deploy} -n {namespace} | tail -5`
- Helm release history: `helm history {release} -n {namespace} --max 5`
- Recent namespace events: `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -20`
