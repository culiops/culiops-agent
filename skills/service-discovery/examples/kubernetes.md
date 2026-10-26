# Examples: Kubernetes & Helm CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the stack is Kubernetes and/or Helm. Use this file in any of these cases — the cluster's hosting location is orthogonal:

- **On-prem / self-managed** Kubernetes (kubeadm, Rancher/RKE, OpenShift, k3s, Talos, bare-metal).
- **Managed** Kubernetes on EKS — use this file **alongside** `examples/aws.md`. The AWS file covers the control-plane / node-group / cloud-integration commands (`aws eks describe-cluster`); this file covers everything inside the cluster once `kubectl` is wired up.
- **Helm releases** deployed anywhere — this file is the source of truth for Helm commands.

Replace placeholders (`{context}`, `{namespace}`, `{deployment}`, `{release}`, etc.) with the values resolved in Step 2.

## Two uses of these commands

This file serves two different purposes. Do not mix them.

- **(a) Commands the skill itself runs** during discovery and enrichment. Their output can reach the catalog, so each one is **projected**: an explicit `-o custom-columns` / `-o jsonpath` / `-o go-template` allowlist of metadata fields. They never print environment variable values, Secret data, ConfigMap data, rendered manifests or log lines. These are the commands marked "projected" below.
- **(b) On-call terminal commands** for runbooks. `kubectl describe`, `get -o yaml|json`, `logs`, `helm get values|manifest|hooks|notes` and `helm status` can print literal env values, config data, rendered Secrets or log lines containing secrets and PII. They appear only under (b), labelled **terminal only — never paste output into a catalog, ticket or chat**, and the skill never runs them for enrichment.

## Prerequisites

**CLI tools:** `kubectl` (≥ 1.28 recommended — keep within the [±1 minor version skew](https://kubernetes.io/releases/version-skew-policy/) of the cluster's control plane). `helm` (≥ 3.12) if Helm is in scope. Optional but useful: `stern` (multi-pod log tailing), `kubectx`/`kubens` (context and namespace switching).

**Authentication:** `kubectl` reads `~/.kube/config` by default (override with `KUBECONFIG` env var). For on-prem clusters, the kubeconfig typically comes from the cluster admin (client-cert + embedded CA, or an OIDC provider). For EKS it comes from the AWS CLI (`--alias` pins the context name to `{context}`):

- EKS: `aws eks update-kubeconfig --name {cluster} --alias {context} --profile {profile} --region {region}`

**Identity check (before each batch).** The current context can change between commands. Re-run this and abort the batch if the context differs from the one the operator confirmed at the gate:

```
kubectl config current-context
kubectl --context {context} auth can-i --list --namespace={namespace}
```

**Pin the context on every command.** Every `kubectl` command in this file carries `--context {context}`; every `helm` command carries `--kube-context {context}` (Helm's spelling of the same flag).

**Least-privilege Kubernetes RBAC — every command below is read-only.** Kubernetes RBAC is orthogonal to cloud IAM; on EKS you may need both (IAM to reach the API server, RBAC to do anything once inside). Grant the operator either:

- **Baseline (simplest):** the built-in `view` `ClusterRole` bound at the relevant namespace(s) via a `RoleBinding`, or cluster-wide via a `ClusterRoleBinding` if multiple namespaces are in scope. Covers `get`/`list`/`watch` on the standard resource kinds the runbooks reference.
- **Tighter (recommended):** a custom `Role` listing only the resource kinds + verbs actually needed (`deployments`, `statefulsets`, `pods`, `pods/log`, `services`, `ingresses`, `events`, `configmaps`, `horizontalpodautoscalers`, `persistentvolumeclaims`, `jobs`, `cronjobs` + verbs `get`/`list`/`watch`).
- **Secrets are *not* included in the `view` role by design, and the catalog does not need them.** RBAC cannot grant metadata-only access to Secrets: any role that can `get`/`list` them can read their values. Do not bind such a role for a runbook. The skill records Secret *references* (names from `envFrom` / `secretKeyRef` / secret volumes in workload specs) and never reads Secrets.
- **Never use `cluster-admin`, `admin`, or `edit`** for read-only investigation — those include write verbs on the whole API surface.
- On EKS, bind the RBAC subject to the IAM principal using an EKS access entry (`aws eks list-access-entries --cluster-name {cluster} --profile {profile} --region {region}`) or the legacy `aws-auth` ConfigMap. On other clusters, use the cluster's OIDC group mapping.
- Helm 3 stores releases as Secrets, so `helm list`, `helm history` and `helm get` need Secret read access, which `view` does not give. See "Helm".

**Mutations are flagged inline.** Most commands here are read-only. State-changing commands (any `kubectl scale|rollout restart|rollout undo|apply|delete|edit|patch|replace|drain|cordon`, `helm install|upgrade|rollback|uninstall`, `argocd app sync|rollback`, `flux suspend|resume|reconcile`) are labeled explicitly. `kubectl exec` and `kubectl port-forward` are *not* technically mutations but give direct pod access and expose local ports — treat them as sensitive: label, justify, and require approval. **Never run a mutation without explicit team approval and an elevated role.**

**Cost awareness:** `kubectl` calls to the API server are free, but the *observability backend* the cluster forwards to is often metered — Prometheus/Grafana/Loki self-hosted is free; Grafana Cloud and Amazon Managed Prometheus meter query volume. Check with the platform team which backend is in use before running large time-range queries.

---

## How to use this file

Each section maps one Kubernetes/Helm resource category to status/config + the four golden signals where applicable. On-prem clusters rely on what's installed — `kubectl top` needs [metrics-server](https://github.com/kubernetes-sigs/metrics-server); rich metrics need Prometheus + Grafana; logs need a backend (Loki, ELK, OpenSearch, or CloudWatch on EKS). If the cluster lacks these, note the gap in the runbook and fall back to the projected `get` commands, `kubectl get events`, and (terminal only) `kubectl describe` / `kubectl logs`.

---

## Cluster & Nodes

- Cluster info: `kubectl --context {context} cluster-info`
- Control-plane health: `kubectl --context {context} get --raw /healthz` / `kubectl --context {context} get --raw '/readyz?verbose'` (quote the path: unquoted `?` is a glob in zsh)
- Nodes list: `kubectl --context {context} get nodes -o wide`
- Node conditions (projected): `kubectl --context {context} get nodes -o 'custom-columns=NAME:.metadata.name,KUBELET:.status.nodeInfo.kubeletVersion,READY:.status.conditions[?(@.type=="Ready")].status,MEMPRESSURE:.status.conditions[?(@.type=="MemoryPressure")].status,DISKPRESSURE:.status.conditions[?(@.type=="DiskPressure")].status,PIDPRESSURE:.status.conditions[?(@.type=="PIDPressure")].status'`
- Node details — **terminal only — never paste output into a catalog, ticket or chat**: `kubectl --context {context} describe node {node}`
- Node CPU / memory usage: `kubectl --context {context} top nodes` (requires metrics-server)
- API server version: `kubectl --context {context} version`

## Namespaces

- List namespaces: `kubectl --context {context} get ns`
- Resource quotas (projected): `kubectl --context {context} get resourcequota -n {namespace} -o custom-columns=NAME:.metadata.name,HARD:.status.hard,USED:.status.used`
- Limit ranges (projected): `kubectl --context {context} get limitrange -n {namespace} -o custom-columns=NAME:.metadata.name,LIMITS:.spec.limits`

## Workloads (Deployments / StatefulSets / DaemonSets)

- List: `kubectl --context {context} get deploy,sts,ds -n {namespace}`
- Workload summary (projected): `kubectl --context {context} get deploy,sts,ds -n {namespace} -l app={service} -o custom-columns=KIND:.kind,NAME:.metadata.name,REPLICAS:.spec.replicas,READY:.status.readyReplicas,SA:.spec.template.spec.serviceAccountName`
- Per-container detail (projected; image, requests/limits, probe paths, env var **names** only): `kubectl --context {context} get deploy/{deployment} -n {namespace} -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\timage="}{.image}{"\trequests="}{.resources.requests}{"\tlimits="}{.resources.limits}{"\treadiness="}{.readinessProbe.httpGet.path}{"\tliveness="}{.livenessProbe.httpGet.path}{"\tenvNames="}{.env[*].name}{"\n"}{end}'` (same for `sts/{statefulset}`; probe paths only — `exec` probes and `httpHeaders` are left out because they can carry credentials)
- Env var names only (projected): `kubectl --context {context} get deploy/{deployment} -n {namespace} -o jsonpath='{.spec.template.spec.containers[*].env[*].name}'`
- Secret references (names only, from the spec): see "Secret references from workloads" in `cloud-discovery/kubernetes.md`
- Rollout status: `kubectl --context {context} rollout status deploy/{deployment} -n {namespace}`
- Rollout history: `kubectl --context {context} rollout history deploy/{deployment} -n {namespace}`
- Replica count & readiness: `kubectl --context {context} get deploy/{deployment} -n {namespace} -o wide`
- Deployment / StatefulSet details — **terminal only — never paste output into a catalog, ticket or chat** (`describe` prints literal env values): `kubectl --context {context} describe deploy/{deployment} -n {namespace}` / `kubectl --context {context} describe sts/{statefulset} -n {namespace}`
- Full spec — **terminal only — never paste output into a catalog, ticket or chat** (full object, including env values): `kubectl --context {context} get deploy/{deployment} -n {namespace} -o yaml`

## Jobs & CronJobs

- List: `kubectl --context {context} get jobs,cronjobs -n {namespace}`
- CronJob schedule & history (projected): `kubectl --context {context} get cronjob -n {namespace} -o custom-columns=NAME:.metadata.name,SCHEDULE:.spec.schedule,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime,ACTIVE:.status.active[*].name`
- CronJob details — **terminal only — never paste output into a catalog, ticket or chat**: `kubectl --context {context} describe cronjob/{cronjob} -n {namespace}`
- Job outcomes (projected): `kubectl --context {context} get jobs -n {namespace} -o custom-columns=NAME:.metadata.name,SUCCEEDED:.status.succeeded,FAILED:.status.failed,ACTIVE:.status.active`
- Completed jobs: `kubectl --context {context} get jobs -n {namespace} --field-selector status.successful=1`. Caveat: `status.successful=0` is **not** "failed" — it also matches jobs that are still running or not started. Use the `FAILED` / `ACTIVE` columns above to tell them apart.

## Pods

- List: `kubectl --context {context} get pods -n {namespace} -o wide`
- By label (e.g., owning service): `kubectl --context {context} get pods -n {namespace} -l app={service}`
- Pod status (projected: phase, node, restarts, waiting reason): `kubectl --context {context} get pods -n {namespace} -l app={service} -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,NODE:.spec.nodeName,RESTARTS:.status.containerStatuses[*].restartCount,WAITING:.status.containerStatuses[*].state.waiting.reason,SA:.spec.serviceAccountName`
- Pod details — **terminal only — never paste output into a catalog, ticket or chat** (`describe` prints literal env values; the Events block at the bottom is the useful part): `kubectl --context {context} describe pod/{pod} -n {namespace}`
- Pending / failed pods: `kubectl --context {context} get pods -n {namespace} --field-selector status.phase=Pending` / `kubectl --context {context} get pods -n {namespace} --field-selector status.phase=Failed`
- Per-pod CPU / memory: `kubectl --context {context} top pods -n {namespace}` (requires metrics-server)
- Per-container resources (requests/limits, projected): `kubectl --context {context} get pod/{pod} -n {namespace} -o jsonpath='{range .spec.containers[*]}{.name}{"\trequests="}{.resources.requests}{"\tlimits="}{.resources.limits}{"\n"}{end}'`

## Services, EndpointSlices & Ingress

- Services (projected): `kubectl --context {context} get svc -n {namespace} -o custom-columns=NAME:.metadata.name,TYPE:.spec.type,CLUSTER-IP:.spec.clusterIP,PORTS:.spec.ports[*].port,SELECTOR:.spec.selector`
- EndpointSlices (what the service is actually routing to; `v1 Endpoints` is deprecated, so use slices): `kubectl --context {context} get endpointslices -n {namespace} -l kubernetes.io/service-name={service}`
- Ingresses (projected): `kubectl --context {context} get ingress -n {namespace} -o custom-columns=NAME:.metadata.name,CLASS:.spec.ingressClassName,HOSTS:.spec.rules[*].host,ADDRESS:.status.loadBalancer.ingress[*].hostname`
- Service / ingress details — **terminal only — never paste output into a catalog, ticket or chat** (annotations are printed in full): `kubectl --context {context} describe svc/{service} -n {namespace}` / `kubectl --context {context} describe ingress/{ingress} -n {namespace}`
- Ingress class & controller: `kubectl --context {context} get ingressclass`

## ConfigMaps & Secrets

- ConfigMaps (names only; the default table shows only the key *count*): `kubectl --context {context} get cm -n {namespace}`
- ConfigMap key names (projected; keys, never values): `kubectl --context {context} get cm/{configmap} -n {namespace} -o go-template='{{range $k, $v := .data}}{{$k}}{{"\n"}}{{end}}'`
- ConfigMap contents — **terminal only — never paste output into a catalog, ticket or chat** (ConfigMaps often hold connection strings and credentials): `kubectl --context {context} get cm/{configmap} -n {namespace} -o yaml`
- **Secrets: the skill skips them.** Record references from workload specs instead (see "Secret references from workloads" in `cloud-discovery/kubernetes.md`). There is no Secret value-fetch template in this skill; a person who needs a Secret value gets it through the team's secret-management process, not from a runbook.
- Secret names, on-call only (**terminal only**; needs `list` on `secrets`, which `view` does not grant and which also exposes values over the API, so this is not "metadata-only access"): `kubectl --context {context} get secret -n {namespace} -o custom-columns=NAME:.metadata.name,TYPE:.type`

## Autoscaling (HPA / VPA)

- HPAs: `kubectl --context {context} get hpa -n {namespace}`
- HPA details (projected: min/max replicas, target vs. current): `kubectl --context {context} get hpa/{hpa} -n {namespace} -o custom-columns=NAME:.metadata.name,MIN:.spec.minReplicas,MAX:.spec.maxReplicas,CURRENT:.status.currentReplicas,DESIRED:.status.desiredReplicas`
- HPA events and per-metric status — **terminal only**: `kubectl --context {context} describe hpa/{hpa} -n {namespace}`
- VPAs (if installed): `kubectl --context {context} get vpa -n {namespace}`

## Persistent Storage (PV / PVC / StorageClass)

- PVCs in namespace (projected): `kubectl --context {context} get pvc -n {namespace} -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName,CAPACITY:.status.capacity.storage,CLASS:.spec.storageClassName`
- PVs (cluster-scoped): `kubectl --context {context} get pv`
- StorageClasses: `kubectl --context {context} get storageclass`

## Events

- Namespace events sorted by most recent: `kubectl --context {context} get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`
- Events for a specific object — **terminal only** (bottom of the `describe` output): `kubectl --context {context} describe {kind}/{name} -n {namespace}`
- Cluster-wide events: `kubectl --context {context} get events --all-namespaces --sort-by='.lastTimestamp' | tail -50`

## Logs

**Logs may contain secrets and PII. Every command in this section is terminal only — never paste output into a catalog, ticket or chat. The skill never runs them for enrichment.**

- Pod logs (single container): `kubectl --context {context} logs {pod} -n {namespace}`
- Multi-container pod: `kubectl --context {context} logs {pod} -c {container} -n {namespace}`
- Previous instance (if pod restarted): `kubectl --context {context} logs {pod} -n {namespace} --previous`
- Follow: `kubectl --context {context} logs -f {pod} -n {namespace}` — **label as interactive; don't chain into the next step**
- By label across pods: `kubectl --context {context} logs -n {namespace} -l app={service} --tail=200`. With a selector, kubectl caps concurrent log streams at `--max-log-requests` (default 5, relevant when following); with more matching pods, raise it or select fewer pods.
- Multi-pod tailing: `stern {service} -n {namespace} --since 15m --context {context}` (if `stern` installed)

## Metrics (on-cluster Prometheus)

- `kubectl top` works if metrics-server is installed. For deeper signals the cluster needs Prometheus. Common patterns:
  - Port-forward to the Prometheus service: `kubectl --context {context} port-forward -n monitoring svc/prometheus 9090:9090` — **opens a local port; label as interactive and approve before running**
  - Then query via the UI at `http://localhost:9090` or via `curl 'http://localhost:9090/api/v1/query?query=...'`
- Typical PromQL signals (adjust label selectors to your cluster's conventions):
  - Request rate (histogram): `sum(rate(http_requests_total{namespace="{namespace}",service="{service}"}[5m]))`
  - p99 latency: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="{namespace}",service="{service}"}[5m])) by (le))`
  - Error rate: `sum(rate(http_requests_total{namespace="{namespace}",service="{service}",code=~"5.."}[5m]))`
  - Pod CPU saturation: `sum(rate(container_cpu_usage_seconds_total{namespace="{namespace}",pod=~"{service}-.*"}[5m])) by (pod)`

## Helm

Helm 3 stores each release as a Secret in the release namespace. `helm list`, `helm history` and `helm get` therefore need Secret read access and fail under the `view` role. If they fail with a permission error, record the releases as `not-queryable (forbidden)` and use the label fallback below instead of asking for a broader role.

- List releases in namespace (`-a` includes failed and pending releases): `helm list -a -n {namespace} --kube-context {context}`
- All releases across namespaces (use when the namespace is unknown): `helm list -a -A --kube-context {context}`
- Release history (rollback candidates): `helm history {release} -n {namespace} --kube-context {context}`
- **Fallback under `view`** (projected; objects Helm manages carry the ownership label and release-name annotation): `kubectl --context {context} get deploy,sts,ds,cronjob,svc,ing,cm,sa,hpa -n {namespace} -l app.kubernetes.io/managed-by=Helm -o custom-columns=KIND:.kind,NAME:.metadata.name,RELEASE:.metadata.annotations.meta\.helm\.sh/release-name`
- Release status (notes can echo credentials) — **terminal only — never paste output into a catalog, ticket or chat**: `helm status {release} -n {namespace} --kube-context {context}`
- Rendered manifests for a release (includes rendered Secrets) — **terminal only — never paste output into a catalog, ticket or chat**: `helm get manifest {release} -n {namespace} --kube-context {context}`
- Resolved values (add `-a` / `--all` for computed defaults; values often hold passwords) — **terminal only — never paste output into a catalog, ticket or chat**: `helm get values {release} -n {namespace} --kube-context {context}`
- Release hooks & notes — **terminal only — never paste output into a catalog, ticket or chat**: `helm get hooks {release} -n {namespace} --kube-context {context}` / `helm get notes {release} -n {namespace} --kube-context {context}`
- Chart source (if the chart is a dependency in the repo): inspect `Chart.yaml` and `charts/` subdir

The skill uses `helm list` and `helm history` (when allowed) and the label fallback; it never runs `helm get values|manifest|hooks|notes` or `helm status`.

## GitOps (ArgoCD / Flux)

If the cluster is managed by ArgoCD or Flux, the **desired state** lives in Git, not in `helm`/`kubectl apply`. Inspect both the GitOps controller and the cluster state. Owner signals: ArgoCD label `argocd.argoproj.io/instance` or annotation `argocd.argoproj.io/tracking-id`; Flux labels `kustomize.toolkit.fluxcd.io/name` and `helm.toolkit.fluxcd.io/name`.

- ArgoCD: `argocd app list` / `argocd app history {app}` (requires ArgoCD CLI + login)
- ArgoCD app detail — **terminal only** (can print Helm parameters): `argocd app get {app}`
- ArgoCD in-cluster (no CLI, projected; strip any `user:token@` userinfo from `repoURL` before recording): `kubectl --context {context} get applications -n argocd -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,REPO:.spec.source.repoURL,PATH:.spec.source.path,REV:.spec.source.targetRevision,DEST:.spec.destination.namespace`
- ArgoCD application details — **terminal only**: `kubectl --context {context} describe application/{app} -n argocd`
- Flux: `flux get kustomizations -A --context {context}` / `flux get helmreleases -A --context {context}`
- Flux per-resource: `flux describe kustomization/{name} -n {namespace} --context {context}` / `flux describe helmrelease/{name} -n {namespace} --context {context}`

## Ingress controllers & service mesh

Common on-prem / portable choices. Use whichever is actually installed. Check CRDs by name rather than hiding errors: `kubectl --context {context} get crd -o custom-columns=NAME:.metadata.name` and filter for `istio|linkerd|traefik|ambassador|contour`.

- ingress-nginx logs — **terminal only** (request lines can contain tokens and PII): `kubectl --context {context} logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=200`
- Traefik routes (projected): `kubectl --context {context} get ingressroute -A -o custom-columns=NAME:.metadata.name,NS:.metadata.namespace` (Traefik CRDs; check `kubectl --context {context} get crd ingressroutes.traefik.io` first) or `kubectl --context {context} get ingress -A`
- Istio: `istioctl proxy-status --context {context}` / `istioctl analyze -n {namespace} --context {context}`
- Linkerd: `linkerd check --context {context}` / `linkerd viz stat deploy -n {namespace} --context {context}`
- cert-manager: `kubectl --context {context} get certificate,certificaterequest,order,challenge -n {namespace}` (check each CRD exists first; query separately if any is absent). Details — **terminal only**: `kubectl --context {context} describe certificate/{cert} -n {namespace}`

## Common mutations (FLAGGED — require approval)

Listed here so runbooks can reference a known mutation by name. **Each is `MUTATION — requires explicit approval`; runbook must state blast radius and elevated permission inline.**

- `kubectl --context {context} scale deploy/{deployment} --replicas={n}` — changes capacity
- `kubectl --context {context} rollout restart deploy/{deployment}` — rolls all pods
- `kubectl --context {context} rollout undo deploy/{deployment} --to-revision={n}` — reverts to prior version
- `kubectl --context {context} delete pod/{pod}` — evicts a single pod (blast radius usually small, but approve)
- `kubectl --context {context} drain {node}` — evicts all pods from a node
- `kubectl --context {context} cordon {node}` / `uncordon {node}` — pause/resume scheduling
- `kubectl --context {context} apply -f ...` / `kubectl --context {context} edit ...` / `kubectl --context {context} patch ...` — any spec change
- `helm upgrade {release} {chart} -f values.yaml --kube-context {context}` — rolls a release
- `helm rollback {release} {revision} --kube-context {context}` — reverts a release
- `helm uninstall {release} --kube-context {context}` — deletes a release
- `argocd app sync {app}` / `argocd app rollback {app} {revision}` — GitOps sync/rollback
- `flux suspend` / `flux resume` / `flux reconcile` (with `--context {context}`) — pause or force reconciliation

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{context}` | kubeconfig context confirmed at the gate; passed to every command | `prod-eu-west-1` |
| `{namespace}` | Kubernetes namespace | `widgetapi-prod` |
| `{deployment}`, `{statefulset}`, `{daemonset}`, `{cronjob}`, `{job}` | Workload name | `widgetapi-web` |
| `{pod}` | Pod name | `widgetapi-web-7d9b-x7k2p` |
| `{service}`, `{ingress}`, `{hpa}`, `{vpa}`, `{pvc}`, `{configmap}`, `{cert}` | Resource names | `widgetapi-web` |
| `{container}` | Container name inside a multi-container pod | `app` |
| `{release}` | Helm release name | `widgetapi` |
| `{chart}` | Helm chart (repo/name or local path) | `bitnami/postgresql` |
| `{node}` | Node name | `ip-10-0-1-42.ec2.internal` |
| `{cluster}` | Cluster name (from cloud side, if managed) | `widgetapi-prod` |
| `{profile}`, `{region}` | AWS profile and region (EKS only) | `widgetapi-prod-ro`, `eu-west-1` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
