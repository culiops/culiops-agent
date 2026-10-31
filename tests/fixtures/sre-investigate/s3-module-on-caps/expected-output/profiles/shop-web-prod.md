# Profile: shop-web prod

Last verified: 2026-04-12 (updated at the end of the run) · Built by: main session, inline (the PROFILE checklist run as one wave of free reads under the helper's rules; no helper dispatched in this simulation, labelled `[helper PROFILE, cheapest tier]` in the run log) · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | shop-web (the service behind shop.example.com) |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / us-east-1 |
| Cluster, context and namespace | ECS Fargate per environment.md; cluster and service names NOT discovered (`aws ecs list-clusters` returned `{}`): `(unverified)` |
| IaC repo and paths | not given in environment.md; not discovered |
| Core flows served | checkout (`POST /checkout`), cart (`/api/cart`), both listed in environment.md; criticality: core |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| none identified | web ACL `example-shop-acl` fronts one ALB only (`shop-web-alb`); no regions, shards or replicas found | n/a |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | unknown `(unverified)`: not in environment.md; app source (`example-org/shop-web`) not readable in this run (`gh api` returned `{}`); the S3 module's salted `client_key` column is used instead |
| Client-ID header name | unknown `(unverified)` |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/ecs/*` per environment.md; `aws logs describe-log-groups --log-group-name-prefix /ecs/` returned `{}` (no group visible) | (unverified) |
| Sidecar or proxy logs | none | n/a |
| APM or trace service name | none (no tracing backend) | n/a |
| Prometheus job and labels | none | n/a |
| Business or flow counters | none named in environment.md | n/a |
| Compute | ECS service shop-web (name from the request/environment.md) | (unverified) |
| Load balancing | ALB `shop-web-alb`, `app/shop-web-alb/9f8e7d6c5b4a3210`: returned by `wafv2 list-resources-for-web-acl` for the ACL below (association verified); ALB CloudWatch metrics returned no data in wave 1 (ledger W1-Q4..Q6) and `elbv2 describe-load-balancers` returned `{}` (W0-Q14) | association (verified 2026-04-12); metrics (unverified) |
| WAF | regional web ACL `example-shop-acl`, id `5b0c7a1e-3d42-4f6a-9e8b-2c1d0a9f7e64`, us-east-1, REGIONAL, default action Allow, 4 rules (see below); metric dimensions `WebACL=example-shop-acl`, `Region=us-east-1`, `Rule` = rule name or `ALL` | (verified 2026-04-12) |
| WAF rule metrics | `AWS-AWSManagedRulesAmazonIpReputationList` (managed group, no override), `geo-block-embargo` (Block, countries KP and IR), `rate-limit-coupon` (Block, rate-based, 10 requests per 300 s per IP, scope-down: URI path starts with `/api/cart/coupon`), `count-new-bot-signals` (COUNT mode: user-agent contains `bot`) | (verified 2026-04-12 by get-web-acl and list-metrics; per-rule BlockedRequests returned data in wave 1; `count-new-bot-signals` CountedRequests returned no data) |
| WAF logging | S3 bucket `aws-waf-logs-example-shop`, no logging filter, no redacted fields (every request is logged, allowed included) | (verified 2026-04-12 by get-logging-configuration) |
| S3 log module dataset | `shop-waf` (type waf) in `~/.config/culiops/sre-investigate/logs.env`; the manifest bucket `aws-waf-logs-example-shop` and key path (account 111122223333, us-east-1, example-shop-acl) equal the ACL's logging destination (W2-Q9); fetched and queried 2026-04-11 13:40-15:20 (W3-Q1..Q13) | (verified 2026-04-12) |
| Data stores | none discovered | n/a |
| Queues and streams | none | n/a |
| Functions | none | n/a |
| Log datasource | CloudWatch via profile prod-read (no group found) | (unverified) |
| Error tracker project | none | n/a |
| Code | `example-org/shop-web` via `gh` (default branch and deployed ref not discovered: `gh api` returned `{}`) | (unverified) |
| Tickets and wiki | none | n/a |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| upstream | clients reaching shop.example.com through the ALB | HTTPS, filtered by the web ACL | `example-shop-acl` | none (no third party in the path found) |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- WAF client mix at normal times (13:40-15:20 slice, W3): about 570 distinct clients, 4 browser user agents (Safari macOS/iOS, Chrome Windows/Android) with ~127 clients each, JA4 t13d1516h2_8daaf6152771_02713d6af862, 8-header browser shape with cookie; ExampleSearchBot/2.1 is a known crawler (COUNT-mode rule count-new-bot-signals counts it).

- Normal load: ~3,300-3,500 allowed requests per 5 minutes at 12:30-15:30 UTC; ~230-270 blocked requests per hour all rules (W1-Q1..3, W1-Q7).
- Known periodic jobs and their usual effect: none discovered (schedule listings returned `{}`).
- Known benign noise: IP-reputation and geo rules block ~10-20 and ~5-10 requests per 5 minutes in every window checked.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| `/ecs/*` log-group prefix (as an application log group) | shop-web-prod-20260412-0915 | `aws logs describe-log-groups --log-group-name-prefix /ecs/` returned `{}` (W0-Q3); nothing replaced it; ask the operator for the exact group name |
| ECS cluster and service for shop-web | shop-web-prod-20260412-0915 | `aws ecs list-clusters` returned `{}` (W0-Q13); never confirmed |
