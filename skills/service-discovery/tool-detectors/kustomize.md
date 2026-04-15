---
name: kustomize
url: https://kustomize.io
deploys: Kubernetes resources via overlay-based composition
---

## File signatures
- `kustomization.yaml` / `kustomization.yml`

## Stack boundary
One *base* = one directory containing a `kustomization.yaml` with no `bases:` / `resources:` referencing parent directories. One *overlay instance* = one directory containing a `kustomization.yaml` that references a base via `bases:` (legacy) or `resources:` (current).

The catalog targets one overlay — confirm with the human which overlay directory to use (typically `overlays/<env>/`).

## Parameter sources (highest to lowest priority)
- `kubectl kustomize <overlay-dir>` / `kubectl apply -k <overlay-dir>` — the overlay directory IS the instance selector
- `patches:` / `patchesStrategicMerge:` / `patchesJson6902:` declared in the overlay's `kustomization.yaml`
- `replacements:` declared in the overlay
- `configMapGenerator:` and `secretGenerator:` in the overlay (the latter — NEVER read literal values; record references only)
- Component overlays referenced via `components:`

## Resource extraction
- Each Kubernetes manifest under `resources:` (after applying overlays) → one inventory entry; raw type is `<apiVersion>/<kind>`
- `bases:` / `resources:` pointing at parent paths → sub-stack reference within the same repo; chase as part of the same deploy unit
- `images:` transformations → record image substitutions

## Naming pattern hints
Detect `namePrefix:` and `nameSuffix:` declarations in the overlay; they're applied to every resource.

## Typical cross-stack dependencies
- Same as Helm (ConfigMaps, Secrets, ServiceAccounts, RBAC, external secret stores, ingress controller, etc.)
