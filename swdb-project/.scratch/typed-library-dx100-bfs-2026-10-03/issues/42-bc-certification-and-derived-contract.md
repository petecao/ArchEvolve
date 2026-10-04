# 42 — BC certification and the derived BC contract

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 18, 17, 28, 40
**Spec:** `../spec.md`

**What to build:** A derived BC contract applies the BFS read-offload contract to BC's forward-pass region and certifies on the Mac.

## Acceptance

- [x] The certification matrix and pass rule become a kernel plug-in; BFS is unchanged.
- [x] BC's instance uses BCVerifier PASS, the forward pass's per-level frontier sizes and an accelerated-chunk witness.
- [x] The derived contract has its own ID, cites the BFS contract, and adds BC-L1 (the path-count test reads the depth on the CPU after the compare-and-swap).
- [x] A BC-L1 violation control is rejected, and the BC forward-pass patch certifies.

## Comments

## Answer

Resolved 2026-10-03 23:20 ET (agent, BC track). Regression in this state: 279 passed; the 3 failures are the pre-existing ticket-39 list (sandbox `/private/tmp` denial).

**Built.**
- The certification matrix instance and pass rule are a kernel plug-in
  (`certification_source`, `_snapshot`, `_rewrite`, `_instrument`, `_oracle`, `_judge`,
  `_control`, `_controls`). `swdb/certification.py` selects the plug-in named by the
  contract's `correctness_check.kernel`; BFS's plug-in calls the unchanged BFS functions
  (`peter_source`, `instrument_source`, `graph_oracle`, `judge_bfs`, `_rewrite_control`),
  and calibration stays BFS-only. Scalar snapshots name their derivation script.
- BC instance (`swdb/kernels/bc.py`): BCVerifier PASS, the forward pass's per-level
  `Starting PBFS:` prints and the trusted queue inspection both equal the oracle's per-depth
  counts, and `accelerated_chunks > 0` whenever a level reaches the threshold. The oracle
  refuses a source without an outgoing edge. The certification build copy drops DX100
  `bc.cc`'s direct `MAA.hpp` include (the strict layer replaces the functional model) and
  includes the certification m5 stub (BC includes m5ops only without FUNC).
- Rewrite `library/dx100/bc_read_offload.inc` (E1-E5 plus BC-L1) and the deliverable
  `library/dx100/bc-forward-pass.patch` (scalar snapshot `bc.cc` plus the canonical lowering
  header), produced by `create_peter_patch(..., plugin=BC)`.
- Derived contract `library/rewrite_contracts/bc_read_offload.yaml`
  (`contract.bc_read_offload`): `provenance.derived_from` pins `contract.bfs_read_offload`
  by content sha256; same pattern key, intrinsics, knobs and fixes; BC correctness check;
  every BFS clause ID kept, plus BC-L1 (differential test, control `stale_depth_hint`).
  `swdb/library.py` validates the citation (existing contract, current hash, all cited clause
  IDs kept) and puts the cited contract in the dependency closure.
- Mac certification (g++-16, strict layer, 4 threads, tile sizes 16384 and 1024, source 0):
  `records/certifications/certification.1e389a959ffb4ff9bfdcf4cea9eace06.yaml`, verdict
  certified: 10/10 cells pass (kronecker-10/14/16, uniform-14, two-level), 18/18 controls
  rejected. BC-L1's control reads the DX100 hint instead of the CPU depth and is rejected by
  BCVerifier. The contract stays experimental (tier from records; ticket 43 promotes).

**Tests.** `tests/test_bc_certification.py`, 11 cases (BFS plug-in keeps its functions;
BC pass rule; forward-pass rewrite and controls; contract citation, BC-L1 and experimental
tier; three citation refusals; vacuous source; candidate scope; patch carries the rewrite;
real strict build where the candidate passes and the BC-L1 control fails BCVerifier).

**Assumptions.**
- The certification ran in a records copy where the BC scalar snapshot was registered from
  the deterministic derivation; the receipt binds the exact patched tree sha256. The
  snapshot itself is registered on mbit10 in ticket 41.
- BC's L3 (depth gathers see no value older than initialization) stays assumed: BC has no
  race companion; BC-L1 makes the path-count test independent of the hint.
- The runtime-guard fallback is the scalar forward pass for the whole BC call.
