# Examples: Azure CLI Templates for `iac-change-execution`

Reference command templates for the `iac-change-execution` skill when the target infrastructure is Azure. The skill reads this file during Step 1 (Research gap-filling), Step 4c (Apply), and Step 5a (Verification).

Replace placeholders (`{cluster}`, `{rg}`, `{subscription}`, `{region}`, `{server}`, `{app}`, etc.) with the values resolved in Step 1 research or detected from the plan output.

## Prerequisites

**CLI tool:** Azure CLI v2 (`az --version` >= 2.x). Verify: `az version`.

**Authentication:** `az login` for interactive sessions, or `az login --service-principal -u {client-id} -p {client-secret} --tenant {tenant-id}` for service principals. Confirm active identity: `az account show`.

**Subscription:** Set the active subscription before running commands: `az account set --subscription {subscription}`. Verify: `az account show --query '{name:name,id:id}'`.

**Least-privilege RBAC — TWO tiers are required for this skill.**

- **Tier 1 (Steps 1 and 5 — read-only):** built-in `Reader` role scoped to the resource group or subscription. Never use `Contributor` or `Owner` for read-only operations.
- **Tier 2 (Step 4 — mutation only):** the minimum scoped role that permits the specific mutation — e.g., `Website Contributor` for App Service, `Azure Kubernetes Service Contributor Role` for AKS, or a custom role with only the required `*/write` actions on the target resource. Elevated permissions must be assumed immediately before the mutation and dropped after.

**Cost awareness:** Azure Monitor Metrics API calls are billed per metric query at scale. Prefer the Azure Portal for spot checks during a live incident; use CLI for scripted verification.

---

## Research Queries (Step 1 — Read-Only)

### AKS — current cluster state

- Cluster details: `az aks show --name {cluster} --resource-group {rg} --subscription {subscription}`
- Cluster version and state: `az aks show --name {cluster} --resource-group {rg} --query '{provisioningState:provisioningState,kubernetesVersion:kubernetesVersion,powerState:powerState.code}'`
- Node pool list: `az aks nodepool list --cluster-name {cluster} --resource-group {rg} --subscription {subscription}`
- Specific node pool details: `az aks nodepool show --cluster-name {cluster} --resource-group {rg} --name {nodepool} --subscription {subscription}`

### App Service — current service state

- App details: `az webapp show --name {app} --resource-group {rg} --subscription {subscription}`
- App state and SKU: `az webapp show --name {app} --resource-group {rg} --query '{state:state,sku:sku.name,kind:kind}'`
- App settings (names only, not values): `az webapp config appsettings list --name {app} --resource-group {rg} --query '[].name'`
- Current deployment: `az webapp deployment source show --name {app} --resource-group {rg}` (if source control connected)

### Azure SQL — current database state

- Server details: `az sql server show --name {server} --resource-group {rg} --subscription {subscription}`
- Database details: `az sql db show --server {server} --name {database} --resource-group {rg} --subscription {subscription}`
- Database tier and state: `az sql db show --server {server} --name {database} --resource-group {rg} --query '{status:status,sku:sku.name,tier:sku.tier,maxSizeBytes:maxSizeBytes}'`
- Pending operations: `az sql db op list --server {server} --name {database} --resource-group {rg}`

### PostgreSQL Flexible Server — current state

- Server details: `az postgres flexible-server show --name {server} --resource-group {rg} --subscription {subscription}`
- Server state: `az postgres flexible-server show --name {server} --resource-group {rg} --query '{state:state,sku:sku.name,tier:sku.tier,version:version}'`
- Server parameters: `az postgres flexible-server parameter list --server-name {server} --resource-group {rg}`

### Container Apps — current app state

- App details: `az containerapp show --name {app} --resource-group {rg} --subscription {subscription}`
- Revision list: `az containerapp revision list --name {app} --resource-group {rg}`
- Current image: `az containerapp show --name {app} --resource-group {rg} --query 'properties.template.containers[0].image'`
- Traffic weights: `az containerapp show --name {app} --resource-group {rg} --query 'properties.configuration.ingress.traffic'`

### NSG rules — current network config

- List NSG rules: `az network nsg rule list --nsg-name {nsg} --resource-group {rg} --subscription {subscription} --output table`
- Specific NSG details: `az network nsg show --name {nsg} --resource-group {rg} --subscription {subscription}`

### Key Vault — names only, never content

- List Key Vault names: `az keyvault list --resource-group {rg} --query '[].{name:name,location:location}' --subscription {subscription}`
- List secret names (not values): `az keyvault secret list --vault-name {vault} --query '[].{name:name,enabled:attributes.enabled}'`
- List key names: `az keyvault key list --vault-name {vault} --query '[].{name:name,enabled:attributes.enabled}'`

**Never retrieve secret or key values during research.** If the change requires knowing a value, ask the operator to provide it.

---

## Verification Checks (Step 5 — Read-Only)

### AKS — post-apply cluster health

- Provisioning state (expect `Succeeded`): `az aks show --name {cluster} --resource-group {rg} --query 'provisioningState'`
- Node pool provisioning state (expect `Succeeded`): `az aks nodepool show --cluster-name {cluster} --resource-group {rg} --name {nodepool} --query 'provisioningState'`
- Workload status (kubectl): `kubectl get deploy -n {namespace} -o wide` (requires `az aks get-credentials --name {cluster} --resource-group {rg}`)
- Pod readiness: `kubectl get pods -n {namespace} -l app={service}`

### Azure SQL — post-apply database state

- Database status (expect `Online`): `az sql db show --server {server} --name {database} --resource-group {rg} --query 'status'`
- Pending operations (expect empty): `az sql db op list --server {server} --name {database} --resource-group {rg}`

### PostgreSQL Flexible Server — post-apply state

- Server state (expect `Ready`): `az postgres flexible-server show --name {server} --resource-group {rg} --query 'state'`
- Pending operations: `az postgres flexible-server show --name {server} --resource-group {rg} --query 'maintenanceWindow'`

### App Service — post-apply state

- App state (expect `Running`): `az webapp show --name {app} --resource-group {rg} --query 'state'`
- Deployment status: `az webapp log deployment list --name {app} --resource-group {rg}`

### Azure Monitor — alert rules and fired alerts

- List alert rules for resource group: `az monitor alert list --resource-group {rg} --subscription {subscription} --output table`
- Alert rules in fired state: `az monitor alert list --resource-group {rg} --query '[?condition.allOf[].operator]' --output table`
- Activity log (recent events for resource): `az monitor activity-log list --resource-group {rg} --start-time {T-1h} --offset 1h --output table`

---

## Apply Commands (Step 4c — MUTATION)

Each command below changes cloud state. The skill presents each command to the operator and waits for explicit approval before running. Assume Tier 2 elevated RBAC permissions are active.

### Terraform

**MUTATION** — `terraform apply tfplan`
- Blast radius: all resources in the plan output; varies by change. Review plan output before approving.
- Elevated permission required: scoped RBAC role with the minimum write actions on the specific Azure resource types in the plan (e.g., `Website Contributor` for App Service, `AKS Contributor` for AKS). Never use `Owner` or unscoped `Contributor` for apply.
- Rollback path: `terraform apply` from the previous state file snapshot, or manual revert per resource; no automated rollback.
- Note: `tfplan` is the binary produced by `terraform plan -out=tfplan`. Never run `terraform apply` without the plan file.

### Bicep — az deployment group create

**MUTATION** — `az deployment group create --resource-group {rg} --template-file {template.bicep} --parameters {parameters.json} --subscription {subscription}`
- Blast radius: all resources defined in the Bicep template targeting the resource group; use `--what-if` flag first to preview changes: `az deployment group what-if --resource-group {rg} --template-file {template.bicep} --parameters {parameters.json}`.
- Elevated permission required: `Contributor` scoped to the target resource group, or a custom role with only the required `*/write` actions on the resource types in the template.
- Rollback path: re-deploy the previous template version with the same command and the previous parameter values. For resources not managed by the Bicep template, revert manually.
- Note: always run `az deployment group what-if` (Step 4a) and review output before running the create command.

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{cluster}` | AKS cluster name | `widgetapi-prod-aks` |
| `{app}` | App Service or Container App name | `widgetapi-prod-api` |
| `{server}` | Azure SQL or PostgreSQL server name | `widgetapi-prod-sql` |
| `{database}` | Database name | `widgetapi` |
| `{nsg}` | Network security group name | `widgetapi-prod-nsg` |
| `{vault}` | Key Vault name | `widgetapi-prod-kv` |
| `{rg}` | Resource group name | `widgetapi-prod-rg` |
| `{subscription}` | Azure subscription ID or name | `00000000-0000-0000-0000-000000000000` |
| `{region}` | Azure region | `westeurope` |
| `{nodepool}` | AKS node pool name | `default` |
| `{namespace}` | Kubernetes namespace | `production` |
| `{T-1h}` | ISO-8601 time offset 1 hour ago | `2026-04-24T09:00:00Z` |
| `{template.bicep}` | Path to Bicep template file | `./infra/main.bicep` |
| `{parameters.json}` | Path to Bicep parameters file | `./infra/prod.parameters.json` |
