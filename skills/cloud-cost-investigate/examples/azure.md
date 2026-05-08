# Azure — cloud-cost-investigate examples

Read-only commands per workflow step. All commands are `show` / `list` / `query` only — no mutations, no `create`, `delete`, `update`, `set`, `add`, `remove`, `start`, `stop`, `restart`, `enable`, or `disable`.

## Step 1 — Detect & Scope: cloud detection

```bash
# Detect current subscription and tenant
az account show --output json

# List all subscriptions the current principal can read
az account list --output table
```

**RBAC:** Any authenticated principal. No additional role required for `az account show/list`.
**API cost:** none.

## Step 2A — Anomaly mode

### Total spend by service, time series

```bash
# Month-to-date spend grouped by service name (replace <sub-id> with subscription GUID)
az costmanagement query \
  --scope "/subscriptions/<sub-id>" \
  --type Usage \
  --timeframe MonthToDate \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping '[{"name":"ServiceName","type":"Dimension"}]' \
  --output json
```

**RBAC:** `Cost Management Reader` on the subscription or billing scope.
**API cost:** Cost Management API is free for typical use. Throttling applies — avoid more than a few dozen queries per minute and note this in the query plan.

### Period comparison (anomalous window vs. baseline)

```bash
# Anomalous window: custom timeframe, grouped by service
az costmanagement query \
  --scope "/subscriptions/<sub-id>" \
  --type Usage \
  --timeframe Custom \
  --time-period from=<current_start>T00:00:00Z,to=<current_end>T23:59:59Z \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping '[{"name":"ServiceName","type":"Dimension"}]' \
  --output json

# Baseline window: same length, prior period — re-run with shifted from/to values
az costmanagement query \
  --scope "/subscriptions/<sub-id>" \
  --type Usage \
  --timeframe Custom \
  --time-period from=<prior_start>T00:00:00Z,to=<prior_end>T23:59:59Z \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping '[{"name":"ServiceName","type":"Dimension"}]' \
  --output json
```

**RBAC:** `Cost Management Reader`.
**API cost:** Cost Management API free; throttle-aware — present estimated query count in the query plan at GATE 2.

### New resources in an anomalous window

```bash
# Resources with a createdTime in the anomalous window (not all resource types expose createdTime)
az resource list \
  --query "[?createdTime>='<start-iso>'].[id,type,name,createdTime]" \
  --output table

# Activity Log fallback: Succeeded write operations in the window (catches resource types
# that don't surface createdTime via az resource list)
az monitor activity-log list \
  --start-time <start-iso> \
  --end-time <end-iso> \
  --status Succeeded \
  --max-events 1000 \
  --query "[?operationName.value | contains(@, 'write')].[eventTimestamp,resourceId,operationName.localizedValue,caller]" \
  --output table
```

**RBAC:** `Reader` on the subscription; `Monitoring Reader` for Activity Log.
**API cost:** none.

## Step 2B — Waste mode

### Advisor cost recommendations

```bash
# All Cost category recommendations across the subscription
az advisor recommendation list \
  --category Cost \
  --output json
```

**RBAC:** `Advisor Reader` on the subscription. Note: Advisor opt-in is required — if `az advisor recommendation list` returns no results or an error, Advisor may not be enabled for the subscription (operator action to enable, not skill action).
**API cost:** none.

### Resource-state sweeps

```bash
# Unattached managed disks
az disk list \
  --query "[?diskState=='Unattached'].[id,name,diskSizeGB,timeCreated]" \
  --output table

# Orphaned snapshots older than 30 days
az snapshot list \
  --query "[?timeCreated<'<iso-30d-ago>'].[id,name,diskSizeGB,timeCreated]" \
  --output table

# Unused public IP addresses (no associated resource)
az network public-ip list \
  --query "[?ipConfiguration==null].[id,name,publicIpAllocationMethod]" \
  --output table

# Storage accounts — check for missing lifecycle management policy
# Run for each account name surfaced by az storage account list:
az storage account list \
  --query "[].name" \
  --output tsv
# Then per account (404 / ResourceNotFound means no policy configured):
az storage account management-policy show \
  --account-name <name> \
  --resource-group <rg> \
  --output json
```

**RBAC:** `Reader` on the subscription covers `az disk list`, `az snapshot list`, `az network public-ip list`, and `az storage account list`. `Storage Account Contributor` (read mode) or `Reader` is sufficient for `management-policy show`.
**API cost:** none.

### Optional — utilization metrics via Azure Monitor

```bash
# Last 14 days average CPU for a specific VM
az monitor metrics list \
  --resource /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Compute/virtualMachines/<vm-name> \
  --metric "Percentage CPU" \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --interval P1D \
  --output json
```

**RBAC:** `Monitoring Reader`.
**API cost:** Standard Azure Monitor metrics reads are free at typical investigative volumes.

## Step 2C — Attribution mode

### Cost filtered by tag

```bash
# Spend for a specific tag key/value (e.g. tag key "Service", value "orders")
az costmanagement query \
  --scope "/subscriptions/<sub-id>" \
  --type Usage \
  --timeframe Custom \
  --time-period from=<start>T00:00:00Z,to=<end>T23:59:59Z \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-filter '{"tags":{"name":"Service","operator":"In","values":["<service-name>"]}}' \
  --dataset-grouping '[{"name":"ServiceName","type":"Dimension"}]' \
  --output json
```

**RBAC:** `Cost Management Reader`.
**API cost:** Cost Management API free; throttle-aware — present estimated query count in the query plan.

### Cost filtered by subscription (multi-subscription environments)

```bash
# Switch active subscription context for the same query pattern
az account set --subscription <sub-id>   # read-only context switch, no mutations

# Or scope the query to a management group (if the principal has access)
az costmanagement query \
  --scope "/providers/Microsoft.Management/managementGroups/<mg-id>" \
  --type Usage \
  --timeframe Custom \
  --time-period from=<start>T00:00:00Z,to=<end>T23:59:59Z \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping '[{"name":"SubscriptionName","type":"Dimension"},{"name":"ServiceName","type":"Dimension"}]' \
  --output json
```

**RBAC:** `Cost Management Reader` at the management group scope. The principal must have read access at that scope.
**API cost:** Cost Management API free; throttle-aware.

## Step 5 — Verification (shared)

No mutation occurs, so verification is just re-reading the report file before commit:

```bash
# Operator inspects the report draft
cat .culiops/cloud-cost-investigate/<scope-slug>-<mode>-<YYYYMMDD-HHmm>.md
```

## Iron Law reminders

- These commands are read-only by name. The skill MUST refuse if the operator asks for any `az ... create`, `az ... delete`, `az ... update`, `az ... set`, `az ... add`, `az ... remove`, `az ... start`, `az ... stop`, or `az ... enable` / `disable` call.
- Cost Management API throttling: avoid issuing more than a few dozen queries per minute per subscription. The query plan presented at GATE 2 must include the estimated number of Cost Management API calls and note the throttle risk for large subscription counts.
- Azure Advisor is opt-in per subscription. If `az advisor recommendation list --category Cost` returns no results or a permission error, Advisor may be disabled or the principal may lack `Advisor Reader` — this is an operator action to resolve, not a skill action.
