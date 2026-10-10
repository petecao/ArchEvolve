# 49 — Port Extensa's machinery

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** resolved
**Blocked by:** 07, 10, 11, 47 (all resolved)
**Spec:** `../spec.md`

**What to build:** Extensa's loop accounting, runtime-probe contract checks, certification profiles and BFS-relevant synthesis run inside SWDB.

Port only what decision D1 lists, from `MaizeHPC/MemAcc` `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, folder `AgenticRefiner/`, read-only. License assumption (Q66): ported files carry `Apache-2.0 WITH LLVM-exception`, pending Peter's confirmation in ticket 02. Ticket 02 is not a blocker.

## Acceptance

- [x] `swdb/extensa/search.py` ports `SearchBudget`, `SearchLedger`, the closed feedback reasons, the leakage check and `plan_rollback`/`apply_rollback` from `refiner/a5/search.py` and `refiner/a5/leakage.py`. Budgets have no code defaults. Tests cover these cases: every opened call is charged; a completed non-improving iteration advances the plateau once; an infrastructure stop does not advance it; rollback restores tracked and untracked files.
- [x] `swdb/extensa/probes.py` ports predicate-to-C++ probe emission from `refiner/legality_testing/contract_check.py` and `dsl_contract.py`. It parses with `swdb/predicate_grammar.py`, emits one negative control per conjunct, and reads verdict lines back into a certification record. Probes are compiled into certification builds only. A test shows that a timed build of the same candidate contains no probe symbol. Provider-supplied bindings are labeled `model_bound` and never make a candidate certified.
- [x] Certification profiles are library YAML (matrix plus control set), modeled on `refiner/a5_certification_profiles.py`. `swdb certify --profile PROFILE` uses them, and there is no second certifier. A test shows that a profile missing a control refuses certification.
- [x] `swdb/extensa/synthesis/` ports `certify.py` (two-binary build, post-hoc seed, sanitizer precondition), `mutants.py`, `families.py`, `spec.py`, `synthesize.py`, `testgen_backend.py`, `targets/base.py`, `targets/cpu_like.py`, `differential_oracle.py`, the pack/regroup/gather/bin-drain case generators of `shape_classes.py`, and the regroup, gather, gather_stream and bin_drain driver templates. A fixture synthesis role call through the provider launcher produces an entry that certifies and enters the experimental tier. A fixture mutant is rejected.
- [x] Every ported file has an SPDX header and a provenance header (commit and original path), and `swdb/extensa/PROVENANCE.md` lists each one. A test fails if a file under `swdb/extensa/` lacks either header.
- [x] Nothing in D1's not-ported list is imported or copied. A test checks `swdb/extensa/` for imports of `agent_runtime`, `claude_invoke`, `measurement`, `fitness`, `profitability`, `a5.loop`, `a5.selection` and `smt_`.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:03 ET (agent, under Yan-Ru's standing implementation approval).

What was built (decision D1 port, MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, read only):

- `swdb/extensa/search.py` (from `a5/search.py`, `a5/outcomes.py`): `SearchBudget` with no code
  defaults (every D5 budget key required, source campaign file named), `SearchLedger` (every opened
  call charged; per-iteration cap refuses the next call; unused calls never carry over; usage-limit
  and login outcomes recorded `counted: false` and the iteration retried; a completed non-improving
  iteration advances the plateau once; an infrastructure stop does not), D6 stop reasons with a
  precedence, closed feedback reasons with structured evaluator fields only, `plan_rollback` /
  `apply_rollback` unchanged. `swdb/extensa/leakage.py` unchanged patterns.
- `swdb/extensa/probes.py` (from `contract_check.py`, `dsl_contract.py`): the deterministic emitter,
  one negative control per conjunct, splice, verdict read-back and `contract_record_from_verdict`.
  Predicates come from library clauses (`extensa_predicate`), sites from the certification build;
  `contract_operand`/`driver_operand` origins are call-bound, anything else (provider) is
  `model_bound` and never passes a certification cell. Probes compile only with
  `probe_build_flags()`; `assert_probe_free` checks timed builds.
- `swdb/extensa/profiles.py` (from `a5_certification_profiles.py`, data model and validation):
  profile YAML under `library/profiles/`; `swdb certify ENTRY --profile P` (one added argument and
  a dispatch line in `swdb/certification.py`) refuses a profile that misses an entry control or a
  required category. No second certifier.
- `swdb/extensa/synthesis/`: `certify.py` (two-binary build, post-hoc seed, sanitizer precondition,
  capture-before-expose, destroy-before-launch, named checks), `mutants.py`, `families.py`,
  `spec.py`, `synthesize.py` and `testgen_backend.py` (through the provider launcher's `synthesis`
  and `independent_test_generation` roles), `targets/base.py`, `targets/cpu_like.py`,
  `differential_oracle.py`, and `shape_classes.py` (pack, regroup, gather, gather_stream, bin_drain
  generators only). Driver templates under `library/library_operations/drivers/` (regroup, gather,
  gather_stream, bin_drain; pack in ticket 50) call SWDB's plain C++ reference
  `library/library_operations/reference/movement_reference.hh`, time nothing, and add an input frame
  check.
- `swdb/library_operations.py` (original SWDB): profile certification of library operations
  (sanitized clang cell, OpenMP g++ cell, optional contract-probe cell; controls rejected only by
  their expected named check), `swdb validate` body rule hook, and `swdb synthesize FAMILY`: one
  synthesis call, install, `swdb certify`; the entry stays (experimental tier) only if certified.
- `swdb/extensa/PROVENANCE.md` lists every ported file; each carries SPDX
  `Apache-2.0 WITH LLVM-exception` and a provenance header (Q66 assumption, pending Peter).

Tests: `tests/test_extensa_machinery.py` (28 cases): budgets, charging, cap, plateau,
infrastructure stop, uncounted pause, rollback of tracked and untracked files, feedback closure,
probes (pass, call-bound failure, model-bound never certifies, timed build probe-free), fixture
synthesis certifies into the experimental tier, fixture mutant rejected and not installed, profile
missing a control refuses, mutation gate, headers and provenance listing, no forbidden imports.
Regression: `test_typed_library`, `test_typed_certification`, `test_library_submit`,
`test_format_doc`: 217 passed; 3 failed only because the sandbox denies `tempfile` writes to
`/private/tmp/swdb-peter-patch-*` (PermissionError, unrelated to this change; they need a normal
shell).

Assumptions (agent-decided, revisable):

- The "matrix" of a library-operation profile is builds (sanitized, OpenMP at the profile's thread
  count) times generated cases; a control is rejected when no build accepts it, none is invalid,
  and its expected named check fired in at least one build.
- `relabel` is an SWDB-added shape class and family (MemAcc has no relabel synthesis driver); it is
  marked as an SWDB addition in the ported file and used by ticket 51.
- Synthesized entries pin the family's generic templates and use the family mutants as their
  controls.
