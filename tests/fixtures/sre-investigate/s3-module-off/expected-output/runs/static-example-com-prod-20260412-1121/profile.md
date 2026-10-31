# Profile: static.example.com prod

Last verified: 2026-04-12 (metrics identifiers verified by W1-Q1; origin, log group and code repo remain unverified) · Built by: helper PROFILE (cheapest tier), run inline in the main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | static.example.com (CloudFront distribution `E3EXAMPLEDIST`, comment "static assets for shop.example.com") |
| Environment | prod |
| Account or profile / Region | `prod-read` (account 111122223333) / us-east-1 (CloudFront metrics, CloudTrail and CloudFront API are read in us-east-1; distribution is global) |
| Cluster, context and namespace | none (no Kubernetes) |
| IaC repo and paths | not known; CloudTrail will show who last changed the distribution (wave 2). Not read yet. |
| Core flows served | asset delivery for `shop.example.com` pages (from environment.md) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| distributions | none: `list-distributions` returned exactly one distribution in the account | n/a |

Single distribution, single origin, CloudFront metrics have `Region=Global`; no regional siblings to compare.

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (static assets; standard logging has IncludeCookies false) |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | none: no CloudWatch log group with prefix `/ecs/static` (W0 `describe-log-groups` returned an empty reply) | (unverified) |
| Sidecar or proxy logs | CloudFront standard logs in S3: bucket `example-edge-logs`, prefix `cf/static/` (from distribution config; objects not read by this run) | (verified 2026-04-12 as configured in the distribution, W0-H2); contents not read |
| APM or trace service name | none | n/a |
| Prometheus job and labels | none | n/a |
| Business or flow counters | none | n/a |
| CloudWatch metrics | namespace `AWS/CloudFront`, dimensions `DistributionId=E3EXAMPLEDIST`, `Region=Global`; metrics Requests, BytesDownloaded, 4xxErrorRate, 5xxErrorRate, TotalErrorRate, 502/503/504ErrorRate, OriginLatency, CacheHitRate (listed by `list-metrics`, additional metrics subscription Enabled) | (verified 2026-04-12): the names Requests, 5xxErrorRate, 4xxErrorRate, TotalErrorRate, 502/503/504ErrorRate, OriginLatency, CacheHitRate, BytesDownloaded returned data (W1-Q1); BytesDownloaded is sum bytes per minute |
| Compute | origin `origin-static` = `origin-static.example.com` (custom origin, https-only); what hosts it is not known (no ECS cluster or load balancer visible from `prod-read` in us-east-1) | (unverified) |
| Load balancing | not discovered | (unverified) |
| Data stores | none known | n/a |
| Queues and streams | none | n/a |
| Functions | none seen in the distribution config | n/a |
| Log datasource | CloudWatch via `prod-read`; no log group for this service | (unverified) |
| Error tracker project | none | n/a |
| Code | `example-org/static-assets` (from environment.md; read through `gh`). Default branch not returned by `gh api` (empty reply). Image tag to ref rule: unknown. | (unverified) |
| Tickets and wiki | none | n/a |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| downstream | origin for static assets | HTTPS, custom origin, read timeout 30 s, connection timeout 10 s, 3 connection attempts | `origin-static.example.com` | not known (owning team of the origin to be named by a human) |
| upstream | browsers of `shop.example.com` pages | HTTPS GET/HEAD on `static.example.com` | alias `static.example.com` | none |

No third party is known to be in the path.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | n/a | n/a |

## Baseline notes

- Normal load and latency (previous window 09:00-10:10 UTC on 2026-04-12 and the 8 hourly days 04-04 to 04-12): about 7,800 requests per minute (hourly median 361,743, p95 467,742); 5xxErrorRate about 0.04% (8-day hourly max 0.053); 504ErrorRate about 0.02%; 4xxErrorRate about 1.2% (1.10 to 1.30 per minute); OriginLatency (average) about 89 ms (8-day hourly max 89.9 ms); CacheHitRate about 94.1%. Source: W1-Q2, W1-Q4.
- Known periodic jobs and their usual effect: none known.
- Known benign noise: 4xxErrorRate about 1.2% per minute at all hours (W1-Q2): harmless baseline, not a finding unless it moves.
- Distribution config facts: `CustomErrorResponses` caches origin 504 responses for 10 s (`ErrorCachingMinTTL` 10); no response page override. `LastModifiedTime` of the distribution is 2026-02-18T09:41:12Z (config unchanged since then).

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none yet | n/a | n/a |
