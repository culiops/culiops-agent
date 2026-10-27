---
name: kubernetes
identity-command: "kubectl config current-context && kubectl --context {context} auth can-i get pods --all-namespaces"
---

## Prerequisites

**CLI tools:** `kubectl` (≥ 1.28 recommended). `helm` (≥ 3.12) if Helm releases are in scope.

**Authentication:** `kubectl` reads `~/.kube/config` by default. For EKS clusters, obtain credentials via `aws eks update-kubeconfig --profile {profile} --region {region} --name {cluster}`; on-prem clusters usually get a kubeconfig from the cluster admin.

**Identity check (before each batch of queries).** The current context can change between commands. Re-run this and abort the batch if it differs from the context the operator confirmed at the gate:

```
kubectl config current-context
kubectl --context {context} auth can-i get pods --all-namespaces
```

**Pin the context on every command.** Every `kubectl` command below carries `--context {context}`; every `helm` command carries `--kube-context {context}` (Helm's spelling of the same flag).

**Least-privilege RBAC — all queries below are read-only.** The operator needs:

- The built-in `view` ClusterRole bound at the relevant namespace(s) via a `RoleBinding`, or cluster-wide via a `ClusterRoleBinding` if the service's namespace is not yet known.

This covers `get`/`list`/`watch` on standard resource kinds. Secrets are excluded from the `view` role by design.

**Secrets: the skill skips them entirely.** If the operator's RBAC does grant `get`/`list` on `secrets` (a custom Role, `edit`/`admin`, or `cluster-admin`), every `get secret` response carries the secret `data` over the wire; `-o custom-columns` only controls what is *printed*. RBAC cannot grant metadata-only access to Secrets. So `secret` is not in any kind list below, and the skill records secret **references** taken from workload specs instead (see "Secret references from workloads").

**Kubernetes discovery is orthogonal to where the cluster runs.** A service may run on EKS or on-prem Kubernetes. Use this template alongside `aws.md` for EKS clusters to cover both the cluster-internal resources and the AWS-level resources (node groups, load balancers, managed databases, etc.). On EKS, cluster access is granted by EKS access entries (`aws eks list-access-entries --cluster-name {cluster} --profile {profile} --region {region}`) or by the legacy `aws-auth` ConfigMap; check both when the caller is denied.

## Rules that apply to every query here

- **Projection only.** Output of these commands can reach the catalog. Use `-o custom-columns` (or `-o jsonpath`) with an explicit allowlist. **Never** `-o json` / `-o yaml` for discovery, including `get all -o json`: whole objects carry env values, annotations such as `last-applied-configuration`, and more.
- **Default projection:**

  ```
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
  ```

  UNVERIFIED that `.kind` is populated for every item in a multi-kind list; if the KIND column comes back empty, query each kind separately (one `kubectl get <kind>` per kind) and fill KIND from the command.
- **Empty is not absent.** Record `not-found (queried <context>/<namespace>)`, `not-queried`, or `not-queryable (forbidden)`. A `Forbidden` error is `not-queryable`, not "does not exist".

## Broad discovery queries

### 1. By label (primary)

Label-based search is the most reliable way to find Kubernetes resources belonging to a service.

```
kubectl --context {context} get all -n {namespace} -l app={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

Teams use different label key conventions. **Run all candidate keys** and record which key matched each resource:

| Label key | Typical usage |
|-----------|---------------|
| `app` | Most common — set by Helm charts and many deployment tools |
| `app.kubernetes.io/name` | Kubernetes recommended label (from the [common labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/) convention) |
| `app.kubernetes.io/instance` | Helm release instance name |
| `service` | Explicit service label |
| `component` | Component within a larger service |

A label key is a membership signal only when the operator confirms it for this service. `component` names a part of a larger service, so it is a hint only (the Kubernetes counterpart of AWS `Project` / `Team` / `Owner` tags): its matches go to **Unattributed — operator assigns** unless another membership signal applies.

For each variation, substitute the label selector:

```
kubectl --context {context} get all -n {namespace} -l app.kubernetes.io/name={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

### 2. By namespace

Many teams map one service to one namespace. If the namespace name matches the service, list everything in it. A namespace match is a membership signal only when it matches the naming pattern the operator confirmed.

```
kubectl --context {context} get all -n {service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

### 3. Broader resource types

`kubectl get all` only returns a subset of resource types (pods, services, deployments, replicasets, statefulsets, daemonsets, jobs, cronjobs). Many important resource types are missed. Query them explicitly. **No `secret` kind** (see Prerequisites). `cm` is listed by name only; the projection never prints `.data`.

```
kubectl --context {context} get deploy,sts,ds,cronjob,job,svc,ing,cm,sa,hpa,pdb,pvc \
  -n {namespace} -l app={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

Without a label selector (namespace-based fallback):

```
kubectl --context {context} get deploy,sts,ds,cronjob,job,svc,ing,cm,sa,hpa,pdb,pvc \
  -n {service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

### 4. Secret references from workloads

Instead of reading Secrets, record which Secrets the workloads *reference*: names only, from the workload specs (envFrom / secretKeyRef / secret volumes). Values are never touched.

```
kubectl --context {context} get deploy,sts,ds -n {namespace} -l app={service} \
  -o jsonpath='{range .items[*]}{.kind}{"/"}{.metadata.name}{"\tenvFrom: "}{.spec.template.spec.containers[*].envFrom[*].secretRef.name}{"\tsecretKeyRef: "}{.spec.template.spec.containers[*].env[*].valueFrom.secretKeyRef.name}{"\tvolumes: "}{.spec.template.spec.volumes[*].secret.secretName}{"\n"}{end}'
```

CronJobs keep the pod template under `.spec.jobTemplate.spec.template.spec`; use that path in the same jsonpath. Record the result as `references secret <name>`; do not look the Secret up.

### 5. CRD-based resources

Clusters with monitoring, certificate management, or advanced ingress controllers have custom resources that `get all` never includes. Check that the CRD exists first, then query **each kind separately**. Do not hide stderr (`2>/dev/null`): `Forbidden` (not queryable) and `the server doesn't have a resource type` (CRD absent) must stay distinguishable.

```
kubectl --context {context} get crd servicemonitors.monitoring.coreos.com
kubectl --context {context} get servicemonitor -n {namespace} -l app={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels

kubectl --context {context} get crd prometheusrules.monitoring.coreos.com
kubectl --context {context} get prometheusrule -n {namespace} -l app={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels

kubectl --context {context} get crd certificates.cert-manager.io
kubectl --context {context} get certificate -n {namespace} -l app={service} \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,LABELS:.metadata.labels
```

Repeat the pattern (`get crd <name>`, then `get <kind>`) for `certificaterequest`, `ingressroute`, or any other CRD the docs hint at. To see what is installed, list CRD names only (`kubectl --context {context} get crd -o custom-columns=NAME:.metadata.name`) and filter client-side.

### 6. Helm release discovery

If the service is deployed via Helm, the release name often matches the service name.

**Helm 3 stores releases as Secrets**, so `helm list` needs permission to read Secrets in the release namespace and fails under the `view` role. Try it only when the operator's role allows; use `-a` so failed and pending releases are shown, and `-A` when the namespace is not known:

```
helm list -a -n {namespace} --kube-context {context} --filter '{service}'
helm list -a -A --kube-context {context} --filter '{service}'
```

**Fallback under `view`:** use the ownership label and annotation that Helm puts on every object it manages, projected to metadata only:

```
kubectl --context {context} get deploy,sts,ds,cronjob,svc,ing,cm,sa,hpa -n {namespace} \
  -l app.kubernetes.io/managed-by=Helm \
  -o custom-columns=KIND:.kind,NAME:.metadata.name,NS:.metadata.namespace,RELEASE:.metadata.annotations.meta\.helm\.sh/release-name,LABELS:.metadata.labels
```

Group the rows by the `RELEASE` column (`meta.helm.sh/release-name`) to reconstruct the release's resource set. Without a namespace, replace `-n {namespace}` with `-A`.

`helm get manifest` and `helm get values` print rendered Secrets and values. The skill **never runs them** for discovery or enrichment; they are terminal-only runbook commands (see `examples/kubernetes.md`).

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Label selector | `-l app={service}` or `-l app.kubernetes.io/name={service}` |
| Namespace | `-n {namespace}` — if unknown, use `-A` (all namespaces) with a label selector |
| Helm release | `helm list -a --kube-context {context} --filter '{service}'` where Secret read is allowed; otherwise the `managed-by=Helm` label query above |
| Field selector | `--field-selector metadata.name={service}` — exact match on resource name |

## Result parsing

Projected output maps to resource hints as follows:

| Column / field | Maps to | Example |
|----------------|---------|---------|
| `NAME` (`metadata.name`) | Resource name | `widgetapi-web` |
| `KIND` (`kind`) | Resource type | `Deployment`, `Service`, `Ingress` |
| `NS` (`metadata.namespace`) | Namespace context | `widgetapi-prod` |
| `LABELS` (`metadata.labels`) | Additional context (app, version, chart) and Owner | `{app: "widgetapi", version: "1.2.3"}` |
| `RELEASE` (`meta.helm.sh/release-name`) | Helm release | `widgetapi` |
| Other `spec` fields | Used during enrichment through projected jsonpath only (see `examples/kubernetes.md`), never fetched whole | |

**Owner detection (recognition only).** Read from the labels and annotations already fetched. Record **every** signal that matched; the Owner is the controller that reconciles the object (Argo CD or Flux when present, otherwise Helm), and the other signals are listed beside it, e.g. `Owner: argocd (<application>) [also helm label: <release>]`. A chart sets its own `app.kubernetes.io/managed-by` label ("for finding all things managed by Helm", `docs: https://helm.sh/docs/chart_best_practices/labels/`, read 2026-10-27), so it says how the chart was written, not who applies it.

| Signal | Result |
|--------|--------|
| annotation `argocd.argoproj.io/tracking-id` (Argo CD's default tracking method; value `<app>:<group>/<kind>:<namespace>/<name>`). Annotations are not in `LABELS`: add `TRACKING:.metadata.annotations.argocd\.argoproj\.io/tracking-id` to the projection | `Owner: argocd (<application>)` |
| label `argocd.argoproj.io/instance`, only if the cluster sets `application.instanceLabelKey` to it | `Owner: argocd (<application>)` |
| label `app.kubernetes.io/instance` alone | **not a signal**: Argo CD's label tracking uses it, but Helm charts and operators set it too (`docs: https://argo-cd.readthedocs.io/en/stable/user-guide/resource_tracking/`, read 2026-10-27). Needs the annotation above or an Argo CD `Application` object that names the app |
| label `kustomize.toolkit.fluxcd.io/name` | `Owner: flux-kustomization (<name>)` — `UNVERIFIED` label key (not in the Flux docs read 2026-10-27); confirm against the Flux `Kustomization` object |
| label `helm.toolkit.fluxcd.io/name` | `Owner: flux-helmrelease (<name>)` — `UNVERIFIED` label key, as above |
| label `app.kubernetes.io/managed-by: Helm` (+ `meta.helm.sh/release-name`) | `Owner: helm (<release>)` when no controller signal matched |
| label `app.kubernetes.io/managed-by` with another value | `Owner: <value>` as written |
| none | `Owner: unknown` |

A GitOps controller means the desired state lives in Git, not in the cluster: record the owner and do not treat the live object as the source of truth.
