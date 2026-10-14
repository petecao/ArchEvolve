# 23 — C-stub translator, fallbacks and check mode

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 22
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order": fallbacks, one summary source, summary-only `assume`s, floats as reals; "Bounds": unroll depth and unwinding assertions; "Formal-half language and the C++ subset": runtime-check form; "DX100 proof semantics": the three summary forms agree; "Proof-of-concept plan": A2 exit; "Testing Decisions", seam 1; choice S1); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 2, 4, 6, 9; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 1, 8; [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) item 5; also [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) item 8 (form agreement)
**Time estimate:** about 3 days

**What to build:** Every summary now exists in all three forms from one source, every bounded fallback works, and each formal half can also run as a runtime check. Our C call-stub translator turns a library entry's formal halves into a C stub: assert the precondition, havoc the `assigns` ranges, assume the postcondition. Those are the only `assume`s a bounded job may contain. When the bounded verifier before it cannot read the code, `swdb prove` falls back in a fixed order: crux-llvm 0.12 on the C++, then crux-llvm on the C lowering, then CBMC 6.11 on the C lowering. Unwinding assertions are always on, and unwind limits are computed from the size bounds. This ticket runs and records a SAW float-mode check on the synthetic CSR pull-sum fixture: if it passes, SAW serves real-valued proof units; if not, the record says "not confirmed in this effort" and crux-llvm `-f real` stays their bounded verifier. CBMC checks floats bit-precisely, so it never serves a real-valued unit. crux-llvm and CBMC each pass map 07's smoke pair through `swdb prove`, and each failure class they emit has a handler. Check mode gives each formal half a runtime form: it snapshots each `\old` range on entry, runs bounded quantifiers as loops, and compares reals within the kernel's certify tolerance. On fixture scenarios, the three summary forms (SAWScript, C stubs, ACSL) give the same verdict.

## Acceptance

- [ ] The C-stub translator is deterministic; its version is pinned in the content-hash set and listed as a trusted-tool entry. Each `assume` it emits is tagged with its summary (entry and hash), and the proof record lists it under that summary.
- [ ] C-stub meaning, with negative controls: a caller that breaks the callee's precondition is refuted (the assert fires). A caller that expects a location inside `assigns` to keep its value is refuted. A caller that relies on a location outside `assigns` proves.
- [ ] Fallback order: on a unit that is not real-valued, with each earlier tool scripted to fail with "parse error", `swdb prove` runs crux-llvm on the C++, then crux-llvm on the C lowering, then CBMC on the C lowering. The record names the tool that gave the verdict.
- [ ] Each fallback, run for real, proves the safe fixture and refutes the seeded bug with a counterexample.
- [ ] Smoke pair: `swdb prove` on map [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)'s smoke pair (the safe smoke program and its seeded bug, `-DBUGGY`), once with crux-llvm and once with CBMC. Each proves the safe program and refutes the seeded bug with a counterexample.
- [ ] Failure classes: every class crux-llvm or CBMC emits (parse error, unsupported construct, unwinding bound too small, timeout, out of memory, solver error, tool crash, and any other met) maps to its entry in 11's vocabulary file and runs that entry's handler (map 11 item 9). For parse error and unsupported construct, the handler is the next fallback (assumption below). Each class is shown on a fixture or a scripted fault. An outcome with no class stops the batch.
- [ ] Regression corpus: each diagnosed crux-llvm or CBMC failure (cause named) adds a case to 21's regression corpus, and the case gives its recorded class again.
- [ ] The record's assumption set lists the tool that gave the verdict and its solver as trusted-tool entries (design S14).
- [ ] Unwinding: crux-llvm and CBMC run with unwinding assertions on and a limit computed from the size bounds. Negative control: a limit one too small reads not proven, "unwinding bound too small", never proven.
- [ ] crux-llvm always gets an explicit float flag (`-f real` for real-valued fixtures), recorded in the proof record.
- [ ] SAW float-mode check, recorded (map 11 item 6: crux-llvm `-f real` "until SAW's float mode is confirmed"): `swdb prove` runs SAW on the synthetic CSR pull-sum fixture and writes the check's record. If it passes, SAW serves real-valued units from then on. If it fails, the record says "not confirmed in this effort" and crux-llvm `-f real` stays. Either outcome closes this criterion; the ticket's answer names it.
- [ ] Float routing (design, "Verifier lineup and order"; map 11 item 6): a real-valued proof unit runs crux-llvm with `-f real` as its bounded verifier, not SAW, unless a counting record of a passing SAW float-mode check exists. The record names the route and the reason. Control: with a fixture record of a passing check in place, the same unit goes to SAW; with one that reads "not confirmed in this effort", it stays on crux-llvm.
- [ ] CBMC never serves a real-valued unit (reading of design "floats as reals"; CBMC checks floats bit-precisely). Control: on a real-valued unit with both crux-llvm runs scripted to fail with "parse error", no CBMC job starts, and the record names that reason.
- [ ] Check mode on a fixture: a correct implementation passes every runtime form, and a seeded bug fails one. A frame clause stating that each `b[k]` equals the old `a[k]` for k below n gets a runtime form and catches a frame violation (E-ACSL drops this form). A quantifier bound that depends on the post-state is refused. A real result within the certify tolerance passes; one outside it fails.
- [ ] Three-form agreement on fixture scenarios: every safe scenario proves in all three forms. On every buggy scenario the SAWScript and C-stub forms refute and WP does not prove.
- [ ] Agreement negative control: a hand-weakened C stub (postcondition dropped) makes the agreement check fail and names the scenario.
- [ ] On the Mac, real jobs go through 21's lock, one at a time, under the ~8 GB RSS watchdog. Tests that need crux-llvm, CBMC or LLVM 22 skip cleanly.

## Notes

- **Not in this ticket:**
  - 22 — SAW adapter and SAWScript translator: the primary bounded verifier and its translator.
  - 29 — Proof-semantics checks: translator agreement on the strict wait-rule fixture scenarios, per proof-semantics version.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions: this ticket's agreement check run on each per-call `dxc_*` summary.
  - 31 — Five-gate drafting and the new bfs_read_offload version: gate 4, the runtime form on every certify run of the reference instance.
  - 36 — Proof setup check and verdict reading: refusing any `assume` that no summary generated.
  - 33 — Minimum-bounds script and A2 exit: minimum bounds, and the A2 exit check.
  - 25 — std::vector and std::pair models: the model as C call stubs.
- Assumption (not decided in the map): a fallback runs only when the tool before it cannot read the code (parse error or unsupported construct). A proof, a refutation or a timeout is that tool's verdict, and a timeout never moves to another tool.
- Assumption (not decided in the map): the SAW float-mode check runs SAW on the synthetic CSR pull-sum fixture (spike (d)'s, 08) and on a seeded bug of it, and passes when SAW's verdicts match crux-llvm `-f real`'s on both (safe proves; bug refuted with a counterexample). Its record is a method-part proof record pinned to the SAW version, so a new SAW pin makes it stop counting and routing returns to crux-llvm `-f real`. A unit counts as real-valued when its interface or its formal halves use a floating type or `real`.
- CBMC and real-valued units (reading, no new decision): the design runs floats as reals; CBMC checks them bit-precisely, so it never serves a real-valued unit. Assumption (not decided in the map): when both crux-llvm runs cannot read a real-valued unit, the chain ends there and the unit reads not proven with the last run's failure class.
- Assumption (not decided in the map): where check mode is exposed (an entry of `swdb prove`, or the certification command for 31's gate 4) is open. Tests go through a public command, never internal helpers.
- Assumption (not decided in the map): "the same verdict" for WP means not proven where the bounded forms refute, because WP never refutes.
- E-ACSL is only a cross-check. It counts only when it emits no "Ignoring annotation" (16 item 8).
- Risk: crux-llvm 0.12 supports LLVM 3.6-21. Map 07 ran it on clang 22 bitcode (compiled first, then `--no-compile`): it warns about debug metadata, but its verdicts were right. Code that needs libc++ (map 08) cannot run on the C++, so expect the second fallback (crux-llvm on the C lowering) there. A stale `crux-build/` folder is silently reused. CBMC cannot parse libc++ 22 headers, which is why it runs only on the C lowering.
- Assumption (not decided in the map): if 09 — Spike verdict chose crux-llvm (22's assumption), crux-llvm on the C++ is the primary bounded verifier, the fallbacks start at crux-llvm on the C lowering, and the agreement check covers the C-stub and ACSL forms. Confirm with Yan-Ru when 09 lands.
- Mac: keep at least 50 GB of disk free; after any Homebrew change, check that LLVM 22 still works for the analytic evaluator.
