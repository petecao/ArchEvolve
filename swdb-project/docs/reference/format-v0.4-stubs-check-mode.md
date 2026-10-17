# C stubs, bounded fallbacks, check mode and summary-form agreement

Created: 2026-10-14 ET, Probata proof of concept ticket 23.
Updated: 2026-10-15 ET, checked Crux source admission and generic summary source/proof-domain binding.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/23-stub-translator-fallbacks-check-mode.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Verifier lineup and order", "Bounds", "Formal-half language and
the C++ subset", "DX100 proof semantics"). Builds on [format-v0.4-cbmc.md](format-v0.4-cbmc.md) (ticket 22).
Code: `swdb/cbmc_translator.py` (version 4), `swdb/crux_adapter.py`, `swdb/bounded_chain.py`, `swdb/summary_bindings.py`,
`swdb/check_mode.py`, `swdb/summary_agreement.py`; the ACSL form of a summary in `swdb/wp_adapter.py`.
Tests: `tests/test_cbmc_adapter.py`, `tests/test_crux_fallbacks.py`, `tests/test_check_mode.py`,
`tests/test_summary_agreement.py`.

**In one line:** one summary source (a library entry's formal halves) now gives C stubs that read `\old` memory,
logic calls and `\separated`; `swdb prove --adapter bounded` runs CBMC, then crux-llvm on the C++, then crux-llvm on
the C lowering; `swdb runtime-check` runs formal halves as runtime checks; `swdb summary-agreement` checks that the
C-stub and ACSL forms agree.

## What changed since ticket 22 (the decision of 2026-10-14 13:19 ET)

Ticket 23 was written when SAW was the bounded verifier. CBMC 6.11 on the C lowering replaced it. Each SAW item
became its CBMC equivalent:

| Ticket text | Built as |
|---|---|
| SAW, the primary bounded verifier | CBMC on the C lowering (ticket 22) |
| fallbacks crux-llvm C++, crux-llvm C lowering, CBMC C lowering | CBMC first, then crux-llvm C++, then crux-llvm C lowering |
| SAWScript, C stubs and ACSL agree | C stubs (CBMC) and ACSL (WP) agree; SAWScript has no verifier left |
| SAW float-mode check | not run: no SAW adapter; recorded as "not confirmed in this effort", so crux-llvm `-f real` stays |

## The C stubs (`swdb.cbmc_translator`, version 4)

A stub replaces a summarized callee. In order:

1. Each `requires` is one named CHECK (assert, then assume).
2. Each `\old(e)` of an `ensures` is snapshotted on entry. Under a bounded quantifier, the snapshot is a table over
   the quantifier's range (`\forall k; 0 <= k < n ==> a[k] == \old(b[k])` works).
3. The `assigns` locations are havocked from the oracle.
4. Each `ensures` is assumed. Its comment names the summary: `assume from summary <entry> sha256 <first 16>:
   <clause>`. These are the only `assume`s after a call.

Updated 2026-10-15 ET: generic summary imports require a fresh binding to the actual
global callee definition. The complete lowered callee closure must equal the
pinned library implementation, excluding only the generated provenance banner.
The summary proof must match that fresh implementation, the current method and
checker, build constants and retained evidence. A newer ineligible proof cannot
mask an eligible one. The same gate applies to WP, CBMC and both Crux forms, and
is independently repeated before launch.

Finite summary dimensions must cover unchanged caller entry arguments or literal
arguments. Pointer imports additionally require distinct entry-buffer bases with
the same physical capacity as the summary proof. A proof for `n <= 2` cannot stand
for a caller admitted at `n <= 3`. Offsets, contextual pointer forwarding, global
state, external-only declarations, and recursive model/summary dependencies remain
unsupported by this generic binding slice. Checked DX imports use their separate
model binding. Native C/C++ agreement alone does not certify a summary substitution.

New in the translated ACSL subset:

- `\old` over memory and globals in stubs (step 2 above);
- logic-library calls: each used `logic`/`predicate` of `library/logic/*.acsl` becomes one C function
  `swdb_logic_<name>` ahead of the code (primitive recursion stays recursion; one label at most, read as "here");
- `\separated(p + (lo .. hi), q + ...)`: disjoint byte ranges or different objects;
- ternaries `c ? a : b`; real literals and names of floating type are `double`.

A quantifier bound that reads the post-state cannot be snapshotted on entry. In a stub that is refused only when an
`\old` sits under it; in check mode it is always refused.

### What the proof record holds

| Field | Meaning |
|---|---|
| `pins.summaries[].assumes` (`assumes`) | the names of the `assume`s that summary's stub emitted (one per `ensures` clause) |
| `pins.translator` | `swdb-cbmc-translator-4` and its content hash |
| `settings.summary_bindings` | exact callee/proof identities and checked finite call-domain scope |
| `proof_setup_check.runs[].hashes.summary_bindings` | digest of independently replayed bindings |

## Bounded fallbacks (`swdb prove --adapter bounded`)

| Unit | Route |
|---|---|
| not real-valued | `cbmc` -> `crux-llvm-cxx` -> `crux-llvm-c` |
| real-valued (a floating type or `real` in its interface or formal halves) | `crux-llvm-cxx` -> `crux-llvm-c`, never CBMC |

- The next tool runs only when the previous one cannot read the code: `parse_error` or `unsupported_construct`.
  That is the handler of those two classes inside a route. Any other result ends the route; a timeout never moves on.
  An explicit checked initializedness/origin-policy refusal also ends the route, even when its class is
  `unsupported_construct`; trying another tool cannot relax that policy.
- The last tool's result stands. A real-valued unit that neither crux-llvm run can read reads not proven, with
  that class, and no CBMC job starts.
- `settings.route` in the record: `order`, `attempts` (`tool`, `verdict`, `failure_class`, `handler`), `reason`,
  `verdict_tool`, `real_valued`, and `cbmc` (why CBMC was skipped) for a real-valued unit.

### crux-llvm (`--adapter crux-llvm-cxx` / `crux-llvm-c`)

- **Code.** `crux-llvm-c`: the C lowering, with the CBMC adapter's C-versus-C++ differential run first.
  `crux-llvm-cxx`: the C++ itself, cut from the source after the original retained closure passes the same
  initialized-input admission. A C++ cut without checked source analysis is currently unsupported. Primitive
  initialized scalars and actual one-dimensional harness buffers remain supported; uncertain arrays,
  aggregates, pointer casts/rebinding and helper reads remain outside the checked source policy. Exact audited
  standard-model policies retain their own restrictions. Summarized callees become the same C stubs; imported
  domain-bearing summaries remain refused.
- **Fresh boundary.** Both forms regenerate the source/closure, initializedness admission, summary stubs and
  exact harness/input view before execution and again at the proof-setup launch boundary. Records carry
  `settings.bounded_initialization`, `settings.source_admission` and the corresponding proof-setup hashes.
  A stale source, changed contract, omitted plan or changed launched view cannot use cached admission metadata.
  Stand-in regression results exercise these guards; they do not establish that all Crux fallbacks prove.
- **Harness.** The CBMC translator's harness built with `-DSWDB_CRUX`: oracle values are crux symbolic values,
  each property is `crucible_assert(cond, "<name>", __LINE__)`.
- **Flags.** `--no-compile --skip-report --solver=z3`, always an explicit `--floating-point=real` (real-valued
  unit) or `--floating-point=ieee`, `--iteration-bound=K --recursion-bound=K` with K = the largest size bound + 1,
  `--timeout` = the job's wall budget. Recorded in `settings.flags` and `settings.float_mode`.
- **Reading.** Proven: crux disproves exactly the reachability asserts, all of them. A disproved named property is
  replayed on the C++ (as for CBMC). "Incomplete" goals (a loop cut at the bound) read `unwinding_bound_too_small`.

| Outcome | Class |
|---|---|
| bitcode the reader refuses (`Invalid magic number`), or clang cannot compile the job | `parse_error` |
| an unsupported LLVM construct; the unit outside the C++ cut | `unsupported_construct` |
| goals incomplete at the iteration bound | `unwinding_bound_too_small` |
| goals unknown | `unknown` |
| over the wall budget | `timeout` |
| the RSS watchdog killed it | `out_of_memory` |
| the SMT solver failed | `solver_error` |
| no goal status and a non-zero exit | `tool_crash` |
| a reachability assert never disproved | `vacuous_pass` |
| the counterexample does not replay on the C++ | `spurious_counterexample` |
| anything else | `unclassified_crux_outcome` (not a class: the batch stops) |

Limits seen on the Mac: crux-llvm 0.12 reads clang 22.1.8 bitcode with debug-metadata warnings (map 07); in
`-f real` mode its counterexample gives no value for a real variable, so the replay uses 0.0.

## Check mode (`swdb runtime-check`)

```
swdb runtime-check --candidate <c> --function <f> --contract <contract> --bounds '{"threads": 1, "n": 3}' \
                   --runs-dir <outside the repo> [--define NAME] [--tolerance X] --format json
```

- The runtime form `swdb_check_<f>` checks each `requires`, snapshots each `\old` on entry, calls `<f>`, then checks
  each `ensures` (bounded quantifiers as loops). `assigns` has no runtime form.
- Reals: `==` and `!=` compare within the tolerance: `--tolerance`, else the kernel's
  `correctness_check.tolerance.value`, else exact.
- It runs the candidate's own C++ on every input of the bounded domain that meets the `requires`.
- Output: `verdict` (`pass`/`fail`), `runs`, `feasible_runs`, `failed_properties`, `first_failures` (property and
  input), `tolerance`, `tolerance_source`, the program and its output by path and sha256. No record is written.

## Summary-form agreement (`swdb summary-agreement`)

```
swdb summary-agreement --scenarios <scenarios.yaml> --runs-dir <outside the repo> --format json
```

- A scenario: `{name, candidate, function, contract, bounds, expect: safe|buggy, defines?}`.
- Each scenario runs the C-stub form (CBMC) and the ACSL form (WP; a summarized callee carries its entry's
  `once: self` formal halves at its own contract anchor).
- Agree: safe means both prove; buggy means CBMC refutes and WP does not prove.
- A disagreement exits 1 and names each scenario with both verdicts. No proof record is written.
- Scripted fault for the negative control: `SWDB_CBMC_STUB_FAULT` (`drop: [clause name, ...]`) leaves those
  `ensures` out of every generated stub.

## For later tickets

- 29: run `swdb summary-agreement` on the strict wait-rule scenarios per proof-semantics version.
- 30: the same check on each per-call `dxc_*` summary; stubs come from `cbmc_translator.stub`.
- 31: gate 4 calls `swdb.check_mode.run(library, contract, source, function, bounds, defines, tolerance, source_note,
  out)` on each certify run of the reference instance.
- 24: once the C lowering reads floating types, a real-valued unit's fixture contract can pin its own baseline, and
  `crux-llvm-c` can serve real-valued units.
- 33: per-loop bounds would replace the single K of CBMC's `--unwind` and crux's `--iteration-bound`.
