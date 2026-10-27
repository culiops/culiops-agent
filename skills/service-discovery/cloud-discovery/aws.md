---
name: aws
identity-command: "aws sts get-caller-identity --profile {profile} --query '{Account:Account,Arn:Arn}'"
---

## Prerequisites

**CLI tool:** AWS CLI v2 (`aws --version` ≥ 2.x).

**Authentication:** same methods as `examples/aws.md` — named profile, AWS SSO, IAM role on compute, or STS temporary credentials.

**Identity check (before each batch of queries).** Re-run the identity command and compare the account with the target the operator confirmed at the gate; abort the batch if it differs:

```
aws sts get-caller-identity --profile {profile} --query Account --output text
```

`sts get-caller-identity` returns account, user ID and ARN, **not a region**. Show the region the commands will use from `aws configure get region --profile {profile}` (or `AWS_REGION` / `AWS_DEFAULT_REGION`), and pass it explicitly as `--region {region}` on every command below.

**Least-privilege IAM — all queries below are read-only.** The operator needs:

- `tag:GetResources` and `tag:GetTagKeys` / `tag:GetTagValues` — for the Resource Groups Tagging API queries.
- `config:SelectResourceConfig` (or `config:SelectAggregateResourceConfig` for an aggregator) — for AWS Config queries (only needed if AWS Config is enabled in the account).

These are a narrow subset of the `ReadOnlyAccess` managed policy. If the operator already has `ReadOnlyAccess` for the enrichment step (`examples/aws.md`), no additional grants are needed.

## Rules that apply to every query here

- **Projection only.** Output of these commands can reach the catalog. Select the allowlisted fields below; never `configuration`, never whole resource documents.
- **Tagging API scope.** It is **regional** and returns only resources that are tagged, or were tagged at some point. Untagged resources and resources in other regions never appear.
- **Global services** (CloudFront, IAM, Route 53, WAF with `CLOUDFRONT` scope) must be queried in `us-east-1` (`--region us-east-1`) in the standard AWS partition; a query in any other region returns nothing for them. In another partition (GovCloud, China) the Region differs and is `UNVERIFIED`: ask the operator.
- **Empty result ≠ absent.** Classify each documented or expected resource as exactly one of:
  - `not-found (queried <account>/<region>)` — a query that can see this kind of resource ran in that account/region and returned nothing.
  - `not-queried` — no query that could see it was run (not approved, wrong service, region skipped).
  - `not-queryable (global or untagged)` — the Tagging API cannot see it (global service queried regionally, or the resource carries no tags).

  Only `not-found` after a query that could have seen the resource may be reported as "not found"; never write "decommissioned" from an empty result alone.
- **Tag values are exact match.** Do not rely on wildcards or prefix matching in `--tag-filters` values (UNVERIFIED that wildcards are unsupported; treat as exact). For prefix-style discovery, list values with `get-tag-values --key <k>` and filter client-side.

## Broad discovery queries

### 1. By tag (primary)

The Resource Groups Tagging API searches tags across resource types in a single call, per region.

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Service,Values={service} \
  --profile {profile} --region {region} \
  --query 'ResourceTagMappingList[].{Arn:ResourceARN,Tags:Tags}'
```

Teams use different tag key conventions. **Run all candidate keys** (do not stop at the first non-empty one) and **record which key matched each resource**:

| Tag key | Typical usage | Treatment |
|---------|---------------|-----------|
| `Service` | Explicit service ownership tag | Membership signal |
| `Application` | Application-level grouping | Membership signal |
| `app` | Lowercase variant, common in Terraform modules | Membership signal |
| `Project` | Project-level grouping (broader than a single service) | **Hint only** |
| `Team` / `Owner` | Ownership tags (broader than service) | **Hint only** |
| `Environment` + `Service` | Compound filter to narrow to one environment | Narrowing filter, not a key on its own |

`Project`, `Team` and `Owner` matches are hints only: they go to the **"Unattributed — operator assigns"** list, not the inventory, unless another membership signal (service tag, confirmed naming pattern, reference from an already-confirmed resource) also applies.

Substitute the key for each run:

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Application,Values={service} \
  --profile {profile} --region {region} \
  --query 'ResourceTagMappingList[].{Arn:ResourceARN,Tags:Tags}'
```

### 2. By tag value (instead of name prefix)

The Tagging API does not do reliable prefix matching on tag values (see rules above). To find resources whose `Name`-style tag *contains* the service name, list the values the account actually uses and filter client-side:

```
aws resourcegroupstaggingapi get-tag-values --key Name \
  --profile {profile} --region {region}
```

Pick the values that match the confirmed naming pattern, then query each as an exact value:

```
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Name,Values={exact-tag-value} \
  --profile {profile} --region {region} \
  --query 'ResourceTagMappingList[].{Arn:ResourceARN,Tags:Tags}'
```

A name match alone is a membership signal only when it matches the naming pattern the operator confirmed.

### 3. Via AWS Config (if enabled)

AWS Config provides a SQL-like query interface across **recorded** resource types. Coverage = the types the Config recorder is set to record in that account/region; an unrecorded type is `not-queryable`, not absent. It can filter on resource properties, not just tags.

**Select only metadata columns:** `resourceId, resourceType, resourceName, awsRegion, accountId, tags`. **Never select `configuration`** — it is the whole resource config and includes Lambda/ECS environment variables and other secret-bearing fields.

Tag filter form is `tags.tag = 'Key=Value'` (the form in the Config query docs). The older `tags.key = 'X' AND tags.value = 'Y'` form is **removed from this skill**: it can match two different tags on the same resource (UNVERIFIED), so it can give false matches.

```
aws configservice select-resource-config \
  --profile {profile} --region {region} \
  --expression "SELECT resourceId, resourceType, resourceName, awsRegion, accountId, tags \
                WHERE tags.tag = 'Service={service}'"
```

Variations for different tag keys:

```
aws configservice select-resource-config \
  --profile {profile} --region {region} \
  --expression "SELECT resourceId, resourceType, resourceName, awsRegion, accountId, tags \
                WHERE tags.tag = 'Application={service}'"
```

Name-based fallback via Config (a hint, not membership, unless the name matches the confirmed naming pattern):

```
aws configservice select-resource-config \
  --profile {profile} --region {region} \
  --expression "SELECT resourceId, resourceType, resourceName, awsRegion, accountId, tags \
                WHERE resourceName LIKE '{service}%'"
```

**Aggregators.** If the account uses a Config aggregator (multi-region or multi-account), use `select-aggregate-resource-config` with the same expression and `--configuration-aggregator-name {aggregator}`. Run it against the aggregator's home region and confirm the aggregator's source accounts/regions before treating results as complete.

## Scoping mechanisms

| Scope | How to apply |
|-------|--------------|
| Tag filter | `--tag-filters Key=<key>,Values=<value>` (Tagging API) or `WHERE tags.tag = 'Key=Value'` (Config) |
| Tag values | `aws resourcegroupstaggingapi get-tag-values --key <k>`, then client-side filtering and exact-value queries |
| Region | `--region {region}` on every command — repeat for each region the service may use. Global services: `--region us-east-1` |
| Resource type filter | `--resource-type-filters <type>` on the Tagging API (e.g., `ec2:instance`, `rds:db`, `elasticloadbalancing:loadbalancer`) — use when doc hints suggest specific types |

## Result parsing

The Tagging API returns a `ResourceTagMappingList` array. Map each entry to a resource hint. **Key each resource on its full ARN**; the name below is for display only.

| API field | Maps to | Example |
|-----------|---------|---------|
| `ResourceARN` | Identity key | the full ARN |
| `ResourceARN` | Display name (per-service rule, see below) | `arn:aws:ecs:us-east-1:123456789012:service/prod/widgetapi-web` → `widgetapi-web` |
| `ResourceARN` | Resource type (service + resource segment of ARN) | `arn:aws:ecs:...` → type `ecs:service` |
| `ResourceARN` | Context (region from ARN, account from ARN) | region `us-east-1`, account `123456789012` |
| `Tags` | Additional context (environment, team, version tags) | `[{Key: "Environment", Value: "prod"}]` |
| `Tags` | **Owner** (recognition only, see below) | `aws:cloudformation:stack-name` → `Owner: cloudformation (<stack>)` |

**Name parsing is per service; the last ARN segment is not always the name.**

- ALB/NLB: `…:loadbalancer/app/<name>/<id>` (NLB: `net/<name>/<id>`) — the name is the **third** segment (`<name>`); the last segment is a hash. Target groups: `…:targetgroup/<name>/<id>` — name is the middle segment.
- Lambda: `…:function:<name>` optionally followed by `:<alias-or-version>` — strip the trailing `:alias`/`:version` for the name; keep the full ARN as the key.
- ECS service: `…:service/<cluster>/<name>` — name is the last segment, cluster is the one before.
- For services not listed here, take the segment after the resource-type prefix and do not guess further; mark unusual shapes UNVERIFIED.

**Owner detection (recognition only).** Read from tags already returned; no extra calls.

| Tag | Result |
|-----|--------|
| `aws:cloudformation:stack-name` (+ `aws:cloudformation:logical-id`) | `Owner: cloudformation (<stack>)`. CloudFormation, SAM, CDK and Serverless deploy via stacks, so this covers them. The skill records the owner and does not parse or manage the stack. |
| none | `Owner: unknown` (do not infer from `Team`/`Owner` tags; those are hints, not the deployment owner). Stack tags are propagated per resource type (`docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-resource-tags.html`, read 2026-10-27), so an untagged resource may still be stack-owned: `unknown`, not "not CloudFormation". Terraform, ecspresso and lambroll leave no native marker: `unknown` unless the operator names a tag convention. |

For AWS Config results, `resourceType`, `resourceName`, `resourceId`, `awsRegion`, `accountId` and `tags` map directly to the hint fields (and the same Owner rule applies to `tags`). There is no `configuration` column to use: enrichment of a discovered resource uses the projected commands in `examples/aws.md`.
