# Kubernetes — cloud-cost-investigate examples

Read-only commands per workflow step. All commands use `get`, `describe`, `top`, `logs`, `port-forward`, or `config` only — no mutations, no `apply`, `create`, `delete`, `edit`, `patch`, `replace`, `scale`, `rollout`, `cordon`, `drain`, `taint`, `label`, `annotate`, or `exec`.

**Prerequisite:** Kubernetes cost investigation requires either OpenCost or Kubecost to be installed in the cluster. Without one of these, the skill cannot report cost allocation and will flag the gap rather than proceed.

**Dollars here are an allocation model, not the bill.** OpenCost / Kubecost price nodes from list or custom pricing unless cloud billing integration is configured. Label every K8s figure `allocation-model` (Principle 4). On EKS, the same node spend appears in the AWS bill as EC2 — never add an AWS report's EC2 line and a K8s allocation together.

**Docs behind the claims** (read in this session before quoting them in a report): OpenCost `/allocation` parameters and idle cost — `https://opencost.io/docs/integrations/api/` · HPA targets are a percentage of requests — `https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/` · node removal / consolidation — `https://karpenter.sh/docs/concepts/disruption/` (or the installed autoscaler's docs). A claim with no page read this session is `UNVERIFIED`. The OpenCost API page does not document `accumulate`, `filterNamespaces` or `filterLabels` for `/allocation` (read 2026-10-27); check them against the installed version.

**Namespace, service and port in the commands below are chart defaults** — use the namespace and service that the Step 1 detection printed. Label keys (`app`, `service`) are examples: use the key the catalog or the operator names (for instance `app.kubernetes.io/name`).

**Never copy pod specs or kubeconfig into the report** (Constraint 10): `kubectl describe pod` and `get pods -o json` print literal `env:` values, and `kubectl config view` prints exec-plugin args / env. Use the projected forms below.

## Step 1 — Detect & Scope: cloud detection

```bash
# Detect current cluster context, and the cluster / server it points at (projected — no credentials)
kubectl config current-context
kubectl config view --minify -o jsonpath='{.clusters[0].name}{"  "}{.clusters[0].cluster.server}{"\n"}'

# Detect whether OpenCost or Kubecost is installed in any namespace, and its version
kubectl get pods -A -l 'app.kubernetes.io/name in (opencost,cost-analyzer)' \
  -o jsonpath='{range .items[*]}{.metadata.namespace}{"  "}{.metadata.name}{"  "}{.spec.containers[0].image}{"\n"}{end}'
# Label selectors vary by chart — fall back to: kubectl get pods -A --no-headers | grep -E 'opencost|kubecost'
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
# Open a local proxy to the OpenCost service. Pick a free local port, and stop the
# tunnel when the batch finishes (kill %1, or kill the recorded PID).
kubectl port-forward -n opencost svc/opencost 9003:9003 &
PF_PID=$!

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

**Retention caveat:** how far back allocation data goes depends on the installed product, version, licence and Prometheus retention — and these change between releases. Before a window longer than ~2 weeks, check the earliest window the API actually returns (query `window=<N>d` and compare the first returned `start` with the one requested) and surface any shortfall. A truncated window fails the Principle 3 window rule; it does not become a shorter "≥ 30d" claim.

**RBAC:** `port-forward` requires `pods/portforward` permission on the `kubecost` namespace.
**API cost:** none (in-cluster query).

**Kubernetes: a "what changed" source for anomaly drivers (new workloads, node-pool changes, GitOps revisions) is not supported yet.** Report allocation deltas only and name no cause.

## Step 2B — Waste mode

### Over-requested / idle workloads — over the window, not a snapshot

`kubectl top` is one instant from Metrics Server: it cannot show "consistently low over 30 days" (Principle 3). Use the allocation API's efficiency fields over the window instead:

```bash
# Per-controller usage vs requests over 30d (port-forward as in Step 2A)
curl -s 'http://localhost:9003/allocation?window=30d&aggregate=controller&accumulate=true' \
  | jq '.data[0] | to_entries[] | {name: .key,
        cpuEff: .value.cpuEfficiency, ramEff: .value.ramEfficiency,
        cpuReq: .value.cpuCoreRequestAverage, ramReq: .value.ramByteRequestAverage,
        cost: .value.totalCost}'
# Field names follow the OpenCost allocation schema — confirm against the installed
# version's API docs; a missing field is UNVERIFIED, not 0.
```

A controller whose CPU **and** memory efficiency stay low over ≥ 30d is a **rightsize-requests** candidate (`allocation-model`, confidence ≤ `medium`). A low average with a high peak is not one: take the peak, and OOM-kill and CPU-throttle history, from Prometheus (`max_over_time` on the usage series) when it exists. Without it the row is `UNVERIFIED` (cap `low`). Check for an HPA or VPA on the controller first: HPA targets are a percentage of requests, so lowering requests changes scaling.

**Lower requests are not a saving yet.** The AWS bill falls only when nodes go away. Until node-level slack (requested vs allocatable, `aggregate=node`) and a removal path — an autoscaler or consolidation policy, or a planned nodegroup resize — are shown, the row is `Realizable: conditional on node reduction` and stays out of the totals. "Idle → delete a workload" is never inferred from usage alone: zero-traffic services may be standbys or batch. That is an owner question.

`kubectl top pods -A` remains useful only to spot-check a live moment; never cite it as window evidence.

Declared requests, projected (no env values):

```bash
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{range .spec.containers[*]}{"  "}{.name}{" cpu="}{.resources.requests.cpu}{" mem="}{.resources.requests.memory}{end}{"\n"}{end}'
```

### PersistentVolumes and claims — what actually costs money

```bash
kubectl get pv -o custom-columns='NAME:.metadata.name,PHASE:.status.phase,RECLAIM:.spec.persistentVolumeReclaimPolicy,SIZE:.spec.capacity.storage,CLASS:.spec.storageClassName,CLAIM:.spec.claimRef.namespace,CLAIMNAME:.spec.claimRef.name,VOLUME:.spec.csi.volumeHandle'
kubectl get pvc -A -o custom-columns='NS:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase,VOLUME:.spec.volumeName,SIZE:.status.capacity.storage'
# Which claims a pod mounts (projected):
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{range .spec.volumes[*]}{.persistentVolumeClaim.claimName}{" "}{end}{"\n"}{end}'
```

| State | Costs money? | Report as |
|---|---|---|
| PV `Released`, reclaim `Retain` | **Yes** — the backing volume (e.g. EBS) still exists | Remediation candidate; cross-check the volume in the AWS sweep (`VOLUME` column = EBS volume ID for the EBS CSI driver), price it from the bill |
| PV `Available` (pre-provisioned, never claimed) | **Yes** | Remediation candidate — confirm intent with the owner |
| PVC `Bound`, mounted by no pod | **Yes** | **Data — owner confirm.** Typically a StatefulSet scaled to 0 or a paused job. Never a delete row on usage alone (`low`) |
| PVC `Pending` | **No** — nothing provisioned yet (often `WaitForFirstConsumer`) | Informational (hygiene), $0 |
| PVC `Lost` | **No** — the backing PV is gone | Informational (hygiene), $0 |

**Kubernetes: orphan snapshots, idle load balancers and empty-node sweeps are not supported yet.**

**RBAC:** `get pods`, `get pvc`, `get pv` require standard read permissions; the allocation API needs `pods/portforward` (Step 2A). `kubectl top` additionally requires Metrics Server.
**API cost:** none.

## Step 2C — Attribution mode

### Idle and shared cost — context, not service cost

OpenCost returns `__idle__` (capacity paid for but used by no workload) only when asked; `includeIdle` defaults to `false`, and `shareIdle` defaults to `false` (`docs: https://opencost.io/docs/integrations/api/`). Without `includeIdle=true`, namespace and service totals do not add up to the cluster's cost, and the gap is silent.

```bash
curl 'http://localhost:9003/allocation?window=30d&aggregate=namespace&accumulate=true&includeIdle=true'
```

Report idle, system namespaces (`kube-system`, monitoring, ingress) and node overhead as **context cost** beside the service's direct cost. Spread them over services (`shareIdle=true`, or a stated method) only when the operator chooses it, and then label the figure `shared-allocated: <method>`. Never present an allocated figure as the service's direct cost.

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
- `kubectl port-forward` is a read-only local proxy. It opens a TCP tunnel to an in-cluster service and does not create, modify, or delete any Kubernetes resource. It is permitted under the Iron Law. The tunnel is closed at the end of each Step 3 batch.
- Allocation-data retention depends on the installed product, version, licence and Prometheus retention. Before a window longer than ~2 weeks, check what the API actually returns and surface any shortfall (see Step 2A).
- `kubectl describe pod`, `get pods -o json/yaml` and `config view` (unprojected) can print secrets. Use the projected forms in this file; never copy their output into the report.
- If neither OpenCost nor Kubecost is installed, the skill MUST stop and flag the gap. It does NOT install or configure any software — that is an operator action.
- `kubectl exec` is explicitly out of scope. Even in read-only usage (e.g. `kubectl exec -- cat /proc/meminfo`), exec is not a permitted verb in this skill.
