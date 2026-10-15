# 23 — C-stub translator, fallbacks and check mode

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 20:35 ET (resolved in its CBMC form); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
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

## Answer

2026-10-14 20:35 ET. **Resolved in its CBMC form** (Yan-Ru's decision of 2026-10-14 13:19 ET: CBMC 6.11 on the C lowering is the
bounded verifier). Branch `probata-poc/t23`. Interface doc:
[`format-v0.4-stubs-check-mode.md`](../../../docs/reference/format-v0.4-stubs-check-mode.md).

**What was built**

| Piece | Where |
|---|---|
| C-stub translator, version 2: `\old` over memory and globals in stubs (snapshot on entry; tabulated under a quantifier), logic-library calls, `\separated`, ternaries, `double` names and literals, a crux build, check mode's runtime form | `swdb/cbmc_translator.py` |
| Assumes listed under their summary (`pins.summaries[].assumes`); logic definitions ahead of the code; stub fault for the agreement control | `swdb/cbmc_adapter.py`, `schemas/proof.schema.json` |
| crux-llvm 0.12 on the C++ / on the C lowering (`--adapter crux-llvm-cxx|crux-llvm-c`) | `swdb/crux_adapter.py` |
| The C++ of a unit with no C lowering (a real-valued unit) | `swdb/cxx_cut.py` |
| The bounded route and its fallbacks (`--adapter bounded`) | `swdb/bounded_chain.py` |
| Check mode (`swdb runtime-check`) | `swdb/check_mode.py` |
| Summary-form agreement (`swdb summary-agreement`); WP places a summarized callee's ACSL at its anchor | `swdb/summary_agreement.py`, `swdb/wp_adapter.py` |
| Fixtures, stand-in crux, 2 corpus cases | `tests/fixtures/proof/cbmc/`, `tests/fixtures/proof/regression_corpus/crux-*.yaml` |

**Acceptance, box by box**

- [x] Translator deterministic, pinned, trusted tool: `swdb-cbmc-translator-2` (sha256 of the module) in
  `pins.translator` and the assumption set; ticket 22's determinism test still holds. Each `assume` carries
  `assume from summary <entry> sha256 <16>: <clause>`, and `pins.summaries[].assumes` lists them.
- [x] C-stub meaning: a caller breaking the callee's precondition is refuted at `add_one_pre` (replayed); a caller
  expecting `a[0]` (inside `assigns a[i]`) to keep its value is refuted; a caller relying on `a[1]` proves.
- [x] Fallback order: with CBMC and crux-llvm-cxx scripted to `parse_error`, `--adapter bounded` runs CBMC, then
  crux-llvm on the C++, then crux-llvm on the C lowering, which proves; `settings.route.verdict_tool` names it.
- [x] Each fallback for real: crux-llvm-cxx and crux-llvm-c prove the safe fill fixture and refute the seeded bug
  with replayed inputs (CBMC: ticket 22).
- [x] Smoke pair: crux-llvm-cxx proves `smoke_main`, refutes `-DBUGGY` with `x = 41` (CBMC: ticket 22).
- [x] Failure classes (crux): `parse_error`, `unsupported_construct`, `solver_error`, `tool_crash`, `timeout`
  (scripted), `out_of_memory` (4 MiB cap), `unwinding_bound_too_small` (loop of 2n), `vacuous_pass` (contradictory
  requires), `spurious_counterexample` (scripted), unclassified stops the batch. Route handler for `parse_error` and
  `unsupported_construct` = next fallback; a timeout ends the route.
- [x] Regression corpus: `crux-loop-beyond-iteration-bound`, `crux-cxx-cut-of-a-graph-function` (a real diagnosis:
  the cut's refusal escaped the handler and crashed the batch; fixed), each gives its class again.
- [x] Trusted tools: the verdict tool and its solver (`crux-llvm-0.12`, `z3-<version>`; CBMC as in 22).
- [x] Unwinding: CBMC `--unwind K --unwinding-assertions`; crux `--iteration-bound/--recursion-bound` from the
  sizes; one too small reads `unwinding_bound_too_small` on both.
- [x] Explicit float flag: `--floating-point=real` for a real-valued unit, `ieee` otherwise, in `settings.flags` and
  `settings.float_mode`.
- [~] SAW float-mode check: not run. SAW has no adapter since 13:19 ET, so nothing can run it through `swdb prove`.
  Recorded outcome: **not confirmed in this effort**; crux-llvm `-f real` stays the bounded verifier of real-valued
  units (the route's `reason` says so). No method-part record was written (there is no SAW verdict to record).
- [~] Float routing: a real-valued unit (`swdb_fixture_half`, double) goes to crux-llvm `-f real` and the record
  names route and reason. **Not built:** the control "with a passing SAW float-mode record the unit goes to SAW"
  (no SAW adapter to route to).
- [x] CBMC never serves a real-valued unit: with both crux runs unable to read it, no CBMC job starts and
  `settings.route.cbmc` names why.
- [x] Check mode: the fill fixture passes, its seeded bug fails `fill_post.ensures1`; the copy frame clause
  `\forall k; 0 <= k < n ==> b[k] == \old(a[k])` gets a tabulated snapshot and catches the seeded frame violation;
  a quantifier bound on `\result` is refused; a result 1e-3 off passes at tolerance 0.01 and fails at 0.0001.
- [x] Agreement (two forms, see translations): safe callers prove in both; on the buggy scenarios CBMC refutes and
  WP does not prove (timeout).
- [x] Agreement negative control: `SWDB_CBMC_STUB_FAULT` drops `add_one_post.ensures1` from the stub; the check
  fails and names `relies-on-the-postcondition`.
- [x] Lock: every real job goes through `swdb prove`'s verifier lock (`real = True`) under the RSS watchdog; tests
  skip without CBMC, crux-llvm, clang 22.1.8 or Frama-C.

**Tests** (Mac; serial, no xdist; pytest outside the lock, each verifier job inside it): `tests/test_format_doc.py`, `test_cbmc_adapter.py`,
`test_crux_fallbacks.py`, `test_check_mode.py`, `test_summary_agreement.py`, `test_wp_adapter.py`,
`test_proof_records.py`: **119 passed** in 5810 s after merging the integration tip 2dff3f58 (commit 268d6534); log
`/tmp/claude/probata-runs/t23/pytest-final2.log` (sha256 `1c94baa4a0cf0595`...), report log `report-final2.jsonl`
(`a7f945cc4e0a6f31`...). A second merge (tip c1bfea05: tickets 27, 35, 61 touched the translator, CBMC and WP
adapters; commit dab3d479) passed `test_format_doc.py` + `test_check_mode.py` (8) and the first tests of the same
targeted set (`pytest-final3.log`); the full rerun was cut short by the pause (see the report).

**SAW to CBMC translations** (each an Assumption; not decided in the map beyond 13:19 ET's change)

- Assumption: the route of a unit that is not real-valued is CBMC (C lowering), then crux-llvm (C++), then
  crux-llvm (C lowering): CBMC moved from the last fallback to the bounded verifier; the other two keep the design's
  order.
- Assumption: "three-form agreement" is two forms, C stubs (CBMC) and ACSL (WP); the SAWScript form has no verifier
  left (the ticket's own crux-llvm assumption already allowed this).
- Assumption: the SAW float-mode check closes as "not confirmed in this effort" without a run (see above).

**Other assumptions**

- Assumption: check mode is its own command (`swdb runtime-check`), not an entry of `swdb prove`: a passing runtime
  check proves nothing, so it writes no record. 31's gate 4 calls `check_mode.run`.
- Assumption: `assigns` has no runtime form (it names locations, not values; E-ACSL drops it too). Reals compare
  within the tolerance on `==`/`!=` only; ordering comparisons stay exact.
- Assumption: the check-mode tolerance is `--tolerance`, else the kernel record's `correctness_check.tolerance.value`,
  else exact.
- Assumption: crux-llvm's iteration bound is per call frame and summed over the frame's loops (measured), so the
  adapter sets it to the largest of K and each generated frame's need (loops x K), and the recursion bound to K + 1
  (a first call counts once). The "one too small" control holds for units whose harness has no loops (twice).
- Assumption: a unit counts as real-valued when its interface or its formal halves use a floating type, `real` or a
  real literal (the ticket's own assumption). After ticket 24's float lowering merged, `crux-llvm-c` can lower such a
  unit too.
- Assumption: the agreement scenarios run the callers on the C++ of the safe candidate; WP proves the callee's body
  against its summary in the same job.

**Side findings**

- The CBMC differential run reports a candidate whose real code has undefined behavior on the bounded domain (an
  out-of-bounds write) as `tool_crash` (the native run aborts). Such code should probably read refuted or get its
  own handling; left as is (ticket 22's code).
- crux-llvm 0.12 in `-f real` mode writes no value for a real variable in its counterexample; the replay uses 0.0.
- `swdb.wp_adapter` still has ticket 22's circular import when imported before `swdb.proof` (unchanged).
- With other sessions' jobs queued on the machine-wide lock, one `swdb summary-agreement` call can exceed the test
  helper's 600 s; the agreement test passes a 3600 s timeout.

**Interface notes**

- 29/30: `swdb summary-agreement --scenarios <yaml>` (`{name, candidate, function, contract, bounds, expect,
  defines}`); stubs from `cbmc_translator.stub(..., logic=, drop=)`; WP now places a callee's `once: self` formal
  halves at `<callee>.contract`.
- 31: gate 4 calls `swdb.check_mode.run(library, contract, source, function, bounds, defines, tolerance,
  tolerance_source, out)`; refusals raise `Untranslatable`.
- 24 (merged): the C lowering reads `float`/`double`; `swdb.cxx_cut` now serves only units the lowering refuses.
- 33: per-loop bounds would replace the single K of CBMC and crux.
- Runs: `/tmp/claude/probata-runs/t23/` (pytest logs, report logs, crux explorations).
