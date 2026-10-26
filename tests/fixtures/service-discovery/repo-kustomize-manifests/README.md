# repo-kustomize-manifests — Kustomize + raw manifests fixture

A synthetic Kubernetes deploy repo with two different ways of shipping workloads, so the skill's Kustomize detector and the new raw-manifests detector (`tool-detectors/kubernetes.md`) are both exercised. Nothing is runnable.

## What's modelled

`notifier` — a fictional notification service in two parts:

- **`notifier-api`** (Kustomize): `base/` (Deployment + Service) and `overlays/prod/` (namespace `notifier`, replicas patch, image tag `1.4.2`, a `configMapGenerator`, and a `secretGenerator` named `notifier-api-secrets`). The generator reads `envs: [secrets.env]` and one `literals:` entry (`WEBHOOK_SIGNING_KEY`). `secrets.env` is gitignored and **absent from this fixture**: the skill must not open it, and it cannot learn that file's key names.
- **`notifier-worker`** (raw manifests): `manifests/worker/` holds a Deployment (3 replicas, image `registry.example.com/notifier-worker:${IMAGE_TAG}`), a Service and a ConfigMap. None sets `metadata.namespace`.
- **Deploy unit for the worker:** `argocd/worker.yaml`, an Argo CD `Application` (`spec.source.path: manifests/worker`, destination namespace `notifier-jobs`).
- The API overlay has no Argo CD / Flux object pointing at it, so its deploy unit is unknown.

## Stack layout

```
repo-kustomize-manifests/
├── base/                    # Kustomize base (template, not an instance)
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
├── overlays/prod/           # Kustomize overlay = the instance
│   ├── kustomization.yaml   # namespace, patches, images, configMapGenerator, secretGenerator
│   └── patch-replicas.yaml  #   (secrets.env: gitignored, not present)
├── manifests/worker/        # raw manifests (no kustomization.yaml here)
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── argocd/
    └── worker.yaml          # Argo CD Application -> manifests/worker
```

## What this fixture exercises in the skill

- **Detection of two tools in one repo:** `kustomize.md` (`base/`, `overlays/prod/`) and `kubernetes.md` (`manifests/worker/`, `argocd/`). Raw-manifest detection excludes the directories a `kustomization.yaml` manages, so `base/*.yaml` is not double-counted.
- **Stack = path + namespace the operator names** for raw manifests (the manifests omit the namespace).
- **Argo CD `Application` as deploy unit:** `argocd/worker.yaml` is itself a raw manifest (`apiVersion` + `kind`), but it is recorded as the deploy unit of `manifests/worker`, not catalogued as a workload stack.
- **Secrets by projection:**
  - `secretGenerator` recorded by generator name + key names only; `secrets.env` is never opened (its key names are therefore unknown and said to be unknown); the `literals:` key `WEBHOOK_SIGNING_KEY` is recorded by name, its value withheld.
  - ConfigMap key `API_TOKEN` matches the secret-key list, so its value is recorded as `<set in manifests/worker/configmap.yaml:11>`.
  - `secretKeyRef` (`notifier-worker-secrets` / `db-password`) recorded as a reference; the Secret is not defined in the repo and is never fetched.
- **Unresolved parameter:** `${IMAGE_TAG}` (an `envsubst`-style placeholder supplied by the deploy pipeline) is recorded as unresolved, not guessed.
