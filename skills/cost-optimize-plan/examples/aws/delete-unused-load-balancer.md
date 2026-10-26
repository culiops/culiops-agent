---
cloud: aws
action: delete
resource_type: load-balancer
applies_when: action == "delete" AND resource matches "arn:aws:elasticloadbalancing:*"
---

# Verify: Delete unused load balancer

## Required IAM
- `elasticloadbalancing:DescribeLoadBalancers`
- `elasticloadbalancing:DescribeListeners`
- `elasticloadbalancing:DescribeTargetGroups`
- `elasticloadbalancing:DescribeTargetHealth`
- `cloudwatch:GetMetricStatistics`
- `route53:ListHostedZones`
- `route53:ListResourceRecordSets`
- `cloudfront:ListDistributions`

## Queries

1. `aws elbv2 describe-load-balancers --names <name>` — LB metadata, DNS name, scheme, and current state.
2. `aws elbv2 describe-listeners --load-balancer-arn <arn>` — active listeners; any listener whose default action forwards to a target group means the LB is wired to serve traffic.
3. `aws elbv2 describe-target-groups --load-balancer-arn <arn>` — lists all target groups attached to the LB.
4. Per target group: `aws elbv2 describe-target-health --target-group-arn <tg-arn>` — confirms all targets are `unused` or `draining` (zero healthy targets).
5. `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCount --dimensions Name=LoadBalancer,Value=<lb-suffix> --start-time <now-90d> --end-time <now> --period 3600 --statistics Sum` — request count over the 60–180d band at hourly granularity (90d used here; Principle 3; use `AWS/NetworkELB` for NLBs). RequestCount alone never justifies deletion — it must agree with the listener / target-health / DNS signals below.
6. Per hosted zone: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id> --query 'ResourceRecordSets[?AliasTarget.DNSName == `<lb-dns-name>.`]'` — checks for Route53 ALIAS records pointing at the LB DNS name.
7. `aws cloudfront list-distributions --query 'DistributionList.Items[?Origins.Items[?DomainName == `<lb-dns>`]]'` — checks whether any CloudFront distribution uses the LB as an origin.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| Listeners forwarding to a target group | 0 | ≥ 1 active listener |
| Healthy targets across all target groups | 0 | ≥ 1 healthy target |
| 90d total `RequestCount` (hourly) | 0 | > 0 |
| Route53 ALIAS records pointing at LB DNS name | 0 | ≥ 1 |
| CloudFront origin references | none | any |
| LB `State.Code` | `active` (confirm it exists, no pending state) | `provisioning` or `active_impaired` |

## Reversibility classification
- **Default:** 🔴 irreversible. The LB DNS name is released on deletion; a new LB receives a different DNS name. All downstream DNS ALIAS records, CloudFront origins, and application configs referencing the old DNS name break immediately.

## Blast radius classification
- **Default:** 🟡 — LBs are commonly referenced from outside the IaC repo (Route53 ALIAS records, CloudFront origins, hardcoded config). Blast radius widens to 🔴 if Route53 or CloudFront references are found.

## Rollback note (informational, shown in plan)
"Deletion frees the DNS name immediately — it is not recoverable. Any references (Route53 ALIAS records, CloudFront origins, application-config base URLs) must be identified and updated to a new LB DNS name BEFORE deletion. There is no grace period after the delete API call returns."
