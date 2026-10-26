# Dry-run of `service-discovery` against `repo-cfn-recognition`

Simulated run of Step 1 and the real-discovery hand-off against this fixture, 2026-10-26.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Recognise, don't improvise (Constraint 8) | `template.yaml` (SAM) and `serverless.yml` matched by `tool-detectors/cloudformation.md`, listed, declared unsupported |
| IaC path stops for recognition-only stacks | No parameters resolved, no inventory, no dependency graph, no runbooks from the templates |
| Escape hatch does not fire | `serverless.yml` has deploy-shape keys (`service:`, `provider:`, `functions:`) but is attributed to a detector, so it is not "unclassified"; `template.yaml` likewise |
| No "teach me" | The prompt offers real-discovery or stop; it never offers `teach me` for a recognised unsupported tool |
| Real-discovery against live AWS | Offered because the repo contains only recognition-only tools; owner from `aws:cloudformation:stack-name` |

## Step-by-step simulation

### Step 1: Detection

**Detector scan:** `cloudformation.md` is the only match. No supported tool (Terraform, Helm, Kustomize, raw manifests, ecspresso, lambroll) and no document signatures. Only top-level keys are read to recognise the tool; `Resources:` entries are not parsed.

**Presentation:**

> "I found infrastructure-as-code for tools I recognise but do not support:
>
> | Tool | File | Stack / service name |
> |------|------|----------------------|
> | AWS SAM (CloudFormation) | `template.yaml` | not stated in the file (the stack name is set at deploy time) |
> | Serverless Framework | `serverless.yml` | service `report-exporter` |
>
> These are **not supported**: I won't build a resource inventory from them, and I won't improvise support. This stops the IaC path for these stacks.
>
> What I can do instead is **real-infrastructure discovery against live AWS** (supported): I find the resources these stacks deployed with read-only queries and show each resource's owner from its `aws:cloudformation:stack-name` tag, e.g. `cloudformation (<stack>)`.
>
> **GATE: Run real-discovery against live AWS, or stop?**"

No `teach me` / `ignore` options are shown.

**Operator response:** real-discovery, service `thumbnailer`. *(Gate 1)*

### Hand-off to the real-discovery path

- **Seed A (hints):** no documents in the repo; the operator names the CloudFormation stack: `thumbnailer-prod`. The names inside `template.yaml` are not parsed into hints.
- **Probe batch (shown and approved first):** `aws sts get-caller-identity --profile thumb-ro --query Account --output text`, `aws configure get region --profile thumb-ro` → account `123456789012`, region `us-east-1`; confirmed at the environment gate.
- **Queries (approved at the query gate):**

  | # | Query (profile `thumb-ro`, `--region us-east-1`) | Scope |
  |---|--------------------------------------------------|-------|
  | 1 | `aws cloudformation describe-stack-resources --stack-name thumbnailer-prod --query 'StackResources[].{Logical:LogicalResourceId,Physical:PhysicalResourceId,Type:ResourceType}'` | resources the stack owns |
  | 2 | `aws resourcegroupstaggingapi get-resources --tag-filters Key=aws:cloudformation:stack-name,Values=thumbnailer-prod --query 'ResourceTagMappingList[].ResourceARN'` | cross-check by tag |

- **Results:** `thumbnailer-prod` (Lambda function), `thumbnailer-prod-items` (DynamoDB table), the generated execution role `thumbnailer-prod-ThumbnailFunctionRole-…` (IAM, found by query 1 only; IAM is global and not reliably visible to the regional Tagging API, so its class is `not-queryable (global or untagged)` for query 2, not "absent").
- **Membership signal:** stack ownership (query 1) plus the `aws:cloudformation:stack-name` tag. All three rows are `Owner: cloudformation (thumbnailer-prod)`, Medium confidence (cloud only, no document).

## What a produced doc would look like

`.culiops/service-discovery/thumbnailer-prod.md` (real-discovery format):

- Header: discovery source=real-discovery, cloud context=AWS / `123456789012` / `us-east-1`, documents used=none.
- `## Resource Inventory`: 3 rows, each `Owner: cloudformation (thumbnailer-prod)`.
- `## Assumptions and Caveats`: "The repo's SAM template and Serverless config are recognised but unsupported and were not parsed; the stack `report-exporter` was not catalogued"; stack ownership read from tags only; no drift check against the template.

## Acceptance checks

1. Both files are listed with tool, path and stack/service name (or "not stated"); each is labelled **not supported**.
2. The IaC path stops: no resolved parameters (`Stage` is not resolved), no inventory rows from `Resources:`, no `!Ref` / `!Sub` resolution, no dependency graph from the templates.
3. The prompt contains no `teach me` option. If the operator asks for it ("just read serverless.yml"), the skill declines and repeats the real-discovery offer (Constraint 8).
4. The escape-hatch prompt ("I see these files that look like deploy descriptors") does not appear.
5. Real-discovery is offered for live AWS, and every discovered resource shows `Owner: cloudformation (<stack>)` from the `aws:cloudformation:stack-name` tag.
6. If the operator declines real-discovery, the skill stops with no catalog written and no commit.
7. No `sam`, `sam build`, `serverless`, `cdk synth` or `aws cloudformation get-template` is run; `aws cloudformation describe-stack-resources` is run only after batch approval and is projected.
8. No inventory is built from the templates: nothing in the catalog is sourced from `template.yaml` or `serverless.yml`.
