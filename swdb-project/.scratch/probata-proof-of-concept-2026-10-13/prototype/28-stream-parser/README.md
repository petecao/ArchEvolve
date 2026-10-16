# Stream parser preparation

2026-10-16 ET.

These five small C files are an inert parser-only gate. Root owns actual Frama
admission, the primary lease, runtime provenance, worker B/c6 coordination and
the 120 s / 8 GiB whole-process-tree guard. No author Frama, WP or solver run
produced this packet.

The old e4cd1a6e stream run stopped in public validation: all three helper
contracts put `terminates` after simple clauses, which Frama33 refuses.
Wrong-size was unexecuted. This successor changes clause order only. State,
initialization, C bodies, nontermination predicates and partial-correctness
policy are unchanged. All source refinement, contract/body agreement,
environment, boot epoch and hardware-liveness boundaries remain explicit.

| Input | Origin |
|---|---|
| `inputs/wp-correct.c` | Exact full public correct-size WP input from the scripted preparation |
| `inputs/wp-wrong.c` | Exact full public wrong-size WP input; same original source |
| `inputs/wp-combined.c` | Exact public input with original `requires/assigns/ensures` in one formal half |
| `inputs/all-contracts.c` | Normal `proof_semantics.acsl_source` output, all 27 declaration contracts |
| `inputs/ordinary-model.c` | Normal `model_for(...).c_text`, with stdint and an explicitly parse-only assertion declaration |

The full public inputs retain all three contracted prototypes, the unit
contract, actual stream → wait → size call order, original 16-element input
initializer and conditional source-constructor entry. No annotation snippet or
toy caller substitutes for them. The ordinary model is separate: parsing it
does not prove its contracts or its source correspondence. No model execution
or termination is requested.

Only standard C headers (`stdbool.h`, `stddef.h`, `stdint.h`) are needed. No
project header, target assembly or ARM build product enters these C files. Root
must pin the actual Frama33 executable and its standard-header/runtime closure;
the Mac native C syntax controls do not replace Frama's x86_64 type check.

`inputs/manifest.json` pins every exported byte and its retained public origin.
`export_bundle.py` reproduces the export from an existing guarded preparation;
it imports only pure source generation and starts no compiler or verifier.
The manifest's absolute paths describe immutable retained Mac preparation,
not Linux runtime identity. `root-recipe.json` is prospective and intentionally
contains an unresolved root-bound executable. It is not an admission.

At admission, root should copy exactly the five pinned inputs into a fresh,
external parser directory, check hashes before and after, then execute each
with precisely `swdb.framac.FLAGS`: `-machdep x86_64 -kernel-warn-key
annot-error=abort`. Preserve argv, stdout/stderr, exit status, resources,
runtime/source pins and input inventory. A nonzero exit, timeout, resource
failure or `Ignoring` in either output is refusal. No `-wp`, solver, report or
additional evaluation flag is part of this gate. Parse success is only syntax
and type feasibility; full public pair acceptance needs a separate reviewed
admission and cold goal/property/smoke audit.
