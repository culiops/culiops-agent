---
name: kubernetes
url: https://kubernetes.io/docs/concepts/overview/working-with-objects/
deploys: Kubernetes resources defined as raw YAML/JSON manifests
---

## File signatures
- `*.yaml` / `*.yml` / `*.json` with top-level `apiVersion:` AND `kind:` (multi-document YAML: check each `---` document)
- Exclude: Helm `templates/**`, any directory managed by a `kustomization.yaml` / `Kustomization` (those are kustomize resources — use `kustomize.md`), `charts/**`, `.terraform/**`, `node_modules/**`
- `kind: Kustomization` with `kustomize.config.k8s.io` is kustomize; with `kustomize.toolkit.fluxcd.io` it is a Flux object (see Stack boundary)

## Stack boundary
One stack = the manifest path plus the namespace the operator names (ask; manifests often omit `metadata.namespace`).

If an Argo CD `Application` (`spec.source.path`) or a Flux `Kustomization` (`spec.path`) points at the path, record that object as the deploy unit and name it in the catalog.

## Secret-bearing files
- `Secret` objects: record `namespace/name` and the KEY names under `data` / `stringData` only. Never record, quote or summarise values (base64 is not protection).
- `secrets*.yaml`, `*.sops.*`, `*.enc.*` are not opened at all; never run `sops -d`. SealedSecret / ExternalSecret objects: record the name and the referenced store/key path only.
- ConfigMaps and env entries: withhold a value (`<set in <file>:<line>>`) when the key contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert`.

## Parameter sources (highest to lowest priority)
- None beyond the files themselves. `envsubst`-style `${VAR}` / `$(VAR)` placeholders are recorded as UNRESOLVED (the deploy pipeline supplies them; ask the operator).

## Resource extraction
- One row per object: `kind/namespace/name`, with `path:line`; raw type is `<apiVersion>/<kind>`
- Pod-spec images, ports, probes, resource requests/limits, and `envFrom` / `secretKeyRef` references → record as references, not values

## Naming pattern hints
Raw manifests carry literal names. Record any recurring `app.kubernetes.io/*` label scheme as the inferred ownership convention.

## Typical cross-stack dependencies
- ConfigMap / Secret references (`envFrom`, `volumes`, `secretKeyRef`) to objects defined elsewhere
- ServiceAccount with IRSA annotation `eks.amazonaws.com/role-arn` → IAM role dependency
- Ingress with AWS Load Balancer Controller annotations (`alb.ingress.kubernetes.io/*`) → ALB, certificates, WAF ACL
- PersistentVolumeClaim `storageClassName` → StorageClass provisioned outside the manifests
