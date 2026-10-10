# 02 — Which existing formal verifiers can check our C++ code as-is?

Created: 2026-10-09 14:22 ET
**Ticket:** [`../issues/02-verifier-landscape.md`](../issues/02-verifier-landscape.md) · **Map:** [`../map.md`](../map.md)
**Method:** primary sources only (tool READMEs, manuals, source files, GitHub API, Crossref).
Release and commit dates come from the GitHub API, queried 2026-10-09. Nothing was installed.

---

## TL;DR

- **No tool reads `bfs.cc` whole** (it pulls in `<iostream>`, the gapbs CLI and graph
  builder, and OpenMP). What a formal verifier gets is a **verification harness**: `TDStep`, one
  candidate artifact, the strict layer as the meaning of `maa_*`, and a small fake graph. For
  the single-thread phase it is compiled without `-fopenmp`.
- **Only Clang/LLVM-based tools read that harness as C++ without changes:** ESBMC (it walks
  Clang's syntax tree and ships its own models of `vector`, `mutex` and `atomic`), crux-llvm/SAW,
  KLEE, SeaHorn and Alive2. **CBMC, Frama-C/WP, CN, SMACK, CPAchecker and Ultimate are C-only in
  practice.** CBMC's maintainer calls its C++ support "certainly spotty".
- **None of the single-thread tools model OpenMP.** Only **VerCors** (unbounded, C subset) and
  **CIVL** (bounded) read `#pragma omp` at all. The concurrency phase will need one of them, or
  a hand-written pthreads version of the OpenMP code.
- **Alive2 re-check:** the 2026-06 reason for rejecting it ("TSVC integer-only", i.e. it only
  works on integer code) **does not apply to BFS**: every BFS type is `int32_t`. Alive2 stays
  out anyway, for other reasons: it cannot follow function calls, it only unrolls loops a
  fixed number of times, and OpenMP code becomes calls into the OpenMP runtime.
- **Shortlist.** Bounded tier: **1 ESBMC · 2 crux-llvm/SAW · 3 CBMC** (CBMC needs the code
  ported to C). Unbounded tier: **1 Frama-C/WP (+RPP) · 2 ESBMC k-induction / loop-invariant
  check · 3 VerCors** (for the concurrency phase). KLEE is a bug-finder, not a prover.

## Recommendation for our case

1. **Bounded tier = ESBMC first.** It is the only tool that combines all of these:
   - reads our C++ harness directly;
   - checks up to a declared bound, and its unwinding assertions catch a bound that is too small;
   - reports SUCCESSFUL / FAILED / UNKNOWN (`src/esbmc/bmc.cpp`);
   - has a Homebrew arm64 package;
   - offers an unbounded mode on the same input, so the agent works on one code base for both
     proven levels.

   **crux-llvm/SAW is second.** It also reads C++ (as LLVM bitcode, linked against `libc++`)
   and SAW can compare two functions directly, but it has no loop invariants for bitcode.
   **CBMC is the fallback** if ESBMC's C++ handling breaks: it is the most mature engine for C,
   but only on a C port of the kernel and the strict layer.
2. **Unbounded tier = Frama-C/WP for the real proofs, ESBMC for cheap ones.** WP has the full
   proof-hint vocabulary: `ghost` code, `lemma`, `loop invariant`, `assert`. It reports a
   verdict per proof goal (valid / unknown / timeout / stepout / failed), which tells the hint
   agent exactly which goal to work on. Its smoke tests detect assumptions that contradict each
   other, which addresses the map's open vacuity-guard item. The cost: WP reads C, not C++. It
   needs a C version of the kernel, or ACSL contracts standing in for `maa_*` (see tickets 05
   and 12). ESBMC's `--loop-invariant-check` proves simple invariants on the C++ input itself,
   but it is weak on invariants that quantify over arrays (open issue #6923).
3. **Concurrency phase = VerCors** (unbounded, reads OpenMP's `parallel for`, `sections` and
   `simd`), with **CIVL** as a bounded cross-check. Neither reads C++, so OpenMP proofs will run
   on a C version.
4. **Ticket 07 installs** (all small next to the 142 GiB free on the Mac today): ESBMC (brew),
   CBMC (brew), crux-llvm 0.12 (59.5 MB arm64 tarball), Frama-C 33.0 with Why3 and Alt-Ergo
   (opam or the ARM `.pkg`). Optional: SAW 1.6 (178.5 MB) and KLEE (brew). VerCors waits for the
   concurrency phase.

---

## Our code versus each tool: what chokes on what

| Construct | Where | Who chokes |
|---|---|---|
| `<iostream>`, gapbs CLI/builder, `main` | `bfs.cc:4-16`, `bfs.cc:511+` | Everyone, in practice. Cut the harness at `TDStep`. |
| Templates: `pvector<T>`, `SlidingQueue<T>`, `QueueBuffer<T>`, `maa_*<T>` | `pvector.h:20`, `sliding_queue.h:24,90`, strict layer | C-only tools (CBMC in practice, WP without Frama-Clang, CN, SMACK, CPAchecker, Ultimate). VeriFast handles only one instantiation at a time (PR #1034). LLVM tools are fine, because bitcode has no templates. |
| `std::vector`, `std::mutex`, `lock_guard`, a `static State` local | `library/dx100/strict/MAA_functional.hpp:3-12,49-52` | CBMC: 0 of 19 C++11/14 headers parse with `goto-cc` 6.6 (issue #8663). ESBMC swaps in its own library models. LLVM tools compile the real library code. Calls to `pthread_mutex_*` will need stubs (our reading). |
| `#pragma omp`, `omp_get_thread_num()`, `omp_in_parallel()` | `bfs.cc:74,170,188,200,235,238`; strict layer `thread()` (`:53`) | No single-thread tool models OpenMP. Without `-fopenmp`, Clang ignores the pragmas (sequential meaning), and the `omp_*` calls need stubs (our reading). VerCors and CIVL read the pragmas. |
| `__sync_bool_compare_and_swap`, `__atomic_load_n/_store_n` | `platform_atomics.h:31`; strict layer `read_memory`, `maa_indirect_store_vector` | GCC built-ins. Per-tool support not verified. Test them in ticket 08. |
| `volatile` register file (functional model) and memory-mapped device registers (gem5 header) | `apps/dx100/benchmarks/API/MAA_functional.hpp:29-32,91-96`; `MAA_gem5.hpp:50-52` | WP: a read from a `volatile` "returns an undefined value" by default (sound, but the value is lost). CBMC: ordinary memory unless `--nondet-volatile` is set. **Prove against the strict layer**, which has no `volatile`; this matches ticket 01. |
| `std::_Exit(86)` when a strict-layer check fails | strict layer `check()` | Each tool must see this as an assertion failure. A verification build maps `check()` to the tool's `assert` (flag for ticket 12). |
| A list of operations that grows with every call, walked recursively by `cover()` | strict layer `issue()`/`cover()` | Bounded tools cope at small sizes. **Unbounded tools need contracts for `maa_*`**; tracing the bookkeeping code itself is hopeless. |

---

## Comparison table

Legend. **Two-program** = can it compare two programs directly ("native") or only through one
harness that runs both and compares the results ("self-composition")? **Hints** = support for
ghost code / loop invariants / lemmas.

| Tool | Input | Bounded / unbounded | Two-program | Hints | C++11 | OpenMP | On timeout or give-up | Status (GitHub, 2026-10-09) | macOS arm64 |
|---|---|---|---|---|---|---|---|---|---|
| **CBMC** | C; C++ "spotty" | Bounded; unbounded with loop contracts | Self-composition | Contracts, loop invariants, history variables, quantifiers; no lemma construct | ✗ in practice | ✗ (pthreads only) | No built-in timeout; verdicts SUCCESSFUL / FAILED / INCONCLUSIVE / ERROR | 6.11.0, 2026-08-21; commit 2026-10-08 | brew bottle, no dependencies |
| **ESBMC** | C, C++ (Clang syntax tree), CUDA, Python | Bounded; unbounded with k-induction, `--loop-invariant-check`, contracts | Self-composition | `__ESBMC_loop_invariant`, `requires`/`ensures`/`assigns`, `__ESBMC_old`; no lemma construct | ✓ (C++11–23 test suites; library models) | ✗ (pthreads, race check) | `--timeout`; SUCCESSFUL / FAILED / UNKNOWN; `--check-vacuity` | 8.5, 2026-08-30; commit 2026-10-09 | brew bottle (brings in `llvm@22`, z3, bitwuzla, boost) |
| **SeaHorn** | LLVM bitcode (C via Clang); built against LLVM 14 | Unbounded (Horn-clause solver Spacer); bounded mode `--bmc` | Self-composition | Assertions only; invariants inferred by the tool | ? not documented | ✗ | `sat`/`unsat`; "unknown" not documented | Release v0.1.0 (2015); commit 2026-07-15 | Docker recommended; no brew |
| **SMACK** | C only (README) | Bounded by default; unbounded experimental | Self-composition | Assertions; invariants not documented | ✗ | ✗ (`--pthread`) | Not documented | 2.10.0, 2026-07-08 | No brew; build from source |
| **Frama-C/WP** | C + ACSL; C++ only through Frama-Clang ("early stage") | **Unbounded** (deductive) | **RPP plugin** (early prototype) | **Full:** `ghost`, `lemma`, loop invariant/assigns/variant, `assert`/`check` | ✗ (Frama-Clang partial) | ✗ (manual does not mention threads) | **Per goal:** valid / unknown / timeout / stepout / invalid / failed; JSON report | 33.0 Arsenic, Jul 2026; RPP 0.0.4 for 33.0 (2026-09-07); Frama-Clang 0.0.20 (2026-09-25) | ARM `.pkg` or opam |
| **VeriFast** | C, Rust, Java; C++ front end in progress | Unbounded (separation logic) | Self-composition | Lemma functions, predicates (README); ghost code and loop invariants not re-checked | Partial (one template instantiation at a time; no standard-library specs found) | ✗ (multithreaded C via its own thread specs) | Not documented | 26.10, 2026-10-05 | 62.7 MB tarball |
| **CN** | C (Cerberus semantics) | Unbounded (separation-logic refinement types) | Self-composition | `inv` loop invariants, restricted ghost variables, lemmas (Rocq export) | ✗ | ✗ | Not documented | No releases; commit 2026-10-07 | opam from source / Docker |
| **SAW / crux-llvm** | LLVM bitcode (C/C++ via Clang; crux links `libc++`) | **Bounded** (symbolic execution; SAW needs concrete loop bounds) | **SAW: native** (implementation vs. spec) | Verified specs reused in later proofs (SAW manual, not re-checked); no loop invariants for bitcode | ✓ (bitcode) | ✗ | crux: `--timeout` makes results "Unknown" | SAW 1.6, 2026-09-17; crux 0.12, 2026-01-29 | SAW 178.5 MB, crux 59.5 MB |
| **Alive2** | LLVM IR; `alive++` is a drop-in for `clang++` | Bounded (fixed unrolling) | **Native** (does the new code refine the old?) | None | ✓ (IR), but only one function at a time | ✗ | "Inconclusive" (timeout or out of memory) | v21.0, 2025-08-12; commit 2026-10-04 | brew bottle |
| **llreve / REVE** | Two C programs → LLVM IR → Horn clauses | Unbounded (infers how the two programs' variables relate) | **Native** | Inferred; user may add | ✗ | ✗ | UNKNOWN (often, when there is multiplication) | **Dead:** last commit 2021-04-20 | Build against old LLVM |
| **CPAchecker** | C ("large subset of GNU C") | Both (bounded checking; k-induction; predicate analysis) | Self-composition | Invariants via correctness witnesses (Witnesses 2.0) | ✗ | ✗ | TRUE / FALSE (and UNKNOWN, as in SV-COMP) | 4.2.2, 2025-12-01; commit 2026-10-09 | Java 21; some configurations unavailable on macOS |
| **Ultimate Automizer** | C, Boogie | Unbounded | Self-composition | Partial ACSL (old evidence) | ✗ | ✗ (GemCutter tool for concurrency) | Not verified | v0.3.1, 2025-12-01; commit 2026-10-09 | Linux and Windows zips only |
| **KLEE** | LLVM bitcode; C++ needs a `libc++` build option | Bounded (explores paths, generates tests) | Self-composition | Assertions only | Partial (`ENABLE_KLEE_LIBCXX`) | ✗ | Stops at `--max-time`; no proof claim | 3.2, 2025-12-23 (LLVM 16) | brew bottle (LLVM 16) |
| **VerCors** | Java, C, OpenCL, **OpenMP**, PVL | **Unbounded** (separation logic with access permissions) | Self-composition | Ghost code (wiki page "Auxiliary Annotations & Ghost Code"), contracts for each loop iteration; others not re-checked | ✗ (not listed) | **✓** (`parallel for`, `sections`, `simd`) | Not documented | 2.4.0, 2026-04-07; commit 2026-10-05 | 167.3 MB tar.xz |
| *CIVL* (extra) | C with OpenMP / MPI / CUDA subsets | Bounded ("relatively small bounds") | Native `compare` mode (prior scan, not re-checked) | None | ✗ | **✓** | Not verified | v1.23.0, 2026-05-26; commit 2026-10-09 | Java |

---

## Ranked shortlist

### Bounded tier ("proven within bounds")

1. **ESBMC 8.5.** Reads the C++ harness without changes, using its own Clang-based front end and
   library models (`src/cpp/library/` includes `vector`, `mutex`, `atomic`, `thread`).
   - It checks up to a declared bound and warns when the bound cut a loop short (`bmc.cpp`).
   - Its unbounded modes run on the same input.
   - **Risks:** C++ coverage is not complete, and its library models are themselves trusted
     semantics.
2. **crux-llvm 0.12 / SAW 1.6.** Reads any C++ that `clang++` compiles.
   - crux uses `--iteration-bound` and turns timeouts into "Unknown".
   - SAW can prove that two functions agree.
   - **Risks:** bounded only. Calls to outside code (pthreads, OpenMP runtime) need hand-written
     overrides. SAW's `llvm_verify` "can only handle loops with concrete bounds" (issue #3285).
3. **CBMC 6.11.** The most mature bounded checker for C, with contracts and history variables,
   and unwinding assertions on by default since 6.0.
   - **Risk:** C++ is spotty, so it needs a C port of the harness and strict layer: a second copy
     of the semantics that must be kept in sync with the C++ one.

### Unbounded tier ("proven unbounded")

1. **Frama-C/WP 33.0 (+ RPP 0.0.4).** The richest proof-hint language and per-goal verdicts
   with timeouts reported separately.
   - Smoke tests catch contradictory assumptions.
   - The relational extension (RPP) is maintained for 33.0.
   - **Risks:** C only (Frama-Clang is "known to be incomplete"). Automation on invariants that
     quantify over arrays is a known pain point. `axiom` and `admit` produce no proof obligation,
     so the hint checker must reject them.
2. **ESBMC** (`--k-induction`, `--loop-invariant-check`, `--enforce-contract`). Unbounded proofs
   on the same C++ input. `--check-vacuity` turns a vacuous success into UNKNOWN.
   - **Risks:** the contract and invariant features are new (many issues opened in 2026, e.g.
     #6923, where a quantified invariant never terminates). There is no lemma construct, and
     "ghost" variables are ordinary program variables.
3. **VerCors 2.4.0.** The only unbounded verifier that reads OpenMP. It is for the concurrency
   phase, on a C version of the code.
   - Runner-up: **VeriFast 26.10.** It is the only deductive verifier with a working C++ front
     end, but it has no standard-library specs and carries a heavy annotation burden.

**Not shortlisted:**
- SeaHorn: built against LLVM 14; C++ not documented; user hints only as assertions.
- SMACK: C only; bounded by default.
- CN: C only; no concurrency documented.
- CPAchecker and Ultimate: C only; built for SV-COMP-style properties; Ultimate has no macOS
  build.
- KLEE: finds bugs, does not prove.
- llreve: dead since 2021.
- Alive2: see the re-check below.

---

## Per-tool notes

### CBMC
- **C++:** the README says "for C and C++ programs". In issue #8663 (2025-06-24) a user
  measured header support with `goto-cc` 6.6: C++98/03 1/31, C++11/14 0/19, C++17 0/8.
  Maintainer M. Tautschnig: "with 6.6.0 it's certainly spotty". There are flags `--cpp98`,
  `--cpp03` and `--cpp11` (`src/util/config.cpp`).
- **Bounds:** "Checks enabled by default in v6.0+" include bounds, pointer and overflow checks,
  plus unwinding assertions (`src/cbmc/cbmc_parse_options.cpp:112-127`).
- **Unbounded:** loop contracts (`__CPROVER_assigns`, `__CPROVER_loop_invariant`,
  `__CPROVER_decreases`) applied with `goto-instrument --apply-loop-contracts`. Quantified
  invariants need `--smt2` (CBMC loop-contract docs).
- **Threads:** pthreads, encoded with partial orders (Alglave, Kroening & Tautschnig, CAV 2013).
  No GitHub issue mentions OpenMP.
- **`volatile`:** `goto-instrument --nondet-volatile-model` models each read of a `volatile` by
  a call to a model function (`src/goto-instrument/nondet_volatile.h`). Relevant to ticket 05.
- **Timeouts:** the CLI has no timeout option. The verdict strings are in
  `src/goto-checker/report_util.cpp`.

### ESBMC
- **Front end:** Clang syntax tree since v7.3 (Song et al., SBMF 2023). v7.6 updated the
  standard-library models (Li et al., arXiv 2406.17862). Test suites `esbmc-cpp11` through
  `esbmc-cpp23` exist. No `omp.h` model, and no GitHub issue mentions OpenMP.
- **Options** (`src/esbmc/options.cpp`):
  - `--loop-invariant-check` "cuts the loop, so cost is independent of the bound".
  - `--check-vacuity` reports "VERIFICATION UNKNOWN (vacuous discharge) instead of SUCCESSFUL".
  - `--enforce-contract` and `--replace-call-with-contract`.
  - `--timeout`.
- **Invariant syntax:** `__ESBMC_loop_invariant(...)`
  (`regression/loop-invariants/0-correct_sum/main.c`).
- **Contract syntax:** `__ESBMC_contract`, `__ESBMC_requires`, `__ESBMC_ensures`,
  `__ESBMC_assigns`, `__ESBMC_old` (`regression/function_contract/annotate_contract_basic/`).
- **LLM precedent:** ESBMC-ibmc (Pirzada et al., ASE 2024) replaces loop unrolling with
  LLM-generated invariants.

### Frama-C/WP (+ RPP, Frama-Clang)
- **Proof obligations generated by WP 33.0** (manual §2.1):
  - "lemma: 1 VC";
  - "loop invariant: 2 VCs (established, preserved)";
  - "axiom: no VC (admitted with no proof)" and "admit: no VC";
  - "statement contracts are not supported".
- **Verdicts:** none / valid / unknown / timeout / stepout / invalid / failed, with a JSON
  report (manual §2.8).
- **Smoke tests** put "False if reachable" on contradictory requirements (`-wp-smoke-tests`).
- **`volatile`:** "accessing a volatile l-value returns an undefined value" by default.
- **Concurrency:** the manual has no mention of threads or concurrency (searched "thread",
  "concurren").
- **C++:** Frama-Clang 0.0.20 (opam, 2026-09-25, libclang 22). The plugin page says it is "in an
  early stage of development" and "known to be incomplete". RPP: "Early prototype", v0.0.4
  "Frama-C 33.0 Arsenic".
- **LLM precedent:** AutoSpec (Wen et al., CAV 2024) writes ACSL with an LLM.

### SAW / crux-llvm
- **crux README:** links "a precompiled LLVM bitcode file containing the `libc++` library";
  "LLVM versions from 3.6 through 23 are likely to work well"; `--iteration-bound`,
  `--path-sat`; a low `--timeout` makes results "Unknown".
- **SAW loops:** issue #3285 (open, 2026-05-27): "`llvm_verify` today can only handle loops
  with concrete bounds". Loop fixpoint and invariant commands exist only for x86 machine code
  (issue #1734).
- **Scope:** the Crux paper (Pernsteiner et al., arXiv 2410.18280) says it targets "bounded,
  intricate pieces of code".

### Alive2: re-checking Extensa's 2026-06 rejection
- **Old claim:** "NOT Alive2 as primary (TSVC integer-only; needs heroics on loops)", from
  `MemAcc/AgenticRefiner/docs/superpowers/2026-06-19-session-handoff-sound-legality-gate.md:31`.
  The source is LLM-Vectorizer (Taneja et al., CGO 2025): its TSVC loops "operate on arrays of
  integer data type exclusively". Extensa's kernels used floating point, which Alive2 checks bit
  for bit; a correct reordering of a floating-point sum would therefore fail.
- **For BFS, that objection is gone.** `NodeID` and `SGOffset` are `int32_t` (`benchmark.h:29`,
  `graph.h:90`), and `bfs.cc` contains no `float` or `double`.
- **Still disqualifying:**
  - "Alive2 does not support inter-procedural transformations" (README), but every candidate
    artifact calls `maa_*`.
  - Loops are unrolled a fixed number of times, and "bugs that manifest only in a large number
    of unrolling may be missed" (LLM-Vectorizer).
  - With `-fopenmp`, each parallel region becomes calls into the OpenMP runtime (our reading).
- **Possible niche:** a quick bounded check of a small kernel slice, single-threaded and with
  everything inlined. Its brew bottle makes a 30-minute trial cheap (optional in ticket 08).

### Others, briefly
- **SeaHorn:** "This version compiles against LLVM 14". Engines: Horn-clause solving with Spacer
  ("invariant inference") and `--bmc`. Output: `unsat` = all assertions hold, `sat` = violated.
  Docker is "the easiest way" to install. Gurfinkel et al., CAV 2015.
- **SMACK:** "Currently SMACK only supports the C language"; "SMACK is a *bounded* verifier";
  `--pthread`. Rakamarić & Emmi, CAV 2014.
- **VeriFast:** README covers "single-threaded and multithreaded C, Rust and Java"; "lemma
  functions" are checked to "terminate and do not have side-effects". The C++ report (Mommen &
  Jacobs, arXiv 2212.13754) names templates as "the main missing feature". PR #1034 (open,
  2026-10-05) says the C++ front end "verifies monomorphized function templates", i.e. one
  instantiation at a time.
- **CN:** builds on Cerberus C semantics (Pulte et al., POPL 2023). Loop invariants use `inv`
  (cn-tutorial `docs/specifications/loop-invariants.md`). Its specs can also be turned into
  runtime checks ("translating those specifications into C assertions", README).
- **CPAchecker:** "Java 21 or later"; "large subset of (GNU)C"; on macOS "some configurations are
  unavailable" (README). Correctness witnesses carry invariants that let a checker rebuild a
  proof (Ayaziová et al., SPIN 2024). That format is a ready-made channel for hints.
- **Ultimate Automizer:** inputs "Boogie" and "C". Six-time SV-COMP overall winner (2016, 2017,
  2023–2026). Release assets are Linux and Windows only.
- **KLEE:** 3.2 notes: "Current recommended version is LLVM 16". C++ needs the
  `-DENABLE_KLEE_LIBCXX=ON` build. Whether the brew bottle includes it is unverified.
- **VerCors:** "Java, C, OpenCL, OpenMP, and PVL" (README). The OpenMP SIMD example checks
  `#pragma omp for simd` with a contract for each loop iteration ("Should Verify: Yes").
  Blom et al., iFM 2017.
- **llreve:** coupling-predicate regression verification (Felsing et al., ASE 2014; Kiefer et
  al., JAR 2017). README: multiplication "often leads to UNKNOWN". The idea transfers; the tool
  does not.

---

## Findings that touch ticket 01 and later tickets

1. **The proof-hint vocabulary depends on the tool (ticket 01 #8, ticket 13).**
   - WP has all four hint kinds natively, but `axiom` and `admit` produce no proof obligation,
     so the checker must reject them.
   - The bounded-checker family (ESBMC, CBMC) has loop invariants and contracts but **no lemma
     construct**, and its "ghost" variables are ordinary program variables. The checker must
     prove that ghost writes never reach program state.
2. **"Unknown" has more forms than timeout/unknown (ticket 13).** In bounded checking, a failed
   unwinding assertion means "bound too small", not "bug". ESBMC can also return UNKNOWN for a
   vacuous success. The hint loop's trigger should list each of these.
3. **For unbounded proofs, the strict layer will be trusted through contracts, not its C++
   (ticket 01 #10; tickets 05 and 12).** No unbounded tool can trace a growing operation list
   and the recursive `cover()`. The practical trusted semantics becomes `maa_*` contracts (ACSL
   or ESBMC). Those contracts need their own evidence against the strict layer, for example
   differential tests, which reopens a testing step inside "proven".
4. **The single-thread proofs check different code from what certification runs (ticket 09).**
   Certification builds with GCC `-O1 -fopenmp`. Verification builds use a Clang-based front end
   without `-fopenmp`, so the OpenMP code runs as sequential code. This falls under "compiler
   trusted" (ticket 01 #10), but what "proven" asserts must name the sequential meaning.
5. **The concurrency phase needs a different tool (map: "Not yet specified").** No shortlisted
   single-thread tool reads OpenMP. The options are VerCors, CIVL, or a pthreads version for
   ESBMC/CBMC.
6. **Vacuity guard (map: "Not yet specified"):** two tools already have one built in: WP smoke
   tests and ESBMC `--check-vacuity`.

## Open questions

- Does ESBMC's front end accept the strict layer as it is, including `static State` in an inline
  function, `lock_guard`, `__atomic_*` and `std::_Exit`? **Test this first in ticket 08.**
- Does Frama-Clang 0.0.20 accept the gapbs templates, so that WP can skip a C port? Not checked.
  It is "known to be incomplete".
- How are the `maa_*` contracts for unbounded proofs validated against the strict layer?
  (Tickets 05 and 12.)
- Is VerCors on macOS native arm64? The asset is named `macos`; the architecture was not
  confirmed.
- Are the ESBMC zip (11.3 MB) and the KLEE bottle built with `libc++` support? Unverified.

---

## Sources

### Papers (all checked through Crossref or the publisher page)

- Lopes, N. P., Lee, J., Hur, C.-K., Liu, Z., & Regehr, J. (2021). Alive2: Bounded translation
  validation for LLVM. *PLDI 2021*. https://doi.org/10.1145/3453483.3454030 · Bounded unrolling;
  basis for the Alive2 re-check.
- Taneja, J., Laird, A., Yan, C., Musuvathi, M., & Lahiri, S. K. (2025). LLM-Vectorizer:
  LLM-based verified loop vectorizer. *CGO 2025*. https://doi.org/10.1145/3696443.3708929 · Source
  of "integer data type exclusively" and of "Inconclusive" on timeout.
- Clarke, E., Kroening, D., & Lerda, F. (2004). A tool for checking ANSI-C programs. *TACAS
  2004, LNCS*. https://doi.org/10.1007/978-3-540-24730-2_15
- Alglave, J., Kroening, D., & Tautschnig, M. (2013). Partial orders for efficient bounded model
  checking of concurrent software. *CAV 2013, LNCS*. https://doi.org/10.1007/978-3-642-39799-8_9
- Gadelha, M. R., Monteiro, F. R., Morse, J., Cordeiro, L. C., Fischer, B., & Nicole, D. A.
  (2018). ESBMC 5.0: An industrial-strength C model checker. *ASE 2018*.
  https://doi.org/10.1145/3238147.3240481
- Song, K., Gadelha, M. R., Brauße, F., Menezes, R. S., & Cordeiro, L. C. (2023). ESBMC v7.3:
  Model checking C++ programs using Clang AST. *SBMF 2023*, 141–152.
  https://sol.sbc.org.br/index.php/sbmf/article/view/28041 (DOI not shown on page).
- Li, X., Song, K., Gadelha, M. R., Brauße, F., Menezes, R. S., Korovin, K., & Cordeiro, L. C.
  (2024). ESBMC v7.6: Enhanced model checking of C++ programs with Clang AST. *arXiv preprint*.
  https://arxiv.org/abs/2406.17862
- Pirzada, M. A. A., Reger, G., Bhayat, A., & Cordeiro, L. C. (2024). LLM-generated invariants
  for bounded model checking without loop unrolling. *ASE 2024*.
  https://doi.org/10.1145/3691620.3695512
- Gurfinkel, A., Kahsai, T., Komuravelli, A., & Navas, J. A. (2015). The SeaHorn verification
  framework. *CAV 2015, LNCS*. https://doi.org/10.1007/978-3-319-21690-4_20
- Rakamarić, Z., & Emmi, M. (2014). SMACK: Decoupling source language details from verifier
  implementations. *CAV 2014, LNCS*. https://doi.org/10.1007/978-3-319-08867-9_7
- Kirchner, F., Kosmatov, N., Prevosto, V., Signoles, J., & Yakobowski, B. (2015). Frama-C: A
  software analysis perspective. *Formal Aspects of Computing*.
  https://doi.org/10.1007/s00165-014-0326-7
- Blatter, L., Kosmatov, N., Le Gall, P., & Prevosto, V. (2017). RPP: Automatic proof of
  relational properties by self-composition. *TACAS 2017, LNCS*.
  https://doi.org/10.1007/978-3-662-54577-5_22
- Wen, C., Cao, J., Su, J., Xu, Z., Qin, S., & He, M. (2024). Enchanting program specification
  synthesis by large language models using static analysis and program verification. *CAV 2024,
  LNCS*. https://doi.org/10.1007/978-3-031-65630-9_16 · AutoSpec.
- Jacobs, B., Smans, J., Philippaerts, P., Vogels, F., Penninckx, W., & Piessens, F. (2011).
  VeriFast: A powerful, sound, predictable, fast verifier for C and Java. *NFM 2011, LNCS*.
  https://doi.org/10.1007/978-3-642-20398-5_4
- Mommen, N., & Jacobs, B. (2022). Verification of C++ programs with VeriFast. *arXiv preprint*.
  https://arxiv.org/abs/2212.13754
- Pulte, C., Makwana, D. C., Sewell, T., Memarian, K., Sewell, P., & Krishnaswami, N. (2023).
  CN: Verifying systems C code with separation-logic refinement types. *POPL 2023 (PACMPL 7)*.
  https://doi.org/10.1145/3571194
- Dockins, R., Foltzer, A., Hendrix, J., Huffman, B., McNamee, D., & Tomb, A. (2016).
  Constructing semantic models of programs with the Software Analysis Workbench. *VSTTE 2016,
  LNCS*. https://doi.org/10.1007/978-3-319-48869-1_5
- Pernsteiner, S., Diatchki, I. S., Dockins, R., Dodds, M., Hendrix, J., Ravich, T., Redmond,
  P., Scott, R., & Tomb, A. (2024). Crux, a precise verifier for Rust and other languages.
  *arXiv preprint*. https://arxiv.org/abs/2410.18280
- Felsing, D., Grebing, S., Klebanov, V., Rümmer, P., & Ulbrich, M. (2014). Automating regression
  verification. *ASE 2014*. https://doi.org/10.1145/2642937.2642987
- Kiefer, M., Klebanov, V., & Ulbrich, M. (2017). Relational program reasoning using compiler IR.
  *Journal of Automated Reasoning*. https://doi.org/10.1007/s10817-017-9433-5
- Beyer, D., & Keremoglu, M. E. (2011). CPAchecker: A tool for configurable software
  verification. *CAV 2011, LNCS*. https://doi.org/10.1007/978-3-642-22110-1_16
- Ayaziová, P., Beyer, D., Lingsch-Rosenfeld, M., Spiessl, M., & Strejček, J. (2024). Software
  verification witnesses 2.0. *SPIN 2024, LNCS*. https://doi.org/10.1007/978-3-031-66149-5_11
- Heizmann, M., Hoenicke, J., & Podelski, A. (2013). Software model checking for people who love
  automata. *CAV 2013, LNCS*. https://doi.org/10.1007/978-3-642-39799-8_2
- Cadar, C., Dunbar, D., & Engler, D. (2008). KLEE: Unassisted and automatic generation of
  high-coverage tests for complex systems programs. *OSDI 2008*.
  https://www.usenix.org/conference/osdi-08/klee-unassisted-and-automatic-generation-high-coverage-tests-complex-systems
- Blom, S., Darabi, S., Huisman, M., & Oortwijn, W. (2017). The VerCors tool set: Verification
  of parallel and concurrent software. *iFM 2017, LNCS*. https://doi.org/10.1007/978-3-319-66845-1_7
- Siegel, S. F., Zheng, M., Luo, Z., Zirkel, T. K., Marianiello, A. V., Edenhofner, J. G., et al.
  (2015). CIVL: The Concurrency Intermediate Verification Language. *SC 2015*.
  https://doi.org/10.1145/2807591.2807635

### Tool documentation and source (read 2026-10-09)

- CBMC: README and loop-contract docs (https://diffblue.github.io/cbmc/contracts-loops.html);
  `src/cbmc/cbmc_parse_options.cpp`; `src/goto-checker/report_util.cpp`;
  `src/goto-instrument/nondet_volatile.h`; `src/util/config.cpp`; issue
  https://github.com/diffblue/cbmc/issues/8663.
- ESBMC: README; `src/esbmc/options.cpp`; `src/esbmc/bmc.cpp`; `docs/manual.tex`;
  `src/cpp/library/` listing; `regression/loop-invariants/0-correct_sum/`;
  `regression/function_contract/annotate_contract_basic/`; issues #6923 and #7516.
- Frama-C: https://frama-c.com/html/get-frama-c.html; WP manual 33.0
  (https://frama-c.com/download/wp-manual-33.0-Arsenic.pdf, §2.1, §2.4, §2.8, limitations);
  https://frama-c.com/fc-plugins/frama-clang.html; https://opam.ocaml.org/packages/frama-clang/;
  https://frama-c.com/fc-plugins/rpp.html; https://github.com/lyonel2017/Frama-C-RPP/releases.
- SeaHorn: https://github.com/seahorn/seahorn (README, branch list).
- SMACK: README and `docs/usage-notes.md` (https://github.com/smackers/smack).
- VeriFast: README; PR https://github.com/verifast/verifast/pull/1034; release 26.10 assets.
- CN: https://github.com/rems-project/cn README; cn-tutorial `docs/specifications/loop-invariants.md`.
- SAW / crux: `crux-llvm/README.md` (https://github.com/GaloisInc/crucible); issues
  https://github.com/GaloisInc/saw-script/issues/3285 and /1734; release assets.
- Alive2: README (https://github.com/AliveToolkit/alive2).
- llreve: https://github.com/mattulbrich/llreve README and `reve/README.md`.
- CPAchecker: README (https://github.com/sosy-lab/cpachecker); https://cpachecker.sosy-lab.org/.
- Ultimate: https://www.ultimate-pa.org/; GitHub releases.
- KLEE: v3.2 release notes (https://github.com/klee/klee/releases/tag/v3.2); build guide
  (`ENABLE_KLEE_LIBCXX`).
- VerCors: README (https://github.com/utwente-fmt/vercors); OpenMP SIMD example
  (https://vercors.ewi.utwente.nl/try_online/example/openmp-simd-programs.html).
- CIVL: https://verified-software-lab.github.io/civl/; GitHub release v1.23.0.
- Homebrew formula API (https://formulae.brew.sh/api/formula/<name>.json): cbmc, esbmc, klee and
  alive2 have arm64 bottles; frama-c, verifast, cpachecker, smack, seahorn, saw, ultimate and
  vercors have no formula.

### Prior internal notes (context, not evidence)

- `MemAcc/.scratch/next-project-verified-agentic-opt-2026-09-20/lit_C_tools_kernels_fp.md` — a
  2026-09-20 tool sweep. Its claims were re-checked here wherever they are used.

## Method and limits

- **Scope:** lit-review discipline, single agent, no sub-agents. Every claim cites a primary
  source; "our reading" marks an inference.
- **Not run:** no tool was installed or run. Statements about what "chokes" on our constructs come
  from documentation and source code; ticket 08 must confirm them empirically.
- **Absence claims are limited to the searches named.** Example: "no OpenMP issue" means a GitHub
  issue search for `openmp` in that repository on 2026-10-09 returned zero results.
- **Not checked:** the CN tactics page and the VerCors ghost-code page (CN's page is an empty
  stub). Ultimate's current ACSL coverage. CIVL's `compare` mode (taken from the 2026-09-20 sweep).
