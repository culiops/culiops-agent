# Investigation: payments-worker prod: pods crash-looping, payments-jobs queue backing up

Run: payments-worker-prod-20261024-1128 · Mode: Fast · Window: 2026-10-24 09:28Z to 11:28Z (11:28 to 13:28 local, Europe/Paris, UTC+2); onset about 10:52Z (12:52 local)

## TL;DR

| Field | Value |
|---|---|
| Cause | Helm release revision 31 (10:52:20Z) shipped a ConfigMap in which the key LEDGER_API_BASE_URL was renamed to LEDGER_BASE_URL. The 5.2.0 worker requires LEDGER_API_BASE_URL at startup, so every new pod exits with code 1 during config load and crash-loops; nothing consumes `payments-jobs`. · label: Confirmed |
| Weakest link | Each chain link is Confirmed; the least direct is the ConfigMap write time (managedFields not returned, W2-Q5), dated via Helm revision 31, pod start 10:52:33Z and the backlog step. Outside the chain, attribution to commit d81e4b7 / PR #377 is Likely (Helm records no SHA). |
| Impact | 0 of 3 workers up since about 10:52Z; backlog 5,989 at 11:25Z (10-30 before 10:50Z), rising about 197 per minute; DLQ 0; ongoing. Customer-visible effect Assumed. |
| Severity | SEV1 (suggested): customer-facing core flow (payment capture and refunds) fully stopped. The incident owner decides. |
| Pattern | unclassified · no alarm history, 14d and -7d pulls empty · Assumed |
| Recommended action | Make the pods see the ledger endpoint setting under the name the 5.2.0 worker reads (LEDGER_API_BASE_URL): revert the rename in prod values or roll the release back to the previous revision's configuration. Cost: one more three-pod rollout, watched until pods stay up. Assess with `pre-flight`, apply in a separate session. |
| Time to cause | not measured (no clock) |
| Similar past incidents | no history yet |

## Impact

0/3 pods ready, 11 restarts each (PB-Q1, W1-Q1). Backlog 10-30 until 10:50Z, 74 at 10:55Z, 5,989 at 11:25Z, +986 per 5 min (W1-Q6); DLQ 0 (W1-Q10). Core flow: payment capture and refunds. Customer effect Assumed (no SLO/APM; W1-Q11 empty). Third party: none known.

## Causal chain

1. Trigger: Helm revision 31 (10:52:20Z) rolled out ConfigMap `payments-worker-config` with LEDGER_BASE_URL and without LEDGER_API_BASE_URL · Confirmed · W1-Q5, W2-Q5, W3-Q1. Attribution to d81e4b7 / #377 · Likely (W2-Q6).
2. Mechanism: new pods (image 5.2.0, unchanged) exit 1 at config load: "required environment variable LEDGER_API_BASE_URL is not set"; identical on all 3 pods; start and exit in the same second · Confirmed · W2-Q1..Q4.
3. Symptom: 0/3 ready, CrashLoopBackOff, no consumer, constant backlog slope from the rollout minute · Confirmed · PB-Q1, W1-Q1, W1-Q6.

Ruled out: image pull/scheduling (W1-Q2), OOM (W2-Q1), probes (W1-Q2, W2-Q1), schedule (W2-Q7), ledger outage as crash cause (W2-Q2).

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Queue history (previous, -7d, 14d) and throughput/age metrics empty (W1-Q7..Q9, Q11) | class unclassified; customer impact Assumed | read the metrics in the CloudWatch console |
| ConfigMap write time not returned (W2-Q5) | change dated via Helm/pod start | read managedFields or the CD run of revision 31 |
| Deployed commit and app source not verifiable | attribution Likely | read the CD run; name the app repo in environment.md |
| Rollout strategy/readiness not read | why all old pods vanished is Assumed | read spec.strategy and probes with a names-only filter |
| `prod-ops` simulation lacked 3 of 10 action rows (W0-Q5) | none on findings; write-capable warning shown | use a read-only role |

open items need your input.

## To confirm, a human would…

1. Check which commit the CD run for Helm revision 31 deployed.
2. Check the 5.2.0 source reads LEDGER_API_BASE_URL (config/load.go:58) and whether a newer version reads LEDGER_BASE_URL.
3. Check the oldest message age and queue retention in the console.
4. After a human fix, confirm pods stay Running, backlog falls, DLQ stays 0.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore the key name the worker reads (or ship the worker version that reads the new name, keeping both keys during transition). Hand to `iac-change-execution` after `pre-flight`. |
| Prevention | Pre-merge check that every required startup env var exists in the rendered chart; keep old pods until a new pod has stayed up (readiness probe, minimum ready time). Strategy not read. |
| Observability gap | No alert on queue age or workers-ready below replicas; no log backend. |

## Cost

37 commands (30 backend read calls, 7 local checks) · 0 GB of logs · 8 CloudWatch metric requests · no other metered units · under 0.01 USD in metered charges
