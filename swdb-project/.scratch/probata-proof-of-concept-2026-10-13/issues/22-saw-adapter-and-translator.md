# 22 — SAW adapter and SAWScript translator

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
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
