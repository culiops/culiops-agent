# CloudWatch metrics — API Gateway (REST API)

For each REST API in scope, the skill fetches these metrics.

| Metric | Namespace | Dimensions | Statistic | Golden signal | Notes |
|---|---|---|---|---|---|
| `Count` | `AWS/ApiGateway` | `ApiName=<name>` | `Sum` | Traffic | total request count |
| `Latency` | `AWS/ApiGateway` | `ApiName=<name>` | `p50` | Latency | median end-to-end latency |
| `Latency` | `AWS/ApiGateway` | `ApiName=<name>` | `p99` | Latency | tail end-to-end latency |
| `IntegrationLatency` | `AWS/ApiGateway` | `ApiName=<name>` | `p99` | Latency | backend integration tail latency |
| `4XXError` | `AWS/ApiGateway` | `ApiName=<name>` | `Sum` | Errors | client error count |
| `5XXError` | `AWS/ApiGateway` | `ApiName=<name>` | `Sum` | Errors | server error count |

**Metric count per API: 6.** 200-metric cap → ~33 REST APIs per run.

**Verdict heuristic:**

- `no-activity-14d` — `Count` has no datapoints (metric listed) or sums to 0.
- `heuristic: healthy` — 5XX rate < 1%.
- `heuristic: degraded` — 5XX rate ≥ 1%.
- 4XX rate is shown as a number, not a verdict: auth-heavy and public APIs routinely run high 4XX rates by design.
- `unknown` — `Count` returned `metric-not-found`.

Empty series are never zero: run the `ListMetrics` existence check (SKILL.md, source d) and record `no-data (metric exists)` or `metric-not-found`. Verdicts describe; they never recommend (Constraint 9). Thresholds are heuristics — always show the raw numbers next to the verdict.

Note: HTTP APIs (v2) are not covered by this file. Add `examples/aws/apigw-http.md` if needed.
