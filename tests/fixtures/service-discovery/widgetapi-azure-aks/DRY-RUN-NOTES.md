# Dry-run of `service-discovery` against `widgetapi-azure-aks`

Simulated run of the post-fixture-A skill against this fixture. Recorded on 2026-04-15.

## Goal

Fixture B tests the skill against a *different* IaC tool (Bicep) and a *different* cloud (Azure) to prove cloud-agnostic and IaC-agnostic design. Same application shape as fixture A, translated to Azure equivalents (AKS, AGW, AFD, PG Flexible, Azure Cache for Redis, Service Bus, Blob Storage, Key Vault, Workload Identity).

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Second IaC tool (Bicep) | 2 Bicep stacks with `*.parameters.<env>.json` parameter files |
| Second cloud (Azure) | Skill must route to `examples/azure.md` not `examples/aws.md` |
| Cross-stack reference pattern (Bicep) | `platform/main.bicep` uses `existing` resources with `scope: resourceGroup(infraResourceGroup)` — the Bicep equivalent of `terraform_remote_state` |
| Different workload-identity model | Workload Identity (federated UAMI) instead of IRSA; ServiceAccount annotation is `azure.workload.identity/client-id` not `eks.amazonaws.com/role-arn` |
| Azure-native + third-party observability coexist | Log Analytics / App Insights / Azure Monitor AND Datadog — the skill surfaces both; `examples/azure.md` covers the native side and Datadog stays as "ask the team" |
| Naming pattern edge case | Storage account must be `widgetapi${env}uploads` (no dashes — Azure restriction) while everything else is `widgetapi-${env}-<component>` — the skill's "record both forms and flag" rule handles this |
| Bicep-specific conditional resources | `if (pgCreateReadReplica)` conditional — true in prod, false in staging — and `environment == 'prod' ? X : Y` ternary conditionals throughout |
| CSI Secrets Store integration | `SecretProviderClass` referencing Key Vault — the skill treats this as a Kubernetes resource and its secret refs are recorded, not read |

## Findings and fixes applied

### F8 — Bicep missing from Step 1 stack-layout bullets *(fixed)*

The Step 1 detection table lists Bicep (`*.bicep`, `bicepconfig.json`), but the stack-layout bullets below only covered Terraform/CloudFormation/Pulumi/Helm/Kustomize. A catalog author following the spec wouldn't know how to define a "Bicep stack." Added a Bicep bullet.

### F9 — Bicep missing from Step 1 parameter-source detection *(fixed)*

Same gap on the parameter-source side. Added a Bicep bullet covering `*.parameters.<env>.json`, `.bicepparam`, inline `-p` overrides, and `@Microsoft.KeyVault(...)` URI references.

### F11 — Bicep missing from Step 3 direct-dependency detection *(fixed)*

The Step 3 dependency-extraction list had Terraform/CloudFormation/Pulumi/Helm/Kustomize but not Bicep. A catalog author wouldn't know that `existing` resources with cross-scope (`scope: resourceGroup(...)`) are the cross-stack references to record. Added the bullet.

### F10 — Naming inconsistency (Azure storage account) *(no change needed)*

The storage account is `widgetapi${env}uploads` (no dashes) because Azure storage-account names must be lowercase alphanumeric only. All other resources follow `widgetapi-${env}-<component>`. Step 2's existing rule — "if the pattern is inconsistent across resources, record both forms and flag" — covers this correctly. The runbook would list both forms.

### F12 — `examples/azure.md` AKS section could add Workload-Identity introspection commands *(no change — enhancement, not a correctness gap)*

The current AKS section in `examples/azure.md` lists cluster status, node pools, credentials, and generic kubectl. Workload-Identity troubleshooting (`az identity federated-credential list`, `az aks show --query 'properties.oidcIssuerProfile'`) would be useful but the runbook can reach these via the generic `az aks show` + `az identity show` pattern. Leave as-is; revisit if a future fixture exercises a WI-specific incident.

## Cross-fixture comparison

| Axis | Fixture A (AWS/EKS/TF) | Fixture B (Azure/AKS/Bicep) | Skill behaviour |
|------|------------------------|-----------------------------|-----------------|
| IaC tool | Terraform | Bicep | Detection table hit both; stack-layout rules now cover both |
| Parameter source | `envs/<env>.tfvars` | `*.parameters.<env>.json` | Both now named in Step 1 |
| Cross-stack ref | `terraform_remote_state` | `existing` + `scope: resourceGroup()` | Both now named in Step 3 |
| Cloud | AWS | Azure | Routed to `examples/aws.md` vs `examples/azure.md` respectively |
| Kubernetes | EKS | AKS | Both → `examples/kubernetes.md` in addition |
| Workload identity | IRSA | WI + UAMI | Skill records the SA → role binding in both cases |
| Secret store | Secrets Manager | Key Vault | Both surfaced as references, never as values |
| Queue | SQS + DLQ | Service Bus + DLQ | Both captured as async-not-critical |
| Naming | Consistent `${service}-${env}-<c>` | Mostly consistent; Azure storage forces no-dashes | Both cases handled |
| Third-party SaaS | Datadog / PagerDuty / Stripe / SendGrid / LaunchDarkly | Same + Azure-native observability alongside | Both surface to "ask the team" for third-party, plus `examples/azure.md` for native |

## What a produced doc would look like

`.culiops/service-discovery/widgetapi-prod.md` (for this fixture):

- Header: tools = **Bicep, Helm**, instance = `prod`, cataloged 2026-04-15.
- `## Prerequisites` — `az` ≥ 2.50 (+ `application-insights` + `log-analytics` extensions), `kubectl` ≥ 1.28, `helm` ≥ 3.12; `az login` → `az aks get-credentials`; least-privilege Azure Reader + Monitoring Reader + Log Analytics Reader + App Insights Reader; Kubernetes `view` at namespace `widgetapi`; Datadog read-only API key; mutations listed.
- `## Resource Inventory` — 21 Azure resources + 8 Kubernetes resources = 29 rows, grouped by category.
- `## Naming Patterns` — `widgetapi-${env}-<component>` plus exception `widgetapi${env}uploads` (Azure storage-account restriction).
- `## Dependency Graph` — `platform → infra` (cross-RG, via `existing` refs); `helm → platform + infra` (via values file); third-party upstreams: Key Vault (for Postgres password, Datadog API key, PagerDuty key, Stripe/SendGrid keys), Stripe, SendGrid, LaunchDarkly, Datadog.
- `## Stack-Specific Tooling` — `examples/azure.md` + `examples/kubernetes.md` primary; Datadog / PagerDuty / Stripe / SendGrid / LaunchDarkly as "ask the team."
- `## Assumptions and Caveats` — drift note; no declared SLO; Helm image tag env-specific.

## Conclusion

Fixture B exposed exactly the kind of gaps a second fixture should: Bicep was completely absent from three SKILL.md lists that a Terraform-only author had no reason to populate. After the three patches, the skill now handles Bicep + Azure end-to-end the same way it handles Terraform + AWS. The cloud×k8s orthogonality introduced for AKS/GKE/EKS held up under the Azure fixture's Workload Identity model without changes.
