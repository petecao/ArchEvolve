# 06 — Contract link tables

Created: 2026-10-09
**Type:** slice
**Status:** resolved
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

## Answer

Resolved 2026-10-11 22:00 ET on `lanl-shaped-db` (commit 1ac6c92a). Built in
`swdb/lanl_contracts.py`. The four `swdb_contract_*` tables (`contract` → `swdb_library_entries`,
the LANL row id, `clause`, `record_id`, `record_field`) hold only stated ties: a certification's
`candidate.contract` + `candidate.snapshot` links the contract to the snapshot's implementation
and its kernel; a statement fact `legality:<contract>:<clause>` links the contract to that
statement's function (`definitions`), the arrays of the steps it names (`data_structures`), and
its implementation and kernel. A link is a tie, not a verdict. Site-finder matches and proposal
offers are not links. Contracts the library lacks get no link. Tests:
`tests/test_lanl_contracts.py` (9 pass).
