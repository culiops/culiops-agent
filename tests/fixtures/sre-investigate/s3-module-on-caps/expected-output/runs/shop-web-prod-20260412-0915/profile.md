# Profile: shop-web prod

Last verified: 2026-04-12 · Built by: main session (profile built inline, helper PROFILE rules, cheapest tier); updated at the end of the run · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | shop-web (public site shop.example.com) |
| Environment | prod |
| Account or profile / Region | prod-read (111122223333) / us-east-1 |
| Cluster, context and namespace | ECS Fargate per environment.md; cluster name not discovered (aws ecs list-clusters returned nothing) (unverified) |
| IaC repo and paths | not named in environment.md (unverified) |
| Core flows served | checkout (`POST /checkout`), cart (`/api/cart`), from environment.md; no counters named |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| (none) | one web ACL, one ALB | single `example-shop-acl` in us-east-1 REGIONAL scope; ACL has no CloudFront-scope sibling |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | name not known (unverified); the WAF logs carry a salted `client_key` (1,546 distinct keys in 13:40-15:19), so a cookie or header is configured for the module |
| Client-ID header name | not known (unverified) |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/ecs/*` per environment.md; prefix `/ecs/shop` returned nothing | (unverified) |
| WAF web ACL | `example-shop-acl`, scope REGIONAL, us-east-1, Id 5b0c7a1e-3d42-4f6a-9e8b-2c1d0a9f7e64, metric name `example-shop-acl` | (verified 2026-04-12) |
| WAF rules (name = metric name) | `AWS-AWSManagedRulesAmazonIpReputationList` (p0, managed group, group's own actions), `geo-block-embargo` (p1, Block, countries KP and IR), `rate-limit-coupon` (p2, Block, 10 requests per 300 s per IP, path starts with `/api/cart/coupon`), `count-new-bot-signals` (p3, Count, UA contains "bot") | (verified 2026-04-12) |
| WAF logging | S3 `aws-waf-logs-example-shop`, no filter, no redaction; module dataset `shop-waf[waf]` (manifest bucket and key tie it to this ACL; log totals equal CloudWatch for 2026-04-11 13:40-15:19) | (verified 2026-04-12) |
| WAF CloudWatch | AWS/WAFV2, dimensions WebACL=`example-shop-acl`, Rule=`ALL` or the rule metric name, Region=`us-east-1` | (verified 2026-04-12 via list-metrics) |
| Load balancing | ALB `app/shop-web-alb/9f8e7d6c5b4a3210` (ARN returned by list-resources-for-web-acl) | the ARN is verified; ALB CloudWatch dimensions and elbv2 listing (unverified): `describe-load-balancers` returned nothing |
| Compute | ECS Fargate service `shop-web`; cluster unknown | (unverified) |
| Error tracker / traces | none connected | n/a |
| Code | `example-org/shop-web` via gh (no clone); image-tag-to-ref rule unknown | (unverified) |
| Tickets and wiki | none named | n/a |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| upstream | AWS WAF (web ACL) in front of the ALB | ACL association | `example-shop-acl` | none (AWS) |
| upstream | ALB | ALB to ECS service | `shop-web-alb` | none |

## Dashboards

None named.

## Baseline notes

- Normal load and latency: allowed requests about 666 a minute (2026-04-11 12:30-13:40 and 2026-04-04 13:40-14:50); blocked about 4.4 a minute (IP reputation about 3, geo-block about 1.4); hourly allowed median 39,678 (2026-04-04 to 2026-04-11). Latency not read (no ALB metrics).
- Known periodic jobs: none found (events list-rules, scheduler list-schedules and ssm describe-maintenance-windows returned nothing; ECS scaling not readable).
- Known benign noise: IP reputation list blocks (median 158 an hour, max 300) and geo-block (median 77 an hour, max 159) every hour; ExampleSearchBot crawler (about 2,700 requests per 100 minutes, few blocks); count-new-bot-signals counts about 900 requests per 100 minutes (Count only).

## Stale identifiers

None yet.
