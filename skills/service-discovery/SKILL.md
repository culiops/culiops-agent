---
name: service-discovery
description: Use when the user asks to discover, map, catalog, or inventory the resources of a service from its infrastructure-as-code repo, or to prepare troubleshooting documentation / runbooks for incident investigation. Triggers include phrases like "discover <service>", "map resources for <service>", "generate service discovery doc", "what does <service> use", "build a runbook for <service>". Cloud-agnostic and IaC-agnostic — works whether the repo is Terraform, Pulumi, CloudFormation, Bicep, Helm/Kustomize, or a mix.
---

# Service Discovery

Scan a service's infrastructure-as-code repo and produce a troubleshooting-oriented inventory: a resource catalog, naming/tagging patterns, a dependency map, and per-symptom investigation runbooks. The output must be accurate enough that an on-caller who has never seen the service can use it to diagnose a live incident.

## The Iron Law

```
NO ASSUMPTIONS. IF UNCLEAR, ASK THE HUMAN.
NO OUT-OF-SCOPE ACTIONS WITHOUT HUMAN APPROVAL.
ONLY READ INFRASTRUCTURE-AS-CODE AND DOCUMENTATION FILES. NEVER READ SECRETS.
```

**Real-discovery extension (when no IaC is found):**

```
NO WRITE API CALLS. EVER.
ALL CLOUD QUERIES ARE READ-ONLY. NO EXCEPTIONS.
```

## Constraints (Non-Negotiable)

1. **The IaC code is the source of truth.** Every claim in the catalog must trace back to a specific file and line in the repo. Do not invent resources, dependencies, or thresholds from outside knowledge of "what services usually look like." If the code does not say it, the catalog does not say it.
2. **No assumptions.** If anything is unclear during discovery — a resource's purpose, a naming token, a dependency, an unresolved parameter, whether a conditional resource is enabled in the target instance — STOP and ask the human. An incomplete catalog with explicit questions is better than a complete catalog with wrong claims.
3. **Stop at the stack boundary.** A "stack" is the deploy unit (Terraform root module, CloudFormation stack, Pulumi project, Helm release, Bicep deployment). Read everything inside the in-scope stack(s); do NOT follow references into other stacks. Cross-stack references get recorded as *dependencies*, not chased.
4. **Strict scope.** Anything outside the named repo paths — running cloud CLIs, modifying infrastructure, reading other repos, calling external APIs — requires explicit human approval before you do it.
5. **No secrets, ever.** Do not read files that are likely to contain secrets (anything matching common patterns: `*.enc.*`, `*.secret.*`, `secrets/`, `.env*`, `*.pem`, `*.key`, `id_rsa*`, files inside `vault/`, files referenced by tools like SOPS / sealed-secrets / Doppler / 1Password CLI). When the IaC declares a secret reference (e.g., `aws_secretsmanager_secret_version`, `data.vault_generic_secret`, `azurerm_key_vault_secret`), record the *reference*, not any value.
6. **Resolve to a single, named instance.** A repo is a template; the catalog is about a specific instance (one environment, one region, one tenant — whatever the smallest deploy-target unit is in this repo). Confirm with the human which instance is being cataloged before scanning.
7. **User confirmation at every gate.** Five workflow gates exist. None are optional.

## Rationalization Prevention

| Thought | Reality |
|---------|---------|
| "This resource is probably X" | STOP — read the code or ask. |
| "The naming pattern is obviously…" | STOP — verify from the code; report what the code actually says. |
| "I'll resolve `${var.x}` to its default value" | STOP — defaults can be overridden per instance. Resolve from the actual instance's parameter source, or ask. |
| "I'll just follow this module reference into the other stack" | STOP — other stacks are out of scope. Record the cross-stack reference as a dependency and stop. |
| "This `.env` file might tell me which region this deploys to" | STOP — never read files in the secrets-shape. Ask the human for non-secret config. |
| "I can skip the dependency-graph step; nothing depends on this service" | STOP — verify by tracing references in the code; absence of evidence is not evidence of absence. |
| "I'll write the runbook section without confirmation" | STOP — runbooks must be validated against the user's actual investigation patterns. |
| "The four golden signals don't apply to this resource type" | STOP — record the envelope as `n/a` with a reason, don't omit. |
| "The documents are clear enough, I don't need to run cloud queries to verify" | STOP — documents may be outdated. The converging discovery approach exists because neither source is reliable alone. |
| "I'll skip the broad discovery query gate since it's all read-only" | STOP — the operator must see and approve every query before execution. Read-only does not mean ungated. |
| "This image diagram is too blurry to extract anything useful" | STOP — present what you can extract with `[uncertain]` markers. The operator can confirm or discard. |
| "The credentials don't match the documents but they're probably the right account" | STOP — flag the mismatch at the Step 3R gate. Mismatched credentials → wrong account → wrong resources in catalog. |
| "I'll run a write API to tag this untagged resource for easier discovery" | STOP — NO WRITE API CALLS. EVER. Record the resource as-is. |

## Red Flags — STOP and Follow Process

| Red Flag | What to do |
|----------|------------|
| Writing the discovery doc before the human confirms inventory and dependencies | STOP → return to the inventory gate (Step 2) and resolve. |
| Skipping the IaC-tool-detection sub-step because "this is obviously Terraform" | STOP → run detection anyway; mixed-tool repos are common. |
| Filling in the dependency section by guessing or by general knowledge of the cloud | STOP → derive from code references only; ask the human for anything inferred. |
| Reading a file outside the named repo paths without approval | STOP → ask the human for permission. |
| Building investigation runbooks before the resource inventory is confirmed | STOP → return to Step 2. |
| A naming-pattern token whose origin you can't point at in the code | STOP → re-trace, or ask the human. |
| Producing a runbook that has no user-visible-symptom anchor | STOP → rewrite to lead with the user-facing symptom. |
| Producing a runbook that has no "is this an upstream dependency?" branch | STOP → add the dependency-first branch. |
| Emitting a final catalog without the "Assumptions and Caveats" section | STOP → add it. The catalog is incomplete without it. |
| Continuing after the human says something is wrong without addressing it | STOP → fix all flagged issues before proceeding. |
| Running cloud API queries before the operator approves the cloud context (Step 3R gate) | STOP → return to Step 3R and present credentials for approval. |
| Running broad discovery queries before the operator approves them (Step 4R gate 4a) | STOP → return to Step 4R and present proposed queries. |
| Using a write/mutating API call during any real-discovery step | STOP → replace with the read-only equivalent. There is no exception. |
| Proceeding with real-discovery when IaC files are present in the directory | STOP → IaC found means IaC path. Real-discovery is the fallback, not an option. |
| Treating vision-extracted hints as high confidence without operator confirmation | STOP → vision hints are always Low confidence. Present with `[uncertain]` markers at Step 2R gate. |

## Workflow

```dot
digraph discovery {
    rankdir=TB;
    node [shape=box, style=rounded];

    input    [label="Repo path + service name\n(from user or CWD)"];
    detect   [label="Step 1: Detect IaC tool(s)\nor document signatures"];

    subgraph cluster_iac {
        label="IaC Path";
        style=dashed;

        gate1    [label="GATE 1: Human confirms\nlayout + instance", shape=diamond];
        inventory [label="Step 2: Resolve parameters,\nbuild resource inventory\n(with naming, identifiers,\nsignal envelope, conditionals)"];
        gate2    [label="GATE 2: Human confirms\ninventory", shape=diamond];
        deps     [label="Step 3: Compute dependency\ngraph (direct + transitive,\nfrom code references)"];
        gate3    [label="GATE 3: Human confirms\ndependencies", shape=diamond];
        runbooks [label="Step 4: Build investigation-tree\nrunbooks (user symptoms first,\nupstream branch always)"];
        gate4    [label="GATE 4: Human validates\nrunbooks", shape=diamond];
        write    [label="Step 5: Write discovery doc\n+ Assumptions section\n+ commit-SHA stamp"];
    }

    subgraph cluster_real {
        label="Real-Discovery Path";
        style=dashed;

        docroute [label="Document signatures\ndetected"];
        gateR1   [label="GATE: Switch to\nreal-discovery mode?", shape=diamond];
        parse    [label="Step 2R: Parse documents,\nextract resource hints\n(structured → text → image)"];
        gateR2   [label="GATE: Confirm\nresource hints", shape=diamond];
        context  [label="Step 3R: Resolve cloud\ncontext (probe creds,\ncross-ref with doc hints)"];
        gateR3   [label="GATE: Confirm target\nenvironment", shape=diamond];
        converge [label="Step 4R: Converging discovery\n(merge doc hints +\ncloud query results)"];
        gateR4a  [label="GATE 4a: Approve\ndiscovery queries?", shape=diamond];
        gateR4b  [label="GATE 4b: Confirm\nresource list?", shape=diamond];
        enrich   [label="Step 5R: Detailed resource\nenrichment + runbooks"];
        gateR5   [label="GATE: Validate\nrunbooks", shape=diamond];
        writeR   [label="Step 6R: Write catalog\n+ confidence flags\n+ unresolved refs"];
    }

    gate5    [label="GATE 5: Human reviews\nfinal doc", shape=diamond];
    commit   [label="Commit if approved"];

    input -> detect;
    detect -> gate1     [label="IaC found"];
    detect -> docroute  [label="no IaC found"];

    gate1 -> inventory  [label="confirmed"];
    gate1 -> detect     [label="corrections"];
    inventory -> gate2;
    gate2 -> deps       [label="confirmed"];
    gate2 -> inventory  [label="corrections"];
    deps -> gate3;
    gate3 -> runbooks   [label="confirmed"];
    gate3 -> deps       [label="corrections"];
    runbooks -> gate4;
    gate4 -> write      [label="validated"];
    gate4 -> runbooks   [label="adjust"];
    write -> gate5;

    docroute -> gateR1;
    gateR1 -> parse     [label="confirmed"];
    parse -> gateR2;
    gateR2 -> context   [label="confirmed"];
    gateR2 -> parse     [label="corrections"];
    context -> gateR3;
    gateR3 -> converge  [label="confirmed"];
    gateR3 -> context   [label="corrections"];
    converge -> gateR4a;
    gateR4a -> gateR4b  [label="approved"];
    gateR4a -> converge [label="narrowed"];
    gateR4b -> enrich   [label="confirmed"];
    gateR4b -> converge [label="corrections"];
    enrich -> gateR5;
    gateR5 -> writeR    [label="validated"];
    gateR5 -> enrich    [label="adjust"];
    writeR -> gate5;

    gate5 -> commit     [label="approved"];
    gate5 -> write      [label="changes requested\n(IaC path)"];
    gate5 -> writeR     [label="changes requested\n(real-discovery path)"];
}
```

---

### Step 1: Detect IaC Tool, Stack Layout, and Target Instance

**Inputs.** A repo path and a service name. If either is missing, ask. Detect a service name from the current working directory if the user said "discover this" without naming one.

**Detect the IaC tool(s) in the repo.** At the start of Step 1, load every file under `tool-detectors/*.md`. Each detector's `## File signatures` section defines what files signal that tool. Match the repo's files against every loaded detector. Record every tool that matches — a repo can use more than one. The currently-shipped detectors are listed in [`tool-detectors/README.md`](tool-detectors/README.md).

For each matched detector, the rest of Step 1 (stack boundary detection) and Steps 2–3 (parameter resolution, resource extraction, dependency derivation) consult the corresponding sections of that detector file (`## Stack boundary`, `## Parameter sources`, `## Resource extraction`, `## Typical cross-stack dependencies`). If a detector omits a section, that dimension is unknown for the matched tool — surface the gap and ask the human.

**If no IaC tool is detected: scan for document signatures.** When the detector pass finds zero IaC tools, do not proceed to "Detect unclassified deploy artifacts." Instead, load every file under `doc-detectors/*.md` and scan the directory for matching file signatures. Each doc-detector's `## File signatures` section defines what files signal that format.

If document signatures are found, present:

> "No IaC files found in this directory. However, I found documentation and diagrams that may describe the infrastructure:
>
> | File | Format | Detected by |
> |------|--------|-------------|
> | `architecture.drawio` | Draw.io diagram | `doc-detectors/drawio.md` |
> | `runbook.md` | Markdown documentation | `doc-detectors/markdown.md` |
> | `infra-diagram.png` | Architecture image | `doc-detectors/image.md` |
>
> I can switch to **real-infrastructure discovery mode** — I'll extract resource hints from these documents, then verify against live cloud APIs (read-only) to build the same service catalog.
>
> **GATE: Switch to real-discovery mode? (Requires cloud credentials configured locally.)**"

If the operator confirms, proceed to **Step 2R** (Document Parsing). If the operator declines, STOP.

If neither IaC tools nor document signatures are found, STOP:

> "No IaC files, documents, or diagrams found in this directory. I need at least one of: infrastructure-as-code files, architecture documents, or architecture diagrams to begin discovery."

**Hybrid directories (IaC + documents):** If IaC files are found, the skill takes the IaC path regardless of whether documents are also present. Supplementing IaC discovery with document hints is out of scope for this version.

**Detect unclassified deploy artifacts.** After running the detector pass, scan the repo for files matching deploy-shape patterns (`*.yml`, `*.yaml`, `*.toml`, `*.json`) that were NOT attributed to any loaded detector. **Apply the secrets-exclusion rule first (Constraint 5) — exclude any file whose path matches secrets-shaped patterns (`*.enc.*`, `*.secret.*`, `secrets/`, `.env*`, `*.pem`, `*.key`, `id_rsa*`, `vault/`) before evaluating deploy-shape.** A file is "deploy-shaped" if its top level contains keys from this list: `service:`, `services:`, `cluster:`, `function:`, `functions:`, `task_definition:`, `app:`, `apps:`, `deploy:`, `provider:`, `runtime:`, `image:`, OR if any value contains an `arn:`, `gs://`, or `projects/<id>/...` reference.

If any unclassified deploy-shaped files are found, **STOP** and present:

> "I see these files that look like deploy descriptors but I don't recognize the tool: `<list>`. For each, please tell me one of:
> - **`<tool name>`** — if it's a known tool I should have a detector for (I'll flag this as a missing detector to contribute)
> - **`teach me`** — describe the stack boundary, parameter sources, and what cloud resources these files deploy. I'll use this for *this scan only* and recommend you contribute a detector file afterward.
> - **`ignore`** — these are not part of any in-scope stack (I'll record them in Assumptions and Caveats)."

Do not proceed to "Detect the stack layout" until every unclassified file has one of the three answers.

This sub-step exists because the Iron Law ("no assumptions, ask the human") cannot fire on files the skill does not look at. Silently skipping unrecognized deploy descriptors would produce a catalog that omits real deployed resources.

**Detect the stack layout.** A "stack" is the deploy unit:

- Terraform: each directory containing a root module (`provider` block + `terraform { backend ... }` or `terraform { required_providers ... }` at the top, no parent module calling it). Instances of a root module are typically multiplied by per-env `*.tfvars` files (commonly `envs/<env>.tfvars` or `terraform.<env>.tfvars`) passed via `-var-file`, by Terraform workspaces, or by Terragrunt environments.
- CloudFormation/SAM: each `template.yaml` / `template.json` is a stack.
- Pulumi: each `Pulumi.yaml` is a project; each `Pulumi.<stack>.yaml` is one instance of it.
- Bicep: each top-level `*.bicep` file deployed at a defined scope (resource group, subscription, management group, or tenant) is a stack. Instances are multiplied by per-env `*.parameters.<env>.json` (ARM parameter files) or `*.bicepparam` files passed via `az deployment <scope> create -p`.
- Helm: each `Chart.yaml` is a chart; each per-environment `values-<env>.yaml` (or each deployed release) is one instance. The base `values.yaml` is the template's defaults, not an instance.
- Kustomize: each directory containing a `kustomization.yaml` (overlay) is an instance.

List the stacks. Note which produce one instance (one-off) vs. many (parameterized template).

**Identify the target instance.** Ask the human:

> "I see this repo is `<tool(s) detected>` and contains the following stacks: `<list>`. Which specific instance should I catalog? (e.g., name an environment, region, workspace, tenant, or release.)"

Do NOT guess. Multi-instance repos are the norm; the wrong instance produces a wrong catalog.

**Detect the parameter sources for the chosen instance.** Examples by tool:

- Terraform: `*.tfvars` files, `TF_VAR_*` env vars, workspace name, remote backend state.
- CloudFormation: stack `Parameters` block, `--parameter-overrides`, exports from other stacks.
- Pulumi: `Pulumi.<stack>.yaml` config + ESC environments + secrets store.
- Bicep: `*.parameters.<env>.json` (ARM parameter files), `.bicepparam` files, inline `az deployment ... -p key=value` overrides, and Key Vault secret URI references (`@Microsoft.KeyVault(SecretUri=...)`).
- Helm: `values.yaml` + `values-<env>.yaml` + `--set` overrides.
- Kustomize: overlay's patches + ConfigMap/Secret generators.

Record where parameters come from, but do not resolve them yet.

**Present and STOP.**

> "Service: `<name>`
> Repo: `<path>`
> IaC tool(s) detected: `<list>`
> In-scope stack(s): `<list>`
> Target instance: `<the one the user named>`
> Parameter source(s) for this instance: `<list of files/refs>`
> Out-of-scope (cross-stack refs to be recorded as dependencies, not followed): `<list>`
>
> Is this correct?"

Wait for human confirmation. Apply corrections and re-present until confirmed.

---

### Step 2: Resolve Parameters and Build Resource Inventory

**Resolve parameters.** For each parameter the in-scope stack(s) declare, resolve it to the value used by the target instance. Sources of a value (in priority order, generally): explicit override → instance-specific file → environment-specific file → workspace mapping → declared default → registry lookup.

If a parameter cannot be resolved (file not present, registry not reachable, value comes from a runtime-only source like an SSM parameter the human hasn't shared) — DO NOT proceed. List the unresolved parameters and ask the human to provide values or to confirm "skip with placeholder, mark as unresolved in catalog."

**Scan the in-scope stack(s).** Use file types from Step 1's tool detection. Read every IaC file in the stack(s). Read documentation files (`README.md`, `docs/**/*.md`) inside the stack(s) to pick up author-supplied context. Skip secrets-shaped files unconditionally.

**Use detector resource-extraction rules.** For each tool matched in Step 1, consult that tool's `## Resource extraction` section in its detector file. Apply the mappings to convert the tool's config keys into inventory rows. The `Type` field uses both the resolved cloud-resource equivalent (e.g., `aws_ecs_service`) AND the detector-prefixed raw type (e.g., `ecspresso/service`) so operators can see the deploy tool's role.

**Extract per resource:**

| Field | Meaning |
|-------|---------|
| Type | The IaC resource type, normalized to a category: compute / storage / database / network / messaging / identity / observability / edge / serverless / data-pipeline / other. Record both the raw type (e.g., `aws_ecs_service`, `google_cloud_run_service`, `Microsoft.App/containerApps`) and the category. |
| Name (resolved) | The actual resource name after parameter substitution — not the template. |
| Naming-pattern fragment | The template form, e.g., `${service}-${env}-${region}-${role}`. |
| Conditional? | If the resource depends on `count`, `for_each`, `enable`, a feature flag, or a Helm `if` — record the gating condition. |
| Identifying dimensions | What an operator would filter by during an incident: tenant id, shard key, region, AZ, deployment id, version. List the ones present in the resource definition or available via tags. |
| Signal envelope | For each critical-path resource, four lines: latency expectation (per percentile), traffic baseline, error budget / threshold, saturation limit (whichever bind first — CPU, memory, connections, queue depth). If declared in code (alarms, SLO objects, alerting rules) — quote it. If not declared — record `not declared` and surface it in the runbook. |
| Source location | File + line range. |

**Detect the naming pattern.** Look across multiple resources for the recurring template (e.g., `${var.service}-${var.env}-${each.key}`). Convert to placeholder form and present it explicitly. Do not invent placeholders the repo does not actually use. If the pattern is inconsistent across resources — record both forms and flag.

**Detect conditional / optional resources.** For each gated resource, write the gating expression and the resolved boolean for the target instance. A resource gated `enable_redis = true` in the target instance → mark "present"; gated and resolved false → mark "not present in this instance."

**Present and STOP.**

> "Resolved parameters: `<key parameters with their resolved values>`
> Unresolved (needs your input): `<list, or "none">`
>
> **Resource Inventory for `<service>` / `<instance>`:**
>
> | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
> | … | … | … | … | … | … | … | … |
>
> **Detected naming pattern(s):** `<list>`
> **Optional resources NOT present in this instance:** `<list>`
>
> **Open questions:**
> - …
>
> Is this correct? Anything missing or wrong?"

Wait for confirmation. Apply corrections and re-present until confirmed.

---

### Step 2R: Document Parsing & Resource Hint Extraction (Real-Discovery Path)

*This step runs instead of Step 2 when the real-discovery path is active.*

**Load matched doc-detector files.** For each document format detected in Step 1, load the corresponding `doc-detectors/*.md` file. Each detector defines how to parse that format and what resource hints to extract.

**Parse in reliability order.** Process documents from most to least structurally reliable:

1. **Structured diagrams first** (Draw.io, Mermaid, PlantUML) — these have explicit node/edge relationships encoded in XML, YAML, or DSL syntax. Parse using the detector's extraction rules.
2. **Text documents second** (Markdown, Confluence exports, plain text) — scan for resource mentions, ARNs, hostnames, IP ranges, region identifiers, service names, and other cloud context clues using keyword lists from the detector.
3. **Image diagrams last** (PNG, JPEG, SVG rasterized) — these require vision analysis and are the most token-heavy and least reliable. Use vision to extract resource labels, relationship arrows, grouping boundaries, and annotations.

**Extract per hint:**

| Field | Meaning |
|-------|---------|
| Resource type | The cloud resource type mentioned or depicted (e.g., "RDS instance", "S3 bucket", "ALB") |
| Resource name | Any specific name, identifier, or ARN mentioned |
| Relationships | Connections to other resources shown in the document (arrows, references, "connects to" language) |
| Cloud context | Region, account, VPC, subnet, or other placement clues |
| Service boundary | Which service or system the resource belongs to, if the document groups resources |
| Source document | The file and location (page, section, coordinates) where the hint was found |
| Extraction confidence | **High** — explicitly named with identifiers in structured format. **Medium** — mentioned in text with enough context to identify. **Low** — inferred from image or ambiguous reference. |

**Cloud context clues.** While extracting resource hints, collect any cloud context that helps narrow discovery in Step 3R:

- AWS account IDs, region names, VPC IDs
- GCP project IDs, region/zone names
- Azure subscription IDs, resource group names, region names
- Kubernetes cluster names, namespace names
- Domain names, IP ranges, CIDR blocks

**Present and STOP.**

> "**Resource hints extracted from documents:**
>
> | # | Hint | Type | Source | Confidence |
> |---|------|------|--------|------------|
> | 1 | `prod-api-db` | RDS instance | `architecture.drawio` (node 14) | High |
> | 2 | `api-cache` | ElastiCache cluster | `runbook.md` (section 3.2) | Medium |
> | 3 | Load balancer | ALB | `infra-diagram.png` (top-center) | Low |
>
> **Cloud context clues:**
> - Region: `us-east-1` (mentioned in `runbook.md`)
> - Account: unknown
> - VPC: `vpc-abc123` (shown in `architecture.drawio`)
>
> **GATE: Do these hints look accurate? Remove/add/correct any before proceeding.**"

Wait for confirmation. Apply corrections and re-present until confirmed.

---

### Step 3R: Cloud Context Resolution (Real-Discovery Path)

*This step runs instead of Step 3 when the real-discovery path is active.*

**Probe local credentials.** Check what cloud credentials are configured locally:

- AWS: `aws sts get-caller-identity`
- GCP: `gcloud config get project`
- Azure: `az account show`
- Kubernetes: `kubectl config current-context`

If no credentials are found for any provider, STOP:

> "No cloud credentials found. Real-discovery requires at least one configured cloud provider (AWS, GCP, Azure) or Kubernetes context to verify resource hints against live infrastructure. Please configure credentials and retry."

**Cross-reference credentials with document hints.** Compare the provider, account/project, and region from the credential probes with the cloud context clues extracted in Step 2R. Flag any mismatches — a credential pointing at `us-west-2` when documents reference `us-east-1` resources is a strong signal that the wrong profile is active.

**Present and STOP.**

> "**Cloud context resolution:**
>
> | Provider | Identity Source | Value | Doc Hint | Match? |
> |----------|----------------|-------|----------|--------|
> | AWS | `aws sts get-caller-identity` | Account `123456789012`, `us-east-1` | Account: unknown, Region: `us-east-1` | Region matches |
> | Kubernetes | `kubectl config current-context` | `prod-eks-cluster` | Cluster: `prod-cluster` (from drawio) | Partial — name differs |
>
> **GATE: Is this the correct target environment?**"

**Hard rule: zero API calls before this gate passes.** No cloud queries — not even read-only ones — are permitted until the operator confirms the cloud context. Running queries against the wrong account produces a catalog of the wrong infrastructure.

**Multi-cloud.** If document hints reference multiple cloud providers, resolve each provider separately. The operator must confirm each provider's context independently.

Wait for confirmation. Apply corrections and re-present until confirmed.

---

### Step 4R: Converging Discovery (Real-Discovery Path)

*This step runs instead of Step 4 when the real-discovery path is active.*

This step merges two independent discovery seeds to build a verified resource list:

- **Seed A: Confirmed document hints** from Step 2R (operator-reviewed).
- **Seed B: Cloud-discovery templates** — load matching templates from `cloud-discovery/` based on the confirmed cloud context. Each template defines broad discovery queries for a resource category.

**Present proposed queries and STOP.**

> "**Proposed discovery queries:**
>
> I'll run these read-only queries to discover resources in the confirmed environment:
>
> | # | Query | Scope | Source |
> |---|-------|-------|--------|
> | 1 | `aws ec2 describe-instances --filters Name=vpc-id,Values=vpc-abc123` | Instances in confirmed VPC | `cloud-discovery/aws-ec2.md` |
> | 2 | `aws rds describe-db-instances` | All RDS instances in region | `cloud-discovery/aws-rds.md` |
> | 3 | `aws elbv2 describe-load-balancers` | All ALBs in region | `cloud-discovery/aws-elbv2.md` |
>
> **GATE 4a: Approve these discovery queries?**"

If the operator declines specific broad queries (e.g., "don't scan all RDS instances, just look for the ones in the documents"), proceed with Seed A only for those resource types. Resources discovered only via Seed A are flagged `documented-only, not verified`.

**Execute approved queries.** Run each approved query and collect results. Do NOT run any query the operator did not approve.

**Merge seeds and assign confidence.**

| Condition | Confidence | Flag |
|-----------|------------|------|
| Resource found in both docs and cloud | **High** | *(none)* |
| Resource found in docs only (not found in cloud, or query not approved) | **Low** | `documented-not-found` |
| Resource found in cloud only (not mentioned in any document) | **Medium** | `undocumented` |

**Present merged resource list and STOP.**

> "**Merged resource list for `<service>`:**
>
> | # | Resource | Type | Source | Confidence | Flag |
> |---|----------|------|--------|------------|------|
> | 1 | `prod-api-db` | RDS instance | docs + cloud | High | |
> | 2 | `api-cache` | ElastiCache cluster | docs only | Low | `documented-not-found` |
> | 3 | `prod-api-alb` | ALB | cloud only | Medium | `undocumented` |
>
> **GATE 4b: Confirm this resource list before detailed discovery?**"

The operator can add, remove, or reclassify resources at this gate. Resources flagged `documented-not-found` are excluded from enrichment in Step 5R but are recorded in the final catalog's Unresolved References section.

Wait for confirmation. Apply corrections and re-present until confirmed.

---

### Step 5R: Detailed Resource Enrichment (Real-Discovery Path)

*This step enriches each confirmed resource from Step 4R with detailed configuration, relationships, and health data.*

**Use the same `examples/<cloud>.md` templates as the IaC path.** The enrichment queries for each resource type are identical — the difference is that real-discovery runs them against live infrastructure rather than cross-referencing with code.

**Data collected per resource:**

| Category | What to collect |
|----------|----------------|
| Configuration | Instance type/size, storage, engine version, runtime settings, scaling config |
| Relationships | Security groups, subnets, VPC, IAM roles, attached policies, target groups |
| Health/status | Current state, last event, active alarms, recent metrics (if accessible) |
| Tags/metadata | All tags, creation date, last modified, ARN/resource ID |
| Access/security | Public accessibility, encryption status, endpoint URLs, access logging |

**Dependency walking.** Using the enrichment data, link confirmed resources to each other:

- Security group references → which resources share security groups
- Subnet/VPC placement → which resources are co-located
- IAM role references → which resources share identity
- Target group membership → which resources sit behind which load balancers
- DNS/endpoint references → which resources connect to which

Note but do not chase references that cross the service boundary (e.g., a security group rule allowing traffic from an unknown CIDR). Record these as boundary dependencies, the same way the IaC path records cross-stack references.

**Report surprises.** If enrichment reveals resources that contradict document hints (e.g., a resource exists but with a different configuration than documented, or a documented relationship doesn't exist in practice), report them inline. This is informational — no gate required. The operator already confirmed the resource list at Gate 4b; surprises are noted in the catalog.

**Build runbooks.** Follow the same Step 4 process as the IaC path: enumerate user-visible failure modes, build investigation-tree runbooks with upstream-first branches, validate with the operator. Real-discovery has an advantage here — live health data and actual resource configurations are available, making the signal envelopes concrete rather than code-declared.

**Present all runbooks and STOP.** Wait for the operator to validate the trees, same as Step 4 in the IaC path.

---

### Step 6R: Write the Catalog (Real-Discovery Path)

*This step produces the same catalog format as the IaC path, with additional metadata reflecting the real-discovery source.*

**Output path.** Same as the IaC path: `.culiops/service-discovery/<service>[-<instance>].md`.

**Stamp the catalog.** Top of the doc, with additional source metadata:

```
**Discovery source:** real-discovery
**Discovery date:** `<YYYY-MM-DD>`
**Cloud context:** `<provider>` / `<account-or-project>` / `<region>`
**Documents used:** `<list of source documents from Step 2R>`
**Target instance:** `<instance name>`
```

**Confidence flags in the catalog.** Resources carry their confidence and flag from Step 4R:

- `undocumented` resources include a note in their inventory entry: *"Discovered via cloud API only — not referenced in any source document. Verify this resource belongs to this service."*
- `documented-not-found` resources appear in a dedicated `## Unresolved References` section (not in the main inventory): *"Referenced in `<source document>` but not found in the live environment. May be decommissioned, renamed, in a different account/region, or the document may be outdated."*

**All other catalog sections follow the IaC path format.** The section order from Step 5 applies:

1. `## Overview` — includes "discovered via real-discovery (documents + live cloud APIs)" instead of IaC tool names.
2. `## Prerequisites` — same structure, derived from the `examples/` files used during enrichment.
3. `## Resource Inventory` — from Step 4R's confirmed list, enriched in Step 5R. Grouped by category.
4. `## Naming Patterns` — detected from actual resource names rather than IaC templates.
5. `## Identifying Dimensions` — derived from tags, naming patterns, and resource placement.
6. `## Dependency Graph` — from Step 5R's dependency walking. Critical-path marked.
7. `## Signal Envelopes` — from live metrics and alarm configurations discovered in Step 5R.
8. `## Investigation Runbooks` — from Step 5R's runbook building.
9. `## Stack-Specific Tooling` — which `examples/<cloud>.md` file applies.
10. `## Unresolved References` — `documented-not-found` resources (real-discovery-specific section).
11. `## Assumptions and Caveats` — **mandatory**, with real-discovery-specific caveats:
    - *"This catalog was built from real-discovery (documents + live cloud APIs), not from infrastructure-as-code. Resources may exist that are not managed by any IaC tool."*
    - *"Document sources may be outdated. Resources marked `documented-not-found` were referenced in documents but not found in the live environment."*
    - *"Resources marked `undocumented` were found in the live environment but not referenced in any source document. They may belong to a different service."*
    - *"No drift detection is possible without IaC — the catalog reflects the live state at discovery time."*
12. `## Open Questions` — anything the operator said "I don't know, ask me later."

**Present and STOP.**

> "Catalog written to `.culiops/service-discovery/<filename>.md`. Please review the file.
>
> **GATE: Review catalog before writing? Should I commit it?**"

If approved: commit with message `Add service discovery doc for <service> (<instance>)`. Do NOT commit until approved.

---

### Step 3: Compute the Dependency Graph

**Direct dependencies** — derive from the code:

- Terraform: `depends_on`, references between resources, `data` lookups across providers, `terraform_remote_state` lookups, module `source` references.
- CloudFormation: `DependsOn`, `Ref`/`Fn::GetAtt` references, cross-stack `Fn::ImportValue` / `Outputs.Export`.
- Pulumi: explicit `dependsOn`, resource references in code, `StackReference`.
- Bicep: `existing` resource declarations (same- or cross-scope, e.g. `scope: resourceGroup(...)` / `scope: subscription()`), `module` imports of other `*.bicep` files, role-assignment `principalId` references, Key Vault secret URI references (`@Microsoft.KeyVault(...)`).
- Helm: `requirements.yaml` / `Chart.yaml` `dependencies`, ConfigMap/Secret refs, ServiceAccount + RBAC bindings.
- Kustomize: bases, `replacements`, `patchesStrategicMerge` targets.
- For tools matched via a detector, also consult the detector's `## Typical cross-stack dependencies` section as a hint for what kinds of upstream references to look for. The actual graph is still derived from references in code — the hints help you avoid missing common patterns.

For each dependency, record: the upstream resource (or stack), the linkage (output name, exported value, registry key), and whether the linkage is hard-coded or parameterized.

**Transitive dependencies** — for each direct upstream that itself is in a different stack, you do NOT chase into that stack (Iron Law: stop at boundaries). But you DO record:

- The upstream stack name (as the human knows it).
- What the in-scope stack consumes from it.
- The expected protocol / interface (HTTP, gRPC, queue, event bus, shared database, shared registry, etc.) inferred from the referenced resource type.
- Anything the human tells you about that stack's reliability characteristics (SLO, blast radius, on-call team).

If the human can't characterize an upstream, mark it "**unknown — investigation entry point**" and surface it in the runbook so on-callers don't dead-end.

**Critical-path classification.** For each direct dependency, ask: does a user request to this service synchronously traverse it? Yes → critical path. No → eventual / async / observability-only.

**Render.** Produce a dependency graph (an indented list is fine if a DOT block isn't needed). Mark critical-path edges. Mark cross-stack dependencies. Mark cross-cloud / cross-region / cross-account dependencies (these are blast-radius signals).

**Present and STOP.**

> "**Dependencies for `<service>` / `<instance>`:**
>
> Upstream (this service depends on):
> - `<name>` [critical-path / async] — linkage: `<output X of stack Y>`; protocol: `<inferred>`; reliability characteristics: `<from human or "unknown">`
> - …
>
> Downstream (depends on this service): `<derived from inbound references in the repo, plus anything the human knows>`
>
> Shared infrastructure (same-stack co-tenants whose failure correlates): `<list>`
>
> Is this graph correct? Are there upstream/downstream edges I missed?"

Wait for confirmation. Apply corrections and re-present until confirmed.

---

### Step 4: Build Investigation-Tree Runbooks

For each user-visible failure mode of the service, build a **decision tree**, not a script. The tree's job is to guide a methodical operator from a symptom to a hypothesis to a test to the next narrowing question.

**Step 4a: Enumerate user-visible failure modes.** Ask the human (or derive from existing alarm definitions found in code) which user-facing symptoms the service can exhibit. Frame them in user terms:

- "User-facing requests slow / timing out"
- "User-facing requests returning errors"
- "User-facing requests returning wrong / stale data"
- "Background processing for users is delayed"
- "<service-specific failure mode the human names>"

These categories replace the legacy alarm-name vocabulary ("5xx spike", "queue backlog"). The technical signals (HTTP 5xx, queue depth) live *inside* the tree as branches, not as the headline.

**Step 4b: Build each tree.** Every runbook must contain, in order:

1. **Anchor — what the user sees.** Sentence one: the user-visible symptom. Sentence two: which SLI/SLO this corresponds to (or "no declared SLI — establish a baseline").
2. **First branch — is this an upstream issue?** List the critical-path dependencies (from Step 3). For each: how to check it (named query / dashboard / metric — generic; the per-cloud commands live in `examples/`). If any upstream is unhealthy, the runbook for *this* service ends and the upstream's runbook takes over.
3. **Second branch — narrow on identifying dimensions.** Use the dimensions captured in Step 2: is this affecting all tenants or one? all regions or one? all shards or one? all deployments or only the latest? Narrowing on dimensions is the single highest-leverage debugging move. Each narrowing answer rules hypotheses in or out.
4. **Third branch — four-signals walk-through.** For each critical-path resource, in dependency order: check latency, traffic, errors, saturation against the envelope from Step 2. The envelope comparisons drive the next branch ("latency p99 above envelope on resource X → check X's saturation → check X's upstream"). If a resource has no declared envelope, the branch is "compare against last 7-day baseline."
5. **Tools branch — what to look at, where.** For each check, name the dashboard / log query / CLI. The skill writes this generically here ("check ALB target group health"); the per-cloud `examples/<cloud>.md` provides exact CLIs. If the operator needs a permission or a secret to run a check, name it ("requires read access to <secret reference>"). Every prescribed CLI is **read-only by default** — the required least-privilege role lives in the matching `examples/<cloud>.md` preamble. If a step would change state (drain, restart, failover, invalidate, scale, rollback, DNS change, config change), label the step **`MUTATION — requires explicit approval`**, state the blast radius, state the elevated permission required, and instruct the operator to pause and confirm with the team before running. The runbook must never chain commands such that one command's output triggers the next without a human review pause.
6. **What this is NOT.** A line per false-friend: the symptoms that *look* like this category but are actually a different one, with a pointer to the right runbook.

**Step 4c: Validate.** For each runbook tree, ask the human:

- "Does this match how your team would actually investigate this symptom? Is there a step you'd take first that's not here?"
- "Has this service had an incident in this category? If yes, would this tree have led the on-caller to the cause?"

If the team has postmortems for past incidents in this category, reference them in the tree.

**Present all runbooks and STOP.** Wait for the human to validate the trees. Adjust ordering, add branches, remove dead-end branches as requested.

---

### Step 5: Write the Discovery Document

Only after Steps 1-4 are all confirmed.

**Output path.** `.culiops/service-discovery/<service>[-<instance>].md`. All output documents produced by any `culiops` skill live under the `.culiops/` directory at the repo root — this keeps plugin-generated artifacts separate from hand-written docs and makes them easy to find, regenerate, or gitignore as a group. If a single instance is cataloged, suffix the filename with the instance name (e.g., `-prod-eu`). If the catalog covers all instances of the same template (rare and only if the human confirms it's safe to combine), no suffix.

**Stamp the catalog.** Top of the doc:

```
**Cataloged from commit:** `<short SHA>`
**Cataloging date:** `<YYYY-MM-DD>`
**Target instance:** `<instance name>`
**IaC tool(s):** `<list>`
```

**Sections, in order:**

1. `## Overview` — service name, instance, tool(s), short purpose (from human or repo README).
2. `## Prerequisites` — what the on-caller must have set up before using this catalog during an incident. Lists: (a) the required CLI tool(s) and minimum versions (from the matching `examples/<cloud>.md` preamble); (b) how to authenticate; (c) the **least-privilege IAM role / scope** needed to run the read-only commands the runbooks reference; (d) any runbook step in this catalog that involves a **mutation** (drain, restart, failover, invalidate, scale, rollback, DNS change, config change) — listed with the elevated permission required and the team-approval expectation.
3. `## Resource Inventory` — the table from Step 2, grouped by category.
4. `## Naming Patterns` — detected patterns, with the placeholder taxonomy used.
5. `## Identifying Dimensions` — the cross-cutting dimensions (tenant, region, shard, etc.) operators can pivot by.
6. `## Dependency Graph` — from Step 3. Critical-path marked.
7. `## Signal Envelopes` — per critical-path resource, the four-signals envelope and where it's measured.
8. `## Investigation Runbooks` — one per user-visible symptom from Step 4. Trees rendered as nested lists or DOT blocks.
9. `## Stack-Specific Tooling` — which `examples/<cloud>.md` file applies, with a 1-line note for any third-party tool the catalog references that doesn't live in `examples/` (the operator will need to ask the team).
10. `## Assumptions and Caveats` — **mandatory**. Drift status (catalog matches code at commit X; running infra may differ — recommend drift check). Unresolved parameters (any that were skipped). Steps requiring secrets or elevated permissions. Upstream stacks marked "unknown." Anything else the operator should not be surprised by. **Mandatory line if the escape hatch fired:** if any "teach me" or "ignore" answer was used in Step 1's "Detect unclassified deploy artifacts" sub-step, add the line: *"Tool `<X>` was not pre-known to the skill; the [stack boundary / parameter resolution / resource mapping] for this tool came from operator input during this scan and is not encoded in any detector file. Recommend contributing `tool-detectors/<X>.md`."*
11. `## Open Questions` — anything the human said "I don't know, ask me later."

**Placeholder taxonomy.** Use only the placeholders the repo actually uses, detected in Step 2. Common ones:

| Placeholder | Description |
|-------------|-------------|
| `{service}` | The service identifier as it appears in resource names |
| `{instance}` | The target instance (env/region/tenant — whatever the repo's smallest deploy unit is) |
| `{T-1h}`, `{T-15m}` | One hour ago / fifteen minutes ago, ISO 8601 |
| `{now}` | Current time, ISO 8601 |

Repo-specific placeholders (e.g., `{shard}`, `{tenant}`, `{region}`, `{role}`, `{version}`) are added based on what Step 2 detected. Do NOT pre-declare placeholders the repo doesn't use.

**Present and STOP.**

> "Discovery doc written to `.culiops/service-discovery/<filename>.md`. Please review the file. Should I commit it?"

If approved: commit with message `Add service discovery doc for <service> (<instance>)`. Do NOT commit until approved.

---

## Stack-Specific Examples

For exact CLI command templates, see:

- AWS: [`examples/aws.md`](examples/aws.md)
- GCP: [`examples/gcp.md`](examples/gcp.md)
- Azure: [`examples/azure.md`](examples/azure.md)
- Kubernetes & Helm (any host): [`examples/kubernetes.md`](examples/kubernetes.md)

**Selection rule.** Cloud and Kubernetes are orthogonal axes — pick one or both:

- Cloud IaC detected (`aws_*`, `google_*`, `azurerm_*`, CloudFormation, Bicep, or equivalent) → use the matching cloud file.
- Helm charts, raw Kubernetes manifests, or Kustomize overlays detected → additionally use `examples/kubernetes.md`. This applies whether the cluster runs on-prem (kubeadm, Rancher/RKE, OpenShift, k3s, bare-metal), on a managed cloud service (EKS / GKE / AKS), or both. The cloud file covers the control-plane / node-pool / cloud-integration side; the Kubernetes file covers everything inside the cluster.
- Neither cloud nor Kubernetes signals → revert to generic descriptions ("check the load balancer's target health") and note the gap.

Each examples file has its own `## Prerequisites` section (CLI version, authentication, least-privilege role, mutation flagging, cost awareness). The runbook's `## Prerequisites` section in the written output (Step 5, section 2) must list prerequisites for **every** examples file the runbook references.

## Model Routing

> These hints guide the orchestrating model on which model tier to use per step. **Rules:** (1) Production-conservative — only route to sonnet when a gate catches errors or the step is purely mechanical. (2) Escalate to opus if a sonnet subagent returns uncertain results. (3) The orchestrator may override any hint based on runtime complexity.

| Step | Model | Inputs | Outputs | Rationale |
|------|-------|--------|---------|-----------|
| Step 1: Detect IaC tool + layout | sonnet | Repo file listing, all detector files from tool-detectors/ | Matched tools, stack boundaries, parameter sources, unclassified artifacts | Pattern matching file paths against detector signatures. GATE 1 catches misdetection |
| Step 2: Resolve params + inventory | opus | IaC files for in-scope stacks, parameter source files, matched detector extraction rules | Resource inventory with resolved names, types, naming patterns, signal envelopes, conditionals | Wrong parameter resolution → wrong resource names in catalog → on-caller searches for nonexistent resources during incident |
| Step 3: Compute dependency graph | opus | Resource inventory, code references (depends_on, data lookups, remote state, cross-stack refs), detector cross-stack hints | Dependency graph with direct/transitive deps, critical-path classification, protocol/reliability per link | Missing a critical-path dependency → runbook won't tell on-caller to check the real upstream cause |
| Step 4: Build runbooks | opus | Inventory, dependency graph, examples/ templates, user journeys (from operator) | Per-symptom investigation decision trees with upstream-first branches | Most judgment-intensive step. Wrong runbook structure wastes incident response time. Domain expertise required |
| Step 5: Write discovery doc | sonnet | All outputs from Steps 1-4, output format from SKILL.md, commit SHA | `.culiops/service-discovery/` document + git commit | Template assembly from validated outputs. GATE 5 catches formatting issues before finalization |

### Model Routing — Real-Discovery Path

| Step | Model | Inputs | Outputs | Rationale |
|------|-------|--------|---------|-----------|
| Step 1: Document detection | sonnet | Directory file listing, doc-detector signatures | Matched formats, routing decision | Mechanical file matching |
| Step 2R: Structured diagram parsing | sonnet | Diagram files, doc-detector rules | Node labels, edges, groupings | XML/text extraction |
| Step 2R: Image diagram analysis | opus | Image file (vision) | Resources, relationships with confidence | Judgment-heavy |
| Step 2R: Text keyword extraction | sonnet | Text docs, keyword lists | Resource mentions, ARNs, regions | Pattern matching |
| Step 2R: Hint consolidation | opus | All hints | Deduplicated hint list | Cross-referencing judgment |
| Step 3R: Cloud context resolution | orchestrator | Cred probes, doc hints | Resolved provider/account/region | Interactive |
| Step 4R: Broad query construction | sonnet | Cloud-discovery templates, service name | Proposed CLI commands | Template assembly |
| Step 4R: Merge + confidence | opus | Seeds A + B | Resource list with flags | Cross-referencing |
| Step 5R: Enrichment queries | sonnet | examples/ templates, resource list | Per-resource data | Template-driven |
| Step 5R: Dependency analysis | opus | Enrichment results, resource list | Dependency graph | Judgment |
| Step 5R: Runbook generation | opus | All data | Investigation trees | Safety-critical |
| Step 6R: Catalog assembly | sonnet | All outputs | Catalog document | Template assembly |
| All gates | orchestrator | Step outputs | Operator decisions | Interactive |
