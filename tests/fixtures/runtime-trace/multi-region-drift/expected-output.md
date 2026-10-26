*(Other sections identical to basic-lambda-service unless shown. Only differences shown here.)*

# Variant A — aggregator index

## Overview (resolved resource set excerpt)

Resolved at Step 2b (`re-001`): 6 resources. 5 in us-east-1 (as in basic-lambda-service) plus:

| Resource | Type | Region | In CloudTrail / Wiring / CloudWatch pass? |
|---|---|---|---|
| payments-archive | lambda:function | us-west-2 | **No** — primary-Region pass only (see Gaps) |

## Cross-Region Footprint (Resource Explorer)

**Request:** `resource-explorer-2:Search` `QueryString=tag:service=payments`, `ViewArn=arn:aws:resource-explorer-2:us-east-1:123456789012:view/all-resources/22222222-aaaa-bbbb-cccc-000000000001` (aggregator Region). Call ID: `re-001`.

| Check | Result |
|---|---|
| Aggregator Region | us-east-1 (`AGGREGATOR`, `ACTIVE`); the view used lives in this Region |
| Indexed Regions | 17 (1 aggregator + 16 local, from `ListIndexes`), including us-west-2 |
| View includes `tags` | yes |
| Search completeness | `Count.Complete=true`, 6 of 6 |

| Region | Count | Resources |
|---|---|---|
| us-east-1 | 5 | 3 Lambdas, 1 SQS queue, 1 DynamoDB table |
| us-west-2 | 1 | 1 Lambda (`payments-archive`) |

**Resources outside primary Region (us-east-1):**

| ARN | Region | Resource type |
|---|---|---|
| arn:aws:lambda:us-west-2:123456789012:function:payments-archive | us-west-2 | lambda:function |

## Gaps and Caveats

- *(carry over basic-lambda-service items)*
- **Cross-Region scope:** Resource Explorer surfaced 1 resource in us-west-2. CloudTrail Event history, Wiring reads and CloudWatch queries were run in us-east-1 only; control-plane events, configured callers and activity baselines for `payments-archive` are NOT captured in this profile. **Re-run with `--region us-west-2` or expand the scoping primitive to cover it.**
- Open question for outgoing team: is `payments-archive` in us-west-2 in scope for the takeover? Why us-west-2?

---

# Variant B — local index only

## Cross-Region Footprint (Resource Explorer)

**Request:** `resource-explorer-2:Search` `QueryString=tag:service=payments`, view in us-east-1 (`LOCAL` index, no aggregator). Call ID: `re-001`.

**cross-Region: not verifiable — local index only.**

| Check | Result |
|---|---|
| Aggregator Region | none — the only index is `LOCAL` in us-east-1 |
| Indexed Regions | 1 (us-east-1) |
| View includes `tags` | yes |
| Search completeness | `Count.Complete=true`, 5 of 5 — but only for us-east-1 |

This profile makes **no claim** about resources outside us-east-1. (No Region table and no "none outside primary Region" line is written: a search through a local index cannot see other Regions.)

## Gaps and Caveats

- *(carry over basic-lambda-service items)*
- **Cross-Region footprint not verifiable.** Resource Explorer has only a local index in us-east-1 and no aggregator index, so resources in other Regions are invisible to this run. Recommended: create an aggregator index and a view in the aggregator Region, then re-run. **Creating it is an operator action and out of scope for this skill.** Alternative: re-run with an explicit ARN list that includes resources from other Regions.
- **Downstream note:** `service-takeover` readiness item 5 (cross-Region footprint) is marked `?` for this profile, not ✓.
