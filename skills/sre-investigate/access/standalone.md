# Access and credentials (standalone)

Phase 0 reads this file before any backend is queried. It has six sections, in order: which mode the run is in, who the run is authenticated as, whether AWS credentials could change anything, the same question for Kubernetes, how each backend gets its token, and how a failing backend is recorded. The ledger and report it mentions are defined in SKILL.md (the ledger is `ledger.md` in the run directory); a person checking access by hand needs only the commands under Mode detection, Identity and the two write-check sections.

Everything here is read-only. The only commands that touch IAM are simulations and describe/get/list calls. No write API is ever called to find out whether a write would work.

## Where `environment.md` lives

`environment.md` holds the per-organisation facts this file refers to: profiles, contexts, datasources, token variable names, budgets. It is copied once per repo from [`../environment.template.md`](../environment.template.md) into the output root and filled in by the operator. Never write the filled-in file back into the skill directory.

- **Location.** `<output root>/environment.md`. The output root and its rules (the `CULIOPS_HOME` override, creation, never committed) are set in SKILL.md and match change-comms constraint 19; this file does not restate them.
- **Missing file.** If `environment.md` does not exist yet, offer to copy the template and stop until the operator has filled it in. A run with no timezone, profiles or datasources is a run of guesses.

## Mode detection

Run once, first:

```bash
command -v agentbox-env
```

- **It succeeds.** Print exactly this line, then run as standalone:

  ```text
  Culibox detected; Culibox integration is not available yet (culiops-skills #38). Running as standalone, so tokens that are not in env vars will be recorded as gaps.
  ```

  Do not call `agentbox-env`, do not read what it would provide, and do not change any behaviour below because it is present.
- **It fails.** Run as standalone and print nothing about Culibox.

Standalone means every credential comes from the operator's own shell: AWS profiles, kubeconfig contexts and environment variables. Nothing is fetched on the operator's behalf.

## Identity

Establish who the run is before it queries anything. One call per profile or context the run will use, all in the first wave of commands (a wave is a batch of read-only commands shown together and run together; SKILL.md defines it).

**AWS, per profile listed in `environment.md`:**

```bash
aws sts get-caller-identity --profile <profile>
```

<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html -->

The reply carries `Account`, `UserId` and `Arn`. Check the account against the `account` recorded for that profile. A mismatch is a stop-and-ask, not a gap: the profile points somewhere the operator did not intend. This call needs no IAM permission, so a failure means the credentials themselves are not usable.

**An expired or missing session.** A failure that mentions an expired token, an SSO session, or no credentials marks that profile as a gap. Record the exact fix for the operator and keep going on the other profiles:

```text
! aws sso login --profile <profile>
```

<!-- doc: https://docs.aws.amazon.com/sdkref/latest/guide/access-sso.html -->

Do not run the login yourself and do not retry in a loop. Findings that depended on that profile are downgraded until the operator signs in and the call succeeds.

**Kubernetes, per context listed in `environment.md`:**

```bash
kubectl auth whoami --context <context>
kubectl config current-context
```

<!-- doc: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_whoami/ -->

`kubectl auth whoami` is marked experimental in the kubectl reference and is absent from older clients and clusters. If it fails with an unknown-command or not-found error, record the user as unverified. `kubectl config current-context` names the current context only, so use it as the fallback just when `<context>` is the current one; for any other context, record only that the context exists. Any other failure (unauthorised, unreachable cluster, expired exec credential) makes that context a gap.

Record every identity in the ledger as profile or context, account or cluster, and the principal's role name. Never record the session name part of an assumed-role ARN; it can carry a person's identifier.

## AWS write-check

Purpose: tell the operator, early, when the credentials they handed this run could change the account. The run itself stays read-only either way. The check uses IAM policy simulation, which evaluates policies and performs none of the simulated actions.

<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-principal-policy.html -->

### 1. Resolve the principal

Simulation needs the ARN of the IAM role or user, not the ARN of the session. Take the `Arn` from `get-caller-identity` and branch on its shape:

| Caller ARN shape | Principal for the simulation |
|---|---|
| `arn:<partition>:sts::<account>:assumed-role/<role>/<session>` | The role. Resolve it with `get-role`, below. |
| `arn:<partition>:iam::<account>:user/<path><name>` | The ARN as returned. |
| `arn:<partition>:iam::<account>:root` | Not simulated. Root is write-capable by definition: show the warning and name root as the reason. |
| Anything else (federated user, unfamiliar shape) | Not simulated. Record "write capability unknown (gap)" with the shape in words. |

The assumed-role ARN carries only the role name. The role's path is not in it, and the path is part of the role's own ARN, so the role ARN cannot be assembled by substituting `iam` for `sts`. Take the name and ask IAM for the full ARN:

```bash
arn=$(aws sts get-caller-identity --profile <profile> --query Arn --output text)
role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile <profile> --role-name "$role" --query Role.Arn --output text)
```

<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/iam/get-role.html -->

For roles created from an IAM Identity Center permission set, the role name starts with `AWSReservedSSO_` and its path is `/aws-reserved/sso.amazonaws.com/`, followed by a region segment when the identity source is hosted outside us-east-1. That is why a hand-built ARN fails for these roles and `get-role` is used.

<!-- doc: https://docs.aws.amazon.com/singlesignon/latest/userguide/referencingpermissionsets.html -->

If `get-role` itself is denied, the principal cannot be resolved: treat it as a denied simulation (section 3) and say the reason is the resolution step.

### 2. Simulate the fixed write list

The list is fixed at ten actions, broad enough to cover storage, compute, network, container, identity, database, function and stack changes. Do not extend it per run and do not shorten it:

`s3:PutObject`, `s3:DeleteObject`, `ec2:TerminateInstances`, `ec2:AuthorizeSecurityGroupIngress`, `ecs:UpdateService`, `iam:PutRolePolicy`, `iam:CreateAccessKey`, `rds:ModifyDBInstance`, `lambda:UpdateFunctionCode`, `cloudformation:DeleteStack`

```bash
aws iam simulate-principal-policy --profile <profile> \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
```

`EvalDecision` is one of `allowed`, `explicitDeny` or `implicitDeny`. Only `allowed` makes an action write-capable. One reply row per action is expected; a missing action or any other word is a gap for that action.

What the result does and does not prove:

- The simulator evaluates identity policies and service control policies against the inputs given. Its own documentation says results can differ from the live environment.
- No resource ARN is passed, so each action is evaluated against any resource. A role allowed to write only to one named bucket can read as `implicitDeny` here. "No listed action allowed" therefore reads "no broad write found", never "proven read-only".
- Session policies and some resource-side policies are not part of this view.

### 3. Report the outcome

There are three outcomes. Use the wording below, then continue to the next profile; none of them stops the run.

**Any action `allowed`: the boxed warning.** Print it as is, filling the brackets, then continue:

```text
+------------------------------------------------------------------+
| WARNING: WRITE-CAPABLE CREDENTIALS                               |
| Profile: <profile>   Account: <account>   Role: <role name>      |
| Simulation allows: <action>, <action>, ...                       |
|                                                                  |
| This investigation is read-only and will not use these           |
| permissions, but the credentials could change the account.       |
| Use a read-only role (ReadOnlyAccess or tighter) for incident    |
| work, or Culibox when it is available. Continuing.               |
+------------------------------------------------------------------+
```

Name only the allowed actions. Never include the role ARN or the session name in the box.

**No action allowed: "read-only confirmed", with its limit.**

```text
Write check, <profile>: read-only confirmed (simulation): none of the 10 broad write actions is allowed. This is not a full proof; resource-scoped writes are not covered.
```

**The simulation, or the role lookup it needs, is denied: informational notice, never the warning.**

```text
Write capability unknown (gap), <profile>: iam:SimulatePrincipalPolicy was not permitted, so write access could not be checked. This is not a finding that the credentials can write.
```

Record the same sentence as a gap in the ledger, then apply the fallback order.

### Fallback order when the simulation is denied

Stop at the first step that yields an answer. Each step is read-only, and none replaces the notice above: the gap stays in the ledger and the answer is added next to it.

1. **List the attached policies.** For an assumed role, use the role name from the caller ARN. For an IAM user principal, use `aws iam list-attached-user-policies --user-name <name>` (and `list-groups-for-user` for group policies) in the same way, or skip to step 2.

   ```bash
   aws iam list-attached-role-policies --profile <profile> --role-name "$role" --query 'AttachedPolicies[].PolicyName' --output text
   ```

   <!-- doc: https://docs.aws.amazon.com/cli/latest/reference/iam/list-attached-role-policies.html -->

   If the call is allowed and every attached policy is a read-oriented AWS managed one (`ReadOnlyAccess`, `ViewOnlyAccess`, `SecurityAudit`), record "likely read-only; inline policies, permission boundary and SCPs not checked". Any other attached policy name is shown to the operator as an unknown, not judged.
2. **Name the role and ask.** Show the role name and account, and ask the operator to confirm in chat that it is a read-only role. Record the answer as `operator-asserted`, not as verified.
3. **No answer.** Leave the gap open and continue. The run is no less read-only; the operator just has not been given a check on the role.

Never probe with a real write, never run a dry-run form of a write call, and never infer "read-only" from a role's name alone.

## Kubernetes write-check

For each context the run uses, list what the identity may do in every namespace named for that context in `environment.md`. When none is named, use the namespace of the current context and say so.

```bash
kubectl auth can-i --list --context <context> --namespace <namespace>
```

<!-- doc: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/ -->

The output is a table with the columns `Resources`, `Non-Resource URLs`, `Resource Names` and `Verbs`. Verbs print in square brackets (for example `[get list watch]`), and resources print group-qualified where the group is not the core one (for example `deployments.apps`). Read the `Verbs` column row by row.

- **Write-capable:** any row whose verbs include `create`, `update`, `patch`, `delete`, `deletecollection` or the wildcard `*`, on any resource. Name the resources and verbs in the warning.
- **Not counted (exclusion list):** a row whose verbs are exactly `[create]` and whose resource is one of the access-review APIs that every authenticated user gets by default so that a person can ask what they may do: `selfsubjectaccessreviews`, `selfsubjectrulesreviews`, `selfsubjectreviews`. Match the resource name regardless of its API group suffix (`selfsubjectaccessreviews.authorization.k8s.io` and `selfsubjectreviews.authentication.k8s.io` both match). Any other `create`, and any row on these resources with additional verbs, counts as write-capable. A `create` on these three changes nothing in the cluster.

  <!-- doc: https://kubernetes.io/docs/reference/access-authn-authz/rbac/ -->
  <!-- verify: docs-only. The RBAC page says only that system:basic-user gives read-only access to basic information about oneself; it does not list the resources. Verify the list on the first real cluster with `kubectl get clusterrole system:basic-user -o yaml`. -->
- **Cluster-scoped rows** that show up in the namespaced list count the same way.
- **Possibly incomplete list.** With webhook authorizers, kubectl may print a notice that the rule list could be incomplete. Treat the result as "no write verbs seen; list may be incomplete", not as a confirmation.

When any write-capable row exists, print the same boxed warning, with the context and namespace in place of the profile and account, and the resources and verbs in place of the actions. Suggest a read-only binding (the built-in `view` ClusterRole, bound where the investigation needs it) or Culibox when it is available. Then continue.

```text
+------------------------------------------------------------------+
| WARNING: WRITE-CAPABLE CREDENTIALS                               |
| Context: <context>   Namespace: <namespace>                      |
| Allowed write verbs: <verb> on <resource>, ...                   |
|                                                                  |
| This investigation is read-only and will not use these           |
| permissions, but the credentials could change the cluster.       |
| Use a read-only binding (for example the view ClusterRole) for   |
| incident work, or Culibox when it is available. Continuing.      |
+------------------------------------------------------------------+
```

With no write-capable row, record "no write verbs in <namespace>" in the ledger. If `can-i --list` fails, or the cluster does not answer, print this informational notice and record it as a gap (it is not the warning):

```text
Write capability unknown (gap), <context>/<namespace>: kubectl auth can-i --list failed, so write access could not be checked. This is not a finding that the identity can write.
```

 The listing reflects RBAC as the API server evaluates it for this identity; it says nothing about admission rules.

## Tokens

Backends that authenticate with a token (Grafana, Prometheus, Loki, Tempo, Sentry, and any mapped vendor) are listed in the `datasources[]` table of `environment.md`. Each row names an environment variable, never a value.

Check presence of each listed `token_env` with `${VAR:+x}`, which expands to the single character `x` when the variable is set and non-empty, and to nothing otherwise. Write one line per variable name taken from `environment.md`, with the name typed literally:

```bash
[ -n "${<ENV_VAR_ONE>:+x}" ] && echo "<ENV_VAR_ONE>: set" || echo "<ENV_VAR_ONE>: unset"
[ -n "${<ENV_VAR_TWO>:+x}" ] && echo "<ENV_VAR_TWO>: set" || echo "<ENV_VAR_TWO>: unset"
```

Each line prints the name and `set` or `unset`, nothing else. Do not turn this into a loop with indirect expansion or `printenv`, and do not run it in a shell with tracing on (`set -x`, `bash -x`): the form is safe because the shell only ever sees `x`, and tracing a different form could print the value.

Rules that do not bend:

- **Names only.** The skill, the ledger, the report and every record hold variable names. A value is never echoed, written, logged, summarised or pasted into a command line.
- **Reference, don't expand in view.** Commands use `$VAR` so the shell substitutes it. Show the command with `$VAR` in it, never with the value substituted in.
- **No token files.** Never open a dotenv file, a credentials file, a kubeconfig's embedded token, the AWS shared credentials file or the SSO cache directory, even to check whether a token exists there. A token that is only in a file is a missing token.
- **Missing means gap.** A backend whose `token_env` is unset is recorded as a gap: name the variable the operator needs to export and which backend is blind without it. The run continues on the rest. Under standalone mode, nothing else can supply the token.
- **Unlisted means not used.** A backend that `environment.md` does not list is not queried, even if an environment variable for it happens to be set.

## Backend gaps

A gap is a source the run could not read. It is not an error to route around. Record each one the moment it appears:

| Field | Content |
|---|---|
| Backend | profile, context or datasource name |
| Cause | expired session, missing token, access denied, unreachable, unknown write capability |
| Fix | the exact command or variable for the operator, for example `! aws sso login --profile <profile>` or `export <ENV_VAR>=...` (name only) |
| Effect | which hypotheses or claims lose evidence because of it |

Behaviour that follows:

- **Continue on the rest.** One failing profile or token never ends the run while another source can still answer.
- **Downgrade, don't fill in.** A claim that needed the missing source can be at most `Assumed` and names the gap beside it. A silent absence is never read as "nothing there".
- **A block is a gap, not something to route around.** An `AccessDenied`, a 403 or a refused connection means the credential does not permit that read. Name the permission or token that is missing, ask for it, and do not try another route to the same data (another profile with more rights, a different tool, a copy of someone's token).
- **Gaps lead the report.** They appear in the ledger as they happen and again in the report's gap list, each with its fix, so that a reader knows what the conclusion could not see.
