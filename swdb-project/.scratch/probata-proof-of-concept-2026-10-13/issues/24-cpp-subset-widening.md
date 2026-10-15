# 24 — C++ subset widening

Created: 2026-10-13 22:17 ET
Updated: 2026-10-15 ET (original Ring/allocation actual pairs and public unsupported controls accepted; remaining matrix open)
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
- [x] Unsupported constructs: inheritance, a virtual function, an exception, a lambda, RTTI, another standard container (such as `std::map`) and a stream each read not proven, "unsupported construct", naming the construct and its source location.
- [x] Once ticket22 lands, run its accepted finite native C++/C agreement subcheck on every original construct fixture; record undefined-input exclusions separately and retain a planted disagreement stop control.
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

## Resumed, 2026-10-15 ET

Assumption: keep inheritance and `omp simd` outside the declared subset, as the acceptance list
requires. The spike does not justify silently widening that boundary. Ticket 25's recovery now
uses the shared `--model` / `c_model` / `pins.models` interface; it is merged into the resumed
integration branch.

WP 33's missing deallocation semantics is a soundness gap, not merely a slow test. The adapter
must refuse every reachable free/delete or vector lifetime obligation until a validated model
exists. The public-seam regressions now require that refusal for safe allocation, an out-of-range
access, and a use-after-delete. The original positive safe-allocation acceptance remains an
explicit strict expected failure. This ticket stays **claimed**, and that expected failure is
never counted as completed acceptance. Bounded verification retains actual `malloc`/`free`.

The full baseline replay completed on mbit10 node 1 from `150930b4`, output
`/data/yanruj/EvolveSWDB_runs/probata-t24-baseline-20261015/r4`. Initial fixture setup failures were
diagnosed one at a time: LLVM 22's default GCC 14 selection lacked C++ headers and the linker
library path. The isolated class C++ versus C differential passes with GCC 13 header/library
paths before the full WP module starts. This baseline precedes the lifetime refusal and the
strict fresh-report reader; its results alone cannot close this ticket. Final guard regressions
must run on the integrated source. The serial baseline finished with **17 passed, 1 xfailed**
in 1823.04 s; the expected failure is the unsafe read after `delete[]`. Its 9.7 MiB of
original output is retained. Passing that earlier source does not establish acceptance for
the new lowerer, allocator refusal or strict report reader.

**Lifetime regression evidence (Mac).** The new public `swdb prove` use-after-delete test
failed before the guard: WP reported `proven` (63.66 s including fixture setup and lock waits).
After integrating the guard at `a41bcd39`, the three refusal controls pass and the positive
safe-deallocation acceptance remains expected-failing: **3 passed, 1 xfailed**, 92.55 s.
Original logs and incremental reports: `/private/tmp/probata-t24-20261015/{red,green}.{log,jsonl}`.
No expected failure counts as acceptance. [WP's official manual](https://frama-c.com/download/frama-c-wp-manual.pdf),
section 1.6, confirms that ACSL allocation/deallocation clauses are not implemented; switching
memory models alone is not evidence that this gap is solved.

## Narrow lifetime implementation — 2026-10-15

A checked terminal-release path is being integrated for the initialized, nonescaping scalar-array fixture.
Code: `swdb/terminal_release.py`, lowering version 4 (naming rules stay 3). It checks a single unchanged
new-int-array owner, full initialization before any read, no aliases/escapes/calls or extra releases,
and terminal delete followed by a scalar return that cannot observe the buffer. The ordinary lowering
retains delete; only a separately pinned WP view elides that unobservable final release. It inserts a
nonnegative-count proof obligation before unsigned conversion. Unsupported freshness/initializedness
facts are not assumed. Every uncertified free/delete and every vector lifetime remains refused.

Public TDD: the safe `swdb prove` test failed with `not_proven` before adapter integration, report
`/private/tmp/probata-lifetime-research-2026-10-15/public-red.jsonl`. The lowerer's 75 tests passed
(51.24 s), then ten focused controls passed after tightening initialization/alias cases (2.32 s).
No positive production-WP acceptance is claimed at this checkpoint. Design, source evidence and the
outside-repository diagnostic logs: `/private/tmp/probata-lifetime-research-2026-10-15/design.md`.

Side finding: WP 33 supports `Pinitialized` (`LogicSemantics.ml:871`), but the frozen `-wp-rte`
flags do not request its separate `-rte-initialized <function>` selector for read-initialization guards.
The certificate requires a canonical full fill loop and initialized scalar locals rather than inferring
arbitrary definedness from omitted obligations. This does not establish general initialization-guard
coverage for the rest of the declared C++ subset. Custom or externally replaced allocator behavior remains outside the ordinary allocator
model's assumption boundary. General vector growth needs real pointer provenance/liveness semantics;
this narrow transformation does not close ticket 25.

Before adapter integration, the expanded public negative set passed: **11 passed** (189.85 s),
`/private/tmp/probata-lifetime-research-2026-10-15/public-negative.jsonl`. These establish conservative
refusal controls, not positive terminal-release WP acceptance; the latter remains the recorded red test.

### Initialization obligations — 2026-10-15 ET

The public summary-proof seam reproduced a separate safety gap: an unused read of an
uninitialized local received `proven` under `-wp-rte` alone. The new WP policy requires
the method to freeze `-rte-initialized @all`, after a parse/inlining stage in the same
fresh process. It does not reuse a normalized file as trusted input. Initialized locals
prove; uninitialized locals, including an inlined callee, and a fresh unfilled array
remain not proven. A pointer with only `\valid` remains not proven, whereas an explicit
`\initialized` precondition establishes the initialized input domain.

Decision under the user's delegated implementation authority: admit the standard ACSL
`\initialized` predicate in formal halves so callers can state this necessary premise.
This small language extension does not enable other memory built-ins or imply a general
heap-lifetime model. Bounded translators must still refuse this predicate unless their
actual harness/storage initialization supports a faithful encoding. No input premise is
silently generated. This policy requires a new method file, not edits to pinned draft 2.
[Frama-C's RTE manual](https://www.frama-c.com/download/frama-c-rte-manual.pdf), section 2.7,
describes the initialization checks; the installed 33.0 help and raw negative controls
confirm the option is separate from the default WP RTE checks.

Raw CBMC initializedness checks are a separate ongoing audit; this WP fix establishes
no initializedness guarantee for bounded proofs. Ticket 24 remains claimed until its
full current-policy construct acceptance completes.

Validation: the unused-local public control failed before the policy (WP reported
proven), then passed after it. The complete focused policy/formal-frame/report suite
passed **121 tests in 114.92 s**, two workers, isolated retained basetemp. Six actual
WP controls include both initialized positives and all four uninitialized negatives.
Logs and incremental report: `/private/tmp/probata-init-final.{log,jsonl}`; initial
reproduction: `/private/tmp/probata-init-red.{log,jsonl}`. No full construct-group or
full-catalog acceptance is inferred from this focused suite.

### Bounded initializedness audit — 2026-10-15 ET

CBMC 6.11's direct command accepts discarded uninitialized reads in raw controls.
Its experimental `goto-instrument --uninitialized-check` catches direct scalar and
whole-array cases but misses alias, heap, C++ new/new[], partial-array and
partial-struct cases. The pinned implementation explicitly leaves dereferences
unhandled. Adding that option alone cannot establish the undefined-behavior
obligation. No existing bounded acceptance is upgraded by this experiment.

Retained primary-source snapshots, binary identities, 61 hashed command logs and
12 raw controls: `/private/tmp/probata-cbmc-initializedness/{REPORT,ADMISSION}.md`
and `results.json`. Harness pointer buffers are explicitly filled up to their
actual capacity; a cap-zero dummy cell is not initialized by that loop. A conservative
AST admission checker is being implemented over the whole lowered closure and both
sides of equivalence; safe heap/class cases it cannot establish will be refused
until a more precise checked analysis exists. A 24-lowering impact sample is bounded
exploration, not a full-catalog acceptance result.

### Bounded admission checkpoint — 2026-10-15 ET

Implemented `swdb.bounded_initialization` with a generated lowerer-6 certificate.
It checks every retained function before summary substitution, evaluates initializers
before binding locals, tracks primitive parameter-buffer origins, refuses unknown
AST effects and heap/aggregate/alias storage, and independently checks candidate and
baseline in both whole-function routes. The final invocation revalidates the source,
lowering, checker/generator identity, actual harness capacity and model policy.
The exact-content DX100 policy admits its reviewed initialized model state and
requires every tile draw and the checked model exit; arbitrary summaries and
changed model bodies receive no such exemption.

Final focused recheck: **43 passed, 4 strict xfailed, 18 deselected**, including all
18 new initialization controls and real DX100 safe/domain/exit checks. The broad
frozen checkpoint passed 153 tests and identified one expected zero-cap error-vs-record
assertion, corrected and rerun in that recheck. Four strict expected-failure cases
retain five original vector proof jobs pending ticket 25's precise object/range
policy; new tests separately verify their current conservative refusal. No full
construct-group, full-catalog or general UB-safety acceptance is inferred. This
ticket remains claimed for the separate aggregate/lifetime acceptance work.
Source checkpoint and hashes, domain exclusions, commands/log hashes and historical
RED controls are in [the evidence](../evidence/cbmc-initializedness-20261015.json).

### Checked terminal release acceptance — 2026-10-15 ET

The narrow initialized, nonescaping `new int[]` / terminal `delete[]` unit now proves through the
public WP seam with mandatory `-rte-initialized @all`: **1 passed,93.13s** fixture time; the actual
proof job took31.15s and records49valid goals. It pins checker2 and the ownership certificate, keeps
the original C/C++ delete, and reports the separate checked WP view. The exact record is
`/private/tmp/probata-terminal-call-init-public/wp24-lifetime-seed0/records/proofs/`
`proof.wp24-safe.candidate-1.20261015t075300z.1453c91b.yaml`; report
`/private/tmp/probata-lifetime-research-2026-10-15/terminal-call-init-public.jsonl`.

WP33's modular call-result rule binds a returned pointer's value without initializing the receiving
lvalue. A checked `+ 0` initializer gives the valid nonempty allocator result an equivalent ordinary
expression assignment; it adds no allocator/freshness/heap-init premise. Before this transformation
the initialized owner-slot invariant failed establishment. The raw repaired control proves49/49
goals plus7/7smoke; an ignored unfilled-array read remains9/10 with its initialization goal unproven.
Only checked pre-release initialization invariants are admitted.

The full current-policy construct suite is still required before closing ticket24. Ticket25's
growing vector lifetime acceptance remains open; this restricted transformation does not apply to it.

### Initialized class fixture — 2026-10-15 ET

The original class contract/hints leave five named initialization obligations unproven under
mandatory `-rte-initialized @all`. Logical bounds on input values do not establish initialized
storage. The fixture now explicitly requires initialized input elements, and its loops prove
preservation of the counter field and scaled array's initialization. The public WP replay is
`proven`: all 153 recorded goals are valid, including 11 smoke checks; 98.31 s wall, 405.8 MiB peak.
The seeded multiplication bug remains `not_proven`, with the functional loop invariant's
preservation unproven. No initialization goal is dropped or assumed.

The common input helper also supplies the explicit initialized-buffer premise to the other
reading fixtures; the atomic fixture states initialized pointees. Their broader acceptance is
pending. An input-only intermediate diagnostic was stopped after reproducing the missing loop
invariant; it is not counted as a completed test. Exact record hashes and source boundary:
[`t24-class-initialization-20261015.json`](../evidence/t24-class-initialization-20261015.json).
Original records/logs remain under `/private/tmp/probata-construct-initialization-20261015/`.
These are focused proofs on the recorded source, not final combined-source construct acceptance.

### Atomic call-result diagnosis — 2026-10-15 ET

Raw WP33 diagnostics of the current integer atomic models isolate another receiving-slot issue:
two RTE initialization goals fail after assigning exchange/fetch-add results to ordinary local
integers. All three explicit pointee-initialization assertions pass, as do all seven smoke checks.
An ordinary `+ 0` expression assignment makes all 19 ordinary goals valid and passes 9 smoke checks;
it adds no input or allocator premise. This is a narrow integer control, not a floating-result or
nullable-pointer rule. The raw runs use three seconds per solver and are diagnostic evidence only;
the production public workflow and full construct-suite acceptance are still required.
Exact source, command, result and artifact hashes:
[`t24-atomic-receiver-initialization-20261015.json`](../evidence/t24-atomic-receiver-initialization-20261015.json).

### Checked integer model results — 2026-10-15 ET

Lowerer9 makes known integer/bool model results ordinary expression assignments with `+ 0`.
It evaluates each call once, preserves the one-thread atomic meaning, and excludes void,
floating and arbitrary pointer results. Discarded normalized results use an explicit void
cast so native C builds stay warning-free. No input initialization premise is generated.

Focused public acceptance: exchange, fetch-add and bool compare-exchange callers all prove
with separately proven model records (**3 passed,591.59s**); std::min proves with its pinned
model (**1 passed,359.86s**). Removing only the caller's initialized-pointee premise leaves
the actual model precondition unproved (**1 negative control passed,143.01s**). All smoke
checks in these records pass. Native/lowering checks:90 existing cases plus4 new cases
pass, including ASan/UBSan C++/C null/live pointer-return behavior. Raw std min/max/OpenMP
result diagnostics also pass; they do not replace the full public construct suite.

Exact source and record hashes, incremental reports and validation boundaries:
[`t24-model-results-public-20261015.json`](../evidence/t24-model-results-public-20261015.json).
Ticket24 remains claimed until combined-source acceptance completes.

After merging the ownership/DX100 initialization checkpoint into isolated7437f3b9,
all94 native/lowering and69 proof-setup cases pass across retained runs. The first
combined invocation stopped after127 passes and5 watchdog process-inspection EPERM
failures inside the sandbox. The first failed case passes alone with the authorized
permissions; only the35 remaining cases were replayed and all pass. The evidence
records this split rather than calling the interrupted run clean. No guard was
disabled, and this does not cover ticket36's later pointer changes.

The two core adapter tests now expect the current lowerer9 tool ID. Their actual
public safe WP/bounded jobs both pass (**2 passed,311.74s**); bounded native
agreement includes4,375 C++/C executions. Exact trusted-tool sets are asserted.
Report:`/private/tmp/probata-t24-lowerer9-tool-pins.jsonl`. This focused replay
precedes ticket36's later pointer policy and does not upgrade historical records.

### Explicit array-domain declaration slice — 2026-10-15 ET

The pointer audit showed that allocation validity does not establish same-array
provenance. `proof_unit.array_domains` now accepts explicit typed array-window
input declarations, bound to actual primitive pointer and scalar integer
parameters. The extent grammar uses mathematical integer arithmetic and preserves
C++ identifier meaning, including names reserved by the parser's host language.
It adds no initializedness fact and is never inferred from concurrency rows.

This is a staged contract format. The universal adapter factory refuses every
nonempty declaration until an independent source-origin certificate also checks
operations and imported-summary calls. A scripted verifier cannot bypass the
refusal. No C++ safety acceptance is inferred from declaration validation.

Final public domain controls: 19 passed in 8.38 s. The existing validate/build fixture
also passes, and the new helper's named dependency pin is checked. Exact hashes
and overlapping validation scopes:
[`t24-array-domain-declarations-20261015.json`](../evidence/t24-array-domain-declarations-20261015.json).
Next: implement origin/call admission, then update explicit fixture input contracts
and replay their actual proofs. Ticket 24 remains claimed.

### 2026-10-15: shared entry-window binding

The staged `array_domains.bind` API now supplies canonical parameter-bound mathematical trees and entry-frozen ACSL rendering; `interval` conservatively evaluates all bounded scalar draws with arbitrary-precision arithmetic. After integrating `a728b529`, 19 public declaration controls and 10 mathematical controls pass (29 total, 7.92 seconds). This is a prerequisite for operation/call admission, not acceptance: proof jobs remain closed to declaration-only metadata. Evidence: `../evidence/t24-array-domain-binding-20261015.json`.

### 2026-10-15 07:16 ET: mbit10 native checkpoint

Frozen replay `aa7be61c` passes all 132 selected compiler/native/domain controls in
69.36 seconds on node 0, lease generation 550; the lease is released. Matching
LLVM/libc++ 22.1.8 and explicit GCC 13 driver selection are recorded. The original
checkpoint `2b4198db` gave 112 passes and 21 failures: 14 driver-selection diagnostics,
6 standard-library/model mismatches and 1 stale raw-endpoint expectation. That
expectation was independently reproduced locally and updated to require the C++
null-plus-zero normalization. The original native shard also selected one CBMC
footprint query; the corrected shard excludes it. Raw outputs of 11 MiB and 17 MiB
remain on mbit10; only compact counts, configuration, lane metadata and hashes are
transferred in `../evidence/t24-native-mbit10-20261015.json`. This is native/compiler
evidence, not final WP acceptance or a reason to resolve ticket 24.

### Generic callee binding repair — 2026-10-15 ET

The public CBMC changed-clamp counterexample established that an unchanged
function name does not permit substituting a summary proved on other code.
The checked generic-summary import now binds the actual complete callee closure
and current proof/method/evidence, and checks finite caller arguments and exact
buffer alignment. Matching scalar/array CBMC controls and a scalar WP import
pass; both Crux forms reject the changed definition before solver launch.
External-only generic declarations still need a separately checked symbol/library
mapping. The old fixture stand-ins are not evidence that arbitrary implementations
behind a declaration satisfy their contracts. Full construct acceptance remains
open; ticket36's [repair evidence](../evidence/summary-source-binding-20261015.json)
records the exact boundary and the original false proof.


## Checkpoint — 2026-10-15 09:53 ET: frozen mbit10 replay

Source `fddb1462dfb9ff8d7885521bc6edaf367d97a12e` (merged into integration
`45560225`) ran in two socket lanes from 09:32 ET. Node 0 native shard passed 132
checks with one deselected in 145.05s; node 1 bounded/source-summary shard passed 17
checks in 581.79s. Both wrappers exited 0 and leases released. The audit covers 27
retained proof records: all referenced artifact hashes match except the deliberately
zeroed report pin in the evidence-mutation negative control. That dependency control
is not accepted as a proof. Raw output remains remote for its readers; only compact
metadata is exported. [Evidence](../evidence/summary-source-binding-mbit10-20261015.json).
This checkpoint does not close the ticket's remaining acceptance criteria.


## Checkpoint — 2026-10-15 10:49 ET: helper/construct remote audit

Frozen `1ece49b8` ran in two socket lanes from 09:57 ET. Entry-window and actual
helper controls passed **17/17 in 1428.35s** on node 1, generation 597. Constructs
on node 0, generation 556, stopped at its first failure: **5 passed, 1 failed in
1268.59s**. The failure is the standalone `std_copy_int` model's uncertified opaque
pointer origin, before WP launch, with zero goals. It is not a failing numerical
proof or full construct acceptance. A separate qualified model-body repair is under
review; caller range discharge remains required.

All referenced artifact hashes match across 43 retained records. Both socket leases
and the legacy lease were released at the 10:49 ET live readback; load was
0.32/0.07/0.30, `/data1` had 21 GiB and `/data` had 97 GiB free. Raw results remain
remote for coordinator, ticket acceptance and independent audit readers.
[Compact audit](../evidence/helper-construct-mbit10-20261015.json). This checkpoint
does not resolve the ticket. Recheck live state before dispatch.

Declaration-attribute sidefinding — 2026-10-15 ET: generic lowering accepted a local
`__attribute__((cleanup(release_local)))` after its initializer and silently dropped its scope-exit
callback. Public `swdb lower` RED1in0.60s; four retained-declaration RED controls in1.03s also exposed
parameter NoEscapeAttr and function ConstructorAttr/NonNullAttr erasure. A native fixed-input witness
returned `7 4` (result, global counter) in original C++ and `7 0` in the old lowered C. This establishes
a lowering mismatch; no actual verifier or falseproof is claimed. The narrow repair validates direct
attributes before processing retained locals, definitions, parameters and summarized declarations.
Only five covered diagnostic/inlining attributes are discarded; unknown/effectful attributes refuse
with their Clang kind. The same guard catches inherited prototype attributes. Ordinary GAPBS includes
remain admitted. Selected public controls:27PASS11.89s, including14new controls and13existing construct
groups with deterministic lowering/C compilation. Full-TU startup effects of otherwise uncalled
functions and class/global attributes are outside this scoped repair. Status remains claimed.
Evidence:[t24-declaration-attributes-20261015.json](../evidence/t24-declaration-attributes-20261015.json).

## Integration checkpoint — 2026-10-15 ET: qualified copy body and declaration attributes

Integration `636b2080` includes declaration-attribute admission `51ff3999` and the
qualified standalone copy checkpoint `0e25002d`. The retained actual copy record at
frozen `1f760ba8` has 36 ordinary Valid and seven smoke PASS goals; its record and eight
named evidence report hashes were independently checked during integration. Its exact
model body and contract hashes remain pinned. This is a body result under an explicit
standard-library typed-range domain, not arbitrary opaque-pointer or caller acceptance;
WP callers still refuse pending checked typed-root/subobject and range discharge.
[Copy evidence](../evidence/t24-std-copy-qualified-body-mac-20261015.json).
The declaration-attribute guard retains its scoped boundary and native cleanup witness;
this integration does not claim a complete startup/global/class-attribute model.
Ticket24 remains claimed, with current-policy construct acceptance still coordinated
separately. Later integration method identities do not upgrade either historical record.

## Caller-range checkpoint — 2026-10-15 ET

Exact `std_copy_int` caller admission now requires the original-TU standard-library
certificate, a current qualified model proof, typed one-dimensional local or explicit
entry-window origins, same-root input endpoints, checked ordered offsets, and checked
destination capacity. Extents retain entry values; direct current offset arithmetic
remains an ordinary obligation. Initialization, validity, separation and all RTE/smoke
checks are preserved. Two-dimensional, member and global origins remain outside this
slice. The std-model fixture gains only explicit `a:n`/`b:n` domain metadata matching
its existing requirements; the initialized-copy fixture similarly declares `out:1`.

Independent compiler controls also found a separate concrete lowering gap: a genuine
standard call and a same-name/type project extern could both select the standard model.
Every free min/max/copy/swap substitution now compares its exact physical CallExpr
range against the full original-TU callee's mangled identity and declaration file.
Same-line mismatches refuse before dependencies, native execution or verification in
all four bounded routes. This is a compiler/admission regression, not a historical
false-proof claim. Agent review covered the caller/request and isolated-parser union;
no personal human review is implied.

Frozen `0831b224` passed four public caller controls in **228.73s**, with one shared
worker and an 8 GiB RSS cap (peak **519,225,344 bytes**). Its fresh model has 36 ordinary
Valid plus seven smoke Valid goals. The initialized caller has 15 ordinary plus two
smoke Valid; the empty range with uninitialized elements has 13 ordinary plus two smoke
Valid. The uninitialized-source control remains not_proven with one ordinary requires
timeout. The destination-window control remains not_proven with one numerical guard
timeout and two failed smoke checks; its requested count two exceeds declared capacity
one despite physical validity for two elements. Unproved negative goals are not claimed
to have been proved false by a solver.

The first frozen `c61af423` attempt proved the model but exposed an ACSL parse error in
an existing generic array-base guard. Repair `d6cf1e98` adds an explicit typed pointer
cast only to that guard's certified one-dimensional base, preserving C operations and
obligations. Its parser regression went RED to GREEN; 14 caller/parser controls and
three merged source/replay controls passed before the fresh actual run. All 200 frozen
source/test hashes, five proof records and 46 evidence artifacts were checked. Later
launch-metadata changes at `d3a5dd48` do not relabel this frozen evidence. Broader
construct acceptance and ticket closure remain open.
[Scoped caller evidence](../evidence/t24-std-copy-callers-mac-20261015.json).


### Focused Linux caller acceptance — 2026-10-15 12:14 ET

At frozen `d3a5dd48`, the qualified copy model proves 36 ordinary/7 smoke goals,
safe copy proves 15/2 and empty copy proves 13/2. Missing initializedness and
insufficient declared capacity stay not_proven; the latter retains its two failed
smoke checks. The focused lane's 20 controls pass, including original-callee
refusals. Mac0831 and Linuxd3a retain separate method identities. The next class
member-window context work and whole ticket remain open.
[Audited source, records and reports](../evidence/focused-parser-owner-final-20261015.json).

### Contextual member-window checkpoint — 2026-10-15 ET

The first current public class diagnostic refused `Bag::data` before WP: validity
and initializedness do not establish a typed array origin for an arbitrary receiver.
A new checker now certifies a narrower selected-entry context: one exact trivial
automatic pointer/count record, immediate immutable captures from an explicit input
window, and original-TU checked direct receiver calls with no copies/escapes or
nonreceiver pointer/reference arguments. The checked closed graph has longest path
at most two, matching an installed Frama-C33 parser probe; both direct calls disappear
from the normalized entry while field-initialization and numeric guards remain.
Exact entry/inlining settings and generated context bytes are bound at prelaunch.
No validity, initialization, separation or numeric premise is added.

Independent agent review found two compiler-admission gaps before actual proof:
a pointer-reference helper could suppress ordinary pointer invalidation, and a shared
callee first visited on a short path could hide a longer path. Both have concrete
RED-to-GREEN controls. Member call exemptions were removed entirely; longest-path
checking is independent of receiver-visit memoization. These are compiler controls,
not historical false-proof claims. The standalone-model optional-lowering path is
also preserved by a public control. No personal human source review is implied.

Frozen `1e93b9cb` passes **26** compiler/policy/public stand-in controls in **15.83s**.
Its actual small safe getter proves **15 ordinary plus one smoke** goal, including
four retained RTE initialization goals. Calling the getter at the advertised extent
stays not_proven with one member-window timeout; the other 14 ordinary goals and one
smoke are Valid. A finite `n=1,i=1` case violates `i<n`; timeout alone is not claimed
as a mathematical disproof. The serial actual pair used the shared two-slot policy,
an 8 GiB watchdog and peaked at **837,943,296 bytes** over **43.38s**. All 206 frozen
source/test hashes, two records and 17 reports were checked.

The original actual pytest result is **one failed, one passed**: the positive record
already proved every obligation, but a test searched for `initialized` instead of
Frama-C's `rte_initialization` goal spelling. Only that test spelling was corrected;
all assertions then passed offline against both immutable records. No solver rerun,
source-premise change or fresh-proof claim is implied. The original test/log/XML and
frozen source snapshot remain retained. This checkpoint does **not** clear the original
Bag/Counter constructor/destructor fixture, fixed member arrays/templates, arbitrary
receiver summaries, or the remaining whole-ticket acceptance criteria. Status remains
claimed. [Scoped member evidence](../evidence/t24-member-windows-mac-20261015.json).

After merging canonical integer-header baseline repair `feb92b5b`, focused member
and header composition controls pass **29/29 in 55.92s** at `6cc5147e`. This checks
current compiler/admission composition; the actual proof records retain their
original `1e93b9cb` runtime and method identities.


### Original Bag/Counter scalar-lifetime checkpoint — 2026-10-15 ET

The original `classes.cc` fixture now reaches WP with its unchanged original
pre/post clauses and existing hint records. The explicit typed `a:n` domain
metadata matches the already-required initialized valid range; it supplies typed
origin rather than new numeric, validity or initialization requires. The old
opaque constructor/destructor refusal is replaced only for one additional exact
automatic scalar/reference object: its reference fields bind prior plain int
locals in a strictly enclosing scope, its complete closed constructor/method/
destructor effects are retained, and no early exit, copy, escape or alias is
admitted. Plain int-reference helpers receive only exact selected-entry locals,
never captured parameters/fields or reference aliases. Bag pointer/count captures
remain immutable. No generic pointer-call exemption was added. A pure single
top-level compound assignment now permits its ordinary guard before the statement;
nested mutation/calls/conditional/volatile operands remain refused.

Independent agent review approved runtime `a70fc6fd` and the subsequent parser/public
attestation; this does not imply personal human source review. The installed
Frama-C33 parser fully expands a depth-two constructor/destructor helper probe,
with zero selected-entry residual calls and verified constructor → update →
destructor → scalar-helper order. Three member numeric guards and six field-init
predicates remain. Compiler/source-policy controls pass **39/39 in 7.84s**, including
constructor/helper attempts to alias `n`, `Bag.n`, an int-reference alias or an
untracked pointer binding. Explicit destructor and reference reinterpret-cast
controls preserve existing lowerer refusals.

Actual public standalone original-fixture proof at frozen `2f85b7a6` is **proven:
146 ordinary and 11 smoke goals Valid**, including **46 RTE initialization goals**.
The original safe pytest result was **one failed** only because the new test read
the optional `failure_class` key after its successful verdict assertion. A test-only
`row.get` correction at `c4cfbf1f` passed the complete remaining safe assertion block
offline against the immutable record. The safe solver was not rerun. The separately
launched original seeded-scaling negative then passes its test in **184.62s**:
**not_proven, 146 ordinary Valid, one distinct loop-invariant-preservation timeout,
and 11 smoke Valid**. Dependent partially proven properties are not extra independent
open goals. A native finite case `n=1,a[0]=1,mode=2` writes 4 in the seeded code
where the original contract requires 3; timeout alone is not a mathematical disproof.
Both original and seeded C/C++ streams match on the supplied **105-case** native
harness each, with no universal C++/C agreement claim.

The three public records, **34 report hashes**, and **209 Git source pins per run**
were audited, together with the exact source/seeded transformation, unchanged
contract/hints and reconstructed generated context hashes. Actual workers used
normal shared two-slot locking, one pytest worker and an 8 GiB RSS cap; safe peak
569,294,848 bytes/94.04s, negative peak 837,517,312 bytes/184.80s, no OOM or outer
timeout. Raw records, the original safe failure, corrected offline replay, native
outputs and source manifests remain outside the repository.

After composing integration `bc457086` at `1bc9eac1`, **48 compiler/policy/public
stand-in controls pass in 22.34s**, with two real-verifier cases deselected. These
are current composition checks; historical actual records retain their original
source and method identities. The complete per-candidate original construct group
and remaining template/member-array/model/lifetime acceptance are still separate
frontiers. Ticket24 remains **claimed**, with no whole-ticket closure.
[Scoped original-class evidence](../evidence/t24-member-lifetimes-mac-20261015.json).


### Pure condition placement and closeout frontier — 2026-10-15 ET

A compiler-only audit on integration `c6636b0d` identified the remaining original
construct boundaries before any new solver batch. The original template Ring
member arrays lack a typed subobject origin; the std combined fixture's conditional
return needs a path-sensitive read check; OMP and floats lacked explicit typed a:n
metadata matching their existing n-element range interfaces. New[] terminal-release,
atomic and fixture-summary shapes already pass compiler admission, but retained
historical records do not establish all current full-group acceptance. The exact
matrix/source hashes are in the [frontier audit](../evidence/t24-acceptance-frontier-20261015.md).

Only the already-active pure IfStmt placement slice was implemented before the
user's closeout steering. A guard immediately before an if now checks an access
that is independently bound to its pure original condition; later branch effects
are not confused with precondition evaluation. Init bindings, short circuit, calls,
volatile reads and mutating indices remain refused. A compiler RED also exposed
Clang AtomicExpr side effects bypassing the call/mutation blacklist; explicit
AtomicExpr refusal repairs it. No real-verifier/false-proof claim is made for that
admission control. OMP/floats metadata is an explicit typed input qualification,
not a validity-to-origin inference; existing requires, source and hints remain.
No _Origins or generic call exemption was changed.

No conditional-return, template/member-array or allocator extension was started.
These are preserved as concrete open gaps for resumption. Ticket24 remains claimed;
this closeout slice does not close the original construct or full-method acceptance.

Focused closeout validation on frozen `c00665c8` passes **72/72 in 26.31s**,
including nine condition compiler controls, the new public fake prelaunch control,
and retained member/class/query/standalone controls. Main-session agent source
review is GREEN. All source pins and retained public report hashes were checked;
no actual solver or remote job was launched. The fake records remain not_proven/
unknown and do not establish original OMP/floats proof acceptance.
[Condition closeout evidence](../evidence/t24-condition-closeout-20261015.json).


### User-paused checkpoint — 2026-10-15 ET

Implementation, evaluation and provider work are paused by user direction. The
claim is released for a later session; acceptance is not complete. Closeout
review, documentation, merge and cleanup continue separately.

Qualified copy and original Bag/Counter slices retain their exact-source proof
and negative evidence. Pure condition placement has 72 focused passing controls;
this is compiler/stand-in coverage, not an actual OMP proof. Remaining: the full
current-policy construct/dependency matrix, including embedded template-array
origins, conditional standard-call placement and broader allocation/lifetime
coverage. See [class evidence](../evidence/t24-member-lifetimes-mac-20261015.json)
and [condition closeout](../evidence/t24-condition-closeout-20261015.json).

### Resumed original construct frontier — 2026-10-15 ET

User resumed implementation and remote evaluation. The exact original Ring
int/long fixtures now gain structural fixed-subobject identity through a closed
live automatic receiver context; pure conditional-return reads carry ordinary
path-conditioned numeric guards. No validity/init/numeric premise is added and
no original source, contract or hint is replaced. Independent source review found
and repaired a runner acceptance gap: original seeded prelaunch refusals cannot
count as actual negative proofs. A separate narrow terminal `i<=n` fill grammar
keeps the original off-by-one fixtures' invalid writes as actual RTE obligations.

All 18 original safe/seeded combined-source compiler admissions now pass at
`b801e5a2`. Original determinism/C11/bounded-native/name/refusal controls pass
29/29; new fixed/conditional/public stand-in/setup controls pass16/16; terminal
controls pass12/12. These overlapping profiles are compiler/stand-in coverage,
not actual construct acceptance. The root coordinator owns fresh lane0 dispatch
through the committed exact-source runner, after mandatory setup hardening is
merged. Original all-goal/init/smoke safe+seeded acceptance and current dependency
pins remain required. Status stays **claimed**.
[Implementation assumptions, exact checkpoints and evidence](../evidence/t24-resume-compiler-20261015.md).

### Original Ring per-candidate actual acceptance — 2026-10-15 ET

Frozen `71771f09` passes the original template pair on mbit10 node0. Safe:
**89 ordinary + 1 smoke Valid**. Seeded original `r.get(0)`: **not_proven,
88 ordinary Valid, one ordinary ensures timeout, 1 smoke Valid**. Both retain
**25 RTE initialization goals**, with zero residual Ring/twice calls in the
normalized selected entry. No new validity/init/numeric requires or replacement
fixture was used. All physical code/baseline/contract/method/checker/report pins,
980 Git/source-manifest files and exact original source substitutions were
independently checked. Raw evidence remains remote; compact audit is committed.
This closes the original embedded-array compiler/proof gap, not the whole ticket.
The remaining eight groups and lifetime/dependency actual matrix are pending;
status remains **claimed**.
[Exact pair audit](../evidence/t24-original-template-pair-mbit10-20261015.json).

### Concrete dxc negative-control correction — 2026-10-15 ET

The old `__dxc_tile_size(tile)+2` variant is not a concrete bug against the
original stand-in: `tile&1` returns 0 or 1, so the variant returns 2 or 3 and still meets
`1<=result<=3`. A modular ensures timeout from the looser proven summary
`0<=result<=2` is a precision control, not genuine seeded semantic-bug acceptance.
The root coordinator authorized changing only this seeded replacement to `+4`.
Safe source, original contract, original summary and actual stand-in body remain
unchanged. At in-domain `tile=0`, native C++ and its C lowering both return 1 for
safe, 2 for the old seed and 4 for the corrected seed. The public native negative
control goes RED (old+2) to GREEN (corrected+4), 2.06 s / 1.71 s. This is native
fixture evidence, not a solver refutation or production DX100 semantics claim.
Frozen `71771f09` records keep their exact old source identities; fresh corrected-seed
actual acceptance remains required. [Native source/binary hashes and outcomes](../evidence/t24-dxc-native-negative-control-20261015.json).

### Original allocation pair and public unsupported controls — 2026-10-15 ET

The original new-array safe/seeded pair now has actual frozen `71771f09`
evidence. Safe proves 42 ordinary + 7 smoke goals. The original `i<=n` seed
reads `not_proven`: 40 ordinary Valid, ordinary invariant-preservation and
memory-access timeouts, 4 smoke Valid and 3 failed smoke. Both retain 11
initialization goals. Independent physical/source/certificate/view auditing
finds no errors; no timeout is labeled a counterexample and no invalid native
write is executed. [Compact actual audit](../evidence/t24-original-allocation-pair-mbit10-20261015.json).

All seven original unsupported groups also pass public proof refusal controls
(7/7, 30.27 s), with named source-line diagnostics, no goals and no verifier
launch. Their `not_proven` result is deliberate prelaunch refusal, distinct from
the actual original semantic negative jobs. Remaining groups, lifetime actuals,
dependency closure, corrected-DXC actuals and accepted ticket22 finite agreement
profile are still pending. Status remains **claimed**.

### Accepted ticket22 finite agreement limb — 2026-10-15 ET

The reviewed original nine-group safe/current-seeded profile at `e48a302e`
records **112,589 defined input comparisons**, all equal between C++ and the
ordinary C lowering. All 18 case classifications are present: 17 agree on
defined inputs; the allocation seed is explicitly UB-only with zero defined
comparisons. The **2,207 known UB exclusions** (500 allocation, 1,702 standard
copy at `n==0`, 5 seeded maa overflow) remain separate from **47,164 original
precondition exclusions**. No runtime sanitizer asymmetry was observed.

Independent review reconstructed every domain/classification and all retained
defined results, rehashed 15,768 references across 1,363 physical files, and
found zero discrepancies. The shared planted C-only lowering mismatch stops
comparison and emits no proof verdict. This completes the separate agreement
limb under the accepted ticket22 decision; it is finite native evidence, not
formal C++ equivalence, a proof of a WP checking view, or device semantics.
[Accepted profile and exact pins](../evidence/t24-finite-agreement-20261015.md),
[independent final review](../evidence/t24-finite-agreement-final-review-20261015.md).

Provenance stays explicit: original Ring/allocation actual records use frozen
`71771f09`; pending remaining actual jobs use `9b75f4a2`; finite agreement uses
`e48a302e`. Production runtime bytes match across those freezes, while shared
seeded artifacts retain their distinct old-DXC+2/corrected-DXC+4 identities.
No historical record is relabeled current. Remaining actual construct pairs,
lifetime controls and fresh model/summary closure still gate ticket completion.
Status remains **claimed**.
