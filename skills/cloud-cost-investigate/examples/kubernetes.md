# Kubernetes — cloud-cost-investigate examples

Read-only commands per workflow step. All commands use `get`, `describe`, `top`, `logs`, `port-forward`, or `config` only — no mutations, no `apply`, `create`, `delete`, `edit`, `patch`, `replace`, `scale`, `rollout`, `cordon`, `drain`, `taint`, `label`, `annotate`, or `exec`.

**Prerequisite:** Kubernetes cost investigation requires either OpenCost or Kubecost to be installed in the cluster. Without one of these, the skill cannot report cost allocation and will flag the gap rather than proceed.

## Step 1 — Detect & Scope: cloud detection

```bash
# Detect current cluster context
kubectl config current-context

# Show full kubeconfig to identify cluster and namespace context
kubectl config view

# Detect whether OpenCost or Kubecost is installed in any namespace
kubectl get pods -A | grep -E 'opencost|kubecost'
```

**If neither OpenCost nor Kubecost is detected:** the skill MUST flag this gap explicitly and tell the operator:

> Kubernetes cost investigation requires OpenCost or Kubecost to be installed in the cluster. Neither was found. The skill cannot proceed with cost allocation analysis until one of these is deployed. This is an operator action — the skill does not install any software.

The skill stops at this point and does not attempt to install, configure, or enable anything.

**RBAC:** Any `kubectl`-authenticated principal with `get pods` permission in all namespaces (`--all-namespaces`).
**API cost:** none.

## Step 2A — Anomaly mode

### OpenCost — allocation API via port-forward

`kubectl port-forward` opens a local TCP tunnel to the in-cluster service. It does **not** mutate cluster state — no resources are created, modified, or deleted. It is a read-only proxy and acceptable under the Iron Law.

```bash
# Open a local proxy to the OpenCost service (runs in the foreground; use & to background)
kubectl port-forward -n opencost svc/opencost 9003:9003 &

# Total allocation by namespace, last 30 days (accumulate=true collapses to one row per namespace)
curl 'http://localhost:9003/allocation?window=30d&aggregate=namespace&accumulate=true'

# Daily time series by namespace (accumulate=false gives per-day rows)
curl 'http://localhost:9003/allocation?window=30d&aggregate=namespace&accumulate=false'

# Drill into a specific namespace
curl 'http://localhost:9003/allocation?window=30d&aggregate=pod&filterNamespaces=<namespace>&accumulate=true'
```

The OpenCost `/allocation` endpoint is a `GET`-only API. `curl` here issues HTTP GET requests — read-only.

**RBAC:** `port-forward` requires `pods/portforward` permission on the `opencost` namespace.
**API cost:** none (in-cluster query).

### Kubecost — allocation API

If Kubecost is installed and exposed via a service (with or without port-forward), the model allocation endpoint provides the same data shape.

```bash
# If Kubecost is accessible via port-forward:
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090 &

# Total allocation by namespace, last 30 days
curl 'http://localhost:9090/model/allocation?window=30d&aggregate=namespace&accumulate=true'

# Daily time series by namespace
curl 'http://localhost:9090/model/allocation?window=30d&aggregate=namespace&accumulate=false'

# If Kubecost is exposed via an ingress or LoadBalancer (replace with actual hostname):
curl 'http://kubecost.example/model/allocation?window=30d&aggregate=namespace&accumulate=true'
```

**Kubecost license caveat:** The free tier of Kubecost retains 15 days of data by default. Queries with `window` values beyond 15 days may return incomplete results unless a paid license is active. The skill MUST surface this caveat when the query window exceeds 15 days.

**RBAC:** `port-forward` requires `pods/portforward` permission on the `kubecost` namespace.
**API cost:** none (in-cluster query).

## Step 2B — Waste mode

### Idle workloads

```bash
# Pods sorted by CPU consumption (highest to lowest) — identify low-utilization candidates
kubectl top pods -A --sort-by=cpu

# Pods sorted by memory consumption
kubectl top pods -A --sort-by=memory

# Inspect declared resource requests for a specific pod (compare to top output above)
kubectl describe pod <pod-name> -n <namespace>

# List all pods with their resource requests across all namespaces
kubectl get pods -A -o json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['items']:
  ns = item['metadata']['namespace']
  name = item['metadata']['name']
  for c in item['spec'].get('containers', []):
    req = c.get('resources', {}).get('requests', {})
    print(f\"{ns}/{name}/{c['name']}: cpu={req.get('cpu','—')} mem={req.get('memory','—')}\")
"
```

Pods where `kubectl top` shows CPU/memory consistently below 10% of their declared `resources.requests` over a sustained period are flagged as idle candidates. The skill compares the `top` snapshot against `describe` output — it does not set any metrics baselines or modify any resource.

### Orphaned PVCs

```bash
# List all PersistentVolumeClaims across all namespaces with their status
kubectl get pvc -A

# Filter to PVCs in a specific status (Pending means unbound; Lost means backing PV is gone)
kubectl get pvc -A --field-selector=status.phase=Pending
kubectl get pvc -A --field-selector=status.phase=Lost

# Inspect a specific PVC
kubectl describe pvc <pvc-name> -n <namespace>
```

PVCs in `Pending` (never bound) or `Lost` (backing PV removed) status are flagged as orphaned. PVCs in `Bound` status that are not mounted by any pod are a secondary signal — the skill cross-references `kubectl get pods -A -o json` to identify those.

### Unattached PersistentVolumes

```bash
# List all PersistentVolumes with their reclaim policy and status
kubectl get pv

# PVs in Released status (were bound, PVC deleted, not yet reclaimed)
kubectl get pv --field-selector=status.phase=Released

# PVs in Available status (never bound to any PVC)
kubectl get pv --field-selector=status.phase=Available

# Inspect a specific PV for storage class, capacity, and timestamps
kubectl describe pv <pv-name>
```

PVs in `Released` or `Available` phase are incurring storage cost with no active workload consuming them. These are flagged as waste candidates.

**RBAC:** `kubectl top` requires the Metrics Server to be installed; `get pods`, `get pvc`, `get pv`, `describe` require standard read permissions.
**API cost:** none.

## Step 2C — Attribution mode

### OpenCost — cost filtered by label

```bash
# Ensure port-forward to OpenCost is active (see Step 2A)
kubectl port-forward -n opencost svc/opencost 9003:9003 &

# Cost for all workloads with label app=<service-name>, last 30 days
curl 'http://localhost:9003/allocation?window=30d&aggregate=label:app&filterLabels=app:<service-name>&accumulate=true'

# If the catalog uses a different label key (e.g. service=<name>):
curl 'http://localhost:9003/allocation?window=30d&aggregate=label:service&filterLabels=service:<service-name>&accumulate=true'

# Drill by pod within the service label
curl 'http://localhost:9003/allocation?window=30d&aggregate=pod&filterLabels=app:<service-name>&accumulate=true'
```

The skill reads the catalog (`.culiops/service-discovery/`) to determine which Kubernetes namespaces and labels map to the target service, then uses those values as filter parameters.

### Kubecost — cost filtered by label

```bash
# Ensure port-forward to Kubecost is active (see Step 2A)
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090 &

# Cost by label, last 30 days
curl 'http://localhost:9090/model/allocation?window=30d&aggregate=label:app&filterLabels=app:<service-name>&accumulate=true'
```

**RBAC:** Same as Step 2A port-forward requirements.
**API cost:** none (in-cluster query).

## Step 5 — Verification (shared)

No mutation occurs, so verification is just re-reading the report file before commit:

```bash
# Operator inspects the report draft
cat .culiops/cloud-cost-investigate/<scope-slug>-<mode>-<YYYYMMDD-HHmm>.md
```

## Iron Law reminders

- `kubectl` has many mutating verbs — `apply`, `create`, `delete`, `edit`, `patch`, `replace`, `scale`, `rollout`, `cordon`, `drain`, `taint`, `label`, `annotate`. The skill MUST refuse all of these. Permitted verbs are `get`, `describe`, `top`, `logs`, `port-forward`, and `config view`/`config current-context` only.
- `kubectl port-forward` is a read-only local proxy. It opens a TCP tunnel to an in-cluster service and does not create, modify, or delete any Kubernetes resource. It is permitted under the Iron Law. The tunnel should be closed when the investigation is complete.
- Kubecost free-tier retains only 15 days of allocation data by default. Before querying with a window longer than 15 days, the skill MUST surface this caveat and confirm with the operator whether a paid license is active.
- If neither OpenCost nor Kubecost is installed, the skill MUST stop and flag the gap. It does NOT install or configure any software — that is an operator action.
- `kubectl exec` is explicitly out of scope. Even in read-only usage (e.g. `kubectl exec -- cat /proc/meminfo`), exec is not a permitted verb in this skill.
