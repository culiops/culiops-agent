# repo-cfn-recognition — recognition-only tools fixture

A synthetic repo whose only IaC is two tools the skill **recognises but does not support**: an AWS SAM template and a Serverless Framework config. Nothing is runnable.

## What's modelled

- `template.yaml` — a SAM app (`Transform: AWS::Serverless-2016-10-31`): one `AWS::Serverless::Function` (`thumbnailer-${Stage}`) and one `AWS::DynamoDB::Table` (`thumbnailer-${Stage}-items`). It states no stack name.
- `serverless.yml` — a Serverless Framework service `report-exporter` (`provider: aws`, one scheduled function `export`).
- `src/app.py`, `handler.js` — placeholder function code.

Both deploy through CloudFormation, so the live resources carry the `aws:cloudformation:stack-name` tag.

## What this fixture exercises in the skill

- **Recognition, not support:** `tool-detectors/cloudformation.md` matches both files (SAM transform; Serverless `provider:` + `functions:`). The skill lists the stacks, says plainly that these tools are not supported, and stops the IaC path for them.
- **No "teach me":** the files are attributed to a detector, so the unclassified-deploy-artifacts escape hatch does not fire, and the operator is never offered "teach me" for them.
- **No inventory from the templates:** the skill does not read `Resources:`, resolve `!Ref` / `!Sub`, or resolve the `Stage` parameter.
- **Real-discovery offer:** a repo with only recognition-only tools is offered real-discovery against live AWS; the owner of each discovered resource is read from the `aws:cloudformation:stack-name` tag where present and shown as `cloudformation (<stack>)` (otherwise `unknown`). Seed A starts empty; the operator supplies the service tag at the query gate.
