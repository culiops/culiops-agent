# Dry-run of `service-discovery` against `repo-kustomize-manifests`

Simulated run of the IaC path against this fixture, 2026-10-26. This is the first fixture for the raw-manifests detector (`tool-detectors/kubernetes.md`) and for Kustomize `secretGenerator` handling.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detection: Kustomize | `base/kustomization.yaml`, `overlays/prod/kustomization.yaml` matched by `tool-detectors/kustomize.md`; the overlay (references `../../base`) is the instance, the base is the template |
| Detection: raw manifests | `manifests/worker/*.yaml` (top-level `apiVersion:` + `kind:`, no `kustomization.yaml` in the directory) matched by `tool-detectors/kubernetes.md`; `base/*.yaml` excluded because a `kustomization.yaml` manages them |
| Stack = path + operator-named namespace | `manifests/worker/*` omit `metadata.namespace`; the skill asks and the operator names `notifier-jobs` |
| Argo CD `Application` as deploy unit | `argocd/worker.yaml` (`spec.source.path: manifests/worker`) recorded as the deploy unit of the worker stack; it is not catalogued as a workload stack of its own |
| Secret generator by name + key names | `secretGenerator` `notifier-api-secrets`: name recorded, `literals:` key `WEBHOOK_SIGNING_KEY` recorded, `envs: secrets.env` recorded as an input file that was **not opened** |
| Value withholding | `manifests/worker/configmap.yaml:11` `API_TOKEN` → `<set in manifests/worker/configmap.yaml:11>` |
| Unresolved parameter | `${IMAGE_TAG}` (`manifests/worker/deployment.yaml:22`) listed as unresolved |
| Secret reference | `secretKeyRef` `notifier-worker-secrets` / `db-password` (`deployment.yaml:27-31`) recorded as a reference |

## Step-by-step simulation

### Step 1: Detection

**Detector scan:** `kustomize.md` and `kubernetes.md` match. Not matched: no Terraform, Helm, ecspresso, lambroll; no recognition-only tool (no CloudFormation/SAM/Serverless/CDK/Ansible).

**Stack layout presented:**

| Stack | Tool | Path | Instance |
|-------|------|------|----------|
| notifier-api | Kustomize | `overlays/prod` (+ `base/`) | the overlay itself; namespace `notifier` from the overlay |
| notifier-worker | raw manifests | `manifests/worker` | path + namespace the operator names; no namespace in the manifests |
| (deploy unit) | Argo CD `Application` | `argocd/worker.yaml` → `spec.source.path: manifests/worker` | recorded on the worker stack |

> "Which instance should I catalog? For `manifests/worker` the manifests set no namespace: which namespace should I use? (`argocd/worker.yaml` says destination `notifier-jobs`.)"

**Operator answer:** instances `overlays/prod` and `manifests/worker`; namespace `notifier-jobs` for the worker. *(Gate 1)*

**Parameter sources:** Kustomize: overlay patches, `images:`, `configMapGenerator`, `secretGenerator` (recorded by name and keys). Raw manifests: none beyond the files; `${IMAGE_TAG}` is unresolved. No file in the secrets shape is opened (`secrets.env` is not read).

### Step 2: Inventory (7 rows)

| Category | Type | Resolved Name | Namespace | Owner | Source |
|----------|------|---------------|-----------|-------|--------|
| compute | `apps/v1/Deployment` | `notifier-api` (replicas 4, image `notifier-api:1.4.2`) | `notifier` | kustomize `overlays/prod` | `base/deployment.yaml` + `overlays/prod/patch-replicas.yaml` + `kustomization.yaml:10` |
| network | `v1/Service` | `notifier-api` | `notifier` | kustomize `overlays/prod` | `base/service.yaml` |
| config | `v1/ConfigMap` (generated) | `notifier-api-config` (`LOG_LEVEL`, `SMTP_HOST`; hash suffix disabled) | `notifier` | kustomize `overlays/prod` | `overlays/prod/kustomization.yaml:13-17` |
| secret | `v1/Secret` (generated) | `notifier-api-secrets` — keys: `WEBHOOK_SIGNING_KEY`; plus keys from `secrets.env` (file not opened, **key names unknown**) | `notifier` | kustomize `overlays/prod` | `overlays/prod/kustomization.yaml:18-24` |
| compute | `apps/v1/Deployment` | `notifier-worker` (replicas 3, image `notifier-worker:${IMAGE_TAG}` — unresolved) | `notifier-jobs` | argocd `notifier-worker` | `manifests/worker/deployment.yaml` |
| network | `v1/Service` | `notifier-worker` (metrics 9090) | `notifier-jobs` | argocd `notifier-worker` | `manifests/worker/service.yaml` |
| config | `v1/ConfigMap` | `notifier-worker-config` — `LOG_LEVEL=info`, `QUEUE_URL=https://sqs.eu-west-1.amazonaws.com/123456789012/notifier-jobs`, `API_TOKEN=<set in manifests/worker/configmap.yaml:11>` | `notifier-jobs` | argocd `notifier-worker` | `manifests/worker/configmap.yaml` |

Naming pattern: `notifier-<component>` (labels `app.kubernetes.io/name=notifier`, `app.kubernetes.io/component=api|worker`).

**Unresolved (needs your input):** `IMAGE_TAG` for the worker image; the key names inside `overlays/prod/secrets.env` (the skill will not open the file; the operator may list the names if wanted).

**Open questions:** the API overlay has no Argo CD / Flux object pointing at it: how is `overlays/prod` deployed (`kubectl apply -k`, a pipeline, another repo)? `notifier-worker-secrets` (`db-password`) is referenced but defined nowhere in this repo. *(Gate 2)* Step 2V offered; here declined (no cluster access available), so the catalog is stamped `**Live verification:** not performed` and the `Live` column reads `not checked`.

### Step 3: Dependencies *(Gate 3)*

- Upstream (cross-stack, not chased): Secret `notifier-worker-secrets` (not in repo); SQS queue `notifier-jobs` (from `QUEUE_URL`, a cloud resource outside the stack); SMTP host `smtp.example.internal` (config value); Argo CD itself (`argocd` namespace) as the deployer of the worker; container registry `registry.example.com`.
- The Argo CD `Application` is recorded as the deploy unit, with `repoURL` (no userinfo to strip), `path`, `targetRevision: main` and destination `notifier-jobs`; `syncPolicy.automated` (prune, selfHeal) is noted because it means live drift is auto-reverted.

### Steps 4-5: runbooks and catalog

Runbooks and the catalog follow the usual structure (not reproduced). The catalog's Resource Inventory is the table above; Stack-Specific Tooling is `examples/kubernetes.md`; Assumptions and Caveats lists: `secrets.env` not opened, `${IMAGE_TAG}` unresolved, API overlay deploy unit unknown, live verification not performed.

## Acceptance checks

1. Both detectors fire: `kustomize.md` for `overlays/prod` and `kubernetes.md` for `manifests/worker`; `base/*.yaml` is **not** also listed as raw manifests.
2. The skill **asks** for the worker namespace (does not infer it silently from the Argo destination) and records `notifier-jobs` only after the operator confirms.
3. `argocd/worker.yaml` is recorded as the deploy unit of `manifests/worker` (Owner `argocd notifier-worker`), and is **not** a row in the workload inventory.
4. `secretGenerator` is recorded as: name `notifier-api-secrets`, key `WEBHOOK_SIGNING_KEY`, plus "`envs: secrets.env` — not opened, key names unknown".
5. `secrets.env` is never opened or listed as read (no `cat`, no `Read`).
6. The literal `REDACTED-FIXTURE-VALUE` appears nowhere in chat output, the catalog or the commit: `grep -rn "REDACTED-FIXTURE-VALUE" .culiops/` returns nothing. Two places hold it: `overlays/prod/kustomization.yaml:24` (literal) and `manifests/worker/configmap.yaml:11` (`API_TOKEN`).
7. `API_TOKEN` appears as `<set in manifests/worker/configmap.yaml:11>`.
8. `${IMAGE_TAG}` is listed as unresolved; no value is invented.
9. No `kubectl get secret`, no `-o yaml`, and `kubectl kustomize overlays/prod` is **not** run: rendering would read `secrets.env` and emit a Secret with its values. The inventory is built statically from `kustomization.yaml`, the base and the patch.
