*(Other sections identical to basic-lambda-service. Only differences shown here.)*

## Cross-Region Footprint (Resource Explorer)

**Request:** `resource-explorer-2:Search` Filter=`tag:service=payments` (aggregator view). Call ID: `re-001`.

| Region | Count | Resources |
|---|---|---|
| us-east-1 | 5 | 3 Lambdas, 1 SQS queue, 1 DynamoDB table |
| us-west-2 | 1 | 1 Lambda (`payments-archive`) |

**Resources outside assumed primary region (us-east-1):**

| ARN | Region | Resource type |
|---|---|---|
| arn:aws:lambda:us-west-2:123456789012:function:payments-archive | us-west-2 | lambda:function |

## Gaps and Caveats

- *(carry over basic-lambda-service items)*
- **Cross-region scope:** Resource Explorer surfaced 1 resource in us-west-2. This run's CloudTrail and CloudWatch queries only covered us-east-1; activity baselines and control-plane events for `payments-archive` are NOT captured in this profile. **Re-run with `--region us-west-2` or expand scoping primitive to cover all regions.**
- Open question for outgoing team: is `payments-archive` in us-west-2 in scope for the takeover? Why us-west-2?
