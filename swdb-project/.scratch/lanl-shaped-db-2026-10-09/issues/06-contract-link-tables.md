# 06 — Contract link tables

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** contracts get typed link tables to LANL rows:
`swdb_contract_definitions`, `swdb_contract_data_structures`, `swdb_contract_kernels` and
`swdb_contract_kernel_variants`. They are filled only from links the records already state (for
example an implementation that applies a rewrite contract, or a clause tied to a statement's
function). No new inference. Library entries, clauses and pattern keys stay in their `swdb_`
tables from ticket 01.

About 2 h.

- [ ] A fixture contract applied by an implementation links to that kernel variant and its kernel
- [ ] A fixture clause tied to a statement links to the matching `definitions` row
- [ ] A contract with no stated link has no link rows
- [ ] Deleting every `swdb_` table leaves LANL tables untouched and the foreign-key check clean
