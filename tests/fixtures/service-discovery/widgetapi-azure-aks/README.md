# widgetapi — Azure / AKS / Bicep / Helm fixture

A synthetic repo used to validate the `service-discovery` skill against a second IaC tool (Bicep) and a second cloud (Azure). Same `widgetapi` architecture as the AWS fixture, re-platformed onto Azure equivalents. Nothing here is runnable — it is **plausible-looking input** for the skill to read.

## Azure equivalents

| AWS (fixture A) | Azure (this fixture) |
|-----------------|----------------------|
| EKS | AKS |
| ALB | Application Gateway |
| CloudFront | Azure Front Door (Standard) |
| RDS PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| ElastiCache Redis | Azure Cache for Redis |
| S3 | Azure Blob Storage (Storage Account) |
| SQS | Azure Service Bus Queue |
| AWS Secrets Manager | Azure Key Vault |
| IRSA (IAM-for-ServiceAccount via OIDC) | Workload Identity (User-Assigned Managed Identity federated to the AKS OIDC issuer) |
| AWS account | Azure subscription |
| AWS region (`eu-west-1`) | Azure region (`westeurope`) |

## What's modelled

Same as fixture A: an HTTP API for CRUD on widgets with image uploads, a web Deployment fronted by Application Gateway and cached at Front Door, plus an async worker Deployment consuming a Service Bus queue.

- **Data:** PostgreSQL Flexible (primary + read replica), Azure Cache for Redis, Blob container for uploads.
- **Async:** Service Bus queue `async` with a dead-letter.
- **Identity:** pods assume a User-Assigned Managed Identity via Workload Identity federation (AKS OIDC issuer → federated credential → UAMI). The UAMI has `Storage Blob Data Contributor` on the uploads container, `Azure Service Bus Data Receiver/Sender` on the queue, and `Key Vault Secrets User` on the vault that holds the Postgres password.
- **Observability (third-party):** Datadog agent via Helm subchart; alerts route to PagerDuty via a Kubernetes Secret. Azure-native observability (Azure Monitor / Log Analytics / Application Insights) runs in parallel — this fixture references both so the skill has to surface both.

## Environments

Two environments, both in `westeurope`:

- `prod` — higher SKUs, zone-redundant where available (PostgreSQL `ZoneRedundant`, Redis `Premium`, AFD `Premium_AzureFrontDoor`).
- `staging` — smaller SKUs, single-zone, reduced replica counts.

Environment selection flows through two axes:

- **Bicep:** each stack (`infra/`, `platform/`) is one `main.bicep` deployed at resource-group scope. Per-env parameter files live alongside as `*.parameters.<env>.json`. An operator runs `az deployment group create -g widgetapi-<env>-rg -f infra/main.bicep -p infra/infra.parameters.<env>.json`.
- **Helm:** one chart under `helm/widgetapi/`; per-env overrides live in `values-<env>.yaml`.

## Stack layout

```
widgetapi-azure-aks/
├── infra/
│   ├── main.bicep                      # VNet + Postgres + Redis + Storage + Service Bus + Key Vault
│   ├── infra.parameters.prod.json
│   └── infra.parameters.staging.json
├── platform/
│   ├── main.bicep                      # AKS + AGW + AFD + UAMI (Workload Identity)
│   ├── platform.parameters.prod.json
│   └── platform.parameters.staging.json
├── helm/
│   └── widgetapi/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-prod.yaml
│       ├── values-staging.yaml
│       └── templates/
└── docs/
    └── oncall.md
```

## Naming convention

All resources follow `widgetapi-<env>-<component>`:

- `widgetapi-prod-pg` (PostgreSQL Flexible Server)
- `widgetapi-prod-cache` (Azure Cache for Redis)
- `widgetapi-prod-uploads` (Storage Account; blob container `uploads`)
- `widgetapi-prod-sb` (Service Bus namespace; queue `async`)
- `widgetapi-prod-kv` (Key Vault)
- `widgetapi-prod-aks` (AKS cluster)
- `widgetapi-prod-agw` (Application Gateway)
- `widgetapi-prod-afd` (Front Door profile)
- `widgetapi-prod-id` (User-Assigned Managed Identity for the workload)

## What this fixture exercises (beyond fixture A)

- **Second IaC tool:** Bicep. The Step 1 detector must pick `*.bicep` and not confuse it with Terraform.
- **Second cloud:** Azure. The skill must route to `examples/azure.md` rather than `examples/aws.md`.
- **Different workload-identity model:** AKS Workload Identity (federated UAMI) instead of EKS IRSA. The ServiceAccount annotations differ (`azure.workload.identity/client-id` instead of `eks.amazonaws.com/role-arn`).
- **Cross-RG reference pattern:** `platform` references `infra` via `existing` resource declarations pointing at a different resource group — Bicep's equivalent of `terraform_remote_state`. The skill must record this as a cross-stack dependency.
- **Azure-native observability coexisting with Datadog:** runbooks need to mention both Azure Monitor/Log Analytics/App Insights (native) AND Datadog (third-party); the skill should surface both paths.
