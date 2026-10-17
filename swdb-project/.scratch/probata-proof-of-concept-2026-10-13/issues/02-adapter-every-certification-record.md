# 02 — Campaign adapter returns every certification record

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Loop, modes and guards", row "Campaign adapter"; "Proof routes" (each rewrite certified alone); "Testing Decisions", seams 2, 3 and 4; "Proof-of-concept plan", Extensa track); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) (item 7; side findings), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (build items)
**Time estimate:** about half a day

**What to build:** A prefactor. A candidate artifact may apply several rewrite contracts. The real
campaign adapter (shared by the native and gem5 targets) already runs `swdb certify` once per
contract, but it hands the campaign only the first certification record ID. The other records exist,
yet nothing in the campaign links them. After this ticket the adapter returns every certification
record ID, one per contract, in contract order, and the campaign's entry for that candidate artifact
links all of them. The pass/fail outcome and the failed-check names stay as today. The bounded gate,
rewrite chains and proof records build on this: each needs to know which certification belongs to
which contract.

## Acceptance

- [x] **Two contracts, both certify.** Through the campaign loop on the native adapter and on the
      gem5 adapter, with the certification command scripted the way the existing campaign tests
      script it: one certification runs per contract, and the adapter returns both record IDs, each
      paired with its contract, in contract order.
- [x] The campaign's entry for that candidate artifact links both record IDs. Each linked ID resolves
      to a certification record bound to that candidate artifact and that contract.
- [x] **One contract fails.** Both record IDs are still returned and linked. The outcome is failed,
      the failed checks are named exactly as today, and the certification repair path runs as today.
- [x] **A contract refused before any record exists.** Its slot is linked with no record ID and with
      its refusal check. The outcome is failed, as today.
- [x] **One contract.** One record ID; otherwise the campaign behaves as today (regression).
- [x] **Fixture seam.** `swdb campaign --fixture`, with a fixture iteration whose candidate artifact
      applies two contracts, writes two fixture certification records (`contract_fixture` evidence)
      and links both. `swdb validate` passes on the store, and `swdb candidate-level` names both
      records among its certifications.
- [x] A campaign saved before this change (one record per candidate entry) still loads and resumes.
- [x] Tests run with at most 2 test workers and start no real target run.

## Notes

- **Not in this ticket:** 14 — Bounded gate in the campaign. 19 — Derived implementations
  (per-rewrite certification links in a rewrite chain, contract lineage on implementation records,
  start from a derived implementation). 10 — Level rule. 12 — Proposal and promotion fields.
- Unchanged: `swdb certify` still takes one contract per run (17 item 7). `swdb candidate-level`
  already reads every certification bound to a candidate artifact; the defect is only the
  campaign's link.
- Today the contract-fixture adapter also writes one certification record, for the first contract
  only. Assumption (not decided in the map): it gets the same one-record-per-contract shape, so
  `swdb campaign --fixture` exercises the fix and the Extensa track's later fixture tests see
  real-shaped links.
- Assumption (not decided in the map): the link's field shape (for example, a list of contract and
  record pairs in contract order) and how an old single-record entry reads (as a one-pair list).
  Pick the smallest shape that keeps old campaign files valid, and record the choice in the answer.
- Assumption (not decided in the map): seam 3 (`swdb campaign --fixture`) drives only the
  contract-fixture adapter, so the real adapters are tested with the existing campaign-test pattern
  (scripted provider and certification command), as the native and gem5 campaign tests do today.
- D35 still refuses every new real-target campaign. Tests use the existing campaign-test pattern;
  nothing starts a real campaign.

## Answer

Resolved 2026-10-14 ET on branch `probata-poc/t02`. All acceptance boxes are met.

- **Adapter** (`swdb/campaign_targets.py`, `TargetAdapter.certify`, shared by native and gem5): returns
  `records`, one `{"contract", "record"}` pair per contract in contract order. A contract refused before
  any record exists is `{"contract", "record": None, "refusal": <check>}`. `record` (first record ID),
  `outcome` and `failed_checks` are unchanged.
- **Campaign entry** (`swdb/campaign.py`): `certification.records` copies the adapter's pairs.
  `certification_links(entry)` reads any entry. An entry saved before this change (only `record`) reads as
  a one-pair list; `contract` is named only when the entry used exactly one contract, else `None` (the old
  `record` was the first non-refused record, not necessarily the first contract's).
- **Contract-fixture adapter** (`swdb/campaign_fixture.py`): one `contract_fixture` certification per
  contract. One contract keeps its old ID; with several, each ID ends in the contract's name
  (`...a0.bfs_read_offload`). `command.contracts` now names only that record's contract.
- **Docs:** `docs/reference/format-v0.4-extensa.md`, campaign summary section.
- **Tests:** `tests/test_campaign_certification_links.py`, 8 tests: two contracts certify (native and gem5);
  one fails (repairs off; repair path on); refusal slot; one contract; `--fixture` with `swdb validate` and
  `swdb candidate-level`; resume of a pre-change `state.json`. A stale exact-dict assertion was updated in
  `tests/test_extensa_targets.py`. Scripted certification command and fixture runners only; one test
  worker; no real target run.
- **Run:** the 18 campaign, Extensa and provider test files that use the Extensa testkits (plus
  `test_extensa_boundary.py`, `test_extensa_machinery.py`): 320 passed, 1 deselected, 44 min, one worker
  (log `/tmp/claude/probata-runs/02/wide.log`, outside the repo). Implementation commit 4c77c651.

Assumption: the link is a list of `{contract, record[, refusal]}` pairs beside the kept `record`. This is
the smallest change: old summaries and state files stay valid, and no schema constrains candidate entries.

Assumption: the contract-fixture adapter applies the attempt's one fixture outcome and `failed_checks` to
every contract. The fixture file has no per-contract outcome, and no acceptance box needs one.

Assumption: seam 3 drives only the fixture adapter. The real adapters use the target-test pattern
(`testkit.extensa_targets.run` with a scripted certify), as the ticket notes say.

Side finding: the real `materialize` reuses the candidate for an identical repaired tree (ticket 80, C19).
A repair that returns the same patch re-certifies the same candidate ID, so a scripted certify must give
each run a unique record ID.
