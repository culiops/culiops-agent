---
cloud: aws
action: delete
resource_type: load-balancer
applies_when: action == "delete" AND resource matches "arn:aws:elasticloadbalancing:*"
---

# Verify: Delete unused load balancer

Three types, three metric families. Identify the type first: ARN `loadbalancer/app/…` = ALB, `loadbalancer/net/…` = NLB, `loadbalancer/<name>` (no type segment) = Classic (CLB), `loadbalancer/gwy/…` = Gateway LB (not covered → ❔). `elbv2` APIs do not return CLBs; `elb` APIs do not return ALB/NLB.

## Required IAM
- `elasticloadbalancing:DescribeLoadBalancers`, `DescribeTags`, `DescribeListeners`, `DescribeTargetGroups`, `DescribeTargetHealth`, `DescribeInstanceHealth` (CLB)
- `cloudwatch:GetMetricData`
- `route53:ListHostedZones`, `route53:ListResourceRecordSets`
- `cloudfront:ListDistributions`, `cloudfront:ListVpcOrigins`
- `globalaccelerator:ListAccelerators`, `ListListeners`, `ListEndpointGroups`
- `apigateway:GET` (VPC links), `apigatewayv2:GET` (optional)
- `ec2:DescribeVpcEndpointServiceConfigurations`

## Queries

0. **Target check + ownership probe** (`examples/aws.md`). Tags: `aws elbv2 describe-tags --resource-arns <arn>` (ALB/NLB) or `aws elb describe-tags --load-balancer-names <name>` (CLB). Tags `elbv2.k8s.aws/cluster`, `service.k8s.aws/stack`, `kubernetes.io/service-name` or `kubernetes.io/cluster/<name>` → owner `k8s` → ❔ `owned-by-k8s` (delete the Service/Ingress; the controller recreates a deleted LB). Drop the remaining queries for that item.
1. Describe (source of the metric dimension, Metrics rule (b)/(c)):
   - ALB/NLB: `aws elbv2 describe-load-balancers --load-balancer-arns <arn>` — type, DNS name, state, scheme. The CloudWatch `LoadBalancer` dimension is the ARN suffix after `loadbalancer/` (`app/<name>/<id>` or `net/<name>/<id>`). State other than `active` (`provisioning`, `active_impaired`, `failed`) → re-check later; do not score.
   - CLB: `aws elb describe-load-balancers --load-balancer-names <name>` — DNS name, listeners, instances. The `LoadBalancerName` dimension is the name.
2. Listeners: ALB/NLB `aws elbv2 describe-listeners --load-balancer-arn <arn>`; CLB listeners come from Query 1.
3. Targets: ALB/NLB `aws elbv2 describe-target-groups --load-balancer-arn <arn>`, then per target group `aws elbv2 describe-target-health --target-group-arn <tg-arn>` (count `healthy`). CLB: `aws elb describe-instance-health --load-balancer-name <name>` (count `InService`).
4. **Activity** — `aws cloudwatch get-metric-data`, `Sum`, **hourly**, window 90d (delete band, Principle 3; Metrics rule: no `get-metric-statistics` at hourly for 90d). Read the temporal distribution.
   - **ALB:** `AWS/ApplicationELB` `RequestCount`, dimension `LoadBalancer=app/<name>/<id>`.
   - **NLB:** there is **no `RequestCount`**. Use `AWS/NetworkELB` `NewFlowCount` and `ProcessedBytes`, dimension `LoadBalancer=net/<name>/<id>`.
   - **CLB:** `AWS/ELB` `RequestCount` (HTTP requests; connections for TCP listeners — verify), dimension `LoadBalancerName=<name>`.
   - Subtract synthetic traffic (Principle 1 rule 2): uniform periodic cadence from uptime probes or Route53 health checkers is not use.
5. **Route53 aliases** — `aws route53 list-hosted-zones` (public and private), then per zone list ALL records (paginate: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id>`) and match client-side, case-insensitive, against the LB DNS name with the trailing dot stripped, with or without a `dualstack.` prefix, in both `AliasTarget.DNSName` and CNAME `ResourceRecords[].Value`. Do not use an exact JMESPath `==` (console-made aliases are `dualstack.<dns>.` and Route53 lowercases names).
6. **CloudFront** — `aws cloudfront list-distributions` (paginate), match `Origins.Items[].DomainName` client-side, case-insensitive. Also `aws cloudfront list-vpc-origins` — `OriginEndpointArn` equal to the LB ARN.
7. **Global Accelerator** (API endpoint `us-west-2`) — `aws globalaccelerator list-accelerators --region us-west-2`, then `list-listeners --accelerator-arn`, then `list-endpoint-groups --listener-arn`; match `EndpointDescriptions[].EndpointId` to the LB ARN.
8. **NLB wiring** — API Gateway REST VPC links: `aws apigateway get-vpc-links` (`targetArns` contains the NLB ARN). `aws apigatewayv2 get-vpc-links` lists subnet-based links with no LB ARN: for HTTP APIs the reference lives in integrations (`aws apigatewayv2 get-apis`, then `get-integrations --api-id <id>`, `IntegrationUri` = a listener ARN of this LB) — opt-in, one call per API (verify). VPC endpoint services (PrivateLink): `aws ec2 describe-vpc-endpoint-service-configurations` (per region) — `NetworkLoadBalancerArns` contains the NLB ARN.
9. **External DNS** (Cloudflare, other registrars' DNS, on-prem) **cannot be swept by this skill.** Record a Gap in the plan: "external DNS not checked". Ask the operator; an `operator-stated` "no external DNS" is accepted, citing who said so.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Type-specific activity (Query 4): ALB `RequestCount`; NLB `NewFlowCount` + `ProcessedBytes`; CLB `RequestCount` — hourly, 90d | required | 0 across the window, Metrics rule satisfied | > 0 on a recurring or recent pattern (Principle 3) |

⚪: Target check failed, Query 1 failed, wrong namespace/dimension for the LB type, or metric not returned → Evidence ⚪ (→ 🔴). An NLB read with `RequestCount` is ⚪, never 🟢.

## Attachment (Dimension 2 / 4 input)

Attachment never produces 🚫 (Principle 1).

| Signal | Query | Effect |
|--------|-------|--------|
| Listener(s) forwarding to a target group / instance | 2 | any → LB is wired: idle-ambiguous (see below); Dependency 🟡 |
| Healthy targets (`healthy` / `InService`) | 3 | ≥ 1 → Blast 🔴 (wired into a serving path); idle-ambiguous |
| Route53 alias / CNAME to the LB | 5 | ≥ 1 → Blast 🔴 |
| CloudFront origin or VPC origin | 6 | ≥ 1 → Blast 🔴 |
| Global Accelerator endpoint | 7 | ≥ 1 → Blast 🔴 |
| API Gateway VPC link / HTTP API integration (NLB/ALB) | 8 | ≥ 1 → Blast 🔴 |
| VPC endpoint service (PrivateLink, NLB) | 8 | ≥ 1 → Blast 🔴 (consumers in other accounts) |
| External DNS not swept | 9 | unless operator-stated none → idle-ambiguous |
| IaC references to the ARN / DNS name (`code:`) | 0 | 1–2 → Dependency 🟡; ≥ 3 → Dependency 🔴 |

**Idle-ambiguous (🔵):** an LB with zero activity (Evidence 🟢) but any wiring above, or with unswept external DNS, routes the delete to 🔵 — only the owner can say decommissioned vs paused/seasonal. Only an LB with Evidence 🟢, no wiring found, and operator-stated no external DNS is a plain delete candidate.

## Reversibility classification
- **Default:** 🔴 irreversible. The LB DNS name is released on deletion; a recreated LB (even from IaC) gets a different DNS name, breaking every external reference. Owner `unmanaged` changes nothing.

## Blast radius classification
- **Default:** 🟡 — LBs are commonly referenced from outside the IaC repo (DNS, CloudFront, hardcoded config).
- **Raised to 🔴:** any Attachment row above that says so.

## Rollback note (informational, shown in plan)
"Deletion frees the DNS name immediately — it is not recoverable, and a replacement LB receives a different name. Every reference (Route53 aliases, CloudFront origins, Global Accelerator endpoints, API Gateway VPC links, PrivateLink endpoint services, external DNS, application-config base URLs) must be identified and moved BEFORE deletion. External DNS is not checked by this skill. There is no grace period after the delete call returns."
