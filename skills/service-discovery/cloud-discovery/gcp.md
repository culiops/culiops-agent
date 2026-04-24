---
name: gcp
identity-command: "gcloud config get project && gcloud auth print-access-token > /dev/null 2>&1 && echo \"authenticated\""
---

## Prerequisites

**CLI tool:** Google Cloud SDK (`gcloud --version` ≥ 450). The `gcloud asset` command group is bundled with the SDK but may require a one-time opt-in: `gcloud components install asset-inventory` (or `gcloud asset` will prompt automatically).

**Authentication:** same methods as `examples/gcp.md` — `gcloud auth login`, service-account key file, Application Default Credentials, or attached service account on GCE/GKE/Cloud Run. Confirm active context: `gcloud config list` and `gcloud auth list`.

**Least-privilege IAM — all queries below are read-only.** The operator needs:

- `roles/cloudasset.viewer` — grants `cloudasset.assets.searchAllResources` and related read permissions on the Cloud Asset Inventory API.

This is a single, narrow role. If the operator already has `roles/viewer` for the enrichment step (`examples/gcp.md`), `roles/cloudasset.viewer` is still needed in addition — `roles/viewer` does not include Cloud Asset Inventory permissions.

## Broad discovery queries

### 1. By label (primary)

Cloud Asset Inventory provides a single API that searches across all resource types in a project (or organization). Label-based search is the fastest way to find resources belonging to a service.

```
gcloud asset search-all-resources \
  --project={project} \
  --query="labels.service={service}"
```

Teams use different label key conventions. Try these common variations:

| Label key | Typical usage |
|-----------|---------------|
| `service` | Explicit service ownership label |
| `application` | Application-level grouping |
| `app` | Short variant, common in Terraform/Helm |
| `project` | Project-level grouping (may be broader) |
| `team` or `owner` | Ownership labels — broader, but useful as fallback |
| `env` + `service` | Compound filter to narrow to a specific environment |

For each variation, substitute the label key:

```
gcloud asset search-all-resources \
  --project={project} \
  --query="labels.app={service}"
```

### 2. By name prefix

When label-based discovery returns no results, fall back to name matching. Cloud Asset Inventory supports substring matching on the resource name (the full resource path):

```
gcloud asset search-all-resources \
  --project={project} \
  --query="name:*/{service}*"
```

The `name:` filter matches against the full resource path (e.g., `//compute.googleapis.com/projects/my-project/zones/us-central1-a/instances/widgetapi-web-01`). The `*/{service}*` pattern matches the service name anywhere in the final path segment.

### 3. By resource type (when doc hints suggest specific types)

When document analysis from earlier steps suggests the service uses specific GCP resource types, narrow the search with `--asset-types` to reduce noise:

```
gcloud asset search-all-resources \
  --project={project} \
  --query="labels.service={service}" \
  --asset-types="sqladmin.googleapis.com/Instance,run.googleapis.com/Service,container.googleapis.com/Cluster,compute.googleapis.com/Instance,redis.googleapis.com/Instance,pubsub.googleapis.com/Topic,cloudfunctions.googleapis.com/Function,storage.googleapis.com/Bucket"
```

Combine with name-based search when labels are absent:

```
gcloud asset search-all-resources \
  --project={project} \
  --query="name:*/{service}*" \
  --asset-types="sqladmin.googleapis.com/Instance,run.googleapis.com/Service"
```

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Label filter | `--query="labels.<key>=<value>"` |
| Name match | `--query="name:*/{service}*"` (substring on resource path) |
| Project | `--project={project}` — or `--scope=organizations/{org-id}` for org-wide search |
| Asset type | `--asset-types="<type1>,<type2>,..."` — fully qualified API resource type names |

## Result parsing

The `search-all-resources` command returns a list of resource entries. Map each entry to a resource hint:

| API field | Maps to | Example |
|-----------|---------|---------|
| `displayName` | Resource name | `widgetapi-web` |
| `assetType` | Resource type (GCP API resource type) | `sqladmin.googleapis.com/Instance` → type `Cloud SQL` |
| `location` | Context (region/zone) | `us-central1` |
| `name` | Full resource path (for enrichment lookups) | `//sqladmin.googleapis.com/projects/myproj/instances/widgetapi-db` |
| `labels` | Additional context (environment, team) | `{env: "prod", team: "platform"}` |
| `project` | Project scope | `widgetapi-prod` |
