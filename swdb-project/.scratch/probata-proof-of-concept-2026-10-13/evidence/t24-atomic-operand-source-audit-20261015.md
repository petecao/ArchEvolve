# Ticket 24 atomic operand soundness audit

2026-10-15 ET. Compiler-only audit; no repository edits, test suite, solver, verifier, provider or remote jobs. Original/lowered native experiments and admission inspection only. Existing accepted worktrees were untouched.

**Finding: real translation defect, not merely an untested ambiguity.** `c_lowering._atomic` discards evaluated success-order, failure-order and weak operands without a purity/definedness or weak=false gate. Valid original C++ and ordinary generated C produce different observable return values. Current generic WP admission does not reject these inputs. Separately, weak=true silently receives strong deterministic CAS semantics; that underapproximates the portable source behavior even with one thread.

## Source pin and seams

Observed root commit: `57df794f59e6416fdbc48089cca52653e72d53a6`. The files below matched that commit byte-for-byte after the experiment:

| File, relative to swdb-project | SHA-256 | Relevant lines |
| --- | --- | --- |
| swdb/c_lowering.py | c452963b546f4bbfe5cc8b54973b4078fd1c6e073b6ff53f17c2859ac8671b88 | 2132–2150 `_atomic`; 2345–2354 strong CAS model; 1892–1893 fence operand dropping; 2532–2535 bounded report generation |
| swdb/wp_adapter.py | 1a8e14c4f09d86843f00ca2c4a0c3ab34210ddb77da546e4efa9e7a8888df55e | 373–386 CPU/pointer admission; generated-C RTE/initializedness checks cannot recover omitted source expressions |
| swdb/bounded_initialization.py | 12885e27dc1cb62b6c89ed4c2b5728c350dc6b0a5781b09ab70ff058e83b287d | 190–211 AtomicExpr has no accepted initializedness policy |
| swdb/wp_pointer_bounds.py | 7033e8e8338d0fc39a5359fd5ceff304842d9df7c8223cffef967246c5f530a0 | 736–792 source inventory check; 983 refers specifically to generated model pointer arithmetic operands, not all original atomic scalar operands |
| swdb/cpu_memory_admission.py | 2d8939807edd361b9962fda45dc75eb05680a2b99a87dbc97af4871b2b0d2656 | 65–68 returns None without covered device summaries |

Clang's AtomicExpr children used here are `ptr, order, expected, order_fail, desired, weak`. `_atomic` prints ptr/expected/desired only, and does not recurse through the three omitted children. Load prints ptr only. `RULES` explicitly permits dropping the *memory order meaning* for the one-thread interpretation; this does not justify dropping the source expression's ordinary effects or RTE obligations. The issue applies to the generic accepted lowering surface, regardless of current fixture constants.

## Real native countercontrols

All raw/small sources, generated C, exact command array, diagnostics, binaries and outputs are retained in `/private/tmp/probata-atomic-audit-20261015/`. `report.json` SHA-256: `0310077ad9b33bf276e4932380d99b878cffedf6087ef5012f264b5c29975194`.

Public API used: `swdb.c_lowering.lower(source, function)`, no alternate translator and no hand-edited model. Original/native glue is appended after each original TU or its generated C. Native compilation uses `/opt/homebrew/opt/llvm/bin/clang++ -std=c++17` and `clang -std=c11`, both LLVM 22.1.8, followed by identical flags `-O0 -g -Wall -Wextra -fsanitize=undefined -fno-sanitize-recover=all <source> -o <binary>`. Exact commands and all compiler stderr are in `report.json`. Lowering's parser uses the pinned compiler with `-x c++ -std=c++17 -fopenmp -fsyntax-only -Xclang -ast-dump=json -Xclang -ast-dump-filter=<function> -I<source-directory> <source>` (`c_lowering.py:335–342`).

The first original control is exactly:

```cpp
int m = 0;
bool ok = __atomic_compare_exchange_n(p, e, 9, false, m++, __ATOMIC_RELAXED);
return 100*m + 10*ok + *p;
```

Native main supplies distinct live initialized `int p=1,e=1`, so success order evaluates to valid RELAXED (0), failure order is RELAXED, weak is compile-time false, desired is constant, and there is no unsequenced competing use of m. The ordinary C retains local m=0 but calls `swdb_atomic_compare_exchange_n_int(p,e,9)` with no m++.

| Original operand control | Initial state | C++ stdout result | Generated C result |
| --- | --- | ---: | ---: |
| CAS success order `m++`, weak=false | p=1,e=1,m=0 | 119 | 19 |
| CAS failure order `m++`, success=SEQ_CST, weak=false; return `100*m+10*ok+*e` | p=1,e=0,m=0 | 101 | 1 |
| Load order `m++`; return `100*m+value` | p=7,m=0 | 107 | 7 |
| CAS weak operand `(m++,false)`, orders=SEQ_CST/RELAXED | p=1,e=1,m=0 | 119 | 19 |
| CAS literal weak=true, orders=SEQ_CST/RELAXED | p=1,e=1 | 19 observed | 19 |

All compiled executions exited 0 with no UBSan diagnostic. The last row establishes that weak=true is admitted and receives the same model, **not** that native weak CAS cannot fail spuriously or that the abstraction is correct. The first four rows are actual mismatching defined executions; no weak-spurious behavior is needed to demonstrate them.

| Source artifact | SHA-256 |
| --- | --- |
| audit.cpp | f0ebbda2d9e0d368a6193cc4982324a849b1be4072377321d7bb2905e213353b |
| audit.c (unmodified public lowering) | 07c9131af897f35c406d7b17aa3ee8f70c363e4aabeaf8bc167ee9465aa0b5aa |
| weak_effect.cpp | 1b523de274bd1a2ae49959ba361b3249016e761d3442aa822692e9698c3c9bc9 |
| weak_effect.c | e746c3f3f0828ce5896797d2a4a31024a17ce36ed0f4523876e840479f78a42b |

Guarded command: `PYTHONDONTWRITEBYTECODE=1 /Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 /private/tmp/probata-atomic-audit-20261015/guard.py`. One sequential compiler worker; actual RSS watchdog cap 8 GiB, timeout 120 s. Successful run: 1.523150834 s, peak 99,237,888 B, exit 0, no timeout/OOM. `resources.json` SHA-256 `9312117f747a22580c7d703db01fcb00860a253feeb6bf6d328bc198ea94b01a`. Initial sandbox attempt failed closed because macOS process-tree inspection was denied; authorized escalation ran the same guarded command successfully. Neither attempt invoked a verifier.

## Possibly undefined operands and existing admission

Additional parse/lower-only control, never executed:

```cpp
int atomic_undefined_order(int *p, int z) {
    return __atomic_load_n(p, 0/z);
}
```

Public lower accepts it and emits `return (swdb_atomic_load_n_int(p) + 0);`; z disappears. At z=0 the original integer division has an RTE obligation while the generated C does not. This is source inspection, not a run of undefined code or a claimed false proof. `undefined.cpp` SHA `47d55e691926639deec6aa6fefd423898bde3cf62310f8b53f710a2f9124285c`; `undefined.c` SHA `5b8fcc06d505c1288b5a120fc2a797a37bd8884a6546b648095a508879d9e013`.

For all three source files, the actual `wp_pointer_bounds.check(lowering)` call accepted with an empty sites list and valid source/lowering hashes, and `cpu_memory_admission.check(lowering,{})` returned None. Bounded initializedness metadata says refused (`AST construct AtomicExpr has no initializedness policy`); `cbmc_adapter.py:222` uses that gate. `wp_adapter.py` does not call it, so it does not protect WP. These observations demonstrate acceptance by the inspected generic gates, not acceptance of any new proof record; no complete WP job was run.

## Primary semantics evidence

Official [GCC atomic builtin documentation](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html), compare_exchange paragraphs (web lines 101–106): weak CAS permits spurious failure; strong CAS excludes it. Some targets implement only strong CAS. Failure orders exclude RELEASE/ACQ_REL and may not exceed the success order. Runtime memory-order arguments are allowed (paragraph at web line 45). A target's permission to use stronger ordering does not authorize discarding expression evaluation.

Official [Clang CodeGen source](https://clang.llvm.org/doxygen/CGAtomic_8cpp_source.html), source lines 984, 1034, 1039: `EmitScalarExpr` evaluates respectively `getOrder()`, `getOrderFail()`, and `getWeak()`. This live upstream source is corroborating primary documentation, not a claim that its current web revision is byte-identical to installed 22.1.8; the actual pinned compiler executions above independently establish the effects.

One-thread execution does not remove a weak operation's allowed spurious-failure branch. With p=e=1 and desired9, portable weak source semantics allow false with p unchanged1; the generated model forces true/p9. Strong behavior observed once on this native target is insufficient to prove portable source equivalence. Supporting weak=true would require an explicit checked nondeterministic model with both outcome/state/frame cases, or an authoritative target-specific semantic restriction and corresponding recorded method scope.

## Minimal fail-closed correction seam

Implement admission in `_Printer._atomic` **before** model generation: require every currently erased operand to be an audited pure, defined constant expression; conservatively admit only recursively whitelisted literal/enum constants and safe wrappers initially. Do not accept arbitrary AST `ConstantExpr`/folded values without checking hidden children; `(m++,false)` shows why inspecting only the resulting value is insufficient. Require weak to be proven constant false; refuse weak=true/dynamic weak until sound weak semantics exist. Require legal orders for each operation and a legal CAS success/failure pair; use the actual ordering relation, not a numeric `failure <= success` shortcut. Refuse dynamic orders, volatile reads, calls, mutations, discarded comma effects and possibly undefined arithmetic rather than trying to preserve partial effects ad hoc.

Apply the same constant/definedness admission to `_call`'s `__atomic_thread_fence`/`__atomic_signal_fence` erased operands (1892–1893); that adjacent seam was inspected but not separately compiled here. The longer-term alternative is full single-evaluation lowering of all arguments with correct sequencing/RTE and weak behavior; this is larger than the needed fail-closed repair.

Focused future regression selectors can be added under existing `tests/test_c_lowering.py`: defined success-order side effect, failure-order side effect, load-order side effect, weak comma effect, pure literal weak=true, dynamic weak, division/shift/volatile erased operands, invalid literal order combinations, and retained constant-order/weak=false fixture success. Add method-pin/importer stale-record coverage because the trusted translator content changes. Existing finite nine-fixture agreement with constant orders/weak=false remains evidence about those exact source pairs; it neither detects nor excuses this generic acceptance defect. Parent owns any source change, method repin and affected re-evaluation.
