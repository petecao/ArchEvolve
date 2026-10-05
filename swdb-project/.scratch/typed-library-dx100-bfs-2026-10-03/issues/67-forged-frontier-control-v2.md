# 67 — forged_frontier v2: a control every correct rewrite can kill

Created: 2026-10-04 21:05 ET (by the ticket 57 a7 audit)
Updated: 2026-10-04 21:05 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`; [57](57-gem5-campaign-target.md), [62](62-spelling-independent-certification-controls.md)

**What to build:** the `forged_frontier` negative control fires for every correct BFS or BC
rewrite, whatever its tile size, frontier threshold or chunk timing, and only the trusted
frontier check (`duplicate_frontier`) rejects it.

## Finding (ticket 57 a7 audit, 2026-10-04)

In 6 of a7's 18 failed certificates, the only failure was `forged_frontier` surviving at tile 16384.
Version 1 of the fault pushed a vertex twice only after an accelerated chunk had been counted
(`swdb_dxc::chunks() > 0`). On the two-level control graph with threshold 64, the only accelerated
level that pushes is one 4,200-element chunk. A candidate that counts its chunk after the chunk's
pushes never fires the fault. This is a false rejection: one of the six carries a7's best patch with
threshold 64.

## Acceptance

- [x] The fault fires independently of chunk and tile timing and is rejected only by the named
  check `duplicate_frontier` (the trusted queue inspection behind `frontier_size_equality`).
- [x] The control is versioned; old certificates keep their meaning.
- [x] The six affected a7 trees, rebuilt from their recorded patches and knobs, have `forged_frontier`
  rejected.
- [x] Ticket 20 (BFS) and ticket 42 (BC) still certify, with every control rejected by its own named check.
- [x] A broken rewrite is still refused.
- [x] The six a7 candidates are re-judged on the Mac, and ticket 57 has a dated addendum.

## Answer

Resolved 2026-10-04 21:05 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

**Decision: duplicate the first CPU queue push of the run.** Version 2 of the fault is in
`library/dx100/faults/dxc_lowering_faults.hpp` (macro `SWDB_DXC_FAULT_FORGED_FRONTIER_V2`). The
first `QueueBuffer::push_back` of the process is pushed twice. A process-wide flag is set once and
`__dxc_session_begin` never resets it. The forged frontier print is unchanged.

- Why not "after the first accelerated read": on the two-level graph a correct candidate with a
  threshold above 4,200 accelerates only the last level, which pushes nothing. That variant
  could still miss correct candidates.
- Why not "at the protected print": the trusted inspection of a window runs just before its print,
  so a duplicate added to that window at the print is never inspected. A vertex added to the next
  window instead comes from the previous level, so it is not a within-level duplicate. Either way,
  the control would test `SlidingQueue` internals rather than the contract's queue seam.
- What it still tests: `duplicate_frontier` (and therefore `once_enqueue`) has power against a
  duplicate hidden by a forged print. It also keeps clause L4's queue seam. A candidate that pushes
  without `QueueBuffer` never fires the fault, so its control survives and it is refused.
  `skipped_cas_recheck` still exercises the accelerated claim path.

**Versioning.**
- `swdb/certification_faults.py` `FAULT_VERSIONS` (`forged_frontier`: 2, others: 1). Each control
  record's `fault` gains `version`.
- Certification command version `1.0` → `1.1` (`swdb/certification.py`).
- Records with command `1.0`, or without `fault.version`, used version 1 and keep that meaning. No
  committed record was changed.

**Verification (Mac, g++-16).**
- Mechanism: ticket 20's patch with `__dxc_accelerated_chunk()` moved after each chunk's pushes (a
  correct rewrite of a7's shape), on the two-level graph:

  | Fault | Tile 16384 | Tile 1024 |
  |---|---|---|
  | v1 | survived | rejected |
  | v2 | rejected (`duplicate_frontier`) | rejected (`duplicate_frontier`) |

  New test: `tests/test_certification_controls.py::test_forged_frontier_v2_is_killed_when_chunks_are_counted_after_their_pushes`.
  It runs a full `certify()`: certified, 10/10 cells, 16/16 controls, `forged_frontier` rejected at
  both tile sizes with version 2.
- Deep-graph test: v2 is now rejected on both the 8-level scalar graph and the 7-level accelerated
  graph. v1 never fired on the 8-level scalar graph.
- Ticket 20, the reformatted and restructured copies, and BC (`certify_bfs`, 24/24 controls) still
  certify. The skipped-CAS rewrite is still refused on the matrix (`frontier_size_equality`). The
  raw-builtin claim is still refused by `skipped_cas_recheck`.
- a7 re-judgement:
  [`evaluation/a7-forged-frontier-v2-rejudge-2026-10-04.json`](../evaluation/a7-forged-frontier-v2-rejudge-2026-10-04.json)
  and the [ticket 57 addendum](57-gem5-campaign-target.md). All six are now `certified`. None has a
  gem5 timing, so no class selection changes.
- Suites (Mac): certification controls 16, typed certification 123, BC certification and
  feedback 40, Extensa campaign/targets/selection/budgets/boundary/machinery/library operations
  123, library index/submit/typed library 105, all passed. `swdb validate`: 524 records valid.

**Open finding (not fixed; for Yan-Ru).** A certification run trusts named-check lines by their text:
- `it5.kronecker.a2` calls `swdb_strict::check(..., "duplicate_frontier")` itself. This is an honest
  self-check that fires before the trusted inspection.
- A control build also defines its `-DSWDB_DXC_FAULT_<ID>` macro where candidate code can see it.
- So a hostile candidate could detect a control build and print the expected check, which would
  "reject" every control.
- Proposed hardening: hide the fault selection from the candidate's translation unit, and report
  evaluator checks on a channel the candidate cannot write, for example a file descriptor the
  evaluator opens.
