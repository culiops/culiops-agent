# widgetapi on-call reference (Azure)

Short pointers for the on-caller. Same shape as the AWS fixture's runbook, pointed at Azure-native observability alongside the existing third-party tools.

## Services and dashboards

- **APM (Datadog):** service `widgetapi`, tag `env:prod`/`env:staging`, `cloud:azure`. Dashboard `WidgetAPI → Service overview`.
- **Azure Monitor / Application Insights:** Application Insights component `widgetapi-<env>-ai` (linked to the web Deployment via the container-level APM SDK). Azure Monitor workbooks for AKS cluster `widgetapi-<env>-aks` in the portal.
- **Log Analytics:** workspace `widgetapi-<env>-law` receives AKS diagnostics, AGW access logs, Front Door access logs, PostgreSQL slow-query logs, and Service Bus diagnostics. Use KQL via `az monitor log-analytics query --workspace <id>` or the portal.
- **Azure portal — Azure Monitor metrics:** available for every resource (PG Flexible, Redis, Storage, Service Bus, AKS, AGW, AFD).

## Logs

- **Application logs:** Datadog Logs pipeline `widgetapi`. Also via `kubectl logs -n widgetapi -l app.kubernetes.io/name=widgetapi`.
- **AGW access logs:** Log Analytics workspace `widgetapi-<env>-law`, table `AzureDiagnostics` filtered by `ResourceType == "APPLICATIONGATEWAYS"`.
- **Front Door access logs:** same workspace, table `AzureDiagnostics` filtered by `Category == "FrontDoorAccessLog"`.
- **AKS control-plane logs:** same workspace, categories `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `cluster-autoscaler` (must be enabled on the cluster's Diagnostic Settings).
- **PostgreSQL:** Server logs via `AzureDiagnostics | where Category == "PostgreSQLLogs"`. Performance via Query Store in the Azure portal.

## Alerting and escalation

- **Primary:** PagerDuty service `WidgetAPI Prod` (routing key mounted into pods as `PAGERDUTY_ROUTING_KEY` via the CSI Secrets Store → Kubernetes Secret `widgetapi-kv-synced`). Staging routes to `WidgetAPI Staging` (low-urgency).
- **Azure Monitor alerts:** a small set of Azure-native alerts (e.g., AKS node NotReady, PG CPU > 85%, Service Bus dead-letter count > 0) route through an Action Group `widgetapi-<env>-ag` to PagerDuty via a webhook.
- **Synthetic uptime:** Application Insights availability test `widgetapi-<env>-healthz` hits `https://api.widgetapi.example.com/healthz/live` from 5 Azure regions; Datadog Synthetics `widgetapi-<env>-healthz` does the same from eu-west + us-east.
- **SLO burn rate:** Datadog monitor `widgetapi-<env>-slo-burn` (availability + latency; target 99.9% over 30 days). No Azure-native SLO yet.

## Feature flags

Feature flags live in **LaunchDarkly**, project `widgetapi`. Matches the Kubernetes namespace.

## Deployment & rollback

- **Deploy:** GitHub Actions workflow `deploy.yml` in `widgetco/widgetapi`. Builds an image, pushes to ACR `widgetcoacr`, bumps `image.tag` in `values-<env>.yaml`, runs `helm upgrade`.
- **Rollback:** `helm rollback widgetapi <revision> -n widgetapi`. Requires cluster-admin or the `widgetapi-deployer` cluster role.

## External dependencies outside this repo

- **Stripe** (payments): configured via the `STRIPE_*` envs loaded from Key Vault via CSI. Stripe dashboard + API logs in the Stripe console.
- **SendGrid** (email): API key also in Key Vault. SendGrid activity feed in the SendGrid UI.
- **Azure Key Vault** (`widgetapi-<env>-kv`): DB password, Datadog API key, PagerDuty routing key, Stripe/SendGrid keys. Accessed by pods via Workload Identity federated to the `widgetapi-<env>-id` UAMI; do NOT add Azure AD user access for investigation — use Key Vault audit logs in Log Analytics instead (`AzureDiagnostics | where ResourceType == "VAULTS"`).
