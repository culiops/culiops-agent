---
name: aws
identity-command: "aws sts get-caller-identity"
---

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` ≥ 2.x).

**Authentication:** same methods as `examples/aws.md` — named profile, AWS SSO, IAM role on compute, or STS temporary credentials. Confirm identity before running anything: `aws sts get-caller-identity`.

**Least-privilege IAM — all queries below are read-only.** The operator needs:

- `tag:GetResources` — for the Resource Groups Tagging API queries.
- `resourcegroupstaggingapi:GetResources` — same API, alternative action name depending on SDK version.
- `config:SelectResourceConfig` — for AWS Config queries (only needed if AWS Config is enabled in the account).

These are a narrow subset of the `ReadOnlyAccess` managed policy. If the operator already has `ReadOnlyAccess` for the enrichment step (`examples/aws.md`), no additional grants are needed.

## Broad discovery queries

### 1. By tag (primary)

The Resource Groups Tagging API searches tags across all resource types in a single call. This is the fastest way to find resources belonging to a service.

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Service,Values={service} \
  --region {region}
```

Teams use different tag key conventions. Try these common variations in order until results are found:

| Tag key | Typical usage |
|---------|---------------|
| `Service` | Explicit service ownership tag |
| `Application` | Application-level grouping |
| `app` | Lowercase variant, common in Terraform modules |
| `Project` | Project-level grouping (may be broader than a single service) |
| `Name` (prefix match) | Many teams prefix the `Name` tag with the service name |
| `Team` or `Owner` | Ownership tags — broader than service, but useful as a fallback |
| `Environment` + `Service` | Compound filter to narrow to a specific environment |

For each variation, substitute the `Key=` value in the command above:

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Application,Values={service} \
  --region {region}
```

### 2. By name prefix

When tag-based discovery returns no results, fall back to name prefix matching via the same API. Many AWS resources carry a `Name` tag whose value starts with the service name:

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Name,Values={service}* \
  --region {region}
```

The trailing `*` is a wildcard — the API supports prefix matching on tag values.

### 3. Via AWS Config (if enabled)

AWS Config provides a SQL-like query interface across all recorded resources. This is more powerful than the Tagging API (it can filter on resource properties, not just tags) but requires AWS Config to be enabled and recording in the target account/region.

```
aws configservice select-resource-config \
  --expression "SELECT resourceId, resourceType, resourceName, tags, configuration \
                WHERE tags.key = 'Service' AND tags.value = '{service}'"
```

Variations for different tag keys:

```
aws configservice select-resource-config \
  --expression "SELECT resourceId, resourceType, resourceName, tags, configuration \
                WHERE tags.key = 'Application' AND tags.value = '{service}'"
```

Name-based fallback via Config:

```
aws configservice select-resource-config \
  --expression "SELECT resourceId, resourceType, resourceName, tags, configuration \
                WHERE resourceName LIKE '{service}%'"
```

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Tag filter | `--tag-filters Key=<key>,Values=<value>` (Tagging API) or `WHERE tags.key = '...'` (Config) |
| Name prefix | `Values={service}*` on the `Name` tag or `WHERE resourceName LIKE '{service}%'` |
| Region | `--region {region}` — repeat the query for each region the service may use, or iterate the account's enabled regions |
| Resource type filter | `--resource-type-filters <type>` on the Tagging API (e.g., `ec2:instance`, `rds:db`, `elasticloadbalancing:loadbalancer`) — use when doc hints suggest specific types |

## Result parsing

The Tagging API returns a `ResourceTagMappingList` array. Map each entry to a resource hint:

| API field | Maps to | Example |
|-----------|---------|---------|
| `ResourceARN` | Resource name (last segment of ARN after `/` or `:`) | `arn:aws:ecs:us-east-1:123456789012:service/prod/widgetapi-web` → name `widgetapi-web` |
| `ResourceARN` | Resource type (service + resource segment of ARN) | `arn:aws:ecs:...` → type `ecs:service` |
| `ResourceARN` | Context (region from ARN, account from ARN) | region `us-east-1`, account `123456789012` |
| `Tags` | Additional context (environment, team, version tags) | `[{Key: "Environment", Value: "prod"}]` |

For AWS Config results, `resourceType`, `resourceName`, and `resourceId` map directly to the hint fields. The `configuration` blob provides additional detail for enrichment.
