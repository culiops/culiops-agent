# Examples: GCP CLI Templates for `service-discovery`

Reference command templates for the `service-discovery` skill when the discovered stack is Google Cloud. The skill reads this file when Step 1 detects GCP resources (resource types prefixed with `google_`, `Microsoft.App` absent, `aws_` absent; or `gcloud` tooling in the repo).

Replace placeholders (`{service}`, `{cluster}`, `{function}`, etc.) with the values resolved in Step 2.

## Prerequisites

**CLI tools:** Google Cloud SDK (`gcloud --version` ≥ 450) plus `kubectl` for the GKE sections. For BigQuery queries, `bq` ships with the Cloud SDK.

**Authentication:** any of — `gcloud auth login` (user credentials), `gcloud auth activate-service-account --key-file=<path>` (service-account key file), `GOOGLE_APPLICATION_CREDENTIALS` env var pointing at a key file (Application Default Credentials), or the attached service account when running on GCE / GKE / Cloud Run / Cloud Functions. Confirm active context before running anything: `gcloud config list` and `gcloud auth list`.

**Least-privilege IAM — every command below is read-only.** Grant the operator either:

- **Baseline (simplest):** `roles/viewer` at the project scope. Broad read-only but covers everything here.
- **Tighter (recommended):** combine baseline monitoring and logging viewer roles with per-service viewer roles — add only those the catalog actually references:
  - `roles/monitoring.viewer` — required for all `gcloud monitoring time-series list` calls.
  - `roles/logging.viewer` — required for all `gcloud logging read` calls.
  - `roles/run.viewer`, `roles/container.viewer` (GKE), `roles/compute.viewer` (GCE / Cloud Load Balancing), `roles/cloudsql.viewer`, `roles/redis.viewer`, `roles/cloudfunctions.viewer`, `roles/pubsub.viewer`, `roles/cloudtasks.viewer`, `roles/dataflow.viewer`, `roles/bigquery.dataViewer`, `roles/storage.objectViewer` (scoped to specific buckets).
- **Never use `roles/editor`, `roles/owner`, or any `*Admin` role** for read-only investigation.

**Mutations are flagged inline.** Most commands here are read-only. A few change state (e.g., `gcloud compute url-maps invalidate-cdn-cache` for CDN invalidation, anything in the form `gcloud * create|update|delete|restart|drain`). Mutations are labeled explicitly where they appear. **Never run a mutation without explicit team approval and an elevated role.**

**Cost awareness:** Cloud Monitoring `time-series list` and Cloud Logging `read` incur small per-call and per-GB-scanned charges. Prefer narrow time windows and log filters. BigQuery `query` charges apply to the `bq` calls.

---

## How to use this file

Each section maps one GCP resource category to status/config + the four golden signals (latency / traffic / errors / saturation) where applicable. These are the CLI realization of the investigation-tree steps in the generic runbook.

Most metrics are queried via Cloud Monitoring (`gcloud monitoring`) or the legacy `gcloud logging` CLI. For richer metric filtering, prefer Cloud Monitoring Query Language (MQL) via the Cloud Console or the `monitoring` API.

---

## Cloud Run

- Service status: `gcloud run services describe {service} --region {region}`
- Recent revisions: `gcloud run revisions list --service {service} --region {region} --limit 10`
- Current traffic split: `gcloud run services describe {service} --region {region} --format='value(status.traffic)'`
- Latency / request count / error count: use Cloud Monitoring metric `run.googleapis.com/request_latencies`, `run.googleapis.com/request_count`
  - `gcloud monitoring time-series list --filter='metric.type="run.googleapis.com/request_latencies" AND resource.labels.service_name="{service}"' --interval="start-time={T-1h},end-time={now}"`
- CPU / memory: `run.googleapis.com/container/cpu/utilizations`, `run.googleapis.com/container/memory/utilizations`

## GKE (Google Kubernetes Engine)

- Cluster status: `gcloud container clusters describe {cluster} --region {region}`
- Node pools: `gcloud container node-pools list --cluster {cluster} --region {region}`
- Workloads (generic kubectl): `kubectl get deploy -n {namespace}` / `kubectl describe deploy/{deploy} -n {namespace}`
- Pod status: `kubectl get pods -n {namespace} -l app={service}`
- CPU / memory per pod: `kubectl top pods -n {namespace}`
- Cluster events (recent): `kubectl get events -n {namespace} --sort-by='.lastTimestamp' | tail -30`

## GCE (Compute Engine) + Managed Instance Groups

- Instance group status: `gcloud compute instance-groups managed describe {mig} --region {region}`
- Instances in group: `gcloud compute instance-groups managed list-instances {mig} --region {region}`
- Autoscaler config: `gcloud compute instance-groups managed describe {mig} --region {region} --format='value(autoscaler)'`
- Instance CPU: metric `compute.googleapis.com/instance/cpu/utilization`

## Cloud Load Balancing

- Backend service status: `gcloud compute backend-services describe {backend-service} --global` (or `--region {region}` for regional)
- Backend health: `gcloud compute backend-services get-health {backend-service} --global`
- Forwarding rules: `gcloud compute forwarding-rules list --filter='target:{backend-service}'`
- Request count: metric `loadbalancing.googleapis.com/https/request_count`
- Request latency: metric `loadbalancing.googleapis.com/https/total_latencies` (extended p50/p99)
- Backend latency: metric `loadbalancing.googleapis.com/https/backend_latencies`
- 5xx count: filter request_count by `response_code_class=500`

## Cloud SQL (PostgreSQL / MySQL)

- Instance status: `gcloud sql instances describe {instance}`
- Recent operations: `gcloud sql operations list --instance {instance} --limit 10`
- CPU: metric `cloudsql.googleapis.com/database/cpu/utilization`
- Connections: `cloudsql.googleapis.com/database/postgresql/num_backends` (Postgres) / `cloudsql.googleapis.com/database/mysql/threads_connected` (MySQL)
- Disk utilization: `cloudsql.googleapis.com/database/disk/utilization`
- Replica lag: `cloudsql.googleapis.com/database/replication/replica_lag`

## Memorystore (Redis / Memcached)

- Instance status: `gcloud redis instances describe {instance} --region {region}`
- CPU: metric `redis.googleapis.com/stats/cpu_utilization`
- Memory usage: `redis.googleapis.com/stats/memory/usage_ratio`
- Evictions: `redis.googleapis.com/stats/evicted_keys`
- Cache hit ratio: `redis.googleapis.com/stats/keyspace_hits` vs. `keyspace_misses`

## Cloud Functions (2nd gen) / Cloud Run Functions

- Function config: `gcloud functions describe {function} --region {region} --gen2`
- Errors: metric `cloudfunctions.googleapis.com/function/execution_count` filtered by `status="error"`
- Duration: `cloudfunctions.googleapis.com/function/execution_times` (extended p50/p99)
- Invocations: `cloudfunctions.googleapis.com/function/execution_count` summed
- Recent logs: `gcloud functions logs read {function} --region {region} --gen2 --limit 100`

## Pub/Sub

- Topic config: `gcloud pubsub topics describe {topic}`
- Subscription config: `gcloud pubsub subscriptions describe {subscription}`
- Publish request count: metric `pubsub.googleapis.com/topic/send_message_operation_count`
- Subscription backlog: `pubsub.googleapis.com/subscription/num_undelivered_messages`
- Oldest unacked message age: `pubsub.googleapis.com/subscription/oldest_unacked_message_age`
- DLQ (dead-letter) policy: visible in subscription describe

## Cloud CDN

- Backend service CDN config: `gcloud compute backend-services describe {backend} --global --format='value(cdnPolicy)'`
- Cache hit ratio: metric `loadbalancing.googleapis.com/https/backend_request_count` with `cache_result=HIT` vs. `MISS`
- Request count: `loadbalancing.googleapis.com/https/request_count` at the LB level
- Invalidations: `gcloud compute url-maps invalidate-cdn-cache {url-map} --path '{path}'` (requires explicit human approval before running — this is a mutation)

## Cloud Armor

- Security policy: `gcloud compute security-policies describe {policy}`
- Rules: `gcloud compute security-policies rules list --security-policy {policy}`
- Request evaluation counts: metric `networksecurity.googleapis.com/https/request_count` filtered by `matched_rule`

## Cloud Storage (GCS)

- Bucket details: `gcloud storage buckets describe gs://{bucket}`
- Object count (approximate): metric `storage.googleapis.com/storage/object_count`
- Bucket size: `storage.googleapis.com/storage/total_bytes`

## Firestore / Datastore

- Database status: `gcloud firestore databases describe --database='{database}'`
- Read / write request count: metric `firestore.googleapis.com/api/request_count`
- API latency: `firestore.googleapis.com/api/request_latencies`

## BigQuery

- Dataset metadata: `bq show --dataset {project}:{dataset}`
- Query history: `bq ls -j --max_results 50 --project_id {project}`
- Slot utilization: metric `bigquery.googleapis.com/slots/allocated_for_project`
- Query errors: filter slot metric by `job_type` and correlate with failed jobs

## Dataflow

- Job status: `gcloud dataflow jobs describe {job-id} --region {region}`
- Running jobs: `gcloud dataflow jobs list --region {region} --status active`
- System lag: metric `dataflow.googleapis.com/job/system_lag`
- Data watermark lag: `dataflow.googleapis.com/job/data_watermark_age`

## Cloud Tasks

- Queue status: `gcloud tasks queues describe {queue} --location {region}`
- Task count: `gcloud tasks list --queue {queue} --location {region} --limit 50`
- Dispatched / completed: metrics `cloudtasks.googleapis.com/queue/task_attempt_count`

## Cloud Logging (filter-log queries)

- Last 15 minutes of errors for a service: `gcloud logging read 'resource.type="{resource-type}" AND resource.labels.service_name="{service}" AND severity>=ERROR AND timestamp>="{T-15m}"' --limit 100 --format json`
- Recent logs for a Cloud Run revision: `gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}"' --limit 100 --freshness 15m`

## Third-party services on GCP

Same as the AWS counterpart — ask the human where logs and metrics live for any vendor tool (APM, bot defender, feature flags). Many GCP-native integrations route logs to Cloud Logging; non-native ones typically use the vendor's own dashboard.

## Placeholder reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{service}`, `{cluster}`, `{function}`, `{instance}`, `{topic}`, `{subscription}`, `{bucket}`, `{table}`, `{job-id}`, `{queue}` | Resource identifiers | `widgetapi-prod-eu-web` |
| `{region}` | GCP region | `europe-west1` |
| `{project}` | GCP project ID | `widgetapi-prod` |
| `{namespace}` | Kubernetes namespace | `widgetapi` |
| `{T-1h}`, `{T-15m}`, `{T-1d}` | ISO-8601 time offsets | `2026-04-15T09:00:00Z` |
| `{now}` | Current time, ISO 8601 | `2026-04-15T10:00:00Z` |
