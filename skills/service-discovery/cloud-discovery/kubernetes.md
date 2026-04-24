---
name: kubernetes
identity-command: "kubectl config current-context && kubectl auth can-i get pods --all-namespaces"
---

## Prerequisites

**CLI tools:** `kubectl` (≥ 1.28 recommended). `helm` (≥ 3.12) if Helm releases are in scope.

**Authentication:** `kubectl` reads `~/.kube/config` by default. For managed clusters, obtain credentials via the cloud CLI (`aws eks update-kubeconfig`, `gcloud container clusters get-credentials`, `az aks get-credentials`). Confirm the active context before running anything:

```
kubectl config current-context
kubectl auth can-i get pods --all-namespaces
```

**Least-privilege RBAC — all queries below are read-only.** The operator needs:

- The built-in `view` ClusterRole bound at the relevant namespace(s) via a `RoleBinding`, or cluster-wide via a `ClusterRoleBinding` if the service's namespace is not yet known.

This covers `get`/`list`/`watch` on standard resource kinds. Secrets are excluded from the `view` role by design.

**Kubernetes discovery is orthogonal to cloud provider.** A service may run on EKS, GKE, AKS, or on-prem Kubernetes. Use this template alongside the matching cloud provider template (if any) to cover both the cluster-internal resources and the cloud-level resources (node groups, load balancers, managed databases, etc.).

## Broad discovery queries

### 1. By label (primary)

Label-based search is the most reliable way to find Kubernetes resources belonging to a service.

```
kubectl get all -n {namespace} -l app={service} -o json
```

Teams use different label key conventions. Try these common variations:

| Label key | Typical usage |
|-----------|---------------|
| `app` | Most common — set by Helm charts and many deployment tools |
| `app.kubernetes.io/name` | Kubernetes recommended label (from the [common labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/) convention) |
| `app.kubernetes.io/instance` | Helm release instance name |
| `service` | Explicit service label |
| `component` | Component within a larger service |

For each variation, substitute the label selector:

```
kubectl get all -n {namespace} -l app.kubernetes.io/name={service} -o json
```

### 2. By namespace

Many teams map one service to one namespace. If the namespace name matches the service, list everything in it:

```
kubectl get all -n {service} -o json
```

### 3. Broader resource types

`kubectl get all` only returns a subset of resource types (pods, services, deployments, replicasets, statefulsets, daemonsets, jobs, cronjobs). Many important resource types are missed. Query them explicitly:

```
kubectl get deploy,sts,ds,cronjob,job,svc,ing,cm,secret,sa,hpa,pdb,pvc \
  -n {namespace} -l app={service} -o json
```

Without a label selector (namespace-based fallback):

```
kubectl get deploy,sts,ds,cronjob,job,svc,ing,cm,secret,sa,hpa,pdb,pvc \
  -n {service} -o json
```

### 4. CRD-based resources

Clusters with monitoring, certificate management, or advanced ingress controllers have custom resources that `get all` never includes. Query these if the relevant CRDs exist:

```
kubectl get servicemonitor,prometheusrule -n {namespace} -l app={service} -o json 2>/dev/null
kubectl get certificate,certificaterequest -n {namespace} -l app={service} -o json 2>/dev/null
kubectl get ingressroute -n {namespace} -l app={service} -o json 2>/dev/null
```

Check which CRDs are installed first to avoid errors:

```
kubectl get crd | grep -E 'servicemonitor|prometheusrule|certificate|ingressroute'
```

### 5. Helm release discovery

If the service is deployed via Helm, the release name often matches the service name. Helm stores release metadata as Secrets in the release namespace.

```
helm list -n {namespace} --filter '{service}'
```

Once a release is found, extract its full manifest to identify all managed resources:

```
helm get manifest {release} -n {namespace}
```

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Label selector | `-l app={service}` or `-l app.kubernetes.io/name={service}` |
| Namespace | `-n {namespace}` — if unknown, use `-A` (all namespaces) with a label selector |
| Helm release | `helm list --filter '{service}'` — then `helm get manifest` for the full resource set |
| Field selector | `--field-selector metadata.name={service}` — exact match on resource name |

## Result parsing

Kubernetes API responses (JSON) map to resource hints as follows:

| API field | Maps to | Example |
|-----------|---------|---------|
| `metadata.name` | Resource name | `widgetapi-web` |
| `kind` | Resource type | `Deployment`, `Service`, `Ingress` |
| `metadata.namespace` | Namespace context | `widgetapi-prod` |
| `metadata.labels` | Additional context (app, version, chart) | `{app: "widgetapi", version: "1.2.3"}` |
| `metadata.annotations` | Deployment metadata (Helm release, last-applied-config) | `{meta.helm.sh/release-name: "widgetapi"}` |
| `spec` | Resource configuration (replicas, containers, ports, volumes) | Used during enrichment, not discovery |
