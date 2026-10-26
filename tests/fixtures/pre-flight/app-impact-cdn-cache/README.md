# app-impact-cdn-cache — pre-flight fixture

A Terraform change adds a CloudFront cache behavior for `/api/catalog/*`. It uses the managed `CachingOptimized` cache policy, whose cache key holds no cookies, headers or query strings and whose default TTL is 24h. It also uses the managed `AllViewer` origin request policy, which forwards every cookie to the origin. Allowed methods are GET, HEAD and OPTIONS. Seen from the infra side, this is a faster, cheaper catalog with nothing destroyed and a healthy service. Seen from the app, it is a data leak and a broken cart.

## Layout

- `shopfront-infra/` is the target repo. It holds a service-discovery catalog written 2026-04-12 that says `/api/catalog/*` is "public product data, not personalised". That note is stale.
- `shopfront-api/` is a separate local checkout (Node / Express). Commit it as a git repo with a tag before a run.

## Ground truth

- `src/routes/catalog.js`:
  - `GET /api/catalog/products` reads the `sid` cookie and returns member prices to members.
  - `GET /api/catalog/cart` returns the signed-in user's cart.
  - `POST /api/catalog/cart/items` adds to the cart.
- The app sets no `Cache-Control`. Even if it set `private`, a cache policy with a minimum TTL above 0 caches anyway (AWS CloudFront API reference, `CachePolicyConfig`).
- After apply:
  - The first viewer's cart and prices are cached for 24h, keyed by URL alone, and served to everyone. That is cross-user data exposure.
  - `POST /api/catalog/cart/items` is not an allowed method on the new behavior, so CloudFront rejects it and "add to cart" breaks.
- The plan's `min_ttl = 0` is the deprecated per-behavior field (CloudFormation `CacheBehavior.MinTTL`: "This field is deprecated … use the `MinTTL` field in a cache policy"). The attached `CachingOptimized` policy sets the TTLs: minimum 1s, default 24h (CloudFront Developer Guide, managed cache policies). So the field is not evidence that caching is off.

## A correct assessment MUST

- Trigger category 11 for a CDN cache-behavior change and ask for the app source (Q8).
- Cite the app routes under the pattern (`catalog.js`) and say that cookie-dependent responses would be cached without the cookie in the cache key.
- Score the cross-user exposure on security posture (category 9) as well, because it exposes another user's data.
- Name the blocked `POST` under the new behavior.
- Prefer the code over the stale catalog note, and list that as drift or a disagreement.
- End with a non-GREEN verdict that is driven by these findings.
- Name the mitigations:
  - Narrow `path_pattern` to the public path, or
  - put the cookie in the cache key, or
  - use `CachingDisabled` for the personalised routes,
  - and allow `POST` where it is needed.

## A correct assessment MUST NOT

- Treat the operator's "all public product data", or the catalog note, as evidence.
- Treat the plan's `min_ttl = 0` as meaning nothing is cached.
