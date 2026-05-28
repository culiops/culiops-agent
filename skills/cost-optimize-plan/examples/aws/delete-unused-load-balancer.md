---
cloud: aws
action: delete
resource_type: load-balancer
applies_when: action == "delete" AND resource matches "arn:aws:elasticloadbalancing:*"
---

# Verify: Delete unused load balancer

## Required IAM
- `elasticloadbalancing:DescribeLoadBalancers`
- `elasticloadbalancing:DescribeTargetGroups`
- `elasticloadbalancing:DescribeTargetHealth`
- `cloudwatch:GetMetricStatistics`
- `route53:ListHostedZones`
- `route53:ListResourceRecordSets`
- `cloudfront:ListDistributions`

## Queries

1. `aws elbv2 describe-load-balancers --names <name>` — LB metadata, DNS name, scheme, and current state.
2. `aws elbv2 describe-target-groups --load-balancer-arn <arn>` — lists all target groups attached to the LB.
3. Per target group: `aws elbv2 describe-target-health --target-group-arn <tg-arn>` — confirms all targets are `unused` or `draining` (zero healthy targets).
4. `aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCount --dimensions Name=LoadBalancer,Value=<lb-suffix> --start-time <now-14d> --end-time <now> --period 86400 --statistics Sum` — 14-day request count (use `AWS/NetworkELB` for NLBs).
5. Per hosted zone: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id> --query 'ResourceRecordSets[?AliasTarget.DNSName == `<lb-dns-name>.`]'` — checks for Route53 ALIAS records pointing at the LB DNS name.
6. `aws cloudfront list-distributions --query 'DistributionList.Items[?Origins.Items[?DomainName == `<lb-dns>`]]'` — checks whether any CloudFront distribution uses the LB as an origin.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| Healthy targets across all target groups | 0 | ≥ 1 healthy target |
| 14d total `RequestCount` | 0 | > 0 |
| Route53 ALIAS records pointing at LB DNS name | 0 | ≥ 1 |
| CloudFront origin references | none | any |
| LB `State.Code` | `active` (confirm it exists, no pending state) | `provisioning` or `active_impaired` |

## Reversibility classification
- **Default:** 🔴 irreversible. The LB DNS name is released on deletion; a new LB receives a different DNS name. All downstream DNS ALIAS records, CloudFront origins, and application configs referencing the old DNS name break immediately.

## Blast radius classification
- **Default:** 🟡 — LBs are commonly referenced from outside the IaC repo (Route53 ALIAS records, CloudFront origins, hardcoded config). Blast radius widens to 🔴 if Route53 or CloudFront references are found.

## Rollback note (informational, shown in plan)
"Deletion frees the DNS name immediately — it is not recoverable. Any references (Route53 ALIAS records, CloudFront origins, application-config base URLs) must be identified and updated to a new LB DNS name BEFORE deletion. There is no grace period after the delete API call returns."
