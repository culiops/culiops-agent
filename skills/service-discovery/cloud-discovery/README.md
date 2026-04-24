
# Cloud Discovery Query Templates

Each file in this directory describes broad discovery API queries for one cloud provider. The `service-discovery` skill reads these templates during Step 4 (Converging Discovery) of the real-discovery path to find resources across an entire cloud account/project/subscription that relate to a given service name — before drilling into per-resource-type detail.

Adding support for a new provider is a data change: drop a new `<provider>.md` file in this directory following the template below. No `SKILL.md` edit required.

## Relationship to the `examples/` directory

These two directories serve different purposes:

- **`cloud-discovery/`** (this directory) contains **broad, cross-resource-type** queries used early in real-discovery to *find* which resources exist. The queries here search by tag, label, name prefix, or resource graph — they cast a wide net and return resource hints (name, type, location).
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
- Authentication methods
- Least-privilege permissions (read-only)

## Broad discovery queries
1. Primary query (by tag/label)
2. Fallback queries (by name prefix, resource graph, etc.)

## Scoping mechanisms
- How to narrow results (tag filter, region, resource type, etc.)

## Result parsing
- How to map API output to resource hints (name, type, context)
````

A template may omit any non-frontmatter section if it doesn't apply (the skill treats omission as "unknown for this dimension, ask the operator").

## Shipped templates

(Updated once all templates are in place.)
