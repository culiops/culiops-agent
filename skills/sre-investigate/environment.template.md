# sre-investigate environment

Copy this file once per repo to `<output root>/environment.md` (`.culiops/sre-investigate/environment.md`, or `$CULIOPS_HOME/<workspace>/sre-investigate/environment.md`) and fill it in. It is local and never committed. The skill reads it at the start of every run; it holds facts about your estate, not method.

Rules for filling it in:

- **Names, never secrets.** Token fields hold the name of an environment variable. Never paste a token, a password or a key here.
- **Placeholders are placeholders.** Every value below is an example. Delete rows you do not have; leave nothing half-filled. An empty list means "not used", and the skill records the matching backend as a gap.
- **Defaults are neutral.** The severity scale and budgets are starting points. Replace them with your organisation's own.

## Timezone

The skill works in UTC everywhere. The report also shows your local time, taken from here. If this is empty the skill asks; it does not guess.

```yaml
timezone: <IANA zone, for example Europe/London>
```

## AWS profiles

One row per account the investigation may read. Use a read-only profile (`ReadOnlyAccess` or tighter), never an administrator one. Profiles are passed with `--profile` on every command.

```yaml
aws:
  profiles:
    - name: <profile-name>
      account: "111122223333"
      region: us-east-1
      purpose: <what runs in this account, for example "production workloads">
    - name: <profile-name>
      account: "444455556666"
      region: eu-west-1
      purpose: <for example "non-production">
```

An account you cannot read from a profile is listed under `purpose` as "no profile", so the run records a gap instead of guessing.

## Kubernetes contexts

```yaml
kube:
  contexts:
    - name: <kubeconfig-context-name>
      cluster: <cluster name>
      namespaces: [<namespace>]    # the namespaces the investigation reads; used by the write-check
      purpose: <for example "production">
```

## Datasources

One row per observability backend you want the skill to use. `id/url` is a datasource UID, a base URL, or a project slug, whichever the backend uses. `token_env` is the environment variable that holds the token. Leave it empty for backends that use your AWS or kube credentials.

```yaml
datasources:
  - backend: <prometheus | loki | tempo | grafana | sentry | cloudwatch | xray | datadog | newrelic | elastic-apm>
    name: <human name, for example "metrics (production)">
    id/url: <datasource UID or https://metrics.example.com>
    token_env: <ENV_VAR_NAME>
  - backend: <backend>
    name: <name>
    id/url: <https://logs.example.org>
    token_env: <ENV_VAR_NAME>
```

Prefer viewer-only tokens.

## Code and tickets

Application source is read by ref only: `gh` (read-only calls) and/or a local clone. The skill never runs `pull` or `checkout`.

```yaml
code:
  github_repos: [example-org/<service-repo>]
  local_clones:
    - repo: <service-repo>
      path: </absolute/path/to/clone>
```

If your tickets are readable through a read-only MCP server or an API, name the route here (variable names only): `tickets: <route and token_env>`.

## Core flows

The user-facing flows whose failure makes an incident severe. They drive the severity scale and the business-metric checks.

```yaml
core_flows:
  - name: <flow, for example "sign-in">
    # optional: how to see this flow in data
    metric: <counter or query name>
    datasource: <datasource name from above>
    key_labels: [<label>, <label>]
  - name: <flow>
```

If your organisation has an SLO or error budget for a flow, say where it lives (used first when sizing impact):

```yaml
slo:
  source: <for example "Prometheus recording rules" or "SLO dashboard URL">
  names: [<slo name>]
```

## Severity

Neutral default scale. Replace it with your organisation's scale; the skill only ever suggests a severity, the incident owner decides.

| Level | Meaning |
|---|---|
| SEV1 | A customer-facing core flow is down, or more than 5% of requests are failing. |
| SEV2 | Significant partial degradation: one feature or one parallel deployment affected, with a workaround or partial service. |
| SEV3 | Minor or internal impact, or a non-critical service. |
| SEV4 | Non-production only, or no impact on customers. |

## Budgets

How much one run may spend on queries. These are neutral starting values, and your organisation should tune them. The skill asks before going past a budget.

```yaml
budgets:
  fast:
    queries: 20
    log_gb_scanned: 2
    cloudwatch_metric_requests: 100
  deep:
    queries: 60
    log_gb_scanned: 10
    cloudwatch_metric_requests: 500
  per_query_soft_limit_gb: 1     # a single log query estimated above this is narrowed or confirmed first

insights_ask_threshold_gb: 2     # a CloudWatch Logs Insights query estimated above this always asks, in both modes
```

`insights_ask_threshold_gb` applies even in Fast mode, where read-only waves otherwise run without waiting.

## Notes

Anything else the skill should know that does not fit above: naming conventions for log labels or service names, parallel deployments (regions, shards, tenants) and how to tell them apart, known noisy alerts. Keep it short and factual.
