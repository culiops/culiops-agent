# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.

## Rows

`<…>` in a pattern is a parameter: the value comes from an earlier output, and the row's table (below the main table) gives the file for each value.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … `arn:aws:sts::*` | `iam-03.txt` | Exit status 254. |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `kubectl config current-context` | `k8s-01.txt` | |
| `kubectl auth whoami` | `k8s-02.txt` | |
| `kubectl auth can-i --list` … | `k8s-03.txt` | |
| `kubectl get pods` … `payments` | `k8s-04.txt` | |
| `kubectl get events` … `payments` … `-o json` (or `-o yaml`) | `k8s-06.json` | |
| `kubectl get events` … `payments` | `k8s-05.txt` | Ages are relative to 11:28:00 UTC. |
| `kubectl describe pod` … `payments-worker` (any of the pods in `k8s-04.txt`) | `k8s-07.txt` | Same content for each pod apart from its name. |
| `kubectl describe deploy` … `payments-worker` | `k8s-14.txt` | |
| `kubectl logs` … `payments-worker` … `--previous` (or `-p`) | `k8s-08.txt` | Any of the pods, or `deploy/payments-worker`. |
| `kubectl logs` … `payments-worker` | `_empty.txt` | |
| `kubectl get deploy` … `payments` | `k8s-12.txt` | |
| `kubectl rollout history` … `payments-worker` | `k8s-10.txt` | |
| `kubectl get rs` … `payments` | `k8s-11.txt` | |
| `kubectl get configmap` … `<name from k8s-13.txt or k8s-07.txt>` | table P1 | `-o json` gets the same content as JSON. |
| `kubectl get configmap` … `payments` … `-o yaml` (or `-o json`), no name | `k8s-16.yaml` | |
| `kubectl get configmap` … `payments` | `k8s-13.txt` | |
| `helm list` … | `helm-03.txt` | |
| `helm history payments-worker` … | `helm-01.txt` | |
| `helm get values payments-worker` … | `helm-02.yaml` | |
| `git -C ~/src/payments-deploy log` … | `git-01.txt` | Any range or path filter that includes these commits. |
| `git -C ~/src/payments-deploy show` … `<commit from git-01.txt>` (or `diff <commit>^ <commit>`) | table P2 | |
| `git -C ~/src/payments-deploy diff` … (a range covering both commits) | `git-03.txt` then `git-02.txt` | Concatenate, oldest first; path filters keep the matching file sections. |
| `aws sqs list-queues` … | `sqs-01.json` | |
| `aws cloudwatch get-metric-data` (or `get-metric-statistics`) … `AWS/SQS` … `ApproximateNumberOfMessagesVisible` … `<queue name from sqs-01.json>` | table P3 | Period 300. Covers 2026-10-24 10:30–11:25 UTC. |

**P1 — ConfigMap by name**

| Name | File |
|---|---|
| `kube-root-ca.crt` | `k8s-15.yaml` |
| `payments-worker-config` | `k8s-09.yaml` |

**P2 — commit**

| Commit | File |
|---|---|
| `d81e4b7` | `git-02.txt` |
| `27c4e91` | `git-03.txt` |

**P3 — SQS queue**

| Queue | File |
|---|---|
| `payments-jobs` | `cw-01.json` |
| `payments-jobs-dlq` | `cw-02.json` |
