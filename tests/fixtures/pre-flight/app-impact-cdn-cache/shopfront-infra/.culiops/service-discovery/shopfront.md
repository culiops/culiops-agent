# Service catalog: shopfront

Generated: 2026-04-12 (service-discovery)

## Resource Catalog

| Resource | Type | Notes |
|---|---|---|
| `aws_cloudfront_distribution.shopfront` | CloudFront | Single origin `api-alb`. Default behavior: caching disabled, all viewer values forwarded |
| `aws_lb.api` | ALB | Fronts the `shopfront-api` ECS service |

## Dependency Graph

| From | To | Notes |
|---|---|---|
| CloudFront `shopfront` | ALB `shopfront-api` | All paths |

## Notes

- `/api/catalog/*` serves public product data (names, images, list prices). Not personalised.
