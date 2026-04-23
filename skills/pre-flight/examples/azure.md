# Examples: Azure CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer when the target infrastructure is Azure.

Replace placeholders (`{rg}`, `{name}`, `{subscription}`, etc.) with values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** Azure CLI (`az --version` >= 2.x).

**Authentication:** `az login` (interactive, service principal, or managed identity). Confirm identity: `az account show`.

**Least-privilege RBAC — every command below is read-only.** Grant the operator:
- **Baseline:** `Reader` role on the resource group(s)
- **Tighter:** `Monitoring Reader` + resource-specific reader roles as applicable

**Never use `Contributor`, `Owner`, or custom roles with write access** for pre-flight read-only checks.

**Cost awareness:** Log Analytics queries incur per-GB charges. Azure Monitor metrics API calls are metered.

---

## Resource Health Checks

### AKS (Azure Kubernetes Service)

- Cluster status: `az aks show --name {cluster} --resource-group {rg} --query 'provisioningState' -o tsv`
- Node pool status: `az aks nodepool list --cluster-name {cluster} --resource-group {rg} --query '[].{name:name,status:provisioningState,count:count,vmSize:vmSize}' -o table`

### Azure SQL / Flexible Server

- Server status: `az postgres flexible-server show --name {server} --resource-group {rg} --query 'state' -o tsv`
- CPU percent (last 1h): `az monitor metrics list --resource {resource-id} --metric-names cpu_percent --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Storage percent: `az monitor metrics list --resource {resource-id} --metric-names storage_percent --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Active connections: `az monitor metrics list --resource {resource-id} --metric-names active_connections --interval PT5M --start-time {T-1h} --end-time {now} -o table`

### App Service / Web App

- Status: `az webapp show --name {app} --resource-group {rg} --query 'state' -o tsv`
- HTTP 5xx: `az monitor metrics list --resource {resource-id} --metric-names Http5xx --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Response time: `az monitor metrics list --resource {resource-id} --metric-names AverageResponseTime --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Requests: `az monitor metrics list --resource {resource-id} --metric-names Requests --interval PT5M --start-time {T-1h} --end-time {now} -o table`

### Azure Functions

- Execution count: `az monitor metrics list --resource {resource-id} --metric-names FunctionExecutionCount --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Execution errors: `az monitor metrics list --resource {resource-id} --metric-names Http5xx --interval PT5M --start-time {T-1h} --end-time {now} -o table`

### Azure Cache for Redis

- Server load: `az monitor metrics list --resource {resource-id} --metric-names serverLoad --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Connected clients: `az monitor metrics list --resource {resource-id} --metric-names connectedclients --interval PT5M --start-time {T-1h} --end-time {now} -o table`
- Cache hit rate: `az monitor metrics list --resource {resource-id} --metric-names cachehits,cachemisses --interval PT5M --start-time {T-1h} --end-time {now} -o table`

---

## Observability Checks

### Azure Monitor Alerts

- Active alerts: `az monitor alert list --resource-group {rg} --query "[?properties.essentials.monitorCondition=='Fired']" -o table`
- Alert rules: `az monitor metrics alert list --resource-group {rg} --query '[].{name:name,enabled:enabled,severity:severity}' -o table`

---

## Timing Context Checks

### Recent Deployments

- App Service deployments: `az webapp deployment list --name {app} --resource-group {rg} --query '[-5:]' -o table`
- AKS workload rollout: `kubectl rollout history deployment/{deploy} -n {namespace}`
