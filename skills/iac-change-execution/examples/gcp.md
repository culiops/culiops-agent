# Examples: GCP CLI Templates for `iac-change-execution`

Reference command templates for the `iac-change-execution` skill when the target infrastructure is GCP. The skill reads this file during Step 1 (Research gap-filling), Step 4c (Apply), and Step 5a (Verification).

Replace placeholders (`{cluster}`, `{service}`, `{project}`, `{region}`, `{zone}`, `{stack}`, etc.) with the values resolved in Step 1 research or detected from the plan output.

## Prerequisites

**CLI tool:** `gcloud` CLI (Google Cloud SDK). Verify: `gcloud --version`.

**Authentication:** `gcloud auth login` for interactive sessions, or `gcloud auth activate-service-account --key-file={key.json}` for service accounts. Confirm active identity: `gcloud auth list` and `gcloud config list account`.

**Project:** Set the active project before running commands: `gcloud config set project {project}`. Alternatively, pass `--project {project}` to every command.

**Least-privilege IAM — TWO tiers are required for this skill.**

- **Tier 1 (Steps 1 and 5 — read-only):** `roles/viewer` on the project, or a custom role scoped to `*.get`, `*.list`, `*.describe` verbs on the relevant resource types. Never use `roles/editor` or `roles/owner` for read-only operations.
- **Tier 2 (Step 4 — mutation only):** the minimum scoped role that permits the specific mutation — e.g., `roles/run.admin` on the target Cloud Run service, or `roles/cloudsql.editor` on the target instance. Elevated permissions must be assumed immediately before the mutation and dropped after.

**Cost awareness:** Cloud Monitoring `timeSeries.list` calls are billed per metric read. Prefer checking the Cloud Console for quick spot checks; use CLI for scripted verification.

---

## Research Queries (Step 1 — Read-Only)

### GKE — current cluster state

- Cluster details: `gcloud container clusters describe {cluster} --region {region} --project {project}`
- Node pool status: `gcloud container node-pools list --cluster {cluster} --region {region} --project {project}`
- Node pool details: `gcloud container node-pools describe {node-pool} --cluster {cluster} --region {region} --project {project}`
- Cluster version: `gcloud container clusters describe {cluster} --region {region} --format 'value(currentMasterVersion,currentNodeVersion)' --project {project}`

### Cloud Run — current service state

- Service details: `gcloud run services describe {service} --region {region} --project {project}`
- Traffic split: `gcloud run services describe {service} --region {region} --format 'value(spec.traffic)' --project {project}`
- Current revisions: `gcloud run revisions list --service {service} --region {region} --project {project}`
- Current image: `gcloud run services describe {service} --region {region} --format 'value(spec.template.spec.containers[0].image)' --project {project}`

### Cloud SQL — current instance state

- Instance details: `gcloud sql instances describe {instance} --project {project}`
- Database flags: `gcloud sql instances describe {instance} --format 'value(settings.databaseFlags)' --project {project}`
- Maintenance window: `gcloud sql instances describe {instance} --format 'value(settings.maintenanceWindow)' --project {project}`
- Backups: `gcloud sql backups list --instance {instance} --project {project}`

### Compute Engine — current instance state

- Instance details: `gcloud compute instances describe {instance} --zone {zone} --project {project}`
- Machine type: `gcloud compute instances describe {instance} --zone {zone} --format 'value(machineType)' --project {project}`
- Instance status: `gcloud compute instances describe {instance} --zone {zone} --format 'value(status)' --project {project}`
- Attached disks: `gcloud compute instances describe {instance} --zone {zone} --format 'value(disks)' --project {project}`

### Cloud Functions — current function state

- Function details: `gcloud functions describe {function} --region {region} --project {project}`
- Function state: `gcloud functions describe {function} --region {region} --format 'value(state,runtime,availableMemoryMb,timeout)' --project {project}`

### Firewall rules — current network config

- List rules for network: `gcloud compute firewall-rules list --filter 'network:{network}' --project {project}`
- Specific rule details: `gcloud compute firewall-rules describe {rule-name} --project {project}`

### IAM policy — current bindings (names only)

- Project IAM policy: `gcloud projects get-iam-policy {project} --format 'table(bindings.role,bindings.members)'`
- Service account roles: `gcloud projects get-iam-policy {project} --filter 'bindings.members:{sa-email}' --format 'value(bindings.role)'`

---

## Verification Checks (Step 5 — Read-Only)

### GKE — post-apply cluster health

- Cluster status (expect `RUNNING`): `gcloud container clusters describe {cluster} --region {region} --format 'value(status)' --project {project}`
- Node pool status (expect `RUNNING`): `gcloud container node-pools describe {node-pool} --cluster {cluster} --region {region} --format 'value(status)' --project {project}`
- Workload status (kubectl): `kubectl get deploy -n {namespace} -o wide` (requires `gcloud container clusters get-credentials {cluster} --region {region}`)
- Pod readiness: `kubectl get pods -n {namespace} -l app={service}`

### Cloud Run — post-apply service health

- Service condition (expect `Ready=True`): `gcloud run services describe {service} --region {region} --format 'value(status.conditions)' --project {project}`
- Latest revision ready: `gcloud run revisions list --service {service} --region {region} --format 'table(name,status.conditions[0].status)' --project {project}`
- Traffic split (confirm expected distribution): `gcloud run services describe {service} --region {region} --format 'value(status.traffic)' --project {project}`

### Cloud SQL — post-apply instance state

- Instance state (expect `RUNNABLE`): `gcloud sql instances describe {instance} --format 'value(state)' --project {project}`
- Pending operations (expect empty): `gcloud sql operations list --instance {instance} --filter 'status!=DONE' --project {project}`

### Cloud Monitoring — alerting policy state

- List alerting policies: `gcloud alpha monitoring policies list --project {project}`
- Specific policy details: `gcloud alpha monitoring policies describe {policy-id} --project {project}`

---

## Apply Commands (Step 4c — MUTATION)

Each command below changes cloud state. The skill presents each command to the operator and waits for explicit approval before running. Assume Tier 2 elevated IAM permissions are active.

### Terraform

**MUTATION** — `terraform apply tfplan`
- Blast radius: all resources in the plan output; varies by change. Review plan output before approving.
- Elevated permission required: scoped IAM role with create/update/delete rights on the specific GCP resource types in the plan (e.g., `roles/run.admin` for Cloud Run, `roles/container.admin` for GKE). Never use `roles/owner` for apply.
- Rollback path: `terraform apply` from the previous state file snapshot, or manual revert per resource; no automated rollback.
- Note: `tfplan` is the binary produced by `terraform plan -out=tfplan`. Never run `terraform apply` without the plan file.

### Pulumi

**MUTATION** — `pulumi up --yes --stack {stack}`
- Blast radius: all resources shown in `pulumi preview` for the stack; varies by change. Always run `pulumi preview` and review output before approving the apply.
- Elevated permission required: scoped IAM role matching the resource types the stack manages. Pass credentials via `GOOGLE_CREDENTIALS` or an active `gcloud auth application-default login` session.
- Rollback path: `pulumi destroy --yes --stack {stack}` for a complete teardown, or revert the Pulumi program to its previous state and run `pulumi up --yes --stack {stack}` to restore.
- Note: omit `--yes` to run interactively if the operator prefers to confirm each resource change.

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{cluster}`, `{service}`, `{function}`, `{instance}` | Resource identifiers | `widgetapi-prod-eu` |
| `{node-pool}` | GKE node pool name | `default-pool` |
| `{project}` | GCP project ID | `widgetapi-prod` |
| `{region}` | GCP region | `europe-west1` |
| `{zone}` | GCP zone | `europe-west1-b` |
| `{network}` | VPC network name | `widgetapi-vpc` |
| `{rule-name}` | Firewall rule name | `allow-internal` |
| `{sa-email}` | Service account email | `svc-widgetapi@widgetapi-prod.iam.gserviceaccount.com` |
| `{policy-id}` | Cloud Monitoring policy ID | `1234567890` |
| `{stack}` | Pulumi stack name | `widgetapi-prod` |
| `{namespace}` | Kubernetes namespace | `production` |
