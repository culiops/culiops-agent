# Dry-run of `pre-flight` against `app-impact-cdn-cache`

Simulated runs on 2026-10-26: the operator from `operator-script.md`, live results from `live-responses.md`, and the app as a separate local checkout (Mode A) tagged `v5.2.0`.

## Baseline (category 11 with an inclusion-list trigger)

Two runs, with the `Application source` section removed from the operator script. Both runners wrote that, read literally, a cache behavior is not an app-contract attribute, so category 11 would be Green. Both scored it ⚪ on their own judgment. Neither found the cross-user cart or the blocked `POST`. The verdict was RED only through Yellow / ⚪ escalation.

## With the fail-closed trigger and Step 5b

| Principle | Exercised by |
|---|---|
| Fail-closed trigger | A cache behavior is not on the not-app-facing list, so category 11 triggers (CDN / edge / routing row) and Q8 is asked |
| Mode A | `git rev-parse` → `30bb533`, clean tree, tag `v5.2.0` |
| Personalised responses under a cookie-less cache key | `src/routes/catalog.js:8-15` (member price from the `sid` cookie) and `:21-24` (the signed-in user's cart) under `CachingOptimized` → served to other viewers for up to the default TTL |
| Method restriction | `POST /api/catalog/cart/items` (`catalog.js:27-32`) vs allowed methods GET / HEAD / OPTIONS (`plan:16-20`) → CloudFront 403 |
| Silent breakage | Prices and carts are 200s. The 403s show only in `4xxErrorRate`. `/healthz` is outside the pattern |
| Category 9 | Another user's cart served to anonymous viewers is data exposure → hard block |
| Source conflict | The catalog note "not personalised" (`catalog:.culiops/service-discovery/shopfront.md:20`, generated 2026-04-12; a catalog is a lead and never satisfies `plan` / `code` / `live`) and the operator's Q7 are contradicted by the code → drift, code wins |
| Decoy | `min_ttl = 0` in the plan is the deprecated per-behavior field. It is not evidence that nothing is cached |
| Step 5b | Citations re-checked. Category 5 Green → ⚪ (peak is a checkable fact, operator-stated only). The cache-policy contents are marked UNVERIFIED (`get-cache-policy` returned no data). Fresh eyes ran because a hard block fired: it agreed on the verdict and disagreed on category 2, which was settled as Yellow |

## Scoring

| # | Category | Score | Signal |
|---|---|---|---|
| 1 | Blast radius | 🔴 | The CDN in front of the whole shop, user-facing (`plan:10-31`) |
| 2 | Reversibility | 🟡 | Revert is minutes. Responses already served can't be recalled |
| 3 | Change velocity | 🟢 | Fixture condition |
| 4 | Dependency impact | 🟡 | Fronts the API for all paths; the catalog is stale |
| 5 | Timing context | ⚪ | Peak is operator-stated; no live baseline |
| 6 | Operator familiarity | 🟢 | Many times |
| 7 | Observability readiness | 🔴 | No alarms in the IaC. The failures are 403s and wrong 200s, not 5xx |
| 8 | Cost impact | 🟢 | No new resources |
| 9 | Security posture | 🔴 HARD BLOCK | Per-user responses cached without the cookie (`app:shopfront-api@30bb533:src/routes/catalog.js:21-24`) |
| 10 | Resource health | ⚪ | Partial live evidence |
| 11 | Application compatibility | 🔴 | Cart, member price, `POST` 403 (`catalog.js:8-15`, `:21-24`, `:27-32`) |

Record header: plan hash `sha256:aba7321776dae8838a1307331fbbefc6289e168c7397a08d1b7594e4a9b6f46b`, target `777788889999` / `us-west-2` (CloudFront global), App source `local shopfront-api @ 30bb533 (v5.2.0)`.

**Verdict: RED — HARD BLOCK** (category 9).

## Mitigations the skill should recommend

- Narrow `path_pattern` to routes proven non-personalised, or keep `/api/catalog/cart*` on `CachingDisabled`.
- If `/products` must be cached: make the price independent of the cookie, or put `sid` in the cache key of a custom policy with short TTLs.
- Allow `POST` on any behavior that covers a write route, or keep write routes outside the pattern.
- Alarm on `4xxErrorRate`, and verify after apply with a signed-in and an anonymous request.
