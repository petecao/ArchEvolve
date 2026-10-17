# 70 — Certification isolation: verdicts the candidate cannot print, faults it cannot see

Created: 2026-10-04 22:05 ET (from the open finding of ticket 67)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-05 13:25 ET (the open items are addressed by ticket 76, certify 1.4); 2026-10-05 00:40 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` (certification command, isolation bullet); [67](67-forged-frontier-control-v2.md), [62](62-spelling-independent-certification-controls.md), [68](68-knob-range-and-schedule-range-checks.md)

**What to build:** `swdb certify` takes every named-check verdict of a candidate-artifact
certification from trusted code outside the candidate's control, and selects negative-control
faults in a way the candidate's translation unit cannot observe.

## Problem (ticket 67 open finding)

Candidate code runs in the same process and the same translation unit as the certification
harness:

- (a) the certifier reads named-check lines (`SWDB_STRICT_ASSERT:`, `SWDB_PRESERVATION_FAIL:`,
  `Verification: PASS`, `SWDB trusted_frontier=`) from stdout and stderr, which the candidate can
  print itself;
- (b) a control build defines `-DSWDB_DXC_FAULT_<ID>` where candidate source can test it.

Either lets a wrong rewrite certify. The candidate behaves normally in positive builds and fakes
the expected rejection, or triggers it on purpose, in control builds. The candidate also owned
`main`, so it chose which vector the verifier saw.

## Acceptance

- [x] Named-check verdicts come only from trusted code; stdout and stderr are never parsed for a
  candidate verdict.
- [x] Fault identity is not visible to the candidate's translation unit.
- [x] A static scan refuses candidate-authored source that names harness or fault symbols.
- [x] Adversarial tests: fake rejection lines are refused; a fault-macro probe is refused by the scan
  and cannot change behavior under faults.
- [x] Ticket 20 (BFS), ticket 42 (BC) and both a7 best candidates still certify, every control
  rejected by its own named check.
- [x] The certify command is versioned (1.3); older certificates keep their meaning.

## Answer

Resolved 2026-10-05 00:40 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation;
revisable.

**Decision: three layers, certify command 1.3.** Code: `swdb/certification_isolation.py`,
`library/dx100/certification/`, `swdb/certification.py` `certify_candidate`.

1. **Record channel; out-of-process verdicts.** For each run the harness opens a record file and
   passes its descriptor (`SWDB_CERT_RECORD_FD`). A separately compiled trusted object
   (`record.cc`) writes these records to it:
   - strict-layer check names (`MAA_functional.hpp` `check()` calls it under `SWDB_CERT_RECORD`);
   - each frontier window as raw vertex IDs;
   - the kernel's returned vector;
   - the witness counters (chunks and strict operations).

   An evaluator-owned `main` (`bfs_driver.inc`, `bc_driver.inc`) calls `DOBFS` or `Brandes` and
   records what it returns. The candidate's own `main` is renamed and never runs. Python computes
   every check from the records with the evaluator's own checks:
   - `verifier`: `bfs_native.verify_parents` or `bc_native.verify_scores` on the returned vector;
   - `duplicate_frontier` and `frontier_size_equality`: from the windows and the oracle counts;
   - `execution_witness`: chunks > 0 and strict operations > 0;
   - strict names: only names in the strict layer's whitelist.

   A malformed or unknown record is `record_invalid`. A strict record cannot name
   `duplicate_frontier`.
2. **Opaque faults.** The candidate is compiled once per tile size with a forced prelude
   (`candidate_prelude.hpp`). The prelude routes the L4 seams to extern functions in `seams.cc`:
   seven DX100 intrinsics, `compare_and_swap` and `QueueBuffer::push_back`. The fault logic of the
   former `faults/dxc_lowering_faults.hpp` moved there unchanged. One fault macro goes on the seam
   object's compile command only.
   - The positive matrix and all eight library-fault controls link the same candidate object.
     Each record carries `candidate_object_sha256` and `seam_object_sha256`, and
     `fault.delivery: separate_object`.
   - `forged_frontier` no longer forges the protected print, because no verdict reads it. Fault
     versions are unchanged (v2).
3. **Harness scan (defense in depth).** Before any build, certify diffs the candidate against the
   registered snapshot and scans only the lines the candidate wrote. It refuses (usage error,
   campaign check `harness_scan`) lines that name:
   - harness or fault symbols (`swdb_strict`, `swdb_seam`, `swdb_cert*`, `SWDB_DXC_FAULT*`, ...);
   - the certification-build macros `SWDB_STRICT` and `FUNC`;
   - descriptor, environment, loader or process primitives (`write`, `getenv`, `dlsym`, `asm`, ...);
   - strings that imitate an evaluator line.

**Versioning.** `VERSION = '1.3'`. Records before 1.3 used printed lines and the in-TU fault macro,
and keep that meaning. Lowering certification and `--calibrate` are unchanged.

**Adversarial results (Mac, g++-16).** The same patches were run under 1.2
(`yanrujhou_main` 1b76897) and under 1.3. Evidence:
[`evaluation/certification-isolation-2026-10-04.json`](../evaluation/certification-isolation-2026-10-04.json).

| Candidate | 1.2 | 1.3 |
|---|---|---|
| Raw-builtin claim. It probes the CAS seam on scratch data, then prints a fake `SWDB_PRESERVATION_FAIL:duplicate_frontier` (built at run time) and exits 88. | **certified**, 20/20 | failed: `skipped_cas_recheck` invalid at both tiles; the fake line is in stderr, no duplicate is on record |
| Raw-builtin claim. It pushes a duplicate under `#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)`. | **certified**, 20/20 | refused by the scan; with the scan disabled it fails: `skipped_cas_recheck` survived, one candidate object per tile |

Tests: `tests/test_certification_isolation.py`, 24 cases. They cover the record judge, malformed
records, the prelude and seam split, the scan, and the three full certifications above.

**Re-certification (1.3 at 401a232, Mac, scratch stores, not committed).**

| Input | Certification | Matrix | Controls rejected by own check |
|---|---|---|---|
| Ticket 20 (BFS patch) | `certification.d0f195fa83fc436fb34e5a1187fcca9a` | 10/10 | 20/20 |
| Ticket 42 (BC patch) | `certification.e6f046255d4e4a35b1f7e2e9a523b054` | 10/10 | 28/28 |
| a7 best kronecker `it4.kronecker.a2` | `certification.5a37994678b2410e8bd1e2a1e36a0a82` | 10/10 | 20/20 |
| a7 best uniform `it8.uniform_random.a1` | `certification.0506911fe295415cb7ab2df5667c36af` | 10/10 | 20/20 |

All four are `certified`, every enforceable clause is matched, and each tile size has exactly one
candidate object across the positive cells and the eight library-fault controls. A run takes
22–41 s, against about 44 s under 1.2, because library-fault controls reuse the candidate object.
Of the six other rebuilt a7 trees, four certify (`it2.kronecker.a1`, `it3.kronecker.a1`,
`it5.kronecker.a1`, `it8.uniform_random.a0`). `it5.kronecker.a2` and `it6.kronecker.a0` are
refused by the scan: the first calls `swdb_strict::check` and tests `SWDB_STRICT`; the second
tests `SWDB_STRICT`. Neither is a class best, and neither was timed, so the a7 selections stand.

**Suites (Mac, at 401a232 or its working tree).**

| Suite | Result |
|---|---|
| Certification isolation and feedback | 52 passed |
| Certification controls | 14 passed |
| Typed and BC certification, legality, feedback | 185 passed |
| Library index, submit and typed library, plus Extensa (7 files) | 228 passed |
| Provider guard, login, pins, role schemas and workspace | 711 passed, 13 skipped |

**Open (not fixed; for Yan-Ru).**
- **Run-time probing remains.** Code in the candidate's process can call a seam on scratch data,
  see the fault's effect, and then misbehave on purpose. One example is a deliberate duplicate push
  after a failed compare "succeeds". 1.3 turns printed fakes into failures, but not real
  misbehavior that a probe triggers. Closing it would need faults the candidate cannot
  distinguish from normal behavior, or process isolation of the seams.
- **The frontier inspection runs inside the candidate's `DOBFS`/`PBFS`**, at the protected print.
  A candidate could hand it a different queue. The final result is still checked out of process.
- **Campaign feedback names surviving controls** (`control:<id>`). This tells an adaptive provider
  which faults exist.
- **Scope.** Calibration (authors' code) and lowering certification still read printed lines.
  Both certify trusted code only.
