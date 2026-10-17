# Installed WP IEEE and progress-state source map

2026-10-16 ET. Read-only source/theory research in the `framac-33` opam switch;
no tool version command, parser/compiler/prover probe, remote job or formal
acceptance. [Exact installed source pins](t28-wp-ieee-progress-source-map-20261016.json).
These files are not asserted equal to a remote runtime without a separate check.

`Cfloat.ml` and `Factory.ml` default to the Float model; `+real` changes it.
`cfloat.mlw` binds32/64 arithmetic and comparisons to Why3's IEEE Float32/Float64
RNE operators. This gives a source-grounded path for typed numerical operations.
The method should explicitly retain typed/IEEE selection and pin these sources.
ALU standard min/max and indirect RMW ternaries still need their actual comparison
and operand-selection rules; the Why3 generic IEEE min/max functions have different
NaN and tied-zero behavior and cannot replace either source expression.

The `Float*_BV_Converter` functions perform numeric integer conversion, not raw
binary reinterpretation. GenericFloat's source comments describe `from_binary`
only for literals. Importing the theory therefore does not establish the needed
arbitrary raw-byte/typed-float `memcpy` relation. No desired IEEE result axiom or
finite native result closes that coherence obligation. The typed-operation route
and raw-image bridge must be reviewed separately before whole value acceptance.

For readiness, mathematical integers in logic do not imply mutable model-integer
support. WP's `LogicSemantics.ml` explicitly rejects `TModel` in reading, updating
and location traversal; `RefUsage.ml` rejects model-field references. A mutable
ACSL model integer field is therefore an unsupported route in these sources.
A finite C delay would silently restrict the approved arbitrary-finite environment
premise and is not an acceptable replacement for the formal rule.

A prospective route is a separately checked mathematical/temporal progress lemma
and an exact summary of an empty busy-poll loop under the explicitly owned fair
scheduler/eventual-response assumption. Any summary must preserve the original
source observations, have no intervening zero-body effects, and refuse a total
claim without that premise. No such transformation or lemma is implemented here;
no extra wait call is inserted. Native bounded controls and partial correctness
remain distinct. The parent coordinator owns representative actual admission.
