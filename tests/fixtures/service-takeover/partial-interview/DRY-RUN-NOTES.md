# Dry-run notes — partial-interview

## What this fixture validates

1. **Section classification at Gate 5:** 7 `complete`, 2 `partial`, 2 `empty` (the three places this was counted — `input.md`, this file and `state.md` — agree).
2. **Accept-as-is** is an explicit, recorded operator decision; the skill does not ask the operator to supply the outgoing team's knowledge.
3. **Empty is `?`, never `✗`.** Items 22-25 (Section 10 empty) and item 14 (incidents empty) are `?`. `✗` needs an explicit "no X".
4. **Catalog facts are reflected but do not replace answers.** The catalog shows PITR and a TTL on `expires_at` for `payments-ledger`; items 23 and 24 say so in their notes and stay `?` because no retention policy, restore test or DR plan was stated.
5. **Strict verdict `partial`:** `?` and `◐` cap the verdict; no item is `✗`, and the one conflict (item 19) is outside the not-ready categories.
6. **Declined verification batch** is recorded (state, plan addendum, scorecard); items 10 and 15 stay `◐` with their check commands listed.
7. Same-target check, single discovery delegation, derived-facts-only probes: as happy-path.

`mock-artifacts/service-catalog.md` and `mock-artifacts/runtime-profile.md` are the shared mock sibling artifacts (runtime-profile-schema 2; catalog with Owner/Live columns, `Live verification: performed`, Unattributed list, secrets as references). The mock Wiring section deliberately lists one configured caller the interview omits (role `legacy-orders-exec` may send to `payments-capture-queue`), so item 19 is a `✗ conflict` wherever both a profile and Section 8 exist. The interview has two variants: A (happy-path only: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) and B (all others: role permitted, 5 deploys/quarter, single-region DR).

---

## Gate transitions

**Gates 1, 1.5, 2, 3, 4** (14:00Z-15:05Z): as happy-path (same probes, one discovery delegation, same-target checks at 14:33Z and 15:05Z).

**Gate 5** (15:05Z-15:45Z). Bob fills Sections 1, 2, 4 (incl. 4b), 5, 7, 8, 9. Classification: 7 complete / 2 partial (6: incidents, recurring issues, MTTR, change failure rate empty; 11: open issues empty) / 2 empty (3, 10). Options shown: return to the outgoing team / accept as-is / abort. Operator accepts as-is; recorded in `state.md`.

**Gate 6** (15:45Z-16:00Z).
- From artifacts: items 4-9 `✓ verified`; 16, 18, 20 `✓ verified`; 19 `✗ conflict`.
- Operator confirms the deploy role (item 2) and attests items 3, 11, 12.
- Batch proposed (15:48Z); **declined** (15:49Z). Items 10, 15 `◐`.
- Items 14, 22, 23, 24, 25 `?`.
- Verdict `partial`.

**Gate 7** (16:00Z-16:05Z). Package: 8 files. README leads with the High items (the conflict and the two empty sections).

---

## Marks

11 ✓ verified, 3 ✓ attested, 5 ◐, 0 ✗, 1 ✗ conflict, 5 ?, 0 N/A (25 items).

| Dimension | happy-path | partial-interview |
|---|---|---|
| Interview sections | 11 complete | 7 complete / 2 partial / 2 empty |
| Step 6 batch | run | declined |
| `?` | 0 | 5 |
| `✗` / `✗ conflict` | 1 / 3 | 0 / 1 |
| Verdict | not-ready | partial |

---

## Acceptance check

- Verdict `partial` for any run with this input set (no `✗`; the conflict is in Dependencies).
- `open-questions.md`: 3 High, 6 Medium, 2 Low; the README top 5 are all present.
- Items 22-25 and 14 are `?` with the citation "empty (`_To be filled in: ___`)".
- `state.md` Gate 5 row records 7 / 2 / 2 and accept-as-is.

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
