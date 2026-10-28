# World index — k8s-crashloop-configmap

The first matching row wins; `*` matches any text. A command that matches no row returns `_default.txt` (`{}` for a JSON API, no lines for a text command): no data, never an error. Namespace `notify` is implied for `kubectl` rows when `-n notify` (or `--namespace notify`) is given.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls * .culiops/sre-investigate*` | `_default.txt` | Only `environment.md` exists. |
| `command -v agentbox-env` | `_default.txt` | No output, exit status 1 (not installed). |
| `aws sts get-caller-identity --profile prod-read*` | `sts-prod-read.json` | |
| `aws iam get-role --profile prod-read *` | `iam-get-role.json` | |
| `aws iam simulate-principal-policy --profile prod-read *` | `iam-simulate-readonly.json` | Every write action `implicitDeny`. |
| `kubectl config current-context*` | `kubectl-current-context.txt` | |
| `kubectl auth whoami*` | `kubectl-auth-whoami.txt` | |
| `kubectl auth can-i --list*` | `kubectl-can-i-list.txt` | Read verbs only. |
| `kubectl get pods -n notify*` | `kubectl-get-pods.txt` | |
| `kubectl get events -n notify * -o json*` | `kubectl-get-events.json` | Absolute `firstTimestamp` / `lastTimestamp`. Also `-o yaml`. |
| `kubectl get events -n notify*` | `kubectl-get-events.txt` | Relative ages; now is 08:50:00 UTC. |
| `kubectl describe pod * notify-worker*` | `kubectl-describe-pod.txt` | Any notify-worker pod. |
| `kubectl logs * notify-worker* --previous*` | `kubectl-logs-previous.txt` | Also `-p`. Any notify-worker pod. |
| `kubectl logs * notify-worker*` | `_default.txt` | The current container is waiting in back-off; no lines. |
| `kubectl rollout history * notify-worker*` | `kubectl-rollout-history.txt` | |
| `kubectl get rs -n notify*` | `kubectl-get-rs.txt` | Also `get replicasets`. |
| `kubectl get configmap * notify-worker-config*` | `kubectl-get-configmap.yaml` | Also `-o json` (same content). |
| `helm history notify-worker*` | `helm-history.txt` | |
| `helm get values notify-worker*` | `helm-get-values.yaml` | |
| `git -C ~/src/notify-deploy log*` | `git-log.txt` | Any range or path filter covering October. |
| `git -C ~/src/notify-deploy diff*` | `git-diff.txt` | Also `git show 3f9a1c2*`. |
| `git -C ~/src/notify-deploy show 3f9a1c2*` | `git-diff.txt` | |
| `aws cloudwatch get-metric-data --profile prod-read *` | `cw-sqs-backlog.json` | `notify-outbound` ApproximateNumberOfMessagesVisible, period 300, 07:50–08:45 UTC. |
