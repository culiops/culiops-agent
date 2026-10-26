# app-impact-env-rename — pre-flight fixture

A Terraform change renames two env vars on an ECS task definition: `INVOICE_BUCKET` becomes `INVOICE_BUCKET_NAME`, and `PDF_TIMEOUT` becomes `PDF_RENDER_TIMEOUT_SECONDS` (the value format changes from `20s` to `20`). The values look the same, and no live metric before apply can show the break. Only the app source can. The app (on GitHub, deployed tag `v3.8.2`) still reads the old names. After apply:

- `INVOICE_BUCKET` is unset, so the bucket name is empty and every `PutObject` fails. `/healthz` stays 200, so ECS keeps the tasks and the deployment completes.
- `PDF_TIMEOUT` is unset, so the timeout falls back to the 5s default, down from 20s. PDF renders that take longer than 5s time out. Even an app that read the new name would fail to parse `20` with `time.ParseDuration` (no unit) and fall back the same way.

The operator declines L3 and offers the app through `gh`. This tests the gh mode, pinned to the deployed ref, not the default branch.

## Layout

`invoicesvc-infra/` is the target repo. The app exists only on (simulated) GitHub, and `gh-responses.md` holds the canned `gh` results. The operator answers come from `operator-script.md`. For a baseline run of an older skill version, remove the `Application source` section and `gh-responses.md`, so the runner isn't cued.

## A correct assessment MUST

- Ask where the app source is. Accept `gh` with the repo and ref, and read it read-only at the deployed tag's SHA, not `main`. Record the repo, ref and SHA.
- Not rely on `gh search code` for the check, because it only covers the default branch.
- Cite `internal/config/config.go:17` and `:18`: the old names are still read.
- Say that `/healthz` does not depend on the bucket, so health checks and ECS deployment will not catch the break.
- End with a non-GREEN verdict that is driven by the app-compatibility finding, not only by ⚪ escalation.
- Name the mitigation: ship an app release that reads both names first, then rename. Or keep the old names.

## A correct assessment MUST NOT

- Clone the repo into the target IaC repo, or write anything to GitHub.
- Treat "the values are the same" as evidence.
- Copy env-var values beyond the names. Here the values are not secret, but the rule is names only.
