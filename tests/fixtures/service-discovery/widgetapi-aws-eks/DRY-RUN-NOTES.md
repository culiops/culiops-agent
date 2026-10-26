# Dry-run of `service-discovery` against `widgetapi-aws-eks`

Simulated run of the IaC path against this fixture. First recorded 2026-04-15; re-run 2026-10-26 for secrets-by-projection, the Secrets Store CSI template and Step 2V (live cross-check). Instance: `prod`.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| IaC tool detection (multi-tool) | Terraform (`*.tf`) + Helm (`Chart.yaml`, `templates/*.yaml`, `values*.yaml`) in one repo |
| Stack boundaries | 3 stacks (`infra/`, `platform/`, `helm/widgetapi/`); platform references infra via `terraform_remote_state` — recorded as dependency, not chased |
| Parameter resolution | `envs/<env>.tfvars` for TF; `values-<env>.yaml` for Helm; prod vs staging |
| Multi-instance | Two envs — skill prompts "which instance?" |
| Cloud × Kubernetes orthogonality | Runbook needs both `examples/aws.md` (EKS control plane, ALB, RDS, ElastiCache, S3, SQS, CloudFront, Secrets Manager) and `examples/kubernetes.md` (Deployment, Service, Ingress, HPA, PDB, Helm release) |
| Registry modules | `module.vpc`, `module.eks`, `module.widgetapi_irsa` (`terraform-aws-modules/*`) recorded as remote modules by source + version (`~> 5.8`, `~> 20.8`, `~> 5.39`); not fetched, their internal resources (subnets, NAT, node group, IAM role internals) are not enumerated |
| Secrets by projection | `templates/secretproviderclass.yaml` (`provider: aws`, gated by `secretsStore.enabled`): catalog records secret **name** `widgetapi/prod/db`, objects/aliases `db_username`/`db_password`, synced Kubernetes Secret `widgetapi-db` with keys `DB_USERNAME`, `DB_PASSWORD`. Never fetched (`secretsmanager get-secret-value` is never run). See "Secrets handling" |
| Third-party SaaS vs README | Datadog and PagerDuty are in Helm values and `docs/oncall.md`; Stripe, SendGrid, LaunchDarkly are only in `docs/oncall.md` (README now says so). All five are "ask the team" entries; the doc-only three are doc claims |
| Doc-declared SLO | `docs/oncall.md:22` declares 99.9% over 30 days (monitor `widgetapi-prod-slo-burn`). Surfaced as a doc claim (`source=doc`, Medium at most), to be verified; not "no SLO declared" |
| Naming patterns | `widgetapi-${env}-<component>` detected consistently across all TF resources |
| Conditional resources | RDS `deletion_protection` on env==prod; CloudFront `price_class` on env==prod; cache `automatic_failover_enabled` on num_nodes>1; Helm `web.autoscaling.enabled`, `ingress.enabled`, `podDisruptionBudget.enabled`, `secretsStore.enabled` |
| Step 2V live cross-check | Offered at Gate 2, accepted; 29 projected reads; 2 drift rows, 1 not found (below) |

## Secrets handling (what the skill reads and records)

| Source | Recorded | Withheld / never done |
|--------|----------|-----------------------|
| `infra/envs/prod.tfvars`, `platform/envs/prod.tfvars` | all variable names and values (none is secret-shaped) | — |
| `values-prod.yaml` `env:` (`DB_HOST_*`, `DB_NAME`, `DB_USER`, `UPLOADS_BUCKET`, `ASYNC_QUEUE_URL`, `AWS_REGION`) | names and values | — |
| `values-prod.yaml:38` `DB_SECRET_ARN` | the ARN `arn:aws:secretsmanager:eu-west-1:123456789012:secret:rds!db-widgetapi-prod` as a **reference** to the RDS-managed secret | the secret's value (never fetched) |
| `values.yaml` `datadog.datadog.apiKeyExistingSecret` / `appKeyExistingSecret` | reference name `datadog-secret` | key value |
| `values.yaml` `secretEnv.secretName` | Kubernetes Secret reference `widgetapi` (created out-of-band; keys such as `PAGERDUTY_ROUTING_KEY`, `STRIPE_*` known only from `docs/oncall.md`) | any value |
| `secretproviderclass.yaml` | Secrets Manager name `widgetapi/prod/db`; key names `DB_USERNAME`, `DB_PASSWORD`; synced Secret `widgetapi-db` | any value; `kubectl get secret` is never run |
| Terraform state (`s3://widgetapi-tfstate/...`) | backend bucket/key as the cross-stack linkage | state is never read; `terraform output` is never run |

Judgement call: keys like `DB_SECRET_ARN` match the withhold list (`secret`), but the value is an ARN reference to a secret store, which the "record the reference" rule says to keep. The fixture assumes the reference rule wins for ARN/name-shaped values; literal-looking values are withheld as `<set in <file>:<line>>`.

## Findings

### F1 — Helm stack rule was ambiguous about base `values.yaml` *(fixed)*

Old wording: "each `values*.yaml` (or each release) is one instance" — but the fixture's base `values.yaml` is defaults, not an instance. Fixed in `SKILL.md` Step 1 stack-layout bullet to distinguish base defaults from per-env instance files.

### F2 — Terraform stack rule didn't name the `*.tfvars` convention *(fixed)*

Old wording only listed Terraform workspaces and Terragrunt as instance-multiplication mechanisms. The fixture uses `envs/<env>.tfvars` passed via `-var-file`, the most common pattern. Fixed in `SKILL.md` Step 1 stack-layout bullet.

### F3 — Multi-stack cataloging under one env axis *(no change — works as written)*

Three stacks all parameterized by `env`. "Instance = env" is cross-stack-aware under the current wording; the presentation template lists all in-scope stacks together.

### F4 — Inventory table width in chat *(no change — ergonomic)*

29 rows × 9 columns is large for chat but fine in the written doc. The per-stack breakdown below is reproducible from the files.

### F5 — Third-party SaaS classification *(no change — covered by Step 5 §9)*

One line per third-party tool outside `examples/`. The README previously listed only Datadog/PagerDuty while the notes claimed all five were "referenced in Helm values"; corrected: only Datadog/PagerDuty are in Helm values.

### F6 — Declared SLO vs "no SLO declared" *(fixed in this fixture's expectations)*

The earlier notes said nothing declared an SLO. `docs/oncall.md:22` declares availability + latency, target 99.9% over 30 days. Step 4 Anchor now reads: "SLO per `docs/oncall.md:22` (doc claim, unverified): 99.9% / 30d; no latency threshold stated". The only **code**-declared saturation limit remains HPA target CPU 65% (`values-prod.yaml:14`).

## Inventory row count (prod): 29, per stack

Counting rule: one row per Terraform `resource` or registry `module` call, and one row per rendered Helm template object enabled in prod. `data` blocks, `terraform_remote_state`, Helm subchart dependencies and registry-module internals are not rows.

| Stack | Rows | Which |
|-------|------|-------|
| `infra/` | 14 | `module.vpc` (1); `aws_security_group.db`, `.cache` (2); `aws_db_subnet_group.db` (1); `aws_db_instance.primary`, `.replica` (2); `aws_elasticache_subnet_group.cache` (1); `aws_elasticache_replication_group.cache` (1); `aws_s3_bucket.uploads` + `_versioning` + `_server_side_encryption_configuration` + `_public_access_block` (4); `aws_sqs_queue.async`, `.async_dlq` (2) |
| `platform/` | 6 | `module.eks`; `aws_iam_policy.widgetapi_workload`; `module.widgetapi_irsa`; `aws_security_group.alb`; `aws_lb.alb`; `aws_cloudfront_distribution.cdn` |
| `helm/widgetapi/` | 9 | Deployment `widgetapi-web`, Deployment `widgetapi-worker`, ConfigMap `widgetapi-env`, Service, ServiceAccount, Ingress*, HPA*, PDB*, SecretProviderClass* (`*` = conditional; all enabled in prod). Datadog subchart `3.60.1` is a dependency, not a row |
| **Total** | **29** | staging would be 28 (`secretsStore.enabled: false` there, so no SecretProviderClass) |

## Step 2V — live cross-check (accepted at Gate 2)

**Pinned identity (probe batch shown and approved first):**

| Probe | Result |
|-------|--------|
| `aws sts get-caller-identity --profile widgetapi-prod-ro --query Account --output text` | `123456789012` |
| `aws configure get region --profile widgetapi-prod-ro` (STS returns no region) | `eu-west-1` |
| `kubectl --context arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod get ns widgetapi -o name` | `namespace/widgetapi` |

Matches the code (`region = "eu-west-1"`, cluster `widgetapi-prod`). Every call below carries `--profile widgetapi-prod-ro --region …` or `--context …`; identity re-checked before the batch.

**Verification batch (GATE: approved as shown).** Scope: `eu-west-1` unless stated; kube context `arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod`, namespace `widgetapi`. All reads; control-plane/metadata calls are free, S3/SQS requests are billed per request (total well under $0.01).

| # | Row | Call (projected) | Scope | Compared fields | Est. cost |
|---|-----|------------------|-------|-----------------|-----------|
| 1 | `module.vpc` | `aws ec2 describe-vpcs --filters Name=tag:Name,Values=widgetapi-prod-vpc --query 'Vpcs[].{id:VpcId,cidr:CidrBlock}'` | eu-west-1 | cidr | free |
| 2 | `aws_security_group.db` | `aws ec2 describe-security-groups --filters Name=group-name,Values=widgetapi-prod-db-sg --query 'SecurityGroups[].{id:GroupId,ports:IpPermissions[].FromPort}'` | eu-west-1 | ingress port | free |
| 3 | `aws_security_group.cache` | same, `widgetapi-prod-cache-sg` | eu-west-1 | ingress port | free |
| 4 | `aws_db_subnet_group.db` | `aws rds describe-db-subnet-groups --db-subnet-group-name widgetapi-prod-db --query 'DBSubnetGroups[].Subnets[].SubnetIdentifier'` | eu-west-1 | subnet count | free |
| 5 | `aws_db_instance.primary` | `aws rds describe-db-instances --db-instance-identifier widgetapi-prod-db --query 'DBInstances[].{class:DBInstanceClass,engine:EngineVersion,multiAz:MultiAZ,storage:AllocatedStorage,delProt:DeletionProtection}'` | eu-west-1 | class, engine, multi-AZ, storage | free |
| 6 | `aws_db_instance.replica` | same, `widgetapi-prod-db-ro`, fields `{class:DBInstanceClass,source:ReadReplicaSourceDBInstanceIdentifier}` | eu-west-1 | class, source | free |
| 7 | `aws_elasticache_subnet_group.cache` | `aws elasticache describe-cache-subnet-groups --cache-subnet-group-name widgetapi-prod-cache --query 'CacheSubnetGroups[].CacheSubnetGroupName'` | eu-west-1 | exists | free |
| 8 | `aws_elasticache_replication_group.cache` | `aws elasticache describe-replication-groups --replication-group-id widgetapi-prod-cache --query 'ReplicationGroups[].{type:CacheNodeType,nodes:MemberClusters,failover:AutomaticFailover,tls:TransitEncryptionEnabled}'` | eu-west-1 | node type, nodes, failover, TLS | free |
| 9 | `aws_s3_bucket.uploads` | `aws s3api head-bucket --bucket widgetapi-prod-uploads` | eu-west-1 | exists | <$0.001 |
| 10 | `..._versioning` | `aws s3api get-bucket-versioning --bucket widgetapi-prod-uploads --query Status` | eu-west-1 | Enabled | <$0.001 |
| 11 | `..._server_side_encryption_configuration` | `aws s3api get-bucket-encryption --bucket widgetapi-prod-uploads --query 'ServerSideEncryptionConfiguration.Rules[].ApplyServerSideEncryptionByDefault.SSEAlgorithm'` | eu-west-1 | AES256 | <$0.001 |
| 12 | `..._public_access_block` | `aws s3api get-public-access-block --bucket widgetapi-prod-uploads --query PublicAccessBlockConfiguration` | eu-west-1 | four flags | <$0.001 |
| 13 | `aws_sqs_queue.async` | `aws sqs get-queue-attributes --queue-url https://sqs.eu-west-1.amazonaws.com/123456789012/widgetapi-prod-async --attribute-names VisibilityTimeout MessageRetentionPeriod` | eu-west-1 | 120s, 345600s | <$0.001 |
| 14 | `aws_sqs_queue.async_dlq` | same, `widgetapi-prod-async-dlq`, `MessageRetentionPeriod` | eu-west-1 | 1209600s | <$0.001 |
| 15 | `module.eks` | `aws eks describe-cluster --name widgetapi-prod --query 'cluster.{version:version,status:status,publicEndpoint:resourcesVpcConfig.endpointPublicAccess}'` | eu-west-1 | version 1.29, public endpoint | free |
| 16 | `aws_iam_policy.widgetapi_workload` | `aws iam list-policies --scope Local --query "Policies[?PolicyName=='widgetapi-prod-workload'].Arn"` (policy document not fetched) | us-east-1 (IAM is global) | exists | free |
| 17 | `module.widgetapi_irsa` | `aws iam get-role --role-name widgetapi-prod-workload --query Role.Arn` | us-east-1 (global) | ARN equals ServiceAccount annotation | free |
| 18 | `aws_security_group.alb` | `aws ec2 describe-security-groups --filters Name=group-name,Values=widgetapi-prod-alb-sg --query 'SecurityGroups[].{id:GroupId,ports:IpPermissions[].FromPort}'` | eu-west-1 | 80, 443 | free |
| 19 | `aws_lb.alb` | `aws elbv2 describe-load-balancers --names widgetapi-prod-alb --query 'LoadBalancers[].{type:Type,scheme:Scheme}'` | eu-west-1 | application, internet-facing | free |
| 20 | `aws_cloudfront_distribution.cdn` | `aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='widgetapi-prod CDN'].{id:Id,price:PriceClass,enabled:Enabled}"` | us-east-1 (global service) | PriceClass_All, enabled | free |
| 21 | Deployment `widgetapi-web` | `kubectl --context <ctx> -n widgetapi get deploy widgetapi-web -o jsonpath='{.spec.template.spec.containers[0].image}'` | ctx | image tag 2026.04.1 | free |
| 22 | Deployment `widgetapi-worker` | `... get deploy widgetapi-worker -o jsonpath='{.spec.replicas}'` | ctx | replicas 3 | free |
| 23 | ConfigMap `widgetapi-env` | `... get cm widgetapi-env -o go-template='{{range $k,$v := .data}}{{$k}} {{end}}'` (key names only) | ctx | key set | free |
| 24 | Service `widgetapi` | `... get svc widgetapi -o jsonpath='{.spec.ports[0].port}'` | ctx | 80 | free |
| 25 | ServiceAccount `widgetapi` | `... get sa widgetapi -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'` | ctx | role ARN | free |
| 26 | Ingress `widgetapi` | `... get ingress widgetapi -o jsonpath='{.spec.rules[0].host}'` | ctx | api.widgetapi.example.com | free |
| 27 | HPA `widgetapi-web` | `... get hpa widgetapi-web -o jsonpath='{.spec.minReplicas} {.spec.maxReplicas}'` | ctx | 4, 20 | free |
| 28 | PDB `widgetapi-web` | `... get pdb widgetapi-web -o jsonpath='{.spec.minAvailable}'` | ctx | 1 | free |
| 29 | SecretProviderClass `widgetapi-db` | `... get secretproviderclass widgetapi-db -o jsonpath='{.spec.provider}'` | ctx | `aws` | free |

No `kubectl get secret`, no `-o json|yaml`, no `get-secret-value`, no `describe-db-instances` without `--query`.

**Results:** 26 `✓ matches`, 2 drift, 1 not found, 0 not checked.

| # | Row | Live | Detail |
|---|-----|------|--------|
| 5 | `aws_db_instance.primary` | `drift: instance_class code=db.m6g.large live=db.m6g.xlarge` | code: `infra/envs/prod.tfvars:10`. Someone resized in the console; the next `terraform apply` would scale it back down |
| 27 | HPA `widgetapi-web` | `drift: maxReplicas code=20 live=30` | code: `values-prod.yaml:13`. Live value was edited with `kubectl`/another pipeline |
| 29 | SecretProviderClass `widgetapi-db` | `not found in arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod / ns widgetapi` | `error: the server doesn't have a resource type "secretproviderclass"`: the Secrets Store CSI Driver CRD is not installed in this cluster, so `secretsStore.enabled: true` in `values-prod.yaml:20` has never been deployed (or the deploy fails). The query could see the type (the API server answered), so this is a real `not found`, not `not-queryable`. The driver and the AWS provider are cluster add-ons outside this repo: open question |

Row 20 note: the first attempt in `eu-west-1` returned an empty list; CloudFront is global, so the skill re-queried in `us-east-1` (Constraint: global services in `us-east-1`) and got `✓ matches`. Empty is not absent.

Drift rows go at the top of Assumptions and Caveats; the catalog keeps the **code** value as declared and shows the live value beside it. Nothing is silently resolved.

## What a produced doc would look like

`.culiops/service-discovery/widgetapi-prod.md` would contain:

- Header: `Cataloged from commit` SHA, date=2026-10-26, instance=prod, tools=Terraform/Helm, `**Live verification:** performed 2026-10-26 against 123456789012/eu-west-1, context arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod` (account `123456789012`, `eu-west-1`, context `arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod`).
- `## Overview` — fictional HTTP API, runs on EKS, env=prod in eu-west-1.
- `## Prerequisites` — `aws` v2, `kubectl` ≥ 1.28, `helm` ≥ 3.12; auth `aws eks update-kubeconfig --name widgetapi-prod`; least privilege: AWS `ReadOnlyAccess` (or scoped, **without** `secretsmanager:GetSecretValue`) + Kubernetes `view` role in `widgetapi` namespace (note: `view` cannot read Secrets, which is intended) + Datadog read-only API key; mutations listed (kubectl rollout restart, helm rollback, kubectl scale).
- `## Resource Inventory` — 29 rows grouped by category, with `Owner` (`terraform infra`, `terraform platform`, `helm widgetapi`) and `Live` columns. Excerpt:

  | Type | Resolved Name | Owner | Live |
  |------|---------------|-------|------|
  | `aws_db_instance` | `widgetapi-prod-db` | terraform infra | drift: instance_class code=db.m6g.large live=db.m6g.xlarge (Q5) |
  | `autoscaling/v2/HorizontalPodAutoscaler` | `widgetapi-web` | helm widgetapi | drift: maxReplicas code=20 live=30 (Q27) |
  | `secrets-store.csi.x-k8s.io/v1/SecretProviderClass` | `widgetapi-db` | helm widgetapi | not found in arn:aws:eks:eu-west-1:123456789012:cluster/widgetapi-prod / ns widgetapi (Q29) |
  | `aws_lb` | `widgetapi-prod-alb` | terraform platform | ✓ matches (Q19) |

- `## Naming Patterns` — `widgetapi-${env}-<component>` with `{env}` placeholder.
- `## Identifying Dimensions` — env, region, pod/replica, CloudFront geography, DB primary vs replica.
- `## Dependency Graph` — platform → infra (cross-stack); helm → platform + infra (cross-stack); remote registry modules by source + version (not fetched); secret references (names/ARNs only): `widgetapi/prod/db` (CSI), RDS-managed secret from `DB_SECRET_ARN`, Kubernetes Secrets `widgetapi`, `datadog-secret`; third-party: Datadog, PagerDuty (code + doc), Stripe, SendGrid, LaunchDarkly (doc only); critical-path edges marked.
- `## Signal Envelopes` — availability SLO 99.9% / 30d, `source=doc` (`docs/oncall.md:22`), Medium, to be verified against Datadog monitor `widgetapi-prod-slo-burn`; no latency threshold stated; HPA target CPU 65% is the one code-declared saturation limit; rest "not declared".
- `## Investigation Runbooks` — 5 trees (latency, 5xx, upload failures, async delay, auth failures).
- `## Stack-Specific Tooling` — `examples/aws.md` + `examples/kubernetes.md`; notes for Datadog/PagerDuty/Stripe/SendGrid/LaunchDarkly.
- `## Assumptions and Caveats` — drift rows first (Q5, Q27); Q29 not found; Helm image tag is env-specific (2026.04.1 prod, 2026.04.1-rc3 staging); catalog never read Terraform state or any secret value.
- `## Open Questions` — Is the Secrets Store CSI Driver + AWS provider installed or planned? S3 bucket `widgetapi-logs-eu-west-1` (ALB/CloudFront logs, `docs/oncall.md:14-15`) is not in any stack in this repo: who owns it? Are Stripe/SendGrid/LaunchDarkly still in use (doc-only)?
