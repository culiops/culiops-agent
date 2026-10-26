
# Cloud Discovery Query Templates

Each file in this directory describes broad discovery API queries for one supported platform (AWS or Kubernetes). The `service-discovery` skill reads these templates during Step 4 (Converging Discovery) of the real-discovery path to find resources across an AWS account/region or a Kubernetes cluster that relate to a given service name — before drilling into per-resource-type detail.

Only AWS and Kubernetes are supported. GCP and Azure templates were removed (archived at tag `archive/multi-cloud-v0.10.0`).

## Rules that apply to every template

- **Every command the skill runs here is projected.** Use explicit `--query` JMESPath, `-o jsonpath` or `-o custom-columns` allowlists, metadata only. Never request a whole object (`-o json`/`-o yaml`), a `configuration` column, Secret kinds, or environment variables: output of these commands can reach the catalog.
- **Pin the target.** Every AWS command carries `--profile {profile} --region {region}` (global services: `--region us-east-1`); every `kubectl`/`helm` command carries `--context {context}`. Before each batch re-check the identity (see the "Identity check" block in each template) and abort if it differs from the confirmed target.
- **Empty is not absent.** Record `not-found (queried <account>/<region>)`, `not-queried`, or `not-queryable (global or untagged)`; never infer decommissioned from an empty result alone.

## Relationship to the `examples/` directory

These two directories serve different purposes:

- **`cloud-discovery/`** (this directory) contains **broad, cross-resource-type** queries used early in real-discovery to *find* which resources exist. The queries here search by tag, label or namespace — they cast a wide net and return resource hints (name, type, location). A hint is not membership: see each template's membership rules.
- **`examples/`** contains **per-resource-type CLI templates** used later to *enrich* each discovered resource with status, metrics, and the four golden signals (latency, traffic, errors, saturation).

In short: `cloud-discovery/` answers "what resources does this service have?" while `examples/` answers "what is the current state of this specific resource?"

## Query template format

````markdown
---
name: <provider-name>
identity-command: "<CLI command to verify credentials>"
---

## Prerequisites
- CLI tools and minimum versions
- Identity check (re-run before each batch)
- Authentication methods
- Least-privilege permissions (read-only)

## Broad discovery queries
1. Primary query (by tag/label)
2. Fallback queries (all projected; no whole-object output)

## Scoping mechanisms
- How to narrow results (tag filter, region, resource type, etc.)

## Result parsing
- How to map API output to resource hints (name, type, context, owner)
````

A template may omit any non-frontmatter section if it doesn't apply (the skill treats omission as "unknown for this dimension, ask the operator").

## Shipped templates

| Template | Provider | Discovery API | Notes |
|----------|----------|---------------|-------|
| [`aws.md`](aws.md) | AWS | Resource Groups Tagging API, AWS Config | Tag scoping, regional; global services in `us-east-1` |
| [`kubernetes.md`](kubernetes.md) | Kubernetes (any host) | kubectl + Helm | Label/namespace scoping; orthogonal to where the cluster runs |
