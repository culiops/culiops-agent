---
name: azure
identity-command: "az account show"
---

## Prerequisites

**CLI tool:** Azure CLI (`az --version` ≥ 2.50). The `az graph` command requires the `resource-graph` extension — install with `az extension add --name resource-graph` if not already present.

**Authentication:** same methods as `examples/azure.md` — `az login` (interactive), service principal, or managed identity. Confirm active context: `az account show`. Set the target subscription: `az account set --subscription {subscription-id}`.

**Least-privilege role — all queries below are read-only.** The operator needs:

- `Reader` role at the subscription level — grants read access to Azure Resource Graph and resource metadata across all resource groups in the subscription.

If the operator already has `Reader` for the enrichment step (`examples/azure.md`), no additional grants are needed. Resource Graph queries execute against the ARM control plane with the caller's existing permissions.

## Broad discovery queries

### 1. Resource Graph by tag (primary)

Azure Resource Graph provides a Kusto-like query interface across all resources in a subscription (or across subscriptions). Tag-based search is the fastest way to find resources belonging to a service.

```
az graph query -q "Resources | where tags['Service'] == '{service}'" \
  --subscriptions {subscription-id}
```

Teams use different tag key conventions. Try these common variations:

| Tag key | Typical usage |
|---------|---------------|
| `Service` | Explicit service ownership tag |
| `Application` | Application-level grouping |
| `app` | Lowercase variant |
| `Project` | Project-level grouping (may be broader) |
| `Team` or `Owner` | Ownership tags — broader, but useful as fallback |
| `Environment` + `Service` | Compound filter to narrow to a specific environment |

For each variation, substitute the tag key:

```
az graph query -q "Resources | where tags['Application'] == '{service}'" \
  --subscriptions {subscription-id}
```

### 2. By name prefix

When tag-based discovery returns no results, fall back to name prefix matching:

```
az graph query -q "Resources | where name startswith '{service}'" \
  --subscriptions {subscription-id}
```

This catches resources named with the service as a prefix (e.g., `widgetapi-web`, `widgetapi-db`, `widgetapi-cache`).

### 3. By resource group

Many teams organize resources into resource groups named after the service. If the resource group name matches the service (or a common pattern like `{service}-rg`), query all resources within it:

```
az graph query -q "Resources | where resourceGroup == '{service}-rg'" \
  --subscriptions {subscription-id}
```

Common resource group naming patterns to try:

- `{service}-rg`
- `{service}-{environment}-rg` (e.g., `widgetapi-prod-rg`)
- `rg-{service}`
- `rg-{service}-{environment}`

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Tag filter | `where tags['<key>'] == '<value>'` in the KQL query |
| Name prefix | `where name startswith '<prefix>'` or `where name contains '<substring>'` |
| Resource group | `where resourceGroup == '<rg>'` |
| Subscription | `--subscriptions {subscription-id}` (can specify multiple, comma-separated) |
| Resource type | `where type == 'microsoft.compute/virtualmachines'` — use when doc hints suggest specific types |

## Result parsing

Resource Graph returns a table of resource entries. Map each entry to a resource hint:

| API field | Maps to | Example |
|-----------|---------|---------|
| `name` | Resource name | `widgetapi-web` |
| `type` | Resource type (ARM resource type) | `microsoft.web/sites` → type `App Service` |
| `subscriptionId` | Subscription context | `00000000-0000-0000-0000-000000000000` |
| `resourceGroup` | Resource group context | `widgetapi-prod-rg` |
| `location` | Region | `westeurope` |
| `tags` | Additional context (environment, team) | `{Environment: "prod", Team: "platform"}` |
