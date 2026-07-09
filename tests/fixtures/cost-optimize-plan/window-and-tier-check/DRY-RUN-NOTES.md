# Dry-run notes — window-and-tier-check

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides the upstream report path (`operator-question.md`) and asks for Principle 3 + 🔵 tier handling. Skill loads `upstream-report.md`, extracts the 2-item Remediation list, reads `**Cloud:** aws`, `**Scope:** 123456789012 / acme-prod`, `**Date:** 2026-07-09 09:00`. **Freshness check:** report is same-day → within the 14d threshold, no staleness warning. $5/mo floor — both items pass. No catalog → Dimension 4 scores ⚪ (🟡-equivalent). Operator approves. Approved.

2. **Step 2 (Plan verification batch)** — Skill matches both items to playbooks:
   - Item #1 → `examples/aws/delete-s3-bucket.md`
   - Item #2 → `examples/aws/delete-kinesis-stream.md`

   Both upstream items were flagged on a **14d** window and are delete actions, so per **Principle 3** the skill re-verifies over the **60–180d delete band (90d fetched)**, not the upstream 14d. GATE 2 approved.

3. **Step 3 (Execute queries)** — All 8 queries succeed. Evidence buffered:
   - `cloudtrail-getobject-archive-exports-2023.json` → **214 GetObject events across 90d**, steady distribution, last 2026-07-08 (a data-event trail is configured, so 0 would have been trustworthy — but it is not 0).
   - `get-bucket-versioning-archive-exports-2023.json` → Suspended (irreversible delete).
   - `list-objects-archive-exports-2023.json` → non-empty, recent object.
   - `describe-stream-summary-orders-ingest.json` → PROVISIONED, 2 shards, 168h retention, ConsumerCount 2.
   - `incoming-records-orders-ingest.json` → 0 across ~2160 hourly datapoints over 90d.
   - `get-records-orders-ingest.json` → 0 over 90d.
   - `list-stream-consumers-orders-ingest.json` → 2 ACTIVE EFO consumers (attachment).
   - `list-event-source-mappings-orders-ingest.json` → 1 enabled Lambda mapping (attachment).

4. **Step 4 (Triage)** — Per-item scoring:

   **Item #1 (Delete archive-exports-2023):**
   - Dimension 3 Evidence: over the Principle 3 delete window (90d), CloudTrail shows 214 GetObject events → **🚫 trigger (activity found)**. The upstream 14d "0 events" was window-too-short.
   - Tier rule 1: Evidence 🚫 → **🚫 Do not act**. (Reversibility 🔴 and other dimensions are moot once Evidence forces 🚫.)

   **Item #2 (Delete orders-ingest):**
   - Dimension 1 Reversibility: 🔴 (re-create yields a new ARN; records lost).
   - Dimension 2 Blast radius: 🟡 (2 EFO consumers + 1 Lambda mapping attached).
   - Dimension 3 Evidence: **🟢** — 0 IncomingRecords AND 0 GetRecords.Records over the 90d delete window at hourly granularity (Principle 3 satisfied; attachment is NOT scored here per Principle 1).
   - Dimension 4 Dependency: ⚪ no catalog (🟡-equivalent).
   - **Idle-ambiguous class check:** a Kinesis stream with 0 throughput but live consumers/mappings is idle-ambiguous. Tier rule 2 fires: Evidence 🟢 AND idle-ambiguous AND delete action → **🔵 Requires owner confirmation**. Rule 2 is evaluated before rule 3 (🔴) and takes precedence, so the 🔴 Reversibility score does NOT reroute the item — an idle-ambiguous delete is typically irreversible, which is exactly why owner confirmation is required. Reversibility 🔴 and Blast 🟡 are still recorded and shown, and the reversible retention-reduction fallback is offered in the dev-note.
   - Dev-note emitted at `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`.

5. **GATE 3 (Plan review)** — Plan drafted:
   - Item #1 in 🚫 with the Principle 3 window explanation (14d 0 → 90d 214 events) as the disqualifying evidence.
   - Item #2 in 🔵 with the idle-ambiguous rationale, the dev-note link, and the reversible retention-reduction fallback.
   - Plan summary shows the 🔵 row between 🟡 and 🔴.

   Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260709-0912.md`; dev-note written alongside.

## What this fixture validates

- **Principle 3 window scaling flips a delete.** Item #1 was flagged idle on 14d; the skill re-checks over the 60–180d delete band (90d) and finds steady activity (214 events, distributed — not one burst), landing it in 🚫 instead of an actionable delete. Validates that the consuming skill does not trust a too-short upstream window for a delete.
- **The 🔵 Requires owner confirmation tier + dev-note.** Item #2 is genuinely idle over the delete window (Evidence 🟢) but idle-ambiguous (live EFO consumers + Lambda mapping). It routes to 🔵, not 🟢/🟡, and emits an owner dev-note with a reversible fallback. Validates the new tier rule (rule 2), the idle-ambiguous class, and the artifact template.
- **Attachment stays out of Evidence (Principle 1).** The 2 EFO consumers and Lambda mapping are scored into Dimension 2 (blast) — they do NOT lift Evidence off 🟢. They ARE what makes the resource idle-ambiguous, which is a separate, explicit tier-routing input.
- **Temporal-distribution reasoning.** Item #1's 214 events are steady (not a single historical burst) → active. Item #2's zeros are flat across 90d → truly idle. The fixture exercises both readings.
- **Freshness gate no-op path.** A same-day report does not trigger the staleness warning — validates the gate fires only when the report is stale.

## Acceptance check

A reviewer confirms: (a) item #1 lands in 🚫 Do not act because the 90d delete-window CloudTrail read (214 GetObject) overrides the upstream 14d "0 events" — the plan names Principle 3 explicitly; (b) item #2 lands in 🔵 Requires owner confirmation (NOT 🟢/🟡 and NOT 🚫), with Evidence scored 🟢 and the EFO/Lambda attachments scored into blast radius, and a dev-note is emitted at `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md` containing the single owner question and the reversible retention-reduction fallback; (c) the plan summary contains the 🔵 row between 🟡 and 🔴; (d) no item claims actionable savings — $0 actionable now, $180/mo pending confirmation.

## Why this fixture was added (v0.10)

The OPS-9169 staging engagement surfaced two failure modes the v0.9 fixtures did not exercise: (1) delete candidates flagged on a 14d window that were actually active over a longer window (Principle 3); and (2) idle-but-wired resources (streams, caches, idle LBs, scheduled pipelines) where metrics prove "no traffic" but only an owner can confirm decommissioned-vs-paused (the 🔵 tier). This fixture exercises both in a single 2-item batch.
