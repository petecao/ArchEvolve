# Review — `contract.bc_read_offload` (ticket 43)

Date: 2026-10-03 23:31 ET. Reviewer: agent acting as independent reviewer (not the ticket-42 author),
under Yan-Ru's 2026-10-03 delegation ("I approve all actions related to this project").
Agent-reviewed and promoted under Yan-Ru's 2026-10-03 delegation; revisable by Yan-Ru.

## Target

- Entry `contract.bc_read_offload`, content sha256
  `969276431d9169701a5ff5862fc422e7578e54bf27419fb1d1d1ece63f90dc9a`
  (`library/rewrite_contracts/bc_read_offload.yaml`).
- Rewrite `library/dx100/bc_read_offload.inc` (sha256 `3898b439…`), deliverable
  `library/dx100/bc-forward-pass.patch`.
- Evidence: `records/certifications/certification.1e389a959ffb4ff9bfdcf4cea9eace06.yaml`.
- Promotion record: `records/reviews/review.contract.bc_read_offload.30a3747420b3.yaml`.

## Verdict

PROMOTE. No blocking or major defect found; nothing was changed in the contract, rewrite or patch.

## Checks performed

1. **Citation.** `provenance.derived_from` pins `contract.bfs_read_offload` at
   `867fac18…db51`; this equals the library's current content sha256 for the BFS contract and the
   hash in `promotion-receipts.json` (ticket 22). Every BFS clause ID (L1–L5, knobs,
   `once_enqueue`) is kept; BC-L1 is added. Library validation passes.
2. **Rewrite against the scalar PBFS** (`apps/dx100/benchmarks/gapbs/src/bc.cc` lines 69–128).
   DX100 does only reads: the frontier stream, the row bounds, the range loop, the neighbor,
   frontier-vertex and depth-hint gathers. The CPU keeps the depth CAS, the queue push, the
   successor bit (`edges[k]` = the CSR edge index `vidx`, which equals `&v - g_out_start`) and the
   atomic path-count update. Within PBFS a depth goes only from -1 to the current level, so a hint
   other than -1 is never wrong, and skipping the CAS on it is sound. A hint of -1 may be stale;
   the CAS then fails and the path-count test reads the depth on the CPU (a relaxed atomic load
   after the CAS). That is exactly BC-L1 and matches the scalar `depths[v] == depth` test. The
   dependency pass and Brandes are unchanged apart from the E3 setup and `__dxc_report()`. The
   memory regions (queue, offsets, neighbors, depths) are already registered by Brandes.
3. **BC-L1 enforcement.** Control `stale_depth_hint` replaces the CPU depth load with
   `claimed ? depth : hint`. On the two-level graph (17,000 vertices with many parents at depth 2)
   it is rejected by BCVerifier FAIL at both tile sizes, with accelerated chunks running (3 and
   22). The rejection is deterministic under the strict layer, because a tile's hints are gathered
   before the CPU loop over that tile.
4. **Matrix and controls.** 10/10 cells pass (Kronecker 10/14/16, uniform 14, two-level; tiles
   16384 and 1024; 4 threads; source 0). Per-level frontier prints and the trusted queue
   inspection equal the oracle. Accelerated levels and scalar-fallback levels both occur in every
   graph. 18/18 controls are rejected and cover the spec's three mandatory kinds: overlapping
   pointer (`shared_context`), double claim (`skipped_cas_recheck`, `forged_frontier`) and dropped
   operand (5 controls).
5. **Re-run on the Mac.** `swdb certify contract.bc_read_offload --snapshot
   bc-dx100-scalar-only-20261003-a1.source --patch library/dx100/bc-forward-pass.patch`, run in a
   records copy (scratchpad, not committed), gave `certification.db570f7f2b244a3a98ee5dd15dd63401`,
   verdict certified, 10/10 cells and 18/18 controls rejected. The contract hash, dependency pins,
   patched tree sha256 (`d6f86eb6…b9`) and per-cell oracle counts are identical to the committed
   record. `tests/test_bc_certification.py`: 11 passed.
   The BC, library and certification test files (`test_bc_*`, `test_library_*`, `test_typed_*`)
   gave 266 passed and 4 failed. None of the 4 involves this contract or the promotion: two hit the
   sandbox `/private/tmp` denial; `test_bc_native` re-registers the snapshot that ticket 41 already
   registered; `test_library_submit` expects the BFS contract at `certified`, but it is
   `evaluated_on_target` since ticket 28.

## Findings (none blocking)

| # | Severity | Finding |
|---|---|---|
| 1 | Minor | L4 now also says that the successor bit and the path-count update stay on the CPU and that the edge index comes from the same chunk. Its only control (`skipped_cas_recheck`) tests the CAS part. No control mutates the edge index or the path-count source. BCVerifier would catch such a mutation, but no control shows it. Suggested follow-up: add a control that, for example, sets the successor bit from a shifted edge index. |
| 2 | Minor | Clause `negative_control.check` names are not checked against the observed rejection reason. L1 names `frontier_size_equality`, but `dropped_continuation` is rejected by `verifier`. `frontier_threshold` and `schedule` name checks (`knob_range`, `schedule_range`) that the BC judge never emits. This is inherited unchanged from `contract.bfs_read_offload`, and the pass rule's semantic-rejection branch accepts these controls anyway. |
| 3 | Info | Certification uses `-n 1` (one source per Brandes call). Depth re-initialization between sources (`depths.fill(-1)` followed by DX100 reads) is covered only by the assumed L3/L5 clauses. BC has no race companion case, so BCVerifier on target is the only check. The contract states this. |
| 4 | Info | The patch restructures PBFS from one parallel region around the level loop to one parallel region per level, and the scalar fallback branch uses the same structure. This preserves semantics but is not byte-identical to the pre-rewrite PBFS, which matters only for timing comparisons against the original scalar code. |

## Second opinion

The Codex CLI (0.153.0) is installed, but `codex exec --sandbox read-only` failed in this agent's
sandbox: "failed to initialize in-process app-server client: Operation not permitted". The run
was not retried outside the sandbox (that was not permitted for this task). No Codex verdict is
recorded. Yan-Ru can run it by hand with the prompt kept in the agent's session scratchpad.
