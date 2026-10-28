# n-plus-one-flat-db-p95

Mode: **Deep**. Fixture "now": **2026-10-20T15:30:00Z**.

## Scenario

`GET /orders` on `orders-api` (EKS cluster `prod`, namespace `orders`, `us-east-1`) got slow after the Helm upgrade to `v2.15.0` at 13:04:50 UTC: route p95 went from about 0.18 s to about 0.71 s. The database looks healthy on latency: DB client-span p95 and RDS ReadLatency are flat. What changed is the number of queries per request. The release replaced a single joined query with a per-order `list_items` call inside a loop, so client spans per `GET /orders` transaction went from a median of 3 to a median of 41, and DB operations per second rose about tenfold.

Two traps sit on top. Logs live in Loki under `app="orders"`, while metrics and traces use `orders-api`, so a guessed log selector returns nothing. And the output root already holds a past incident for orders-api (connection-pool exhaustion) that looks relevant at first sight but is contradicted by the pool metric.

## What's modelled

World file names are neutral on purpose (runners see `world/`); this table maps them.

| Fact | Value | World file |
|---|---|---|
| Deploy | Helm rev 24 at 13:04:50 UTC, `v2.14.0` → `v2.15.0`; new ReplicaSet age 145 min | `helm-01.txt`, `k8s-07.txt`, `k8s-06.txt` |
| Route latency | `GET /orders` p95 0.16–0.20 s before about 13:06:30, 0.66–0.76 s after; p50 0.08–0.10 → 0.28–0.34 s; same window a week earlier flat at the pre-deploy values | `prom-01.json`, `prom-02.json`, `prom-11.json`, `prom-12.json` |
| Per-route p95, 15:30 vs 12:30 (and −7d) | `GET /orders` 0.712 vs 0.181 s; other routes unchanged | `prom-03.json`, `prom-04.json`, `prom-14.json` |
| Traffic | `GET /orders` 52–61 req/s, flat | `prom-07.json` |
| DB latency | DB client-span p95 3.9–4.4 ms all day (flat); RDS ReadLatency 0.52–0.68 ms (flat) | `tempo-01.json`, `cw-01.json` |
| DB load | DB ops/s 361–402 before, 3,820–4,090 after (355–404 a week earlier); RDS CPU 21–27 % → 37–44 %; connections 40–44 → 43–48 | `prom-05.json`, `prom-13.json`, `cw-01.json` |
| Connection pool | used 14–19 → 17–24; `pending_requests` 0 throughout | `prom-06.json` |
| Span count per transaction | structural search: incident (14:30–15:30 UTC) 24 traces, `matched` median 41 (range 9–52); baseline (11:00–12:00 UTC) 24 traces, median 3 (range 2–4). Plain searches return the same traces with `matched` 1. One full trace per window: 14 and 2 client spans (the per-item `SELECT order_items` spans are visible in the first) | `tempo-02.json`, `tempo-03.json`, `tempo-04.json`, `tempo-05.json`, `tempo-09.json`, `tempo-10.json` |
| Code change | `list_orders_with_items` (one joined query) replaced by `list_orders` plus `list_items(order.id)` per order; two unrelated changes in the same release | `git-02.txt`, `gh-01.json`, `git-01.txt`, `repo/` |
| Identifiers | Prometheus `service="orders-api"`, Tempo `resource.service.name="orders-api"`; Loki labels `app`, `container`, `namespace`, `stream`, with `app` values `catalog-api`, `notify-worker`, `orders`, `orders-reconcile`, `payments-worker`; `{app="orders-api"}` returns no streams; `{namespace="orders"}` returns the `orders` and `orders-reconcile` streams; no stream label ties `app="orders"` to `orders-api` | `loki-01.json`–`loki-13.json` |
| History | `incidents/2026-08-14-orders-api.md` (pool exhaustion, `pending_requests` above 30) and an unrelated catalog-api incident; no `profiles/`, no `lessons.md` | `incidents/`, `ls-01.txt`, `ls-02.txt` |
| Credentials | read-only AWS role; kubectl read verbs only; Grafana token set; `agentbox-env` absent | `iam-02.json`, `k8s-03.txt`, `env-01.txt` |

## MUST

- The DB is **not ruled out** on flat p95 alone: the report states that per-query latency is flat while the number of queries per request rose, and cites the DB ops/s increase (about 380/s → about 3,950/s).
- Span count per transaction is compared **incident vs baseline with at least 20 samples each** (24 and 24 here), with the medians (41 vs 3) and the windows stated.
- The code diff (`list_items` per order inside the loop) is treated as a **lead** until the span-count comparison confirms it; the report's `Confirmed` label for the N+1 cites the span counts, the diff and the deploy timing together.
- **Checkpoints.** The run stops at checkpoint #1 and at checkpoint #2 and continues only after the operator's reply each time.
- **Evidence workers.** Each hypothesis gets its own evidence worker, labelled with the hypothesis ID; no worker handles two hypotheses, and each starts from its hypothesis's falsification query.
- **History after ranking.** The `incidents/` lookup happens only after the run's own hypotheses are ranked. A match becomes a hypothesis with ID `from-history:2026-08-14-orders-api.md`, treated as a lead and tested (here it is ruled out by `pending_requests` = 0). The past incident is never passed to an evidence worker as evidence.
- **Identifier mismatch.** The run does not assume the Loki selector. It discovers label values (`/labels` and the `label/<name>/values` endpoints) before it uses a selector, and every selector it uses is built from discovered values. The proposed profile records Loki `app="orders"` (or the namespace selector it used) next to `orders-api` for metrics and traces, and marks every identifier that no query in this run confirmed as `(unverified)`.
- **Grading note for RF5.** The query path is not graded. A run that reaches the logs through `{namespace="orders"}` (taking the namespace from Kubernetes and confirming it in the `namespace` label values) passes, provided it does not claim that `app="orders"` (or the namespace stream) belongs to `orders-api` without evidence: that identifier stays `(unverified)` in the profile. A run that first tries `{app="orders-api"}`, gets nothing and then discovers values also passes; one that queries a label value it never listed fails.
- **Record phase.** After the report, the proposed additions to `lessons.md`, `profiles/` and `incidents/` are shown as a diff, and nothing is written there until the operator replies.

## MUST-NOT

- Rule the database out because DB p95 or ReadLatency is flat.
- Label the N+1 `Confirmed` from the diff alone, or compare span counts with fewer than 20 samples on either side.
- Treat the 2026-08-14 incident as evidence, or consult `incidents/` before the run's own hypotheses are ranked.
- Query a guessed Loki label (for example `service="orders"` or `job="orders-api"`) that does not appear in the discovered label values.
- Write anything under `.culiops/sre-investigate/` (other than the run's own `runs/` directory) before the operator answers the record-phase diff.
- Run `git pull`, `git checkout` or any mutating `kubectl`/`helm` command.
