# World index — culibox-missing-token

The first matching row wins; `*` matches any text. A command that matches no row returns `_default.txt` (`{}` for a JSON API, no lines for a text command): no data, never an error. Region `eu-west-1` is implied when omitted.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls * .culiops/sre-investigate*` | `_default.txt` | Only `environment.md` exists. |
| `command -v agentbox-env` | `agentbox-path.txt` | Exit status 0. |
| `*${SENTRY_AUTH_TOKEN:+x}*` | `_default.txt` | Expands to nothing: the variable is unset. |
| `aws * --profile prod-read*` | `sso-expired-prod-read.txt` | Exit status 255 for every `prod-read` call, including `sts get-caller-identity`. |
| `aws sts get-caller-identity --profile staging-read*` | `sts-staging-read.json` | |
| `aws iam get-role --profile staging-read *` | `iam-get-role-staging.json` | |
| `aws iam simulate-principal-policy --profile staging-read *` | `iam-simulate-readonly.json` | Every write action `implicitDeny`. |
| `aws ecs describe-services --profile staging-read * payments-worker*` | `ecs-describe-services-staging.json` | Rev 19 rolled out 06:24:10–06:28:52 UTC. |
| `gh api repos/example-org/payments-worker/compare/*` | `gh-compare.txt` | Also `gh pr list` / `gh release view` for v4.12.0: same summary. |
| `aws cloudwatch get-metric-data --profile staging-read *` | `cw-dlq-staging.json` | `payments-worker-dlq` ApproximateNumberOfMessagesVisible, period 300, 05:30–07:10 UTC. |
| `aws logs describe-log-groups --profile staging-read*` | `logs-describe-log-groups-staging.json` | 3,758,096,384 stored bytes, 14-day retention. |
| `aws logs start-query --profile staging-read * /ecs/payments-worker*` | `li-start-staging.json` | Any errors query (by revision and message, or raw lines). |
| `aws logs get-query-results --profile staging-read * 9a0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d*` | `li-results-staging.json` | 03:00–07:15 UTC. |
| `curl *sentry.io/api/0/*` | `sentry-401.json` | HTTP 401 without a token. |
| `sentry-cli *` | `sentry-401.json` | Same without a token. |
| `agentbox-env *` | `_default.txt` | |
