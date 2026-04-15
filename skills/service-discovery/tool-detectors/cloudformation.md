---
name: cloudformation
url: https://aws.amazon.com/cloudformation/
deploys: AWS resources via CloudFormation templates (covers AWS SAM)
---

## File signatures
- `*.yaml` / `*.yml` with top-level `AWSTemplateFormatVersion:` or `Resources:`
- `*.json` with top-level `"AWSTemplateFormatVersion"` or `"Resources"`
- `template.yaml` / `template.yml` (SAM convention)
- `samconfig.toml` (SAM CLI configuration)

## Stack boundary
One stack = one template file (`template.yaml`, `template.json`, or any `*.yaml`/`*.json` with `AWSTemplateFormatVersion`).

Multi-instance is expressed via:
- the `Parameters:` block with values supplied by `--parameters` / `--parameter-overrides`
- separate parameter files passed via `--parameter-overrides file://...`
- per-stage configurations in `samconfig.toml` (`[<stage>.deploy.parameters]`)

## Parameter sources (highest to lowest priority)
- `--parameter-overrides Key=Value` on the CLI
- Parameter files passed via `--parameter-overrides file://path/params.json`
- `samconfig.toml` per-stage `parameter_overrides`
- `Parameters:` block default values
- `Fn::ImportValue` from another stack's exported `Outputs` (cross-stack — record as dependency, do NOT chase)
- AWS Systems Manager Parameter Store lookups via `{{resolve:ssm:...}}` (record as runtime reference)
- AWS Secrets Manager lookups via `{{resolve:secretsmanager:...}}` (record reference, NEVER read)

## Resource extraction
- Each entry under `Resources:` → one inventory entry; raw type is the AWS resource type (e.g., `AWS::ECS::Service`, `AWS::S3::Bucket`, `AWS::Lambda::Function`)
- SAM transforms (`AWS::Serverless::Function`, `AWS::Serverless::Api`, etc.) → expand mentally to the underlying CloudFormation resources, but record the SAM type as the raw type
- `Outputs:` with `Export:` → declares a cross-stack export; record the export name
- `Conditions:` referenced by `Condition:` on resources → conditional resource (resolve the condition for the target instance)

## Naming pattern hints
CloudFormation does not enforce a naming convention. If `Name:` properties use `!Sub` with a recurring template (e.g., `!Sub "${Service}-${Env}-${AWS::Region}"`), present that as the inferred pattern.

## Typical cross-stack dependencies
- Other CloudFormation stacks via `Fn::ImportValue` / `Outputs.Export`
- SSM Parameter Store / Secrets Manager via `{{resolve:...}}` references
- IAM roles / KMS keys referenced by ARN
