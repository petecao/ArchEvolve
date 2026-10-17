# Research 11: Verifier facts for the bounded and unbounded tiers

Created: 2026-10-12 23:21 ET
**Ticket:** [11](../issues/11-verifier-choice.md) · **Map:** [../map.md](../map.md)
**Method:** primary sources (manuals, release assets via the GitHub API, source files at the
release tags, the local opam repository snapshot) plus small scratch runs on the Mac with the
tools ticket 07 installed. Nothing was installed, upgraded or downloaded as a binary. Scratch
files lived in the session scratchpad and are not kept. "Our reading" marks an inference.
"Unconfirmed" marks what could not be checked.

---

## TL;DR

1. **Floats as reals: only crux-llvm (`-f real`) and Frama-C/WP (`-wp-model +real`) give a clean
   exact-real mode.** ESBMC `--ir` is reals with IEEE-like overflow and underflow clamps, and it
   also makes integers unbounded. CBMC has no usable mode. SAW has no flag. No mode models the
   rounding error, so "rounding in the assumption set" must be stated outside the proof.
2. **crux trap:** with no `-f` flag, the float mode depends on the solver: z3 and bitwuzla use
   IEEE, cvc5, yices, cvc4 and stp use reals. Always pass `-f`.
3. **Summaries (contracts that replace calls):** SAW (`llvm_verify` returns an override;
   `llvm_unsafe_assume_spec`), ESBMC and CBMC (both confirmed by a run). crux-llvm has no contract
   feature. A hand-written C stub (`check` the precondition, havoc, `assuming` the
   postcondition) works, but the link to the real body is manual.
4. **SAW 1.6:** a macOS arm64 asset exists. Its bitcode parser (llvm-pretty-bc-parser 0.6.1.0)
   adds LLVM 21 and 22 metadata, which is what crux 0.12 (parser 0.6.0.0) warned about. The
   README says it was tested only up to LLVM 20. Loops need concrete bounds, except through
   **experimental "cutpoint" loop invariants** (partial correctness only).
5. **WP cannot prove an induction lemma automatically** (Alt-Ergo, Z3 and CVC5 all time out). The
   `Wp.induction` tactic can be applied from ACSL `\wp::strategy` text without the GUI and
   replayed from JSON scripts. In our test, 2 of its 3 subgoals were proved and the third was
   never attempted (cause unresolved). **No Rocq/Coq in the `framac-33` switch.**
6. **VerCors 2.4.0 does not verify OpenMP parallel regions.** A `#pragma omp parallel { … }` block
   is rejected as "not supported", and loop pragmas are dropped. Parallelism comes only from
   **iteration contracts**, encoded as one logical thread per iteration, so the proof does not
   depend on the thread count. GAPBS's region with per-thread buffers and `omp for reduction
   nowait` must be rewritten first. VerCors reads a basic C++ subset (no classes, no templates).
7. **Frama-Clang 0.0.20:** opam pins libclang 22. On this Mac its configure step would pick the
   `llvm` keg from `PATH`, so no keg change is needed, but it inherits the hand-copied
   `libz3.4.16` repair. Its manual says templates are "not robust", the standard library is
   "very rudimentary" and ACSL++ ghost code is "not yet implemented".
8. **RPP 0.0.4 handles loops only by inlining each function with its own one-program loop
   invariants** (confirmed on RPP's own loop test). It has no relational (coupling) invariants and
   no product programs. **CBMC's contract flags live in `goto-instrument --dfcc`, not in
   `cbmc`.**

---

## A. Floating point as real arithmetic

The test property was `(a*b)*c == a*(b*c)` with `a, b, c` in [1, 2]. It is true over the reals and
false in IEEE double.

| Tool | Real mode | What it does | Run on the Mac (2026-10-12) | Sound for "equal over the reals"? |
|---|---|---|---|---|
| crux-llvm 0.12 | `-f real` (`--floating-point=real`) | What4 `FloatReal` (details below) | z3 (default IEEE): Invalid. z3 `-f real`: Valid. cvc5 (default): **Valid**. cvc5 `-f ieee`: Disproved. bitwuzla (default): Invalid | Yes, for the real idealization of the code, if the code never needs NaN, infinity or float bit casts |
| SAW 1.6 | none (no flag) | Backend fixed to What4 `FloatReal` in source; docs say float support is rudimentary | not run (SAW is not installed) | Unconfirmed |
| ESBMC 8.5 | `--ir`; `--ir-ieee` | Integer/real SMT encoding with clamps (details below) | default: FAILED. `--ir`: SUCCESSFUL. `--ir-ieee`: **SUCCESSFUL** (an IEEE-false property) | Not cleanly (clamps; unbounded integers) |
| CBMC 6.11 | none | IEEE only (`--fpa` = SMT float theory; rounding-mode flags) | `__CPROVER_real` parses, but the SAT back end warns "ignoring typecast" and reports a true assertion as FAILURE; `--z3` crashes with an invariant violation | No usable mode |
| Frama-C/WP 33.0 | `-wp-model +real` (`+float` is the default) | Manual §1.5 (details below) | float model: Timeout. `+real`: 3/3 proved | Yes, for the real idealization. The manual's "unsound" is about IEEE |

**crux-llvm 0.12**
- Flag: "`--floating-point=FPREP`, `-f FPREP`: … one of `real`, `ieee`, `uninterpreted`, or
  `default`. Default representation is solver specific: `real` for CVC4 and Yices, and `ieee` for
  Z3" (bundled `doc/README.md:281-284`; `crux-llvm --help`).
- Default per solver (source `crux/src/Crux.hs:375-382` at the 0.12 commit `31cc4ad4`): Yices,
  CVC4, **CVC5** and STP use reals; Z3 and Bitwuzla use IEEE.
- What `FloatReal` means (What4 at the pinned commit, `What4/FloatMode.hs:50-54`): values are
  "treated as real-number values, to the extent possible. Expressions that would result in
  infinities or NaN will yield unspecified values in this mode, or directly produce runtime
  errors."
- Rounding (What4 `Expr/Builder.hs:4066-4140`):
  - `iFloatAdd sym _ = realAdd sym`, and the same for sub, mul and div: the rounding-mode argument
    is ignored.
  - `iFloatCast _ _ _ = return`: double-to-float casts are the identity.
  - `iFloatIsNaN` and `iFloatIsInf` are always false, and NaN or infinity literals abort.
  - A double literal becomes its exact binary value (`realLit sym . toRational`).
  - Float-to-bits casts become uninterpreted functions.
- Our reading: a proof in this mode is a proof about the real-number program, which is exactly
  "equal over the reals". It says nothing about IEEE results. Division by zero becomes SMT real
  division, whose value at 0 is unspecified (not checked).

**SAW 1.6**
- Source: `type Backend solver = OnlineBackend … (W4.Flags W4.FloatReal)`
  (`saw-central/src/SAWCentral/Crucible/Common.hs:80`, tag v1.6). The same file maps
  `BaseRealRepr` and `BaseFloatRepr` to no Cryptol type (line ~169).
- Docs: `llvm_float`/`llvm_double` exist, "However, SAW's support for floating point is
  rudimentary so these types are currently of little use" (`doc/saw-user-manual/verifying-code.md`,
  "LLVM Types"). The developer notes say "For LLVM, floating point is not supported at all"
  (`doc/developer/limitations.md:141-144`).
- So whether SAW proves float code over the reals is **unconfirmed**.

**ESBMC 8.5**
- Help: "`--ir` Use solver with integer/real arithmetic. Integer/real have an unbounded range,
  overapproximating normal integers/reals"; "`--ir-ieee` Use integer/real arithmetic with
  real-arithmetic enclosure constraints for floating-point operations" (`esbmc --help`).
- Manual: integer mode "also represents floating point numbers as reals", and "there can be no
  accurate byte model" (`docs/manual.tex:1274-1287`, tag v8.5).
- Source for `--ir` (`src/solvers/smt/smt_fp_conv.cpp`, `apply_ieee754_semantics`, tag v8.5):
  - the exact real result is kept in the normal range;
  - overflow saturates to ±max normal;
  - results below half the smallest subnormal flush to 0.
- Source for `--ir-ieee` (`src/solvers/smt/fp/ir_ieee_conv.cpp:501-538`): the code asserts
  `ra_lo <= r <= ra_hi` around the exact result `r`, but returns `r` itself (after the flush). The
  rounding error therefore never reaches the value. That is why it proved the IEEE-false
  property above.
- More runs:
  - Add-associativity on (−1000, 1000) **failed** under `--ir`: the counterexample uses values
    near 4.9e-324, where a partial sum hits the flush.
  - `0.1 + 0.2 == 0.3` failed in every mode: literals keep their double value.
- Our reading: `--ir` can call two different reals equal when both overflow, can break real
  identities near zero, and drops integer wraparound. It is not a clean "reals" mode for mixed
  integer/float kernels.

**CBMC 6.11**
- `cbmc --help` offers only the IEEE choices: `--fpa` "use theory of floating-point arithmetic",
  and `--round-to-nearest/-plus-inf/-minus-inf/-zero`.
- No real mode is documented. The `__CPROVER_real` keyword exists in the binary (`strings`), but
  the runs above show the back ends do not support it.

**Frama-C/WP 33.0**
- `frama-c -wp-h`: "`+real/+float` real / IEEE floating point arithmetics" under `-wp-model`.
- WP manual 33.0, §1.5 Arithmetic Models (p. 11):
  - "Real Model: floating-point operations are transformed on reals, with no rounding. This is
    completely unsound with respect to C and IEEE semantics. There is no way of recovering a
    correct or partial property from the generated proof obligations on floating-point
    operations with this model."
  - "Float Model … correct with respect to the IEEE specifications, this model still provides
    very little support for proving properties with automated provers."
- How literals are treated in `+real` mode: unconfirmed.

---

## B. SAW 1.6

- **macOS arm64 asset: yes.** Release v1.6 (2026-09-17) has `saw-1.6-macos-15-ARM64.tar.gz`
  (178,457,834 B) and `saw-1.6-macos-15-ARM64-with-solvers.tar.gz` (226,501,546 B) (GitHub API,
  `repos/GaloisInc/saw-script/releases`).
- **Bitcode versions:**
  - README (tag v1.6, "Notes on LLVM"): "We have tested SAW with LLVM and `clang` versions from
    3.5 to 20.0, as well as the version of `clang` bundled with Apple Xcode."
  - Tag v1.6 pins `deps/llvm-pretty-bc-parser` at `e9cb31e7`, which is tag
    `llvm-pretty-bc-parser-0.6.1.0` (GitHub API).
  - That parser's changelog: "Support LLVM 22: … `sourceLanguageVersion` fields in
    `DICompileUnit` … `dataSize` fields in `DIBasicType`", plus LLVM 21 `DISubrangeType`/
    `DIFixedPointType`. The SAW 1.6 release notes repeat the LLVM 21 items.
  - crux 0.12 pins parser `b78d998c` = 0.6.0.0 (crucible `dependencies/` at commit `31cc4ad4`).
    Its warnings in ticket 07's logs, "Invalid record size: 23" on `METADATA_COMPILE_UNIT` and
    "9" on `METADATA_BASIC_TYPE`, match exactly those two LLVM 22 fields (our reading).
  - So clang 22 bitcode should parse in SAW 1.6. **Untested.**
- **C++:** "it will be necessary to link your code with a version of the `libc++` library compiled
  to LLVM bitcode"; SAW "only understands the mangled names"; "there is no support for calling
  constructors in specifications" (manual "Working With C++"). Unlike crux, SAW bundles no
  `libc++` bitcode (our reading of the same section).
- **Compositional verification (summaries):**
  - Signature: `llvm_verify : LLVMModule -> String -> [LLVMSpec] -> Bool -> LLVMSetup () ->
    ProofScript () -> TopLevel LLVMSpec`. The list holds "already-verified specifications to use
    as overrides" (manual "LLVM Verification").
  - At a call to an overridden function, the simulator "will not follow calls". It checks the
    spec's preconditions and points-to facts, then updates the state from the post-state
    (manual "Compositional Verification").
  - `llvm_unsafe_assume_spec` takes "only the LLVM module handle, function name, and spec": an
    override with no proof, meant for library code (manual "Overrides and Compositional
    Verification").
  - Limit: it reuses "proof effort", not "specification effort".
- **Loops with symbolic bounds:**
  - Symbolic execution unrolls each loop until it "symbolically terminates". "Counting loops with
    symbolic bounds in general do not symbolically terminate", unless the bound itself has a
    concrete bound and path-sat checking is on. "The inability to handle unbounded loops is a
    fundamental limitation of symbolic execution" (manual `symbolic-execution.md:127-190`).
  - The Salsa20 example proves the top-level function separately for sizes 63, 64 and 65 "due to
    the limitation that SAW can only operate on finite programs".
  - **Exception, "Multi-Step Proofs and Loop Invariants with Cuts"** (manual, LLVM only,
    "highly experimental"):
    - Put a call to an empty `__cutpoint__name(&live1, &live2, …)` in the loop condition.
    - Assume its spec with `llvm_unsafe_assume_spec m "__cutpoint__inv#f"`.
    - Verify that spec with itself as the override, then verify `f` with it.
    - This is "a proof by induction", but "this technique only provides partial correctness".
      You must pass every live variable by pointer in LLVM stack-frame order; errors crash SAW
      "deep inside the logic". Tests: `intTests/test_cutpoint/` (8 tests at v1.6).
  - `llvm_verify_fixpoint` for bitcode is **PR #3285 (open)**, not part of 1.6. The fixpoint
    commands that exist work on x86 machine code only.
- **Comparing two functions:**
  - Documented way: `llvm_extract` both functions to terms, then `prove` that they are equal
    (`ffs_ref == ffs_imp`, tutorial "Equivalence Proof"). Only for functions that "take some fixed
    number of integral parameters and return an integral result" and touch no mutable globals
    (manual "Extracting Code").
  - For functions over pointers or memory: verify both against one `llvm_verify` spec whose
    post-state is a shared Cryptol model (our reading; there is no dedicated command).

---

## C. crux-llvm 0.12 without SAW: summaries in C

- **No contract feature.** The README describes only "inline specifications (in the form of
  function calls to create non-deterministic values and assert properties)" (bundled
  `doc/README.md:7-10`).
- **C-level intrinsics** (`c-src/includes/crucible.h:12-49`; overrides registered in
  `crux-llvm/src/Crux/LLVM/Overrides.hs:89-349` at `31cc4ad4`):
  - Assume and assert: `crucible_assume(uint8_t, file, line)` and
    `crucible_assert(uint8_t, file, line)`, with the macros `assuming(e)` and `check(e)`.
  - Fresh values: `crucible_int8_t` … `crucible_int64_t`, `crucible_uint8_t` …
    `crucible_uint64_t` (macros), `crucible_float`, `crucible_double`, and
    `crucible_string(name, max_len)` (read-only).
  - Memory and debugging: `crucible_havoc_memory(void *p, size_t len)` ("Fill a region of memory
    with fresh symbolic bytes"), `crucible_print_uint32`, `crucible_dump_memory`.
  - CBMC style: `__CPROVER_assume`, `__CPROVER_assert`, `__CPROVER_r_ok`, `__CPROVER_w_ok`, and
    `nondet_bool/char/uchar/short/ushort/int/uint/long/ulong/size_t/float/double`,
    `nondet_[u]intN_t`.
  - SV-COMP style: `__VERIFIER_nondet_*` (int, uint, long, ulong, longlong, short, ushort, char,
    uchar, bool, size_t, float, double, u8/u16/u32, loff_t).
  - `crucible_size_t` is declared in `crucible.h` but has no override in `Overrides.hs`. Whether
    it works: unconfirmed.
- **The manual summary pattern works.** Compile a stub definition of the callee in place of its
  body. Run on 2026-10-12:

  ```c
  void fill(int *a, unsigned n) {               /* stub = contract of fill */
    check(n <= 4);                              /* precondition, asserted at each call */
    crucible_havoc_memory(a, 4 * sizeof(int));  /* frame: outputs become arbitrary */
    for (unsigned i = 0; i < 4; i++) if (i < n) assuming(a[i] == 7);  /* postcondition */
  }
  ```

  - The caller proved: 5/5 goals Valid.
  - A caller claim that the contract does not imply (`a[3] == 0`) was Disproved.
- **What is missing compared with SAW and ESBMC:**
  - Nothing checks that the real body meets the stub. That needs a second harness (`assuming(pre)`,
    call the real body, `check(post)`) kept in sync by hand.
  - There is no `\old`: pre-state values must be copied by hand.
  - Havoc with a symbolic length: untested.
- **Loops:** the real `fill` with a symbolic bound `n ≤ 4` did not finish in 120 s without
  `--path-sat`. With `--path-sat` it was Valid (4 goals) in 0.15 s. This matches the README: path
  satisfiability "can help programs terminate, particularly in the case where the bounds on loops
  are complex" (`doc/README.md:362-364`).

---

## D. Frama-Clang 0.0.20

- **In opam: yes.**
  - Local repository snapshot (`~/.opam/repo/default.tar.gz`,
    `packages/frama-clang/frama-clang.0.0.20/opam`) depends on: `"frama-c" {>= "33.0~" & <
    "34.0~"}`, `"conf-libclang" {= "22"}`, `camlp-streams`, `dune >= 3.13`, `zarith >= 1.5`,
    `conf-cmake`.
  - ocaml.org shows it "Added to opam-repository: 25 Sep 2026".
- **Which LLVM it would use on this Mac:**
  - `conf-libclang.22` has the Homebrew system dependency `llvm@22`. That keg is installed
    (22.1.8, `/opt/homebrew/opt/llvm@22`).
  - Its configure script (`opam-source-archives/patches/conf-libclang/configure-generic.sh.1`)
    tries `command -v llvm-config` first, then `$(brew --prefix)/opt/llvm/bin/llvm-config`, and
    accepts any major version ≤ 22.
  - Here `command -v llvm-config` = `/opt/homebrew/opt/llvm/bin/llvm-config` (22.1.8), the
    unversioned `llvm` keg.
  - **So installing would not change the `llvm` keg** (our reading of the script).
  - But Frama-Clang would link that keg's `libclang.dylib` → `libLLVM.dylib` →
    `/opt/homebrew/opt/z3/lib/libz3.4.16.dylib`, the hand copy from ticket 07 (`otool -L`). If
    that copy disappears, Frama-Clang breaks with the analytic evaluator.
  - The `llvm@22` keg's `libLLVM.dylib` does not link z3 (`otool -L`). Putting
    `/opt/homebrew/opt/llvm@22/bin` first on `PATH` during the install should select it (our
    reading; untested).
- **What opam would add:** `camlp-streams`, `conf-libclang`, `conf-cmake`. `dune` 3.24.2 and
  `zarith` 1.14 are already in the switch; `cmake` is at `/opt/homebrew/bin/cmake`.
- **Builds on macOS arm64?** Unconfirmed. Opam CI ran 0.0.19 on a
  `macos-homebrew-ocaml-5.4-arm64` variant, but the result page returned 403.
- **C++ support** (Frama-Clang manual v0.0.20 "for Frama-C version 33.0 Arsenic"):
  - "The plug-in aims for the C++11 version of C++" (p. 5).
  - The manual still says "compatible with version 11.0-18.0 of Clang" (pp. 5–6), which is stale
    against opam's libclang 22 pin. Its change log also stops at 0.0.15.
  - §5.1, "not implemented … (the list is not nearly complete)": "uses of typename", "uses of
    templates are not robust", "uses of typeid", "implementation of the standard library is very
    rudimentary", "main target of Frama-Clang is C++11" (p. 14).
  - §5.2, ACSL++ not yet implemented: "ghost code is not yet implemented", "ACSL++ definitions
    within template declarations", "rounding mode and related builtin functions", "set
    comprehensions", "\valid_function \allocable \freeable \fresh" (pp. 14–15).
  - Lambdas: "support for C++14 generic lambdas" (0.0.12); "Preliminary support for lambdas"
    (0.0.7).
  - Standard headers: Frama-Clang ships replacement headers with ACSL++ specs, "a subset", "still
    very much a work in progress" (p. 6). "The system header files supplied by Frama-Clang does
    not include all C++ system files."
  - `enum class`: not mentioned anywhere. Unconfirmed.

---

## E. VerCors 2.4.0

- **macOS asset:** one file, `vercors-2.4.0-macos.tar.xz` (167,326,220 B), with no architecture
  in the name (GitHub API, release v2.4.0, 2026-04-07).
  - VerCors is a JVM tool: "requires a java runtime environment (version 17 or later), as well as
    clang if you want support for C" (README).
  - The README's Mac section names `res/deps/z3/4.8.6/Darwin/x86_64/bin/z3`. That path is stale:
    at v2.4.0 the tree has `res/universal/deps/darwin/z3/bin/z3`, last changed by "update z3 to
    4.12.5" (2024-01-28).
  - **Native arm64: unconfirmed** (the binary was not downloaded).
- **OpenMP in 2.4.0 is mostly not supported:**
  - The grammar parses `parallel`, `for`, `parallel for`, `for simd`, `sections` and `section`,
    with `nowait`, `private`, `shared`, `schedule(static)`, `simdlen`, `num_threads` and
    `reduction` (`src/parsers/antlr4/LangOMPParser.g4`).
  - But the C converter maps a `#pragma omp parallel { … }` block to `??(block)`
    (`src/parsers/vct/parsers/transform/CToCol.scala:491`). `??` fails with "This construct … is
    syntactically valid, but not supported by VerCors" (`ToCol.scala:235-239`).
  - A loop's OpenMP pragma (`maybePragma`) is dropped, and the loop becomes an ordinary loop
    (`CToCol.scala` ~575–640).
  - The test helper cancels any example that fails with "not supported"
    (`test/…/helper/VercorsSpec.scala:105-110`). Of the nine examples in `OpenMPSpec.scala`:
    - five use a `#pragma omp parallel` block and are therefore skipped, not verified (our
      reading): `add-spec.c`, `add-spec-simd.c`, `sections-reduced.c`,
      `sections-reduced-fail.c`, `sum-spec.c`;
    - three put `#pragma omp parallel for private(i)` on a single loop and can verify through
      its iteration contract: `copy-spec.c`, `init-spec.c`, `zero-spec.c`;
    - the ninth, `addvec2.pvl`, is PVL, not C.
- **How parallel loops are verified (any thread count):**
  - A `for` loop whose contract uses `requires`/`ensures`/`context_everywhere` (not
    `loop_invariant`) becomes an `IterationContract` (`ToCol.scala` `consumeLoopContract`).
  - `IterationContractToParBlock` rewrites it into a `ParBlock` with one iteration variable over
    `[low, high)`: "Translate loops with an iteration-style contract to a parallel block"
    (`src/rewrite/vct/rewrite/IterationContractToParBlock.scala`).
  - Theory (Blom, Darabi & Huisman, "Verification of Loop Parallelisations", FASE 2015, extended
    abstract at ris.utwente.nl): an iteration contract "specifies the iteration's resources, i.e.,
    the variables read and written by one iteration". The soundness proof shows "the
    instrumented semantics of an independent loop is equivalent to the parallel execution of the
    loop".
  - The example comment `examples/concepts/openmp/sum-spec.c` says: "there are len logical thread
    that are mapped to an unknown number of physical threads".
  - Our reading: the proof treats each iteration as its own thread, so it holds for any number
    of OpenMP threads and any schedule.
- **What the user must write** (from `add-spec.c`):
  - a function contract with permissions, e.g. `context \pointer(a, len, 1\2) ** \pointer(c, len,
    write)`;
  - a per-iteration contract, e.g. `context Perm(c[i],1) ** Perm(a[i],1\2); ensures c[i] ==
    a[i];`;
  - functional `ensures` with quantifiers.

  Per-physical-thread state is the hard part. `sum-spec.c` calls its private accumulator
  "difficult to encode into PVL". The same applies to GAPBS's per-thread `QueueBuffer` and
  `reduction(+:scout_count)` (our reading).
- **C++: a basic subset, since 2.1.0** (PR #1052, "Implemented basic C++ support"):
  - Covered: `if`, `while`, simple `for`, arithmetic, functions, arrays, pointers, namespaces,
    basic types.
  - Not covered: "Implementing classes is to much work".
  - `CPPToCol.scala` comments: "Do not support templates", "Do not support enum or class
    declarations", and `templateDecl => ??`. It has no OpenMP hooks (grep for `omp`/`pragma`
    found none).
  - The release notes also list a "Pallas" LLVM-IR front end. Not evaluated.

---

## F. Frama-C/WP 33.0 and induction lemmas

- **Automatic: no.** Test lemma (axioms `sum(0)==0` and `sum(n)==sum(n-1)+n`):
  `\forall integer n; n >= 0 ==> 2*sum(n) == n*(n+1)`. Alt-Ergo 2.6.4, Z3 5.1.0 and CVC5 1.2.1
  each returned **Timeout** at 20 s.
- **Tactic route (machine-checked inside WP, replayable):**
  - `frama-c -wp-tactic Wp.induction` prints "Proof by integer induction", with parameter `base`.
    Manual §2.3.9 (pp. 25–26) gives the rule: strong induction with three subgoals (base case,
    `b < e`, `e < b`).
  - Scripts are JSON files in the session's `script/` folder (§2.6, p. 51).
    `-wp-prover script,Alt-Ergo` replays them and "never modifies the proof session and the proof
    scripts" (§2.3.5, p. 20).
  - **No GUI needed:** since Frama-C 28, ACSL annotations `\wp::strategy` and `\wp::proof` apply
    tactics automatically under `-wp-prover tip` (§2.5, p. 48). An agent can write this as text.
    Patterns must use the printed name (`L_sum(n)`, not `sum(n)`).
- **What happened:**
  - `\tactic("Wp.induction", \pattern(L_sum(n)), \select(n), …)` applied induction.
  - Alt-Ergo proved "Base" and "Induction (sup)".
  - "Induction (inf)" was **never attempted** in five variants (with `\children`, with an explicit
    `\child` per subgoal, with `-wp-strategy`, with and without `base`). The result stayed
    `Unknown (Alt-Ergo 2/3)`. **Cause unresolved.**
- **Trust:** tactics run inside WP itself, not in a separate proof kernel (our reading).
- **Rocq/Coq backend:** WP supports Coq through Why3 "Since Frama-C 22.0" via
  `-wp-interactive batch|update|edit|fix|fixup` (§2.4.8, p. 39).
  - **Not installed:** `opam list` for `framac-33` shows no `coq`/`rocq` package; there is no
    `coqc`, `coqtop` or `rocq` on `PATH`; `frama-c -wp-list-provers` lists only Alt-Ergo 2.6.4,
    CVC5 1.2.1 and Z3 5.1.0.
  - Adding it would need `why3-coq.1.8.2`, which requires `coq {>= "8.16" & < "8.17~"}` or
    `coq-core` + `coq-stdlib {< "9.1~"}` (local opam repository).
  - `frama-c-gui` is installed (`~/.opam/framac-33/bin/frama-c-gui`).

---

## G. Contract flags in CBMC 6.11 and ESBMC 8.5

- **CBMC 6.11: the flags exist, in `goto-instrument`, not in `cbmc`.**
  - `cbmc file.c --enforce-contract increment` → "Unknown option: --enforce-contract".
  - `goto-instrument --help` ("Code contracts") lists: `--dfcc harness`, `--enforce-contract
    function[/contract]`, `--replace-call-with-contract function[/contract]`,
    `--enforce-contract-rec`, `--apply-loop-contracts`, `--loop-contracts-no-unwind`.
  - Run with `goto-cc` → `goto-instrument --dfcc main …` → `cbmc`:
    - enforce, correct body: SUCCESSFUL;
    - enforce, buggy body: FAILED on "Check ensures clause of contract";
    - replace, buggy body: SUCCESSFUL (the caller uses the contract).
  - The first run failed until `main` set the global `counter = 0`. With `--dfcc`, globals appear
    to start nondeterministic (our reading).
- **CBMC C mode: confirmed.** `cbmc file.c` uses the C front end; the default standard is C11
  ("`--c89, --c99, --c11, --c17, --c23` set C language standard (default: c11)", `cbmc --help`).
  Plain C with `__CPROVER_*` contracts parsed and verified.
- **ESBMC 8.5: confirmed.** `esbmc --help` "Function Contracts": `--enforce-contract fun`,
  `--replace-call-with-contract fun` ("*" for all), `--enforce-all-contracts`,
  `--replace-all-contracts`. Runs:
  - C: enforce, correct: SUCCESSFUL; enforce, buggy: FAILED; replace: SUCCESSFUL.
  - C++: enforce, correct and buggy: as in C. **Named replace of `int increment(int)` failed**
    with "no function of that name has a body here". `--replace-call-with-contract '*'` worked,
    and so did ESBMC's own regression `cpp_replace_pass` (`void increment(void)`).

---

## H. RPP 0.0.4 and loops

- Release v0.0.4 (2026-09-07): "compatible with Frama-C 33.0 Arsenic". RPP "is based on the
  technique of self-composition and works like a preprocessor for *WP*" (README).
- **Loops are allowed, but only one-program invariants are used.** On RPP's own test
  `tests/rpp/loop_rela.c` (two loop functions `f` and `g`, property
  `\callpure(f,n) == \callpure(g,n)`, each with its own functional loop invariants and `ensures`),
  run with `frama-c -rpp loop_rela.c -then-last -wp`:
  - The wrapper inlined both loops with their six original invariants. All were proved, and so
    was `check Rpp`.
  - `Relational_lemma_1` and the `terminates` goals timed out (the loops have no
    `loop variant`).
- **No relational (coupling) invariants, no product programs:**
  - "it is not possible yet to specify 'relational invariants'", "treatment of loops needs to be
    improved", "Solutions based on program products [2] look promising" (Blatter, Kosmatov,
    Le Gall, Prevosto & Petiot, "Static and Dynamic Verification of Relational Properties on
    Self-Composed C Code", TAP 2018, arXiv 1801.06876).
  - The 0.0.4 source has no loop-specific code (no match for `loop`/`invariant` in
    `rpp_*.ml`). Our reading: loops are copied as they are.
- **Consequence for PR and BC:** a relational proof over loops needs a complete functional spec
  of each loop (e.g. `ensures \result == sum(...)`), because the two copies run one after the
  other.
- **Other limits** (README and ticket 07):
  - `\callpure` only for pure functions with `assigns \result \from <formals>`; side effects need
    `\callset(\call(f,…,id))` with `\at(…, Pre_id/Post_id)`.
  - The generated `Relational_lemma` always times out; `check Rpp` decides.

---

## Contradictions with tickets 02, 07 and 08

1. **02 (table, shortlist and per-tool notes): "VerCors: OpenMP ✓ (`parallel for`, `sections`,
   `simd`)", "the only unbounded verifier that reads OpenMP"; "C++11 ✗ (not listed)".**
   - VerCors 2.4.0 parses those pragmas but rejects `#pragma omp parallel { }` blocks (and so
     `sections` and `for simd` inside them) and drops loop pragmas.
   - Only a single `parallel for` loop with an iteration contract verifies (section E).
   - It does read a basic C++ subset (since 2.1.0).
2. **02: "SAW … no loop invariants for bitcode"; "Loop fixpoint and invariant commands exist only
   for x86 machine code".** The SAW 1.6 manual documents experimental cutpoint loop invariants
   for LLVM bitcode (partial correctness). Also, #3285 is an open PR, not an issue.
3. **02 (research, SAW/crux notes): "LLVM versions from 3.6 through 23 are likely to work well".**
   The README bundled with crux-llvm 0.12 says "3.6 through 21". Ticket 07 is right; 02 quoted
   the current master README.
4. **02 (CBMC row): "Contracts".** True, but the flags are in `goto-instrument --dfcc`; `cbmc
   --enforce-contract` is an unknown option. This is a precision fix, not a reversal.
5. **07 and 08 (operational, not a contradiction):**
   - With `--solver=cvc5`, crux uses real floats by default. 08's runs were integer-only, so no
     verdict changes, but PR and BC runs must pass `-f`.
   - Inside the agent sandbox, WP's prover calls fail with a why3server socket error and WP
     reports `[Failure]`, not `Timeout`. WP must run outside the sandbox.

## Still unconfirmed

- Whether SAW 1.6 parses clang 22 bitcode in practice, and how it treats LLVM floats.
- Whether VerCors's bundled macOS z3 is arm64.
- Whether Frama-Clang 0.0.20 builds on macOS arm64; whether it supports `enum class`.
- WP `+real` literal handling.
- Why WP's induction strategy skips the "inf" subgoal.
- crux `crucible_size_t` and havoc with a symbolic length.

---

## Sources

**Tool output (Mac, 2026-10-12):** `esbmc --help` (8.5.0 aarch64 macos); `cbmc --help` and
`goto-instrument --help` (6.11.0); `crux-llvm --help` (Crux 0.9, crux-llvm 0.12, commit
`31cc4ad4`); `frama-c -wp-h`, `-wp-tactic`, `-wp-list-provers` (33.0 Arsenic); `opam list` for
switch `framac-33`; `otool -L` on the `llvm` and `llvm@22` kegs; the scratch runs cited above.

**Release metadata (GitHub REST API, queried 2026-10-12):** releases of `GaloisInc/saw-script`
(v1.6), `utwente-fmt/vercors` (v2.4.0, v2.1.0 notes), `esbmc/esbmc` (v8.5),
`lyonel2017/Frama-C-RPP` (v0.0.4); tree of `saw-script` v1.6 (`deps/`) and of `crucible`
`31cc4ad4` (`dependencies/`); tags of `llvm-pretty-bc-parser`; PRs saw-script #3285 and vercors
#1052.

**Documents and source files:**
- SAW v1.6: `README.md`, `CHANGES.md`, `doc/saw-user-manual/verifying-code.md`,
  `doc/saw-user-manual/symbolic-execution.md`, `doc/developer/limitations.md`,
  `doc/llvm-java-verification-with-saw/example-find-first-set.md`,
  `saw-central/src/SAWCentral/Crucible/Common.hs` — https://github.com/GaloisInc/saw-script/tree/v1.6
- llvm-pretty-bc-parser `CHANGELOG.md` — https://github.com/GaloisInc/llvm-pretty-bc-parser
- crux-llvm 0.12: bundled `doc/README.md` and `c-src/includes/crucible.h`;
  `crux/src/Crux.hs`, `crux-llvm/src/Crux/LLVM/Overrides.hs` at
  https://github.com/GaloisInc/crucible/tree/31cc4ad4a5d476458610cfeaf962fb098a24b1c9
- What4 at `121714d2`: `what4/src/What4/FloatMode.hs`, `what4/src/What4/Expr/Builder.hs` —
  https://github.com/GaloisInc/what4
- ESBMC v8.5: `docs/manual.tex`, `src/solvers/smt/smt_fp_conv.cpp`,
  `src/solvers/smt/fp/ir_ieee_conv.{h,cpp}`, `src/solvers/smt/smt_solver.cpp`,
  `regression/function_contract/{annotate_contract_replace_pass,cpp_replace_pass}` —
  https://github.com/esbmc/esbmc/tree/v8.5
- Frama-C WP manual 33.0 — https://frama-c.com/download/wp-manual-33.0-Arsenic.pdf (§1.5, §2.3.5,
  §2.3.9, §2.4.8, §2.5, §2.6)
- Frama-Clang manual v0.0.20 — https://www.frama-c.com/download/frama-clang-manual.pdf; plug-in page
  https://frama-c.com/fc-plugins/frama-clang.html; https://ocaml.org/p/frama-clang/0.0.20
- Local opam repository snapshot `~/.opam/repo/default.tar.gz`: `frama-clang.0.0.20`,
  `conf-libclang.22`, `why3-coq.1.8.2`, `frama-c-rpp.0.0.4` opam files; conf-libclang script
  https://github.com/ocaml/opam-source-archives/raw/refs/heads/main/patches/conf-libclang/configure-generic.sh.1
- VerCors v2.4.0: `README.md`, `src/parsers/antlr4/LangOMPParser.g4`, `LangCParser.g4`,
  `src/parsers/vct/parsers/transform/{CToCol,CPPToCol,ToCol}.scala`,
  `src/rewrite/vct/rewrite/IterationContractToParBlock.scala`,
  `test/main/vct/test/integration/{examples/OpenMPSpec,helper/VercorsSpec}.scala`,
  `examples/concepts/openmp/{add-spec,sum-spec}.c`, `examples/concepts/cpp/*.cpp` —
  https://github.com/utwente-fmt/vercors/tree/v2.4.0; wiki sidebar
  https://github.com/utwente-fmt/vercors/wiki
- Blom, S. C. C., Darabi, S., & Huisman, M. (2015). Verification of loop parallelisations.
  *FASE 2015*. Extended abstract: https://ris.utwente.nl/ws/files/6132966/ParLoopVerification.pdf
- RPP v0.0.4: `README.md`, `rpp_*.ml`, `tests/rpp/loop_rela.c` —
  https://github.com/lyonel2017/Frama-C-RPP/tree/v0.0.4
- Blatter, L., Kosmatov, N., Le Gall, P., Prevosto, V., & Petiot, G. (2018). Static and dynamic
  verification of relational properties on self-composed C code. *TAP 2018*.
  https://arxiv.org/abs/1801.06876
