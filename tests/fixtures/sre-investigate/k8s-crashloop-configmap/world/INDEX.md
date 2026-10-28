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

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `kubectl config current-context` | `k8s-01.txt` | |
| `kubectl auth whoami` | `k8s-02.txt` | |
| `kubectl auth can-i --list` … | `k8s-03.txt` | |
| `kubectl get pods` … `notify` | `k8s-04.txt` | |
| `kubectl get events` … `notify` … `-o json` (or `-o yaml`) | `k8s-06.json` | |
| `kubectl get events` … `notify` | `k8s-05.txt` | Ages are relative to 08:50:00 UTC. |
| `kubectl describe pod` … `notify-worker` (any of the pods in `k8s-04.txt`) | `k8s-07.txt` | Same content for each pod apart from its name. |
| `kubectl describe deploy` … `notify-worker` | `k8s-14.txt` | |
| `kubectl logs` … `notify-worker` … `--previous` (or `-p`) | `k8s-08.txt` | Any of the pods, or `deploy/notify-worker`. |
| `kubectl logs` … `notify-worker` | `_empty.txt` | |
| `kubectl get deploy` … `notify` | `k8s-12.txt` | |
| `kubectl rollout history` … `notify-worker` | `k8s-10.txt` | |
| `kubectl get rs` … `notify` | `k8s-11.txt` | |
| `kubectl get configmap` … `notify-worker-config` (or `get configmap -n notify` with `-o yaml`/`-o json`) | `k8s-09.yaml` | JSON requests get the same content as JSON. |
| `kubectl get configmap` … `notify` | `k8s-13.txt` | |
| `helm list` … | `helm-03.txt` | |
| `helm history notify-worker` … | `helm-01.txt` | |
| `helm get values notify-worker` … | `helm-02.yaml` | |
| `git -C ~/src/notify-deploy log` … | `git-01.txt` | Any range or path filter that includes these commits. |
| `git -C ~/src/notify-deploy diff` … or `git -C ~/src/notify-deploy show 3f9a1c2` … | `git-02.txt` | |
| `aws sqs list-queues` … | `sqs-01.json` | |
| `aws cloudwatch get-metric-data` (or `get-metric-statistics`) … `AWS/SQS` … `ApproximateNumberOfMessagesVisible` … `notify-outbound` | `cw-01.json` | Period 300. Covers 2026-10-22 07:50–08:45 UTC. |
