# GCP — cloud-cost-investigate examples

Read-only commands per workflow step. All commands are `list` / `describe` / `get-*` / `SELECT` only — no mutations, no `create`, `delete`, `update`, `set-*`, `add-*`, `remove-*`, `enable-*`, or `disable-*`.

## Step 1 — Detect & Scope: cloud detection

```bash
# Detect current account, project, and region
gcloud config list account project

# List configured credentials (verify which identity is active)
gcloud auth list

# List projects the current principal can read
gcloud projects list
```

**IAM:** Any authenticated principal. `resourcemanager.projects.list` for `gcloud projects list`.
**API cost:** none.

## Step 2A — Anomaly mode

### Cost time series via BigQuery billing export

GCP cost analysis without billing export is severely limited. The Cloud Billing API's cost reporting surface is primarily a GUI (Cloud Console Billing Reports). For CLI-based cost time-series, the skill uses BigQuery billing export. At the start of an investigation the skill checks whether billing export is configured and flags the gap if not.

```bash
# Confirm that a billing export dataset exists
bq ls --project_id=<project> --format=json
```

```sql
-- Daily spend by service, last 30 days (bq query --use_legacy_sql=false)
SELECT DATE(usage_start_time) AS usage_date, service.description AS service,
       SUM(cost) AS total_cost, currency
FROM `<project>.<dataset>.gcp_billing_export_v1_<BILLING_ACCOUNT_ID>`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY 1, 2, 4 ORDER BY 1, 3 DESC;
```

**IAM:** `roles/billing.viewer` on the billing account; `roles/bigquery.dataViewer` on the export dataset.
**API cost:** BigQuery charges per byte scanned (~$5/TB on-demand). The skill MUST surface estimated bytes scanned in the query plan before running.

### Period comparison (anomalous window vs. baseline)

```sql
-- Compare current period to same-length prior period
SELECT service.description AS service,
  SUM(IF(DATE(usage_start_time) >= '<current_start>', cost, 0)) AS current_cost,
  SUM(IF(DATE(usage_start_time) <  '<current_start>', cost, 0)) AS prior_cost,
  SUM(IF(DATE(usage_start_time) >= '<current_start>', cost, 0))
    - SUM(IF(DATE(usage_start_time) <  '<current_start>', cost, 0)) AS delta
FROM `<project>.<dataset>.gcp_billing_export_v1_<BILLING_ACCOUNT_ID>`
WHERE DATE(usage_start_time) BETWEEN '<prior_start>' AND '<current_end>'
GROUP BY 1 ORDER BY 4 DESC;
```

**IAM:** `roles/bigquery.dataViewer` on the export dataset.
**API cost:** BigQuery per-byte-scanned (~$5/TB); surface bytes estimate in query plan.

### New resources in an anomalous window

```bash
# Compute instances launched within window
gcloud compute instances list \
  --filter='creationTimestamp>"<start-iso>"' \
  --format='table(name,machineType.basename(),zone.basename(),creationTimestamp)'

# Cloud SQL instances and GKE clusters
gcloud sql instances list --format='value(name,databaseVersion,region,createTime)'
gcloud container clusters list --format='table(name,location,currentNodeCount,createTime)'
```

**IAM:** `roles/compute.viewer`, `roles/cloudsql.viewer`, `roles/container.clusterViewer`.
**API cost:** none.

## Step 2B — Waste mode

### Recommender — rightsizing and idle resources

```bash
# Rightsizing recommendations (machine type changes)
gcloud recommender recommendations list \
  --project=<project> --location=<zone-or-region> \
  --recommender=google.compute.instance.MachineTypeRecommender --format=json

# Idle VM instances
gcloud recommender recommendations list \
  --project=<project> --location=<zone> \
  --recommender=google.compute.instance.IdleResourceRecommender --format=json

# Unattached persistent disks
gcloud recommender recommendations list \
  --project=<project> --location=<zone> \
  --recommender=google.compute.disk.IdleResourceRecommender --format=json

# Idle static IP addresses
gcloud recommender recommendations list \
  --project=<project> --location=<region> \
  --recommender=google.compute.address.IdleResourceRecommender --format=json
```

**IAM:** `roles/recommender.viewer` on the project.
**API cost:** none.

### Resource-state sweeps

```bash
# Unattached persistent disks (no instance using the disk)
gcloud compute disks list --filter='users:""' \
  --format='table(name,sizeGb,type.basename(),zone.basename(),creationTimestamp)'

# Snapshots older than 30 days
gcloud compute snapshots list --filter='creationTimestamp<"-P30D"' \
  --format='table(name,diskSizeGb,storageBytes,creationTimestamp,sourceDisk)'

# Unused static external IP addresses (not attached to any resource)
gcloud compute addresses list --filter='status=RESERVED' \
  --format='table(name,region.basename(),address,status)'

# Load balancers (forwarding rules) — operator confirms traffic via Monitoring below
gcloud compute forwarding-rules list --format='table(name,region.basename(),IPAddress,target)'

# Cloud Storage buckets without lifecycle policies
gcloud storage buckets list --format='value(name,lifecycle_config)'
# Buckets with empty lifecycle_config are flagged; drill with:
# gcloud storage buckets describe gs://<name> --format=json
```

**IAM:** `roles/compute.viewer`, `roles/storage.objectViewer` (or `roles/storage.admin` in read mode) for bucket metadata.
**API cost:** none.

### Optional — utilization metrics via Cloud Monitoring

```bash
# Last 30 days average CPU for a specific instance (MQL)
gcloud monitoring query --project=<project> --query='
  fetch gce_instance
  | metric "compute.googleapis.com/instance/cpu/utilization"
  | filter resource.instance_id == "<instance-id>"
  | within 30d | every 1d | mean'
```

**IAM:** `roles/monitoring.viewer`.
**API cost:** Cloud Monitoring standard metrics reads are no-charge at typical investigative query volumes.

## Step 2C — Attribution mode

### Cost filtered by label (with billing export)

```sql
-- Cost by team label, monthly, last 3 months
SELECT invoice.month,
  (SELECT value FROM UNNEST(labels) WHERE key = 'team') AS team_label,
  SUM(cost) AS total_cost, currency
FROM `<project>.<dataset>.gcp_billing_export_v1_<BILLING_ACCOUNT_ID>`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY 1, 2, 4 ORDER BY 1, 3 DESC;
```

```sql
-- Drill into one label value by service
SELECT service.description AS service, sku.description AS sku, SUM(cost) AS total_cost
FROM `<project>.<dataset>.gcp_billing_export_v1_<BILLING_ACCOUNT_ID>`
WHERE DATE(usage_start_time) BETWEEN '<start>' AND '<end>'
  AND EXISTS (SELECT 1 FROM UNNEST(labels) WHERE key = 'service' AND value = '<service-name>')
GROUP BY 1, 2 ORDER BY 3 DESC;
```

**IAM:** `roles/billing.viewer`; `roles/bigquery.dataViewer` on the export dataset.
**API cost:** BigQuery per-byte-scanned (~$5/TB). Surface bytes estimate before running.

### Attribution gap — billing export not configured

If billing export is not configured the skill cannot perform cost attribution by label or project breakdown via CLI. The skill MUST flag this gap, stop attribution analysis, and tell the operator to:

```bash
# Check whether a billing account has an export configured (read-only)
gcloud billing accounts get-billing-info --project=<project>
# Returns the linked billing account ID; operator then checks the Cloud Console
# Billing > Billing export to confirm BigQuery export is enabled.
```

**IAM:** `roles/billing.viewer`.
**API cost:** none.

## Step 5 — Verification (shared)

No mutation occurs, so verification is just re-reading the report file before commit:

```bash
# Operator inspects the report draft
cat .culiops/cloud-cost-investigate/<scope-slug>-<mode>-<YYYYMMDD-HHmm>.md
```

## Iron Law reminders

- These commands are read-only by name. The skill MUST refuse if the operator asks for any `create`, `delete`, `update`, `set-iam-policy`, `add-iam-policy-binding`, `remove-iam-policy-binding`, `enable`, or `disable` API call.
- BigQuery billing export is the primary cost data path for GCP. Without it, anomaly and attribution modes are severely limited. The skill MUST surface this gap at the start of any investigation where billing export is absent, and MUST surface the estimated bytes scanned (and approximate dollar cost at ~$5/TB) before executing any BigQuery query.
- GCP Recommender API requires the Recommender to be enabled per project. If `gcloud recommender recommendations list` returns a permission-denied or API-not-enabled error, the skill stops and tells the operator to enable the Recommender API (`recommender.googleapis.com`) — that is an operator action, not a skill action.
