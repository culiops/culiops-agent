
# Tool Detectors

Each file in this directory describes one infrastructure-as-code or deploy tool that the `service-discovery` skill knows how to recognize. The skill loads every `*.md` file here at the start of Step 1 (Detect IaC tool(s)).

Adding support for a new tool is a data change: drop a new `<tool>.md` file in this directory following the template below. No `SKILL.md` edit required.

## Detector file template

````markdown
---
name: <tool-name>
url: <upstream URL or homepage>
deploys: <one-line description of what this tool deploys>
---

## File signatures
- <list of file patterns and/or top-level-key signals that identify this tool>

## Stack boundary
<one paragraph: what counts as one "stack" / deploy unit for this tool, and how multi-instance is expressed>

## Parameter sources (highest to lowest priority)
- <list of sources the tool consults to resolve parameter values for a given instance>

## Resource extraction
- <list of mappings from this tool's config keys to cloud-resource equivalents>

## Naming pattern hints
<one paragraph: what naming convention or template (if any) this tool encourages or enforces>

## Typical cross-stack dependencies
- <list of upstream stack types this tool commonly references>
````

A detector may omit any non-frontmatter section if it doesn't apply (the skill treats omission as "unknown for this dimension, ask the human").

## Shipped detectors

| Detector | Deploys | Notes |
|----------|---------|-------|
| [`terraform.md`](terraform.md) | Multi-cloud and on-prem infrastructure | Covers Terragrunt-on-Terraform |
| [`cloudformation.md`](cloudformation.md) | AWS resources | Covers AWS SAM |
| [`pulumi.md`](pulumi.md) | Multi-cloud infrastructure (general-purpose languages) | |
| [`bicep.md`](bicep.md) | Azure resources | Compiles to ARM |
| [`helm.md`](helm.md) | Kubernetes resources via templated charts | |
| [`kustomize.md`](kustomize.md) | Kubernetes resources via overlays | |
| [`jsonnet.md`](jsonnet.md) | (preprocessor only) | Always paired with a consuming tool |
| [`ansible.md`](ansible.md) | Cloud and on-prem via playbooks | |
| [`ecspresso.md`](ecspresso.md) | AWS ECS services and task definitions | |
| [`lambroll.md`](lambroll.md) | AWS Lambda functions | |
