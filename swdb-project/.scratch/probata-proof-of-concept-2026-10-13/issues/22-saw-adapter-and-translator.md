# 22 — SAW adapter and SAWScript translator

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 16:40 ET (resolved as the CBMC adapter); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order": bounded verifier, cross-check of the C lowering, pinned versions, failure classes, one summary source; "Bounds": build constants, 15 minutes per bounded job; "Formal-half language and the C++ subset": the translators; "Further Notes": main risks; "Testing Decisions", seam 1; choice S1); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 1, 2, 3, 4, 8; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 1, 3; [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) items 2, 8
**Time estimate:** about 3 days

**What to build:** Yan-Ru runs `swdb prove` on 21's fixture with the bounded verifier and gets either a proof within recorded bounds or a refutation with a concrete counterexample. Our SAWScript translator turns the fixture contract's formal halves into a SAW spec. It also turns each called library entry's formal halves into a spec that SAW uses as an override in place of that entry's code. The SAW adapter (SAW 1.6; or crux-llvm 0.12, if 09 — Spike verdict chose it) proves the safe fixture within bounds and refutes the seeded bug; through `swdb prove` it does the same on map 07's smoke pair. It runs on both the C++ (clang 22.1.8 bitcode) and the C lowering, and the two verdicts must agree: this is the only check on the trusted C lowering tool. A unit outside the C++ subset has no C lowering: SAW runs on the C++ only, with no agreement check, and the record names the reason. Every build constant is recorded exactly; a knob that is only compared stays a symbolic constant limited by its legality clause. Every failure class SAW emits has a handler, and diagnosed failures join 21's regression corpus.

## Acceptance

- [ ] The translator is deterministic: the same formal halves give byte-identical SAWScript. Its version is pinned in the content-hash set and listed as a trusted-tool entry.
- [ ] Summary: `swdb prove` first proves the fixture callee against its generated spec, in one proof record whose subject is a library entry's summary. The unit's record then pins that summary (entry hash plus proof record ID), and SAW uses the spec as an override, not the callee's code.
- [ ] Override negative control: with the callee's spec weakened by hand (one postcondition dropped), the unit no longer proves.
- [ ] Safe fixture: proven within bounds. The record gives each bound dimension's value (threads = 1 and every size bound) and each build constant's exact value. Inputs stay symbolic up to their size bounds.
- [ ] Compared knob (map 19 item 2): a fixture knob that is only compared (like the frontier threshold) is a symbolic constant limited by its legality clause, not a fixed build constant. The record lists it as symbolic, with that clause. Control: a seeded bug that fails at only one legal knob value is refuted, and the counterexample gives that value.
- [ ] Seeded bug: refuted, with a counterexample (concrete input values) stored inline in the proof record.
- [ ] Smoke pair: `swdb prove` on map [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)'s smoke pair (the safe smoke program and its seeded bug, `-DBUGGY`). SAW proves the safe program and refutes the seeded bug with a counterexample.
- [ ] Both forms: one job runs SAW on the C++ and on the C lowering. On the safe fixture both prove; on the seeded bug both refute. The record names both verdicts.
- [ ] Agreement negative control: a hand-mutated C lowering of the safe fixture (one off-by-one) gives disagreeing verdicts. The job stops the batch and names the disagreement; no proven verdict is recorded.
- [ ] Outside the subset: a unit outside the C++ subset has no C lowering, so the job runs SAW on the C++ only, without the agreement check, and the record names the reason ("outside the C++ subset"), as 61 states for itself. Such a candidate artifact reaches at most proven within bounds: with no C lowering, WP has nothing to run on (same skip reason; see 37). Control: a fixture unit outside the subset gets a C++-only verdict, and its record names the reason and no C-lowering verdict.
- [ ] Budget: a job over its time budget (starting value 15 minutes; set small in the test) reads not proven, failure class timeout. It is never retried at smaller bounds.
- [ ] Failure classes: every class the SAW adapter emits (parse error, timeout, out of memory, solver error, tool crash, and any other it meets) maps to its entry in 11's vocabulary file and runs that entry's handler (map 11 item 9). Each class is shown on a fixture or a scripted fault. An outcome with no class stops the batch.
- [ ] Regression corpus: each diagnosed SAW failure (cause named), a C++-versus-C-lowering disagreement included, adds a case to 21's regression corpus, and the case gives its recorded class again.
- [ ] SAW version, solver, flags and clang 22.1.8 are pinned in the content-hash set. SAW and its solver are trusted-tool entries in the assumption set (design S14). On the Mac, jobs go through 21's lock, one at a time, under the ~8 GB RSS watchdog. Tests that need SAW or LLVM 22 skip cleanly.

## Notes

- **Not in this ticket:**
  - 21 — C lowering and WP adapter (A2 tracer): the unbounded verifier.
  - 23 — C-stub translator, fallbacks and check mode: C call stubs, the crux-llvm and CBMC fallbacks, routing real-valued units to crux-llvm `-f real`, check mode, and agreement of the three summary forms.
  - 25 — std::vector and std::pair models: the model's overrides, and mapping struct fields through debug information (16 item 3).
  - 27 — Proof semantics for the BFS read-offload calls: ghost hazard state in SAW.
  - 33 — Minimum-bounds script and A2 exit: minimum bounds, and "below minimum, no level".
  - 13 — Counterexample-guided repair: what happens to a counterexample.
  - 46 — CIVL adapter; 47 — GenMC adapter and agreement: threads > 1.
  - 60 — Strict-layer replay and whole-kernel reproduction: replaying a refutation on the strict layer and reproducing it on the whole kernel (13 item 10).
  - 61 — SAW whole-function equivalence (bounded direct route).
- Assumption (not decided in the map): if 09 — Spike verdict chose crux-llvm, this ticket builds the crux-llvm adapter on the C++ with hand-written C call stubs as summaries (the design's risk table: "crux-llvm with hand stubs"). The SAWScript translator is then not built, and 23's stub translator replaces the hand stubs. Confirm with Yan-Ru when 09 lands.
- Assumption (not decided in the map): a C++-versus-C-lowering disagreement stops the batch and blocks a proven verdict. The design says the verdicts "must agree" but names no handler. Proposed handler: root-cause it as a C lowering tool defect and add the case to 21's regression corpus (acceptance above).
- Risk: whether SAW reads clang 22 bitcode (its README claims LLVM 20) is spike (a)'s question; 09's verdict decides the tool.
- Risk: crux-llvm 0.12 reads LLVM 3.6-21 and could not run libc++ 22 code in map ticket 08. Six crux jobs at once exhausted the Mac's 36 GB, so run one at a time.
- Mac: keep at least 50 GB of disk free; if SAW needs a Homebrew change, check that LLVM 22 still works for the analytic evaluator.

## Later changes
- 2026-10-14 13:19 ET (Yan-Ru accepted ticket 09's A2 changes): this ticket becomes the CBMC adapter on 21's C lowering (no longer SAW): C stubs with one named assert + assume per check, unwind bounds from the sizes with `--unwinding-assertions`, reachability asserts against vacuity, counterexample replay on the C++ (sets `spurious_counterexample` when it does not replay). Reference: `prototype/06c-cbmc/`, shared note cbmc-two-lanes.md.

## Answer

2026-10-14 16:40 ET. **Resolved as the CBMC adapter** (Later changes, 13:19 ET). Every acceptance box is met in
its CBMC form (translations below). Branch `probata-poc/t22`. Interface doc:
[`format-v0.4-cbmc.md`](../../../docs/reference/format-v0.4-cbmc.md).

**What was built**

| Piece | Where |
|---|---|
| CBMC translator (formal halves to a harness and summary stubs; one oracle; three builds: CBMC, differential, replay) | `swdb/cbmc_translator.py` |
| CBMC adapter `swdb prove --adapter cbmc --bounds ...` (lowering, summaries, compared knobs, C-vs-C++ differential, CBMC, reader, replay, handlers) | `swdb/cbmc_adapter.py` |
| `swdb prove --summary <entry>` (subject `library_summary`); `pins.translator` | `swdb/proof.py`, `schemas/proof.schema.json` |
| 14's contract: `TargetAdapter.bounded_job` gives `{adapter: cbmc}` for `threads_1`; `outside_cpp_subset` reads the C lowering; outside the subset skips both rungs | `swdb/campaign_targets.py`, `swdb/bounded_gate.py` |
| Fixtures, stand-in `cbmc`, 4 corpus cases | `tests/fixtures/proof/cbmc/`, `tests/fixtures/proof/regression_corpus/cbmc-*.yaml` |

**Acceptance, box by box (CBMC form)**

- Translator deterministic: two jobs give byte-identical `job.c`; `pins.translator` (ID + sha256 of the module);
  the method version must list it in `c_lowering.translators`; trusted-tool entry `swdb-cbmc-translator-1`.
- Summary: `swdb prove --summary contract.fixture_cbmc_clamp` writes a `library_summary` record (proven); the
  unit `swdb_fixture_clamp_all` then pins `{id, sha256, proof_record}` in `pins.summaries`, and `job.c` holds the
  stub, not the callee's code. Without the summary record the unit job refuses to run.
- Override negative control: one `ensures` dropped from the callee's formal half: the summary still proves, the
  unit no longer does.
- Safe fixture: proven at `{threads: 1, n: 3}` (record bounds exactly these), unwind K = 4, inputs symbolic
  (oracle), build constants in `pins.build_constants`; level `proven_within_bounds_threads_1`.
- Compared knob: `swdb_fixture_threshold` is drawn symbolically within its range and legality clause, listed in
  `settings.symbolic_knobs` with the clause; never a build constant. The one-value bug (`SWDB_SEEDED_KNOB_BUG`)
  is refuted with `inputs.swdb_fixture_threshold == 3`.
- Seeded bug (`i < n - 1`): refuted; `counterexample` inline with concrete `inputs` (n, v, a) and the oracle.
- Smoke pair (map 07's smoke.c as `smoke_main`): safe proven; `-DBUGGY` refuted with `inputs == {x: 41}`.
- Both forms: each job runs CBMC on the C lowering and the C-vs-C++ differential on the bounded domain; a
  refutation is replayed on the C++. `settings.forms` names both verdicts (safe: proven / agrees; bug: refuted /
  refuted, replayed).
- Agreement negative control: a hand-mutated lowering (`SWDB_CBMC_LOWERING_FAULT`, loop stops one early) stops
  the batch with `c_lowering_disagreement` and the first differing input; no record.
- Outside the subset: GAPBS `InitParent` gives not proven, `unsupported_construct`, `settings.outside_cpp_subset`
  names the reason, no agreement and no forms.
- Budget: a job over `--budget-minutes` reads `timeout`, bounds unchanged; handler: never retried smaller.
- Failure classes, each shown: `timeout`, `out_of_memory` (4 MiB cap), `unwinding_bound_too_small` (loop of 2n),
  `vacuous_pass` (contradictory requires), `spurious_counterexample` (stand-in trace that does not replay),
  `parse_error`, `solver_error`, `tool_crash` (stand-in), `unsupported_construct`; unclassified
  (`unclassified_cbmc_outcome`) stops the batch. Each writes `cbmc/handler.json`.
- Regression corpus: 4 cases (`cbmc-lowering-disagreement`, `cbmc-loop-beyond-size-bound`,
  `cbmc-contradictory-preconditions`, `cbmc-cpp-cut-without-build-constants`), each rerun and giving its class.
- Pins and lock: CBMC version (6.11 matches 6.11.0), solver flag, clang 22.1.8 checked against the lineup (a
  mismatch runs nothing); CBMC and its SAT solver are trusted-tool entries; jobs take 21's lock (`real = True`;
  two jobs started together never overlap); RSS watchdog; tests skip without CBMC or clang 22.1.8.

**Tests** (Mac; serial; no xdist; inside `verifier_run.py`): `tests/test_cbmc_adapter.py` (27),
`test_format_doc.py`, `test_proof_records.py`, `test_proof_method_version.py`: **142 passed** in 293 s. Log
`/tmp/claude/probata-runs/t22/pytest-4.log` (sha256 `29128cba38222936`...), report log `report-4.jsonl`
(`6d1c1f4d4be0fbcf`...). Gate and ArchEvolve proof path: `test_bounded_gate_campaign.py`,
`test_archevolve_proof_path.py` (no verifier, `SWDB_FRAMA_C=none`): 40 passed, 1 failed only because this
ticket edited `swdb/proof.py` during the run (estimator identity); after merging the integration tip
(2b3f39dd): `test_cbmc_adapter.py` + `test_format_doc.py` **31 passed** (`pytest-final.log`) and the two gate
cases **2 passed** (`pytest-gate.log`). Runs: `/tmp/claude/probata-runs/t22/` (pytest temp folders deleted).

**SAW to CBMC translations** (each an Assumption; not decided in the map beyond 13:19 ET's change):

- Assumption: "SAWScript translator" = the CBMC translator (ACSL to C harness and stubs); "SAW override" = the C
  stub replacing the callee's definition in the C lowering.
- Assumption: "SAW on the C++ and on the C lowering, verdicts agree" = CBMC on the C lowering plus (a) the native
  C-vs-C++ differential on the bounded domain every job and (b) replay of every counterexample on the C++.
  CBMC never reads the C++ (libc++ 22). A disagreement stops the batch (the ticket's own assumption kept).
- Assumption: "outside the subset: SAW on the C++ only" has no CBMC form: no C lowering means no bounded job;
  directly it reads `unsupported_construct` with the reason; in the gate both rungs skip (`outside_cpp_subset`),
  so such a candidate keeps its certification level (was: at most proven within bounds). Ticket 14's test updated.
- Assumption: SAW's counterexample = CBMC's trace read as the oracle values `swdb_next()` returned, decoded into
  named inputs by the native replay.
- Assumption: SAW's solver = the SAT solver bundled in CBMC, named from the lineup's `--sat-solver` (`cadical`),
  sha256 of the CBMC binary.

**Other assumptions**

- Assumption: size bounds name integer parameters of the proof unit; every interface array has the largest size
  bound's length; one unwind K = largest bound + 1 for every loop (per-loop bounds: ticket 33).
- Assumption: the differential domain is each size -1..bound, knobs over their range, values {-2..2} (scalars
  also INT_MIN/INT_MAX), at most 20 000 runs (fixed-seed sample beyond).
- Assumption: a summary is any formal-frame library entry with a `proof_unit` whose function the unit calls and
  `once: self` formal halves; the fixture uses a rewrite-contract-shaped entry (real per-call summaries: 30).
- Assumption: a compared knob is a contract knob that is a global of the lowering used only as a comparison
  operand; any other use must be a `--define` build constant.
- Assumption: CBMC runs without `--slice-formula` by default (the lineup may add it); slicing could hide oracle
  steps and make a true counterexample read spurious.

**Side findings**

- Diagnosed during the work (corpus case `cbmc-cpp-cut-without-build-constants`): the C++ cut was compiled
  without the build constants; the differential run and the replay caught it (spurious smoke bug, knob
  disagreement). Fixed.
- `swdb.wp_adapter` has the same circular import as the first `cbmc_adapter` draft if imported before
  `swdb.proof`; the CBMC adapter registers itself to avoid it.

**Interface notes**

- 23: extend `swdb.cbmc_translator` (`stub`, `harness`, `expression`): `\old` over memory in stubs, logic calls,
  `\separated`, check mode; the three-form check compares against these stubs.
- 25: model calls become stubs through `tr.stub`; struct-field `assigns` are not translated yet.
- 27: ghost hazard arrays as globals; the harness snapshots scalar globals for the frame; arrays need work.
- 33: minimum-bounds records must use the unit's integer parameter names as dimensions; add per-loop
  `--unwindset`; the A2 exit replays the 14 verdicts with generated stubs (needs 24's widening first).
- 46/47: reuse `cbmc_adapter.Code` (lowering + C++ cut) and the oracle replay; `bounded_job` for `threads_k`.
- 60: start from `counterexample.oracle` / `inputs`; `replay.form: cxx` is stage 1.
- 61: CBMC on a product of two C lowerings with this harness is the natural replacement.
