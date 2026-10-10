# 76 — Certify 1.4: blinded controls, attributed rejections, a trusted frontier ledger, aggregate feedback

Created: 2026-10-05 12:13 ET (from the open items of ticket 70)
Updated: 2026-10-05 17:45 ET (version-label drift addendum); 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-05 14:21 ET (the open library-operation item is addressed by ticket 77); 2026-10-05 13:25 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** 70
**Spec:** `../spec.md` (certification command, "Blinding and attribution" bullet); [70](70-certification-isolation.md), [67](67-forged-frontier-control-v2.md), [65](65-range-loop-convention-and-named-check-feedback.md)

**What to build:** close, as far as one process allows, the four items ticket 70 left open, and
state the rest precisely. Agent-decided under Yan-Ru's delegation ("continue working"); revisable.

## Problem (ticket 70 open items)

1. A candidate can probe a seam at run time (call it on scratch data, watch its behavior, timing,
   symbol addresses or side effects), then misbehave on purpose only under controls.
2. The frontier inspection runs inside the candidate's own function, at the protected print.
3. Campaign feedback names the surviving controls (`control:<id>`); an adaptive provider can learn
   which faults exist and which one it evades.
4. Calibration and lowering certification read printed lines.

## Acceptance

- [x] Positive runs and library-fault control runs are indistinguishable to the candidate until
  the fault acts: one binary, one argument list, one environment, one descriptor layout.
- [x] A control's rejection counts only when attributable to the fault's own action.
- [x] Frontier windows come from trusted code observing the queue, not from code in the
  candidate's function; positive runs check clause L4 directly (seam witness).
- [x] Extensa feedback reports surviving controls only as one aggregate category.
- [x] Calibration and lowering certification: confirmed to run only trusted code, documented, and
  calibration refuses candidate input.
- [x] Adversarial tests for each closed hole; ticket 20, ticket 42 and both a7 bests certify, every
  control rejected by its own named check.
- [x] Certify command 1.4; 1.3 stays selectable and older certificates keep their meaning.

## Answer

Resolved 2026-10-05 13:25 ET by the agent. Agent-decided under Yan-Ru's delegation; revisable.

**Decision: certify 1.4 for candidate artifacts, default; 1.3 unchanged and selectable**
(`certify(..., version='1.3')`, CLI `--command-version 1.3`). Ticket 75's concurrent 1.3 records
stay valid and repeatable. Code: `swdb/certification_blinding.py`,
`library/dx100/certification/v1_4/` (prelude, record, seams, two drivers), `swdb/certification.py`.

1. **One binary, blinded plan, random order (item 1).** Per tile size, one candidate object, one
   record object and one seam object that holds all eight faults are linked once. The positive
   matrix and every library-fault control run that same file (`binary_sha256`). The fault comes in
   a 43-byte plan on a pipe, the same length for "none"; record.cc drains and closes the pipe before
   `main` and echoes the plan's nonce. Both descriptor variables are present in every run and unset
   before `main`. All runs of a tile size (matrix cells and all controls) take a fresh
   `SystemRandom` order (`schedule_order`). State carried across runs therefore cannot tell a control
   from a positive run. Fault behavior is 1.3's, unchanged; fault versions are unchanged.
2. **Attributed rejections (item 1).** The seams record where a fault acted. A library-fault control
   is `rejected` only if its own named check fired *and* the attribution rule holds; otherwise it is
   `invalid`, reason `check_not_attributed_to_fault`.

   | Fault | Rule (from trusted records) |
   |---|---|
   | skipped_cas_recheck | the duplicated window vertex has a push paired with a forged claim at its slot |
   | forged_frontier | the duplicated vertex is the forged push copy, in the frontier queue |
   | chunk_off_by_one, index_wrap | the strict failure is raised inside the stream load the fault modified |
   | shared_context, dropped_wait, read_before_wait | the strict failure is raised on a thread the fault acted on |
   | dropped_continuation | the first divergent level misses a vertex that heads an edge the fault removed |

3. **Trusted frontier ledger, seam witness (item 2).** Nothing is inserted into the candidate's
   function. The prelude's `SlidingQueue` hands each new window to trusted code at `slide_window`.
   The 1.4 driver records the source and, for BFS, the returned parent buffer. Every positive run
   must also pass `seam_witness` (contract clause L4):
   - one frontier queue;
   - each window equals the pushes made into it since the previous slide;
   - every pushed vertex but the source is claimed by the pushing thread through `compare_and_swap`
     at `base + 4·v`, with one `base` per run (for BFS, the returned parent array).

   The execution witness also needs a DX100 gather from that array on a level at the threshold.
   Bypassing the claim or push seam fails every positive cell, whatever the controls do.
4. **Aggregate feedback (item 3).** `certification_feedback.public_checks`: the provider-facing names
   (FEEDBACK.json, CERTIFICATION.json, the rejection text) are as follows.
   - `control:<id>` becomes `negative_controls_not_rejected`, named once and with no count.
   - `negative_control_site:<id>` becomes `negative_control_site`.
   - Matrix checks keep their names.

   The campaign record keeps the detailed names. The contract file the workspace already holds
   still lists every control; only which one survived is withheld.
5. **Calibration and lowering (item 4): confirmed, documented, not moved.** Calibration builds the
   vendored authors' tree, whose identity is checked before and after; `certify --calibrate` now
   refuses candidate input. Lowering certification runs only library files whose sha256 the entry
   pins, checked before and after; candidates are routed to the rewrite-contract path. No provider
   output reaches either path.

The 1.4 scan adds descriptor reads, temporary and shared files, and frame or loader introspection
(`PRIMITIVES_1_4`). It is defense in depth only: no 1.4 guarantee rests on it.

**Not done: a randomized fault activation point.** Attribution makes the activation point
irrelevant to soundness. forged_frontier v2's first-push activation (ticket 67) exists to avoid
false survivals, and randomizing it would bring them back.

**Adversarial results (Mac, g++-16).** Each candidate certifies under 1.3 and fails under 1.4.
Evidence: [`evaluation/certification-blinding-2026-10-05.json`](../evaluation/certification-blinding-2026-10-05.json).

| Candidate | 1.3 | 1.4 |
|---|---|---|
| `probe_claim`. It claims with a raw builtin, probes the claim seam on scratch data each step, and pushes one real duplicate after a probe "succeeds". | **certified**, 10/10, 20/20 | failed: 0/10 cells (`seam_witness`); skipped_cas_recheck not attributed at both tiles |
| `decoy_frontier`. It enqueues up to 8 vertices twice in every run (once_enqueue broken; parents valid). The print and 1.3's hook see a de-duplicated copy, unmasked only when a claim probe or a probe queue push sees a fault. | **certified**, 10/10, 20/20 | failed: 0/10 cells (`duplicate_frontier` read from the real queue); forged_frontier not attributed |

Tests: `tests/test_certification_blinding.py`, 33 cases:
- 30 synthetic-record cases: every seam-witness bypass, the plan binding, each attribution rule
  both ways, the 1.4 scan, the calibration guard and the feedback;
- the two attacks under both versions;
- ticket 20 under 1.4: one binary per tile, distinct nonces, every fault attributed, a
  non-canonical run order.

Suites (Mac, final working tree): certification blinding, isolation, controls, legality, BC and
typed certification, 228 passed; Extensa (7 files), library index, submit and typed library, kernel
plug-ins and feedback, 266 passed. Changed 1.3-era tests: the isolation tests now pass
`version='1.3'`; the claim-bypass control test also expects `seam_witness` on every 1.4 cell; the
feedback test expects the aggregate category.

**Re-certification (1.4, sources_sha256 29f3bcab…, equal to commit c2fb788, Mac, scratch stores, not committed).**

| Input | Certification | Matrix | Controls rejected by own check | Library faults attributed |
|---|---|---|---|---|
| Ticket 20 (BFS patch) | `certification.7fe57c9acff040d6b6f909180693f7a2` | 10/10 | 20/20 | 16/16 |
| Ticket 42 (BC patch) | `certification.b7e2768569754d27a39597a07489eb3c` | 10/10 | 28/28 | 16/16 |
| a7 best kronecker `it4.kronecker.a2` | `certification.50f4824881a44ee2b8bb7ae8d4ac7478` | 10/10 | 20/20 | 16/16 |
| a7 best uniform `it8.uniform_random.a1` | `certification.887956ca495847dab20447785b7c28d9` | 10/10 | 20/20 | 16/16 |

All four are `certified`. Each has one binary per tile size across its positive cells and
library-fault controls, no seam-witness problem, and every enforceable clause matched. A run takes
14–36 s, against 22–41 s under 1.3. Four other a7 trees certify (`it2.kronecker.a1`,
`it3.kronecker.a1`, `it5.kronecker.a1`, `it8.uniform_random.a0`). `it5.kronecker.a2` and
`it6.kronecker.a0` are refused by the scan, as under 1.3. The a7 selections stand.

**Residual threats (in-process limits).**
- **R1, memory introspection.** Candidate code shares the address space with the record and seam
  objects. With pointer arithmetic it can read the drained plan or seam state, read trusted code,
  or write lines to the record descriptor. The scan refuses the names and primitives, not arbitrary
  pointer arithmetic. *Closure:* run the strict model, the seams and the records in an evaluator
  process. The candidate process would hold no evaluator descriptor and would call the seams over
  shared-memory RPC, under a syscall filter (seccomp on Linux) or a ptrace monitor.
- **R2, same-thread probe then amplify.** This applies to the thread-attributed faults
  (shared_context, dropped_wait, read_before_wait) and to dropped_continuation. A candidate can
  route a probe through the faulted seam on the same thread (or stream the real CSR through a probe
  continuation) and then fail the check, or drop exactly the lost heads, on purpose; that is still
  attributed. *Bound:* these controls show only that the matrix exercises the DX100 path. Every
  DX100 operation the candidate really performs is still checked by the strict layer, and every
  result by the verifier, the frontier oracle and the seam witness. *Closure:* data-flow
  attribution, that is, taint from the faulted tiles to the claims and pushes. It needs compiler
  instrumentation of the candidate (a DFSan-style pass), a binary instrumentation tool, or tile
  reads served by the out-of-process model.
- **R3, coverage.** The execution witness's gather-from-the-claimed-array binding can be met by a
  probe gather. Hints and CPU-read values are equal by design, so the data flow from gathered hints
  into claims is not traced. *Closure:* as for R2.
- **R4, input recognition.** A candidate can recognize the finite certification graphs. This is out
  of scope: target correctness is the gem5 check (ADR 0008).

**Open (for Yan-Ru).** Library-operation certification (`certify --profile`, ticket 49) certifies
agent-synthesized bodies. It still classifies a control's abort by the printed line
`SWDB_PRESERVATION_FAIL:frame_violation` (`swdb/extensa/synthesis/certify.py` `classify_abort`).
Its positive verdict compares output bytes, which is sound. A follow-up ticket should give its
controls the same record-channel treatment.

## Addendum: version-label drift (2026-10-05 17:45 ET, code review)

Agent-decided under Yan-Ru's delegation; revisable. No record is edited.

Two behavior changes kept the label "1.4":
- **`certification.b7954f4df9dd4e228fb12437b845f190`** (ticket 75) says command 1.4, but it ran the
  1.3-isolation native path: the ticket 75 branch at 6e1fe61 numbered that path "1.4" before this
  ticket's 1.4 was merged (its `sources_sha256` `06fe4cc5…` is what 6e1fe61's own code records).
  Its procedure is native 1.3.
- **Commit 93a2a94** (ticket 78) renamed the record files of DX100 1.4 runs from the cell or control
  name (`<log>.record`, so the descriptor's path named the fault) to `run-<nonce>.record`, without a
  version change. DX100 1.4 records with `sources_sha256` from c2fb788 (`29f3bcab…`, this ticket's
  re-certifications), 9490d57, 537818e, be156e8, 8c08fe6, 12ec6fe, ce6e6e9 or 9e267fd used cell-named
  files. The same commit added the DX100 directive rule to 1.5, whose prototype records from 12ec6fe,
  ce6e6e9 and 9e267fd lack it.

From 2026-10-05 the labels are disambiguated, not rewritten: `swdb.certification_procedures.classify`
maps each old record to the procedure it ran through `LEGACY_ALIASES`, keyed by family, label and
`sources_sha256` (computed from each commit's own code). Going forward any behavior change gets a new
version: each version's files have a frozen manifest digest in the version table, and
`tests/test_certification_procedures.py` fails when they change without a table change. Ticket 78
records the rest of the review fixes.
