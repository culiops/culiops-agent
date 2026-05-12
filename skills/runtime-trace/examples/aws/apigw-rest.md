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

- `idle` — `Count` sum is 0.
- `healthy` — 5XX rate < 1% and 4XX rate < 5%.
- `degraded` — 5XX rate ≥ 1% OR 4XX rate ≥ 5%.
- `unknown` — any required metric returned no datapoints.

Note: HTTP APIs (v2) are not covered by this file. Add `examples/aws/apigw-http.md` if needed.
