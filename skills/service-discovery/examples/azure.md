# Examples: Azure CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the discovered stack is Azure. The skill reads this file when Step 1 detects Azure resources (Bicep files, ARM templates, Terraform `azurerm_*` resources, or `az` tooling).

Replace placeholders (`{app}`, `{rg}`, `{sub}`, etc.) with the values resolved in Step 2. Note that most `az` commands require either `--resource-group` explicitly or a default set via `az configure`.

## How to use this file

Each section maps one Azure resource category to status/config + four golden signals (latency / traffic / errors / saturation). For Azure metrics, the `az monitor metrics list` command is the workhorse; for logs, Log Analytics (KQL) via `az monitor log-analytics query` is the equivalent of CloudWatch Logs Insights.

---

## Azure Container Apps

- App status: `az containerapp show --name {app} --resource-group {rg}`
- Recent revisions: `az containerapp revision list --name {app} --resource-group {rg}`
- Current traffic split: `az containerapp show --name {app} --resource-group {rg} --query 'properties.configuration.ingress.traffic'`
- Replica count: `az containerapp replica list --name {app} --resource-group {rg}`
- CPU / memory / request metrics: `az monitor metrics list --resource {app-resource-id} --metric 'UsageNanoCores','WorkingSetBytes','Requests' --interval PT1M --start-time {T-1h} --end-time {now}`

## AKS (Azure Kubernetes Service)

- Cluster status: `az aks show --name {cluster} --resource-group {rg}`
- Node pools: `az aks nodepool list --cluster-name {cluster} --resource-group {rg}`
- Credentials for kubectl: `az aks get-credentials --name {cluster} --resource-group {rg}`
- Workloads (generic kubectl): `kubectl get deploy -n {namespace}` / `kubectl describe deploy/{deploy}`
- Pod metrics: `kubectl top pods -n {namespace}`
- Cluster events: `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`

## App Service (Web Apps / Function Apps)

- Web app status: `az webapp show --name {app} --resource-group {rg}`
- App settings (non-secret view): `az webapp config appsettings list --name {app} --resource-group {rg}`
- Deployment slots: `az webapp deployment slot list --name {app} --resource-group {rg}`
- HTTP 5xx: `az monitor metrics list --resource {app-resource-id} --metric 'Http5xx' --interval PT5M --start-time {T-1h} --end-time {now}`
- Response time: `az monitor metrics list --resource {app-resource-id} --metric 'AverageResponseTime' --aggregation Average,Maximum --interval PT1M --start-time {T-1h} --end-time {now}`
- CPU / memory: metrics `CpuTime`, `MemoryWorkingSet`

## Azure Functions

- Function app status: `az functionapp show --name {app} --resource-group {rg}`
- Functions listed in app: `az functionapp function list --name {app} --resource-group {rg}`
- Executions: metric `FunctionExecutionCount`
- Execution units (memory × time): `FunctionExecutionUnits`
- Failures: metric `Http5xx` (for HTTP-triggered) or custom Application Insights query

## Application Gateway / Front Door

- App Gateway status: `az network application-gateway show --name {agw} --resource-group {rg}`
- Backend health: `az network application-gateway show-backend-health --name {agw} --resource-group {rg}`
- Front Door status: `az afd profile show --profile-name {profile} --resource-group {rg}` (Standard/Premium) or `az network front-door show --name {fd} --resource-group {rg}` (Classic)
- Request count / failed: metrics `TotalRequests`, `FailedRequests`
- Response time: metric `ApplicationGatewayTotalTime` / `BackendLastByteResponseTime`

## Azure SQL Database / PostgreSQL / MySQL

- SQL DB status: `az sql db show --name {db} --server {server} --resource-group {rg}`
- Flexible Postgres: `az postgres flexible-server show --name {server} --resource-group {rg}`
- Flexible MySQL: `az mysql flexible-server show --name {server} --resource-group {rg}`
- CPU: metric `cpu_percent`
- Connections: `connection_successful` / `connection_failed` / `active_connections`
- Storage: `storage_percent`
- Replica lag: `replica_lag`

## Azure Cache for Redis

- Cache status: `az redis show --name {cache} --resource-group {rg}`
- CPU: metric `serverLoad`
- Memory: metric `usedmemorypercentage`
- Evicted keys: metric `evictedkeys`
- Cache hits / misses: metrics `cachehits`, `cachemisses`
- Connected clients: metric `connectedclients`

## Service Bus

- Namespace status: `az servicebus namespace show --name {namespace} --resource-group {rg}`
- Queue details: `az servicebus queue show --namespace-name {namespace} --name {queue} --resource-group {rg}`
- Topic details: `az servicebus topic show --namespace-name {namespace} --name {topic} --resource-group {rg}`
- Active messages: metric `ActiveMessages` with `EntityName={queue}`
- Dead-letter count: metric `DeadletteredMessages`
- Throttled requests: metric `ThrottledRequests`
- Age of oldest message: metric `AgeOfOldestMessage`

## Event Grid / Event Hubs

- Event Grid topic: `az eventgrid topic show --name {topic} --resource-group {rg}`
- Event Grid subscription: `az eventgrid event-subscription show --name {sub} --source-resource-id {source-id}`
- Event Hub namespace: `az eventhubs namespace show --name {namespace} --resource-group {rg}`
- Event Hub: `az eventhubs eventhub show --namespace-name {namespace} --name {hub} --resource-group {rg}`
- Incoming messages: metric `IncomingMessages`
- Throttled requests: metric `ThrottledRequests`
- Consumer lag: metric `ConsumerLag` (per consumer group)

## Front Door WAF

- Policy: `az network front-door waf-policy show --name {policy} --resource-group {rg}`
- Blocked requests: metric `WebApplicationFirewallRequestCount` filtered by `Action=Block`
- Allowed requests: same metric filtered by `Action=Allow`
- Rule matches: filter the metric by `RuleName`

## Storage Accounts

- Account details: `az storage account show --name {account} --resource-group {rg}`
- Blob service metrics: `az monitor metrics list --resource {account-resource-id}/blobServices/default --metric 'Transactions','BlobCount','BlobCapacity'`
- Transaction success rate: `Availability`
- End-to-end latency: `SuccessE2ELatency` / `SuccessServerLatency`

## Cosmos DB

- Account status: `az cosmosdb show --name {account} --resource-group {rg}`
- Database / container: `az cosmosdb sql database show --account-name {account} --name {db} --resource-group {rg}`
- RU consumption: metric `TotalRequestUnits`
- Throttled requests (HTTP 429): metric `TotalRequests` filtered by `StatusCode=429`
- Server-side latency: metric `ServerSideLatency`

## Application Insights (APM)

- List apps: `az monitor app-insights component show --app {ai-name} --resource-group {rg}`
- Run a KQL query: `az monitor app-insights query --app {ai-name} --analytics-query "requests | where timestamp > ago(1h) | summarize count() by resultCode" --resource-group {rg}`
- Common queries: request latency percentiles, exception rate, dependency failures — all via KQL.

## Azure Monitor / Log Analytics

- Run a KQL query: `az monitor log-analytics query --workspace {workspace-id} --analytics-query "AzureDiagnostics | where TimeGenerated > ago(15m) and Category == '{category}' | take 100"`
- List activity log events for a resource: `az monitor activity-log list --resource-id {resource-id} --start-time {T-1h} --max-events 50`

## Azure CDN

- CDN profile: `az cdn profile show --name {profile} --resource-group {rg}`
- Endpoint: `az cdn endpoint show --profile-name {profile} --name {endpoint} --resource-group {rg}`
- Cache hit ratio: metric `CacheHitRatio` (Front Door / Standard profile)
- Request count: metric `RequestCount`
- Total latency: metric `TotalLatency`

## Third-party services on Azure

Same as the AWS/GCP counterparts — ask the human where logs and metrics live for any vendor tool. Azure-native integrations typically forward to Log Analytics; others to their own dashboards.

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{app}`, `{cluster}`, `{cache}`, `{server}`, `{db}`, `{queue}`, `{topic}`, `{namespace}`, `{profile}`, `{endpoint}` | Resource identifiers | `widgetapi-prod-eu-web` |
| `{rg}` | Resource group | `widgetapi-prod-rg` |
| `{sub}` | Subscription ID | `00000000-0000-0000-0000-000000000000` |
| `{resource-id}`, `{app-resource-id}`, `{account-resource-id}` | Full ARM resource IDs (from the resource catalog) | `/subscriptions/{sub}/resourceGroups/{rg}/providers/...` |
| `{region}` | Azure region | `westeurope` |
| `{workspace-id}` | Log Analytics workspace GUID | `00000000-0000-0000-0000-000000000000` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
