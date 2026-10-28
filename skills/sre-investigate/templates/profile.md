# Profile: <service> <env>

A profile records how one service is named in each backend, so later runs do not rediscover or guess. It lives at `<output root>/profiles/<service>-<env>.md`. During a run, the working copy is the run directory's `profile.md`; this stored file changes only in the record phase. A helper discovers identifiers; the main session writes the file; the user confirms it (in Fast mode it is shown, the run continues, and the user corrects it in parallel).

Rules:

- Every identifier is marked `(verified <date>)` after a query returned data for it, or `(unverified)` when it came from a guess, a doc or memory. Never promote a mark without a query. A log label whose value differs from the service's name stays `(unverified)` until a query ties it to the service (shared pod or host names, or a trace or request ID present in both).
- Identifiers are names, labels, ARNs, UIDs and paths. No tokens, passwords, cookie values or header values. Token variables are named in `environment.md`.
- When logs, metrics and traces use different names for the same service, record each one separately.
- Delete the guidance lines when you copy the file.

Last verified: <date> · Built by: <helper or main session> · Status: <confirmed | partly unverified>

## Identity

| Field | Value |
|---|---|
| Service | <name> |
| Environment | <free text> |
| Account or profile / Region | <profile name from `environment.md`> / <region> |
| Cluster, context and namespace | <for Kubernetes workloads> |
| IaC repo and paths | <repo, directories, and how modules map to this service> |
| Core flows served | <flows from `environment.md` this service is part of, and its criticality> |
| SLO or error-budget source | <where it lives, or "none"> |

## Sibling set

The parallel deployments of this service that a run compares before digging into one of them: regions, shards, tenants, availability zones or replicas.

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| <regions, shards, tenants, AZs or replicas> | <name> | <identifier> |

## Client identity (for WAF triangulation)

Used by `playbooks/waf.md` to tell a shared egress from rotating clients and bots.

| Field | Value |
|---|---|
| Session cookie name | <name only, never a value, or "none"> |
| Client-ID header name | <name only, never a value, or "none"> |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | <label and value, or group name> | (verified <date>) or (unverified) |
| Sidecar or proxy logs | <label or group> | <…> |
| APM or trace service name | <exact, case-sensitive> and its environments | <…> |
| Prometheus job and labels | <job, key labels> | <…> |
| Business or flow counters | <datasource UID, metric, key labels> | <…> |
| Compute | <ECS cluster and services, or namespace, workload, HPA, ConfigMaps> | <…> |
| Load balancing | <load balancers and target groups, or ingresses and services> | <…> |
| Data stores | <RDS or Aurora clusters, caches> | <…> |
| Queues and streams | <names> | <…> |
| Functions | <names> | <…> |
| Log datasource | <UID or CloudWatch profile> | <…> |
| Error tracker project | <organisation and project> | <…> |
| Code | <owner>/<repo>, default branch. Image tag to ref rule: <for example tag is the commit SHA, or `v<semver>`>. Local clone paths live in `environment.md`, not here. | <…> |
| Tickets and wiki | <project key, pages for runbook, design, past incidents> | <…> |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| <upstream or downstream> | <name> | <how it is called> | <identifier> | <link or route, if a third party> |

A third party in the path means the impact block says who to ask and through which route. The run cannot contact vendors.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| <name> | <id> | <panel names> |

## Baseline notes

- Normal load and latency: <request rate, p95, from which window>
- Known periodic jobs and their usual effect: <job, schedule with its zone, expected effect>
- Known benign noise: <message or alarm, with its normal rate>

## Stale identifiers

Identifiers that returned no data on a later run. They stay here until corrected or removed.

| Identifier | Last empty run | Note |
|---|---|---|
| <identifier> | <run directory name> | <what was tried, what replaced it> |
