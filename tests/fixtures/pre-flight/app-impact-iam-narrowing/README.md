# app-impact-iam-narrowing — pre-flight fixture

A Terraform change that removes an IAM statement from an ECS task role. Seen from the infra side, it is a security improvement: least privilege, nothing destroyed, the service is healthy. Seen from the app, it is an outage that no health signal will show. The app still calls `sqs:SendMessage` on every checkout and logs the failure as a non-fatal warning. Checkouts keep returning 201 while finance ledger entries are silently lost.

## What's modelled

`cartapi`: a fictional ECS Fargate HTTP service in `eu-west-1` (account `111122223333`). There are two repos:
- `cartapi-infra/` is the target repo. Its `infra/` files show the code after the change.
- `cartapi-app/` stands for a **separate** application checkout. Commit it as a git repo with a tag before a run, so Mode A has a SHA to pin.

When the app code sits inside the IaC repo, the skill finds it without being asked. A separate repo is the case category 11 exists for.

## The proposed change

`plan-output.txt`: one in-place update to `aws_iam_role_policy.cartapi_task_publish`. It drops the `AllowSQSSendLedger` statement (`sqs:SendMessage` on `cartapi-ledger.fifo`) and keeps `sns:Publish`.

## Ground truth

- `cartapi-app/cmd/cartapi/main.go` calls `sqs.SendMessage` with the URL from `LEDGER_QUEUE_URL`. That env var is still set in `cartapi-infra/infra/ecs.tf`.
- The error is logged as `WARN … (non-fatal)` and the request still returns 201. So the ALB 5xx rate, ECS health and the alarms all stay green after apply.
- Live: the ledger queue receives about 1,150 messages per day, and IAM last-accessed shows `sqs` used today.

## A correct assessment MUST

- Ask where the application source is (Q8), and read it in local mode at a pinned SHA.

- Say the app still calls `sqs:SendMessage` on the ledger queue, citing the app source file and line.
- Say the failure is silent: logged as non-fatal, invisible to 5xx / health / alarms. So resource health being Green does not clear this.
- Not score this change as safe because it narrows privilege. Narrowing IAM scores Green on security posture, but that Green says nothing about breakage. It is Green only because the full before and after policy documents were compared: the plan alone hides an attribute (`# (1 unchanged attribute hidden)`).
- End with a verdict that is not GREEN, and name the mitigation: keep the statement, or change the app first and then remove it.

## A correct assessment MUST NOT

- Treat the operator's "I don't think it's used" as evidence.
- Copy env-var values into the record.
- Write anything into `cartapi-app/` or `cartapi-infra/`.

## Running it

Target repo: `cartapi-infra/`. The operator answers come from `operator-script.md` and the live results from `live-responses.md`. For a baseline run of an older skill version, remove the `Application source` section from the operator script first, so the runner isn't cued to ask.
