# Symbolic floating copy mode

Created 2026-10-16 ET. This is an isolated source and mode selector proposal.
The current adapter/setup still require `+real`; neither shared file is edited.

`selected(method)` recognizes only `method.wp-vector-float-copy-v1`, with one
current checker pin, exact original model identity, one Frama-C 33 lineup row
and one canonical `-wp-model +float`. `model_option(method)` preserves `+real`
for every old method. `check_source` and `check_certificate` bind that intent to
the complete unchanged count, value and copy constructor units for float and
double. The exact old clauses, helper definitions and loop annotations remain.
No finite or non-NaN caller premise is added. Other types, members, arithmetic,
format changes, source edits and mode overrides refuse.

This selector grants no source, allocation, lifetime or record admission. A
future shared integration must invoke it at the planned method and generated
input boundaries while preserving every existing generic source, tool,
environment, flag, native report, property and consistency check. The method
intent is not a runnable method record: actual tool hashes, the normal lowering
pin, runtime closure, driver choice and fresh observations remain required.

The pinned local Frama-C 33 sources establish the intended distinction:
`Factory.ml` selects `Cfloat.Float` for `FLOAT`/`CFLOAT`, using Typed+Var and
machine integers by default. `Cfloat.ml` selects distinct `f32`/`f64` value
sorts, while Real selects logical reals. `MemTyped.ml` stores/loads those
selected value sorts, and `CodeSemantics.ml` keeps same-format casts as the
identity. The float Why3 theory imports `ieee_float.Float32` and `Float64`,
including nonfinite classification. These static facts do not establish the
actual generated import/driver/task or physical source representation.

The CVC5 and `z3_487` drivers import native SMT floating encodings, including
`fp.eq` and `fp.isNaN`. The installed Alt-Ergo driver documents partial support.
The local partial Why3 config's Z3 5.1 version is not an explicit version match
in the observed detector entries. The actual selected driver is pending; a
version or driver filename alone is never accepted as a capability result.

ACSL 1.24 section 2.2.5 distinguishes plain annotation equality, which compares
logical real promotions with unspecified nonfinite promotion, from the C IEEE
comparison predicates `\eq_float` and `\eq_double`. The C expression
`NaN == NaN` is not a counterexample to the original plain ACSL clause. No
original model defect or new model successor follows from this preparation.
Native floating abstraction also does not establish preservation of NaN
payload bits, signaling state or physical signed-zero representation.

The public pure controls were written first: RED five missing-module failures,
then GREEN five passes with no child process, socket or library load after the
audit hook. The canonical directory contains the exact six original units and
their explicitly pending mode certificates. No compiler, native code, prover,
driver, version query, SSH or formal workflow has executed for this proposal.
