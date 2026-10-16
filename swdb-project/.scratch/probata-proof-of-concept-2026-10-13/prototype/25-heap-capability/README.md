# Original count/value constructor and destructor capability gate

Created: 2026-10-15 ET. This prototype prepares a trusted, source-mapped unbounded
heap VC translation for the unchanged `std_vector_int_ctor_count_value` and
`std_vector_int_dtor` C model texts. It creates no `c_model` record and does not
establish a complete member-body proof or formal C++ equivalence.

`packets.py prepare --output NEW_DIRECTORY` emits original source snapshots,
source/event/clause bindings and 42 isolated packets. `packets.py check --input
DIRECTORY` rebuilds the entire canonical declaration and refuses changed source,
semantics, missing obligations, forged claims, or extra packet files. Admission
is closed to the independently reviewed full original model/module hashes.

The heap has unbounded mathematical allocation identities, separate addresses,
issued/dead identities, arbitrary incoming well-formed heaps, escaped aliases,
explicit initialization and typed access/alignment. Allocation supplies a fresh
identity, an available address and uninitialized cells under the existing
allocation-success/freshness policy. Release invalidates the whole identity and
preserves aliases and fields. No old allocation is freed by construction; no
receiver/buffer disjointness is added to destruction. Zero-size and legal address
reuse controls retain stale identity invalidity. The typed memory interpretation
covers complete int and receiver cells; byte casts, partial writes and generic
caller composition remain unsupported.

Every packet contains one top-level `check lemma`, except one actual numeric C
kernel with all ordinary contract/RTE/initialization/smoke goals selected. Global
check lemmas have no assumed previous or future proof lemmas: dependencies are
empty. Two concrete source-entry feasibility witnesses use a definitional empty
heap and a legal source execution trace. These witnesses do not restrict the
arbitrary incoming heaps in the member obligations. Four negative controls keep
the selected ordinary lemma open; `unknown`/`timeout` is never called a solver
refutation. No desired result is imported as an axiom.

`experiment.py --plan-only --input DIRECTORY --output NEW_DIRECTORY` emits exact
commands without discovering or executing a formal tool. Actual execution is
coordinator-only, at a reviewed, published, clean exact commit, inside a lane or
approved Mac outer RSS/time guard:

```sh
python3 .scratch/probata-proof-of-concept-2026-10-13/prototype/25-heap-capability/experiment.py \
  --run-admitted --expected-commit FULL_PUBLISHED_SHA \
  --why3-stdlib VERIFIED_TOOLCHAIN_STDLIB_DIRECTORY \
  --output NEW_RAW_DIRECTORY --seconds-per-prover 10 \
  --public-timeout-seconds 180
```

The runner reuses the shared verifier lock, fresh report-module compilation and
complete generated-goal reader. Every leaf retains cache-off RTE/init/smoke,
x86_64, single-worker settings, raw normalized input, per-goal/property/inventory
reports, resources, emitted prover files and import/task diagnostics. Output must
be outside the checkout; it rechecks source and canonical inputs between leaves.
The same watchdog boundary is tested with a bounded sleep. A synthetic public
`--check-result` control tests the additional experiment expectation policy; it
creates no actual evidence or proof record.

A full worst-case leaf budget is 42×180 = 7,560 seconds, plus bootstrap and
cleanup. Use at least 8,100 seconds for the whole guard, with additional wrapper
margin, an 8 GiB process-tree RSS cap and one worker. Expected raw output is under
1 GiB but has not been measured; coordinator disk monitoring remains required.
The run stops at the first unmatched result and retains all partial evidence.

Actual import syntax and capability remain unvalidated. A zero command exit or
all expected statuses cannot close this gate: independently inspect the actual
resolved import closure, all imported propositions, emitted task hypotheses and
full original clause/RTE/init/frame/lifetime correspondence. Declared physical
Why3 standard-library hashes are separate from the actual resolved import audit.
`int.Int` standard arithmetic is part of the explicit trusted foundation; no
additional external compiler-correctness theorem is required by this TCB.

The preparation evidence is `../../evidence/t25-heap-capability-preparation-20261015.json`.
Independent intermediate reviews are retained in `reviews/`; the runner review's
four findings are addressed by the current controls and await final review.
Further public adapter integration and every remaining ticket25 acceptance item
remain open after this first capability gate.
