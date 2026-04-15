# widgetapi on-call reference

Short pointers for the on-caller. This is **not** an incident runbook — it lists where the dashboards, alerts, and logs live.

## Services and dashboards

- **APM (Datadog):** service name `widgetapi`, environment tag `env:prod` or `env:staging`. Primary dashboard: `WidgetAPI → Service overview`. Trace explorer: filter by `service:widgetapi`.
- **Infra (Datadog):** Kubernetes dashboard scoped to cluster `widgetapi-prod` (or `widgetapi-staging`). Host map filtered by `cluster:widgetapi-prod`.
- **CloudWatch:** RDS Performance Insights for `widgetapi-prod-db`; ElastiCache metrics for `widgetapi-prod-cache`; ALB metrics for `widgetapi-prod-alb`; CloudFront metrics for the `widgetapi-prod-cdn` distribution.

## Logs

- **Application logs:** Datadog Logs — pipeline `widgetapi`. Also available via `kubectl logs -n widgetapi -l app.kubernetes.io/name=widgetapi`.
- **ALB access logs:** S3 bucket `widgetapi-logs-eu-west-1` under `alb/widgetapi-<env>/`.
- **CloudFront access logs:** same bucket under `cdn/widgetapi-<env>/`.
- **Audit logs (EKS control plane):** CloudWatch log group `/aws/eks/widgetapi-<env>/cluster` (if enabled — check Terraform).

## Alerting and escalation

- **Primary:** PagerDuty service `WidgetAPI Prod` (routing key in Kubernetes Secret `widgetapi.PAGERDUTY_ROUTING_KEY`, namespace `widgetapi`). Staging alerts route to `WidgetAPI Staging` (low-urgency).
- **Synthetic uptime:** Datadog Synthetics test `widgetapi-prod-healthz` — runs every 60s against `https://api.widgetapi.example.com/healthz/live` from eu-west and us-east probes.
- **SLO burn rate:** Datadog monitor `widgetapi-prod-slo-burn` (availability + latency; target 99.9% over 30 days).

## Feature flags

Feature flags live in **LaunchDarkly**, project `widgetapi`. Environments in LaunchDarkly match the Kubernetes namespace — ask the platform team for access if you don't have it.

## Deployment & rollback

- **Deploy:** GitHub Actions workflow `deploy.yml` in the `widgetco/widgetapi` repo. Tags a new image, bumps `image.tag` in `values-<env>.yaml`, runs `helm upgrade`.
- **Rollback:** `helm rollback widgetapi <revision> -n widgetapi` (see `helm history widgetapi -n widgetapi`). Requires cluster-admin or a dedicated `widgetapi-deployer` role — coordinate with platform on-call.

## External dependencies outside this repo

- **Stripe** (payments): configured via the `STRIPE_*` envs loaded from the `widgetapi` Secret. Stripe dashboard and API logs live in Stripe's own console.
- **SendGrid** (email): API key in the same Secret. SendGrid activity feed in the SendGrid UI.
- **AWS Secrets Manager:** DB master user password managed by RDS; pulled at startup using the IRSA role. Do not rotate without coordinating a rolling restart.
