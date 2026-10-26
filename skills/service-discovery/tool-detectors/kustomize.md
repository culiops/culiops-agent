---
name: kustomize
url: https://kustomize.io
deploys: Kubernetes resources via overlay-based composition
---

## File signatures
- `kustomization.yaml` / `kustomization.yml`
- `Kustomization` (capital K, no extension; also accepted by kustomize)
- A YAML file with `kind: Kustomization` and `apiVersion: kustomize.config.k8s.io/...` is a kustomize file; one with `kustomize.toolkit.fluxcd.io/...` is a Flux object (a deploy-unit signal, not a kustomize file)

## Stack boundary
One *base* = one directory containing a `kustomization.yaml` with no `bases:` / `resources:` referencing parent directories. One *overlay instance* = one directory containing a `kustomization.yaml` that references a base via `bases:` (legacy) or `resources:` (current).

The catalog targets one overlay — confirm with the human which overlay directory to use (typically `overlays/<env>/`). A Flux `Kustomization` (`spec.path`) or Argo CD `Application` pointing at the directory is recorded as the deploy unit.

## Secret-bearing files
- NEVER run `sops -d`; `secrets*.yaml`, `*.sops.*`, `*.enc.*` are not opened at all.
- `secretGenerator` (`files:` / `envs:` / `literals:`): record the generator NAME and the KEY names only. Never open the files or envs it lists, never record literal values.
- `configMapGenerator`: key names and non-secret values only; withhold a value (`<set in <file>:<line>>`) when the key contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert`.
- Rendered `Secret` objects: name and keys only.

## Parameter sources (highest to lowest priority)
- The overlay directory IS the instance selector (`kubectl kustomize <overlay-dir>` / `kubectl apply -k <overlay-dir>`)
- `patches:` / `patchesStrategicMerge:` / `patchesJson6902:` declared in the overlay's `kustomization.yaml`
- `replacements:` declared in the overlay
- `configMapGenerator:` and `secretGenerator:` in the overlay (see Secret-bearing files)
- `components:` — reusable pieces referenced from the overlay; read them as part of the same deploy unit
- `helmCharts:` (Helm inflation) — record chart name, repo, version, `releaseName`, `namespace`, `valuesFile` / `valuesInline` (apply the Helm detector's secret rules); do not render or fetch

## Resource extraction
- Each Kubernetes manifest under `resources:` (after applying overlays) → one inventory entry; raw type is `<apiVersion>/<kind>`
- `bases:` / `resources:` pointing at parent paths → sub-stack reference within the same repo; chase as part of the same deploy unit
- Remote bases / resources (`github.com/org/repo//path?ref=<tag>`, `https://...`): record URL + ref as a dependency; do not fetch. Flag a floating ref (branch, no `?ref=`) as unpinned
- `images:` transformations → record image substitutions

## Naming pattern hints
Detect `namePrefix:` and `nameSuffix:` declarations in the overlay; they're applied to every resource.

## Typical cross-stack dependencies
- Same as Helm (ConfigMaps, Secrets, ServiceAccounts, RBAC, external secret stores, ingress controller, etc.)
