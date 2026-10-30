# Infra-state playbook

Backends: ECS, Elastic Load Balancing, EC2 Auto Scaling, RDS, EC2 networking and Lambda (AWS CLI describe/get/list calls) · kubectl (get and describe only) · IaC files read from git by ref
verified: live (AWS CLI, 2026-10-30: ecs describe-services) · docs-only (every other recipe, AWS and Kubernetes)

**Purpose.** This playbook describes how the service is put together and connected: capacity and its limits, health checks, connection limits, timeouts, routing and dependencies. It also answers whether what runs matches what the IaC says. Its findings explain why a symptom took the shape it did (a pool that tops out, a health check that drains healthy tasks, a deregistration delay that drops requests). They rarely date anything: the state read here is the state now.

## Cost ladder

1. **The service profile.** What is already known about capacity, limits and wiring. Confirm only what a hypothesis needs.
2. **Describe calls with a narrow `--query`,** one resource at a time, through the read-only profile. They are free, but they share the account's API rate limits, so never fan out over hundreds of resources.
3. **kubectl read verbs** (`get`, `describe`, `top`) for the workload, its autoscaler and its disruption budget.
4. **IaC at a ref** for the intended state, read with `git show` or `git grep`; never the working tree, never a state file.

`<profile>`, `<region>`, `<context>`, `<namespace>` and the resource names come from `environment.md` and the service profile.

## Live config vs IaC

Read the live value, then the value the IaC declares at the ref that was last applied (see the changes playbook for how to find that ref). Record both side by side.

### ECS service and task definition

```bash
aws ecs describe-services --profile <profile> --region <region> --cluster <cluster> --services <service> \
  --query 'services[0].{desired: desiredCount, deployment: deploymentConfiguration, capacity: capacityProviderStrategy, launchType: launchType, loadBalancers: loadBalancers, registries: serviceRegistries, healthGrace: healthCheckGracePeriodSeconds}'
aws ecs describe-task-definition --profile <profile> --region <region> --task-definition <family>:<revision> \
  --query 'taskDefinition.{cpu: cpu, memory: memory, containers: containerDefinitions[].{name: name, image: image, cpu: cpu, memory: memory, memoryReservation: memoryReservation, stopTimeout: stopTimeout, healthCheck: healthCheck, ulimits: ulimits, env: environment[].name}}'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/ecs/describe-services.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/ecs/describe-task-definition.html -->

Things to compare with the symptom: `minimumHealthyPercent`/`maximumPercent` (how much capacity a deploy removes), the health-check grace period against the app's start time, a container `stopTimeout` shorter than the app's drain, and a hard `memory` limit close to the observed working set.

### Load balancer target group

```bash
aws elbv2 describe-target-groups --profile <profile> --region <region> --target-group-arns <tg-arn> \
  --query 'TargetGroups[0].{protocol: Protocol, port: Port, path: HealthCheckPath, interval: HealthCheckIntervalSeconds, timeout: HealthCheckTimeoutSeconds, healthy: HealthyThresholdCount, unhealthy: UnhealthyThresholdCount, matcher: Matcher}'
aws elbv2 describe-target-group-attributes --profile <profile> --region <region> --target-group-arn <tg-arn> \
  --query "Attributes[?Key=='deregistration_delay.timeout_seconds' || Key=='slow_start.duration_seconds' || Key=='load_balancing.algorithm.type']"
aws elbv2 describe-target-health --profile <profile> --region <region> --target-group-arn <tg-arn> \
  --query 'TargetHealthDescriptions[].[Target.Id, TargetHealth.State, TargetHealth.Reason]' --output text
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/elbv2/describe-target-groups.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/elbv2/describe-target-group-attributes.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/elbv2/describe-target-health.html -->

A health check that calls a dependency turns a dependency blip into a fleet-wide drain. A deregistration delay longer than the task's stop timeout means requests still arrive at a container that is already exiting.

### Capacity: Auto Scaling group and ECS capacity providers

```bash
aws autoscaling describe-auto-scaling-groups --profile <profile> --region <region> --auto-scaling-group-names <asg> \
  --query 'AutoScalingGroups[0].{min: MinSize, max: MaxSize, desired: DesiredCapacity, mixed: MixedInstancesPolicy.LaunchTemplate.Overrides[].InstanceType, onDemandBase: MixedInstancesPolicy.InstancesDistribution.OnDemandBaseCapacity, suspended: SuspendedProcesses[].ProcessName, instances: length(Instances)}'
aws ecs describe-capacity-providers --profile <profile> --region <region> --capacity-providers <capacity-provider> \
  --query 'capacityProviders[].{name: name, asg: autoScalingGroupProvider.autoScalingGroupArn, scaling: autoScalingGroupProvider.managedScaling}'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/autoscaling/describe-auto-scaling-groups.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/ecs/describe-capacity-providers.html -->

`desired` equal to `max` during the incident means the group could not grow. A suspended process (`Launch`, `Terminate`, `HealthCheck`) is a frozen control loop that someone left that way.

### Database: class, roles and connection limit

```bash
aws rds describe-db-clusters --profile <profile> --region <region> --db-cluster-identifier <db-cluster> \
  --query 'DBClusters[0].{engine: Engine, version: EngineVersion, members: DBClusterMembers[].[DBInstanceIdentifier, IsClusterWriter]}'
aws rds describe-db-instances --profile <profile> --region <region> --db-instance-identifier <db-instance> \
  --query 'DBInstances[0].{class: DBInstanceClass, paramGroups: DBParameterGroups[].DBParameterGroupName}'
aws rds describe-db-parameters --profile <profile> --region <region> --db-parameter-group-name <parameter-group> \
  --query "Parameters[?ParameterName=='max_connections'].[ParameterName, ParameterValue, Source]" --output text
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-clusters.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-instances.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-parameters.html -->

`max_connections` is often a formula of instance memory rather than a number; record the expression as returned, and the instance class it resolves against. Compare it with the sum of the pool sizes of every client, at peak task count.

### Network: what a subnet really routes to

A subnet named "private" can route to an internet gateway. Read its route table instead of trusting the name:

```bash
aws ec2 describe-route-tables --profile <profile> --region <region> \
  --filters Name=association.subnet-id,Values=<subnet-id> \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock, DestinationPrefixListId, GatewayId, NatGatewayId, TransitGatewayId, VpcEndpointId, State]' --output text
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-route-tables.html -->

An empty result means the subnet has no explicit association and uses the VPC's main route table: query again with `Name=vpc-id,Values=<vpc-id> Name=association.main,Values=true`. A `0.0.0.0/0` route to an `igw-` target makes the subnet public, whatever it is called; a route in state `blackhole` points at a target that no longer exists.

### Lambda

```bash
aws lambda get-function-configuration --profile <profile> --region <region> --function-name <function> \
  --query '{runtime: Runtime, memory: MemorySize, timeout: Timeout, vpc: VpcConfig.SubnetIds, envNames: keys(Environment.Variables || `{}`)}'
aws lambda get-function-concurrency --profile <profile> --region <region> --function-name <function>
aws lambda list-event-source-mappings --profile <profile> --region <region> --function-name <function> \
  --query 'EventSourceMappings[].{source: EventSourceArn, state: State, batch: BatchSize, lastResult: LastProcessingResult}'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-concurrency.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/lambda/list-event-source-mappings.html -->
<!-- doc: https://jmespath.org/specification.html -->

The function configuration returns environment variable values. The `--query` above keeps only their names (`keys(...)`); never run the call without it. Reserved concurrency set to a small number, or to zero, is a hard ceiling on the function.

### Kubernetes: probes, requests and limits, HPA, PDB

Probes and resources for each container, with environment variable names only:

```bash
kubectl --context <context> -n <namespace> get deployment <service> -o json \
  | jq '.spec.template.spec.containers[] | {name, resources, readinessProbe, livenessProbe, startupProbe, env: [.env[]?.name]}'
```
<!-- doc: https://kubernetes.io/docs/concepts/workloads/pods/probes/ -->

A liveness probe that calls a dependency, or that times out under load, restarts pods that were only slow and turns slowness into an outage. A failing readiness probe restarts nothing; it takes the pod out of the Service's endpoints. A memory limit close to the working set predicts OOMKilled restarts; a CPU limit well below what the pod uses at peak predicts throttling (see the metrics playbook for the throttling series).

Autoscaler and disruption budget:

```bash
kubectl --context <context> -n <namespace> get hpa
kubectl --context <context> -n <namespace> describe hpa <hpa>
kubectl --context <context> -n <namespace> get pdb
kubectl --context <context> -n <namespace> top pod -l <selector>
```
<!-- doc: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ -->
<!-- doc: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/ -->
<!-- doc: https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ -->

- **HPA.** In `describe hpa`, the `Conditions` block says whether the autoscaler could scale and whether it was capped: `ScalingLimited` true with a `TooManyReplicas` reason means it wanted more than `maxReplicas`. If any container has no CPU request, CPU utilization is undefined and the HPA takes no action on that metric.
- **PDB.** `ALLOWED DISRUPTIONS` of 0 blocks voluntary evictions such as node drains; involuntary disruptions still happen and count against the budget. A budget that is always at 0 can stall a node rotation for hours.
- **`kubectl top`** is the current usage only; the history comes from the metrics playbook.

### IaC: the intended state

```bash
git -C <iac-clone> show <applied-ref>:<path/to/service.tf>
git -C <iac-clone> grep -n -e 'deregistration_delay' -e 'health_check' <applied-ref> -- <service-path>
```
<!-- doc: https://git-scm.com/docs/git-grep -->

For Kubernetes, read the manifests, Kustomize overlays or Helm values files at the applied ref the same way. A live value that differs from the declared one is drift: record which side changed last, using the changes playbook (a CloudTrail write, a `kubectl` managed-fields entry, a console edit).

What this playbook does not run, because each one goes beyond reading: `terraform plan` or `refresh` (they read the state, can take its lock, and need the workspace's credentials), `terraform state pull` or `show` (state is stored in plain text, secrets included), `kubectl diff` (it computes what an apply would do against the live cluster), `helm get values`.
<!-- doc: https://developer.hashicorp.com/terraform/language/manage-sensitive-data -->
<!-- doc: https://developer.hashicorp.com/terraform/language/state/locking -->
<!-- doc: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_diff/ -->

When the comparison needs one of them, put it in the report's "To confirm, a human would…" list as a sentence, for example "run a Terraform plan on the service's workspace and compare the target group's health check path with the live value".

## Gotchas

- **Drift is a finding, not a cause.** A live value that differs from IaC matters only if it is on the failing path and explains the symptom. Record it either way; label it as a cause only with evidence from the other playbooks.
- **Now is not then.** Everything here is the current state. If the incident is over, someone may already have scaled, rolled back or edited the value. For a past incident, prefer the change history (changes playbook) to establish what the value was at the onset, and say "current value" in the ledger.
- **Names lie.** Check the route table, the security group rules or the target group, not the name of the subnet, group or service.
- **Never read secrets.** No `secretsmanager get-secret-value`, no `ssm get-parameter --with-decryption`, no `kubectl get secret -o yaml` or `-o json`, no decrypting an encrypted file, even when the IaC points at it. A secret is recorded by its name and the path that references it.
- **Values that are not secrets can still be sensitive.** Environment variables, Lambda configuration and Pod templates are read with names-only queries.
- **One resource at a time.** No describe call over every resource in the account or cluster; the profile says which resources are in the path.

## What to write in the ledger

One row per setting read:

- resource, setting, live value, declared value and the ref it was read at (or "not in IaC"), and whether they match;
- whether the setting is on the failing path, and what symptom it would explain;
- the note "current state, read at <UTC time>" on every row;
- secrets and environment variables by name only;
- a deeplink for a human: the CLI command with its `--query`, or the IaC file path and ref.
