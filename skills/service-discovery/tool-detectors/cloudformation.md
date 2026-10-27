---
name: cloudformation
url: https://aws.amazon.com/cloudformation/
deploys: AWS resources via CloudFormation, SAM, Serverless Framework or CDK (recognition only)
---

## File signatures
- **CloudFormation**: `*.yaml` / `*.yml` / `*.json` with `AWSTemplateFormatVersion`, or a top-level `Resources:` whose entries have `Type: AWS::...`
- **SAM**: a template with `Transform: AWS::Serverless-2016-10-31`; `samconfig.toml`
- **Serverless Framework**: `serverless.yml` / `serverless.yaml` / `serverless.ts` / `serverless.js` with `provider:` plus `functions:` or `service:`
- **CDK**: `cdk.json`. Ignore generated `cdk.out/**` (synthesized templates are output, not source)

## Support level: recognition only
List the stacks found (tool, file path, and stack/service name when the file states one), tell the operator these tools are not supported, and stop the IaC path for them. Do NOT extract resources, resolve parameters, or offer "teach me" — improvised support for an unsupported tool produces a catalog nobody has validated.

## Offer: real-discovery against live AWS
For the resources these stacks own, offer real-discovery (supported, live AWS). Ownership is read from the `aws:cloudformation:stack-name` tag (SAM, Serverless and CDK all deploy through CloudFormation); record it as `Owner: cloudformation (<stack>)` where the tag is present (propagation varies by resource type, so an untagged resource is `unknown`, not proof of another owner). A repo containing only these tools goes straight to this offer.

## Pre-import ownership check (read-only)
Used so no skill imports or modifies a resource a stack owns. Run only after the operator approves the batch:

```
aws cloudformation describe-stack-resources --stack-name <s> --profile {profile} --region {region} \
  --query 'StackResources[].{Logical:LogicalResourceId,Physical:PhysicalResourceId,Type:ResourceType}'
```

and check the tag on the candidate resource (`aws:cloudformation:stack-name`, `aws:cloudformation:logical-id`). If the resource appears in a stack, it is stack-owned: report the owner and do not import or modify it.
