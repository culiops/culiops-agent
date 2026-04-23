# Examples: GCP CLI Templates for `pre-flight`

Reference command templates for the `pre-flight` skill's L3 (live signals) layer when the target infrastructure is GCP.

Replace placeholders (`{project}`, `{cluster}`, `{service}`, `{region}`, `{zone}`, etc.) with values from the IaC plan or L1 analysis.

## Prerequisites

**CLI tool:** `gcloud` CLI (`gcloud --version`). Install components as needed: `gcloud components install kubectl`.

**Authentication:** `gcloud auth login` or service account key. Confirm identity: `gcloud auth list`.

**Least-privilege IAM — every command below is read-only.** Grant the operator:
- **Baseline:** `roles/viewer` on the project
- **Tighter:** `roles/monitoring.viewer`, `roles/logging.viewer`, `roles/container.viewer`, `roles/cloudsql.viewer` as applicable

**Never use `roles/editor` or `roles/owner`** for pre-flight read-only checks.

**Cost awareness:** Cloud Monitoring API and Cloud Logging API queries incur charges based on volume.

---

## Resource Health Checks

### GKE (Google Kubernetes Engine)

- Cluster status: `gcloud container clusters describe {cluster} --zone {zone} --project {project} --format='value(status)'`
- Node pool status: `gcloud container node-pools list --cluster {cluster} --zone {zone} --project {project} --format='table(name,status,config.machineType,autoscaling.enabled)'`

### Cloud SQL

- Instance status: `gcloud sql instances describe {instance} --project {project} --format='value(state)'`
- CPU utilization: `gcloud monitoring read "metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\" AND resource.label.database_id=\"{project}:{instance}\"" --interval-start-time={T-1h} --project {project}`
- Disk utilization: `gcloud monitoring read "metric.type=\"cloudsql.googleapis.com/database/disk/utilization\" AND resource.label.database_id=\"{project}:{instance}\"" --interval-start-time={T-1h} --project {project}`
- Connection count: `gcloud monitoring read "metric.type=\"cloudsql.googleapis.com/database/network/connections\" AND resource.label.database_id=\"{project}:{instance}\"" --interval-start-time={T-1h} --project {project}`

### Cloud Run

- Service status: `gcloud run services describe {service} --region {region} --project {project} --format='value(status.conditions)'`
- Request count: `gcloud monitoring read "metric.type=\"run.googleapis.com/request_count\" AND resource.label.service_name=\"{service}\"" --interval-start-time={T-1h} --project {project}`
- Request latency: `gcloud monitoring read "metric.type=\"run.googleapis.com/request_latencies\" AND resource.label.service_name=\"{service}\"" --interval-start-time={T-1h} --project {project}`

### Compute Engine

- Instance status: `gcloud compute instances describe {instance} --zone {zone} --project {project} --format='value(status)'`
- CPU utilization: `gcloud monitoring read "metric.type=\"compute.googleapis.com/instance/cpu/utilization\" AND resource.label.instance_id=\"{instance-id}\"" --interval-start-time={T-1h} --project {project}`

### Cloud Functions

- Error count: `gcloud monitoring read "metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" AND metric.label.status!=\"ok\" AND resource.label.function_name=\"{function}\"" --interval-start-time={T-1h} --project {project}`

---

## Observability Checks

### Cloud Monitoring Alerts

- List alert policies: `gcloud alpha monitoring policies list --project {project} --filter="displayName:{service}" --format='table(displayName,enabled,conditions.displayName)'`
- Currently firing incidents: `gcloud alpha monitoring incidents list --project {project} --filter="state=OPEN"`

---

## Timing Context Checks

### Recent Deployments

- Cloud Run revisions: `gcloud run revisions list --service {service} --region {region} --project {project} --limit=5 --format='table(name,creationTimestamp,status)'`
- GKE workload rollout: `kubectl rollout history deployment/{deploy} -n {namespace}`
