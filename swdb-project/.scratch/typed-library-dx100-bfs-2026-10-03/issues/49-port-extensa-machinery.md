# 49 — Port Extensa's machinery

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 07, 10, 11, 47 (all resolved)
**Spec:** `../spec.md`

**What to build:** Extensa's loop accounting, runtime-probe contract checks, certification profiles and BFS-relevant synthesis run inside SWDB.

Port only what decision D1 lists, from `MaizeHPC/MemAcc` `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, folder `AgenticRefiner/`, read-only. License assumption (Q66): ported files carry `Apache-2.0 WITH LLVM-exception`, pending Peter's confirmation in ticket 02. Ticket 02 is not a blocker.

## Acceptance

- [ ] `swdb/extensa/search.py` ports `SearchBudget`, `SearchLedger`, the closed feedback reasons, the leakage check and `plan_rollback`/`apply_rollback` from `refiner/a5/search.py` and `refiner/a5/leakage.py`. Budgets have no code defaults. Tests cover these cases: every opened call is charged; a completed non-improving iteration advances the plateau once; an infrastructure stop does not advance it; rollback restores tracked and untracked files.
- [ ] `swdb/extensa/probes.py` ports predicate-to-C++ probe emission from `refiner/legality_testing/contract_check.py` and `dsl_contract.py`. It parses with `swdb/predicate_grammar.py`, emits one negative control per conjunct, and reads verdict lines back into a certification record. Probes are compiled into certification builds only. A test shows that a timed build of the same candidate contains no probe symbol. Provider-supplied bindings are labeled `model_bound` and never make a candidate certified.
- [ ] Certification profiles are library YAML (matrix plus control set), modeled on `refiner/a5_certification_profiles.py`. `swdb certify --profile PROFILE` uses them, and there is no second certifier. A test shows that a profile missing a control refuses certification.
- [ ] `swdb/extensa/synthesis/` ports `certify.py` (two-binary build, post-hoc seed, sanitizer precondition), `mutants.py`, `families.py`, `spec.py`, `synthesize.py`, `testgen_backend.py`, `targets/base.py`, `targets/cpu_like.py`, `differential_oracle.py`, the pack/regroup/gather/bin-drain case generators of `shape_classes.py`, and the regroup, gather, gather_stream and bin_drain driver templates. A fixture synthesis role call through the provider launcher produces an entry that certifies and enters the experimental tier. A fixture mutant is rejected.
- [ ] Every ported file has an SPDX header and a provenance header (commit and original path), and `swdb/extensa/PROVENANCE.md` lists each one. A test fails if a file under `swdb/extensa/` lacks either header.
- [ ] Nothing in D1's not-ported list is imported or copied. A test checks `swdb/extensa/` for imports of `agent_runtime`, `claude_invoke`, `measurement`, `fitness`, `profitability`, `a5.loop`, `a5.selection` and `smt_`.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
