# 24 — C++ subset widening

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 22:35 ET (Progress, paused)
**Type:** slice
**Status:** claimed
**Blocked by:** 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Formal-half language and the C++ subset": the subset by construct and kept names; "Verifier lineup and order": failure classes; "Records and levels": method-version file contents; "Testing Decisions", seam 1; choice S1); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 3, 9; [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 2; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 3, 6
**Time estimate:** about 4 days

**What to build:** The C lowering tool grows from 21's core (functions, arrays, loops) to the declared C++ subset, construct by construct, so GAPBS-style candidate artifacts can reach WP. Accepted: C plus references; classes without inheritance or virtual functions; member functions and operators; constructors and destructors as explicit calls; instantiated templates; `new[]` and `delete[]`; `enum class`, `constexpr`, `static_assert`; `std::min`, `std::max`, `std::copy`, `std::swap` through C models proven once; the OpenMP constructs (`parallel`, `for` with static, dynamic and `nowait`, `critical`, `atomic`, `barrier`, `reduction`); `__sync_*` and `__atomic_*`; `__dxc_*` and `maa_*` calls through summaries. The C lowering keeps C++ names: a class becomes a struct with the same name and fields, references become pointers, operators become named functions. So formal halves type-check unchanged. Anything outside the subset gives failure class "unsupported construct", never a crash or a partial C lowering. The naming rules are versioned and belong to the content-hash set.

## Acceptance

- [ ] One fixture per construct group lowers deterministically (twice, identical C and anchors). Its ACSL type-checks over the kept names. `swdb prove` with the real WP adapter proves the safe version, and a seeded bug reads not proven.
- [ ] Kept names: a class fixture's formal half, written over the class's field names, type-checks against the C lowering with no renaming. A reference parameter becomes a pointer; an operator and a member function become named functions under the naming rules; constructors and destructors appear as explicit calls.
- [ ] Templates: a template instantiated at two types lowers to two C functions, named by the naming rules. `enum class` lowers to `int`.
- [ ] `new[]` and `delete[]`: a fixture that indexes out of range, or reads after `delete[]`, reads not proven; the in-range fixture proves.
- [ ] Each of `std::min`, `std::max`, `std::copy`, `std::swap` lowers to a call of its C model. Each model's ACSL contract is proven once (one proof record each, subject: a library entry's summary). A unit that uses a model pins that record.
- [ ] An OpenMP fixture (`parallel for` with a `reduction`, a `critical` section, an `atomic`, a `barrier`) and an atomics fixture (`__sync_*`, `__atomic_*`) lower and prove at threads = 1.
- [ ] A fixture with a `__dxc_*` call and one with a `maa_*` call keep each as a call whose contract comes from a fixture summary. The record lists the summary used.
- [ ] Unsupported constructs: inheritance, a virtual function, an exception, a lambda, RTTI, another standard container (such as `std::map`) and a stream each read not proven, "unsupported construct", naming the construct and its source location.
- [ ] Naming rules carry a version. Every proof record pins it in its content-hash set, and bumping the version gives a different pin.
- [ ] Each diagnosed failure joins 21's regression corpus. Fixtures use no BC, PR or SSSP code. Tests that need Frama-C or LLVM 22 skip cleanly.

## Notes

- **Not in this ticket:**
  - 25 — std::vector and std::pair models: `std::vector<T>`, `std::pair`, and the "allocation succeeds" entry (which then covers `new[]` too).
  - 45 — Per-thread lowering: the program for one symbolic thread of N, sharing classes, uniform control, and the memory-model meaning of atomics for symbolic N (history reads, a CAS as a sequentially consistent read-modify-write).
  - 44 — Shared-action kinds and commutativity lemmas: the closed list of kinds and their lemmas.
  - 46 — CIVL adapter: the history-read encoding CIVL needs. 47 — GenMC adapter and agreement: the pthreads harness GenMC runs.
  - 27 — Proof semantics for the BFS read-offload calls; 28 — Proof semantics for the remaining maa_* calls: the contracts behind `maa_*` calls and the hazard check at each tile-pointer read.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions: the real per-call summaries for `__dxc_*`.
  - 22 — SAW adapter and SAWScript translator: the C++-versus-C-lowering agreement check.
  - 11 — Method-version file and failure classes: the method-version file that lists the subset and naming rules.
  - 16 — Post-campaign WP phase and budgets: the loop's skip reason "outside the C++ subset" (a candidate artifact outside it reaches at most proven within bounds).
- Assumption (not decided in the map): OpenMP constructs and atomics get their single-thread meaning here (a parallel region runs as one thread; a CAS is a read, a compare and a write). Their meaning for symbolic N comes with 45 — Per-thread lowering (history reads; a CAS as a sequentially consistent read-modify-write), not 44. CIVL's history-read encoding is delivered with 46 — CIVL adapter, and GenMC's pthreads harness with 47 — GenMC adapter and agreement.
- Assumption (not decided in the map): 24 does not wait for 22, so until 22's agreement check runs on these fixtures, nothing checks that each construct's C lowering is faithful. WP proves the C lowering, not the C++. Once 22 lands, the agreement check should run on every fixture here; a disagreement reopens this ticket.
- Assumption (not decided in the map): a `__dxc_*` or `maa_*` call with no summary available reads "unsupported construct" until 27, 28 and 30 supply summaries.
- Measuring subset coverage on Extensa-campaign candidate artifacts (13 item 2) is not part of this ticket.
- Why `std::copy` and `std::swap`: GAPBS's `QueueBuffer` and `pvector` use them (13 item 2).
- Held-out kernels (BC, PR, SSSP) are never used before the freeze (59 — Method-version review and freeze).
- Mac: one real verifier job at a time through 21's lock, under the ~8 GB RSS watchdog; keep at least 50 GB free. If the C lowering tool uses LLVM 22, the analytic evaluator must keep working.
- WP runs fail inside the Bash sandbox (the Why3 socket is blocked); run WP jobs outside it.

## Answer

2026-10-14 17:10 ET (first pass; superseded in part by "Progress (paused)" below). The C lowering tool now covers the declared C++ subset (plus
`float`/`double`, asked by ticket 26), and its lowering of spike (b)'s proof unit 1 agrees with ticket 06's
hand lowering on every bounded input. The WP-proof boxes are **not met** (see "Not met"). Branch
`probata-poc/t24`. Interface doc: [`format-v0.4-c-lowering-wp.md`](../../../docs/reference/format-v0.4-c-lowering-wp.md)
("`swdb lower`", naming-rules table).

**What was built**

| Piece | Where |
|---|---|
| Widened lowering: `_Unit` (dumps by name, structs, functions, models, summaries) and `_Printer`; `TOOL_VERSION` 2 | `swdb/c_lowering.py` |
| Naming rules `kept-names.2` (`RULES`, `RULES_SHA256`, `naming_rules()`), pinned as `pins.naming_rules` by the WP adapter | `swdb/c_lowering.py`, `swdb/wp_adapter.py`, `schemas/proof.schema.json` |
| `swdb lower --summary NAME=SUMMARY`; `lower(..., summaries={...})` (keyword, default None: 22's call is unchanged) | `swdb/c_lowering.py` |
| One fixture + one C/C++ harness per construct group; the spike differential fixture | `tests/fixtures/proof/lowering/` |
| Regression corpus: spike case renamed to `lowering-spike-unit-push-hook-inheritance`, new `lowering-dxc-call-without-summary` | `tests/fixtures/proof/regression_corpus/` |

**Constructs added** (each with a fixture): references (pointers; bound temporaries as compound literals);
classes without inheritance or virtual functions (fields, member functions, const members, operators as
named functions, constructors with member initializers incl. reference members, destructors called at scope
end); instantiated function and class templates (type and integer arguments, defaulted arguments named);
`enum`/`enum class` (underlying type, enumerators as values); `constexpr`; `static_assert` (dropped with a
comment); default arguments (expanded at the call); `new[]`/`delete[]` (`malloc`/`free`); `std::min`,
`std::max`, `std::swap`, `std::copy` as C models with ACSL contracts; OpenMP `parallel`, `for` (static,
dynamic, `nowait`), `critical`, `atomic`, `barrier`, `reduction` at one thread (clauses read from the pragma
text, since clang's JSON dump omits clause kinds); `__atomic_*` and `__sync_*` as one-thread C models;
summarized calls; string literals; `float`/`double`.

**Acceptance, box by box**

- Fixture per construct group lowers twice to identical C and anchors, compiles as C11 `-Wall -Werror`, and
  agrees with the C++ on a bounded domain (one shared harness, two builds): **met**. The class group's
  formal half (over `Bag`'s field names) type-checks with Frama-C; a wrong field name is refused: **met**.
  `swdb prove` with the real WP adapter on each group (safe proves, seeded bug not proven): **not met**.
- Kept names: struct of the same name and fields, reference parameter to pointer, `Bag_operator_index`,
  `Bag_size`, `Counter_ctor`/`Counter_dtor` as explicit calls: **met**.
- Templates at two types give `twice_int`/`twice_long`, `Ring_int_3`/`Ring_long_2`; `enum class` to `int`: **met**.
- `new[]`/`delete[]` lower (safe and both seeded bugs): **met**; proving/refusing them with WP: **not met**.
- `std::*` lower to model calls with contracts: **met**; each model proven once with its own proof record,
  pinned by units that use it: **not met** (no record kind or pin path for a library model yet).
- OpenMP and atomics fixtures lower and agree with the C++ (one thread): **met**; proved at threads = 1: **not met**.
- `__dxc_*` and `maa_*` fixtures keep the call through a fixture summary; `<f>.anchors.json` lists the
  summary: **met**; the proof record listing it (`pins.summaries` needs a summary proof record): **not met**.
- Unsupported: inheritance, virtual function, exception, lambda, RTTI, `std::map`, stream (and `long double`,
  other OpenMP directives and clauses, no body, overloads) give `unsupported construct: <what> (<file> line N)`,
  nothing written: **met** at `swdb lower` (the WP adapter already maps it to not proven, `unsupported_construct`).
- Naming rules carry a version and hash; WP records pin `pins.naming_rules`; a bumped version hashes
  differently: **met** (`test_wp_adapter.py` passes with the new pin).
- Regression corpus, no BC/PR/SSSP code, skips without clang or Frama-C: **met**.

**Spike differential (the dispatch target).** `tests/fixtures/proof/lowering/spike_peter_unit.cc` is
`unit_peter.cpp` with one change: the candidate prelude's push hook (`swdb_hooked_QueueBuffer : public
QueueBuffer<T>`) uses inheritance, so it is undone (`#undef QueueBuffer`); Peter's code is included unchanged.
Its lowering (summaries for the 12 declared-only DX100 and probe calls, defined in the test by the 06c stubs
as `faith/faith_cxx.cpp` does) and `prototype/06c-cbmc/unit_peter.c` run ticket 06's native harness over all
1,731,456 bounded inputs: identical output stream (state hash, DX100 call-trace hash, P2 failures) and
identical full trace on the SAW concrete input. Safe build only: the seven fault builds need the push hook.
`unit_maa.cpp` was not attempted.

**Not met, and why.** Every WP box needs a contract library entry and candidate artifact per group plus a WP
job each through the machine-wide lock; today the lock queue (8-10 jobs from parallel tickets) cost 18-20
minutes per acquisition, and the model-proof box also needs a decision on how a library model's proof record
is named and pinned. Suggested follow-up "24b: WP proofs of the construct-group fixtures": one fixture
contract per group (the fixtures and seeded bugs exist), one proof record per C model, summaries in
`pins.summaries`. For it: WP has no `\fresh` (ticket 07), so the in-range `new[]` fixture may need ticket 25's
"allocation succeeds" entry before it proves.

**Findings**

- The spike unit as built is outside the subset only because of the push hook's inheritance: a hook without
  inheritance in `library/dx100/certification/candidate_prelude.hpp` would bring the fault builds in.
- clang prints class template types without defaulted arguments (`CSRGraph<int>`); the struct name spells
  every argument (`CSRGraph_int_int_true`). GAPBS's `InitParent` and `TDStep` now pass `CSRGraph` and stop
  at `EdgePair<int>`: two instantiations match its printed arguments (`EdgePair<int, int>` and
  `EdgePair<int, NodeWeight<...>>`), refused as "defaulted arguments that match more than one instantiation".
  Resolving it needs the template's default arguments (dependent in clang's dump); left for the GAPBS
  coverage measurement (13 item 2).
- clang's JSON dump omits OpenMP clause kinds, so the tool reads the pragma text by file offset.
- `std::min` on `size_t` names its model `std_min_size_t` (the C type as printed); struct names resolve
  typedefs (`pvector<int32_t>` and `pvector<int>` are one struct).

**Assumptions** (not decided in the map)

- Assumption: `reinterpret_cast` between pointer types, default arguments and string literals are in the
  subset ("C plus references"; the spike needs them); each lowers to plain C.
- Assumption: a `__dxc_*` or `maa_*` function defined in the translation unit still goes through its
  summary, never its body.
- Assumption: a `return`, `break` or `continue` out of a scope that must run a destructor is refused (not
  lowered with destructor calls on each exit); temporaries with destructors are refused.
- Assumption: a reduction lowers as the plain update only when each use of the variable is an `op=` update
  (`+ - * & | ^`); otherwise refused.
- Assumption (ticket 26's request): `float` and `double` are in the subset; the C is IEEE-faithful and the
  proof's float model is the method version's WP flag (`-wp-model +real`: floats as reals, the rounding gap an
  assumption entry per map 11 item 6). `long double` stays out.

**Evidence.** Targeted runs (no xdist, `-m "not whole_store"`) after merging the integration tip:
`tests/test_c_lowering.py`, `test_format_doc.py`, `test_wp_adapter.py`, `test_cbmc_adapter.py`,
`test_formal_frame.py`: 163 passed; 2 WP-adapter cases hit the test's 600 s subprocess timeout while
`swdb prove` waited in the shared verifier queue (both passed in the pre-merge run r3) and were rerun alone: 2 passed
(`tests9.log`). Logs and report logs: `/tmp/claude/probata-runs/t24/` (`tests8.log`, `report-r8.jsonl`).
Merge note: ticket 22's CBMC adapter now also pins `naming_rules`, and its tests and doc name
`swdb-c-lowering-2`; `c_lowering._named` stays for its `_cut`.

## Progress (paused)

2026-10-14 22:35 ET. Paused at Yan-Ru's request; **Status stays `claimed`**. Branch `probata-poc/t24`.

**Done since the first pass**

- WP proofs of the construct groups through the real `swdb prove --adapter wp` (`tests/test_wp_subset.py`; seed:
  GAPBS bfs.cc with every fixture of `tests/fixtures/proof/lowering/` inserted, one safe and one seeded-bug
  candidate, one fixture contract per group). Safe proves and seeded bug reads not proven for classes, OpenMP,
  atomics, floats, the `__dxc_*` summary, the `maa_*` summaries and `new[]` (run r12,
  `/tmp/claude/probata-runs/t24/tests12.log`). std_models and templates proved in the dev runs
  (`/tmp/claude/probata-runs/t24/dev1.log`, `dev2.log`) but hit the test's 600 s subprocess timeout in r12 while
  `swdb prove` waited in the shared verifier queue.
- WP adapter (`swdb/wp_adapter.py`): lowered callees are inlined (`-inline-calls`), WP proves only the unit
  (`-wp-fct`), and the verdict reader reads only the unit's properties. Summarized callees stay calls, with the
  entry's `once: self` halves as their contract. `swdb prove --summary ENTRY --adapter wp` proves a summary on the
  entry's own code. Unit records pin `pins.summaries: [{id, sha256, proof_record}]` (ticket 22's shape) and list
  a `summary` assumption entry each. `formal_frame.lowered` lowers with the same summaries.
- `new[]`/`delete[]` lower to allocation models whose contracts are the assumption entry "allocation succeeds"
  (`assumed_clause`). An index out of range reads not proven. A read after `delete[]` proves, because WP 33 has
  no deallocation (`\fresh`, `\freeable` and `frees` are unsupported; experiment
  `/tmp/claude/probata-runs/t24/explore/alloc.log`). It is kept as a strict xfail.
- C models: `model_definition`/`model_text` in `c_lowering.py`. `swdb prove --model NAME --adapter wp` (subject
  `c_model`, `pins.models`) is built, and its 14 model records prove. **The coordinator moved this item to
  ticket 25 (2026-10-14, about 21:20 ET)**: 25 replaces or adopts it at merge; nothing else depends on it.
- Inheritance stays outside the declared subset (map 16 item 6, "out at first"). It is not built, so
  unit_peter's fault builds still cannot run. `unit_maa.cpp` now lowers up to `#pragma omp simd`, which is
  outside the declared OpenMP list: regression case `lowering-spike-unit-maa-omp-simd`. `__restrict` pointers
  are in (C99 `restrict`).
- Assumption: a summary prototype takes the declaration's parameter names (the summary's formal halves name them).
- Assumption: a `new[]` fixture contract has no `assigns` clause (WP sees the buffer as caller memory).

**Open**

1. Rerun `tests/test_wp_subset.py` in full on a quiet queue (std_models, templates, the pin tests and the
   `new[]` out-of-range case), then record the result. The module-scoped seed reruns every model and summary
   job (about 40 WP jobs).
2. Settle the C-model records with ticket 25 at merge: keep 24's `--model`/`c_model`/`pins.models`, or take 25's.
3. Decide with Yan-Ru whether single non-virtual inheritance and `omp simd` join the subset. Either would
   unblock part of the spike: inheritance the fault builds, `omp simd` unit_maa.

**Merge state (2026-10-14 22:55 ET):** the integration tip is merged. Tickets 27 and 35 conflicted in
`wp_adapter.py` and `formal_frame.py`; the resolution keeps 35's hint records and hint check, 27's
proof-semantics lowering options, and 24's summaries, inlining and `-wp-fct`. After the merge,
test_c_lowering, test_format_doc and test_formal_frame give 124 passed, and the WP adapter's safe-fixture proof
passes (`report-r14.jsonl`, `report-r15.jsonl`). `test_wp_subset.py` now writes ticket 35's hint records and has
not been rerun since the merge.

**Next step:** merge 25 through the integration tip, resolve the model-record overlap, then do item 1.
