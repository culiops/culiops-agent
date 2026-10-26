# Application source — read recipes (pre-flight Step 3b)

Read-only reads of the application code, used for category 11 (application compatibility). Two equal modes. The operator picks one at Q8. Many employers don't approve a GitHub token for `gh`, so the local mode is never a fallback of lower standing.

Both modes:
- **Pin the deployed version.** Resolve what is actually running to a commit SHA. Where it comes from: the image tag in the task definition / Deployment (`code:` or `live:`), a release tag the operator names, or a SHA. If none can be confirmed, read the closest ref the operator names and record `deployed version unverified`.
- **Never** clone into the target repo, write to the app repo, push, comment, open issues, or build / test / run app code.
- **Cite** `app:<repo>@<short-sha>:<path:line>`. Quote only the line that uses the attribute. Config files in app repos can hold secrets: never copy a value.
- Searching text finds literal uses only. Names built at runtime (`os.Getenv(prefix + "_URL")`), reflection-based config loaders (struct tags, `envconfig`, Spring `@Value`), and other services that use the same contract are easy to miss. Search for the config loader too, and say what the search could not see.

## Mode A — local checkout

Prerequisites: a checkout on disk. No token, no network.

```bash
git -C <path> rev-parse HEAD                 # SHA being read
git -C <path> status --porcelain             # dirty tree → note it
git -C <path> describe --tags --always       # compare with the deployed ref
git -C <path> rev-parse <deployed-ref>       # does the deployed ref exist here? (no fetch)
```

If HEAD is not the deployed ref and the tree is clean, read the deployed version without checking it out:

```bash
git -C <path> grep -n -e '<OLD_NAME>' -e '<NEW_NAME>' <deployed-ref> -- .
git -C <path> show <deployed-ref>:<file>
```

Otherwise search the working tree, skipping vendored and generated code:

```bash
grep -rn --exclude-dir={.git,node_modules,vendor,dist,build,target} -e '<OLD_NAME>' -e '<NEW_NAME>' <path>
```

Don't `git fetch`, `git checkout` or `git stash` in the operator's checkout. Those change their working state.

## Mode B — GitHub through `gh`

Prerequisites: `gh` logged in with read access to the repo. The least privilege is a fine-grained token with **Contents: read** and **Metadata: read** on that repo only. Never ask for a broader token "for pre-flight".

Choosing `gh` at Q8 approves exactly these four `GET` read types — no second prompt. A clone or any other endpoint needs its own approval:

```bash
gh auth status
gh api repos/<owner>/<repo>/commits/<deployed-ref> --jq .sha                         # pin the SHA
gh api "repos/<owner>/<repo>/git/trees/<sha>?recursive=1" \
  --jq '.truncated, (.tree[] | select(.type=="blob") | .path)'                       # file list at that SHA
gh api "repos/<owner>/<repo>/contents/<path>?ref=<sha>" \
  -H 'Accept: application/vnd.github.raw'                                            # one file, raw text
```

How to search:
1. From the tree, pick candidate files: source files for the app's language, config loaders, the files that construct SDK clients, the health-check handler, the dependency lockfile.
2. Fetch them at the pinned SHA and search the text in memory. If there are too many to read through the API, write them to a temporary directory **outside the target repo** and delete it at the end of the run.
3. `truncated: true` in the tree response, or a repo too large to read file by file → offer Mode A, or a shallow clone into a temporary directory outside the target repo (`gh repo clone <owner>/<repo> <tmp> -- --depth 1 --branch <tag>`), deleted at the end of the run.

Don't use `gh search code` as evidence of "no use". GitHub code search covers the default branch only, can lag, and skips some files. At most it can suggest where to look.

Rate limits: authenticated REST calls have an hourly quota (`gh api rate_limit --jq .resources.core`). A typical scan is tens of calls.

If `gh` is not logged in, the token lacks access, or the employer doesn't allow a token: say so, offer Mode A once, else category 11 is ⚪ with the reason.

## What to look for, per attribute

| Changed attribute | Search for | Read at each hit |
|---|---|---|
| Removed IAM action | the SDK operation name (`SendMessage`, `PutObject`, `Publish`, `GetSecretValue`), the resource name / ARN, the env var that carries it | what the caller does on error: return / crash / retry / log-and-continue |
| Renamed / removed env var or config key | old name, new name, the config loader | default value when unset; how the value is parsed (`20` vs `20s`) |
| Endpoint / port / path | hostname, port, path literals; service-discovery names | whether the client takes it from config or hard-codes it |
| Engine / runtime version | the driver / client version in the lockfile | the driver's supported-server matrix (vendor docs, cited) |
| Timeouts / limits | processing loops, pool sizes, client timeouts | whether the app's own timeout or pool fits inside the new limit |
| Health check | the handler the probe / target group calls | whether it exercises the dependency that breaks |
