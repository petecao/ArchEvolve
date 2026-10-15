# Atomic operand admission v1

Updated: 2026-10-15 ET. Scope: public lowering and WP prelaunch controls;
no actual WP proof or solver counterexample is claimed.

Independent [source/native audit](t24-atomic-operand-source-audit-20261015.md)
found four defined C++/C mismatches: discarded load/success/failure orders and
a comma weak operand erase ordinary increments. A possible division-by-zero
operand was inspected but never executed. Portable weak CAS also permits a
spurious failure missing from the deterministic strong model. These findings
apply to generic admission, even though the original constant fixtures do not
contain those problematic expressions.

The narrow fix validates operands before generating a model or erasing a fence.
Literal/enum constants and recursively checked safe wrappers form the initial
closed domain. Loads/stores use their specific legal order sets, CAS checks an
explicit success/failure relation, and weak must be constant false. Dynamic
reads, volatile reads, calls, mutations, arithmetic, invalid flags/pairs and
weak true refuse with a source location. No folded ConstantExpr value bypasses
its children. The six order codes and strong/weak distinction follow the
[GCC contracts](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html).
Target-specific flag bits and other constant-expression spellings remain
outside this initial admitted shape.

TDD traces: load side effect, three CAS operand variants and both fence variants
first failed to refuse, then passed. A valid same-named public fence context
with historical source reaches the external stand-in (`unknown`, one goal,
`verifier_launched:true`, WP input present); the fix refuses prelaunch. This
is an actual scripted launch control, not a real verifier false-proof example.

The final composed controls pass: 69 lowerer/baseline/public refusal cases in
227.92 s, followed by the corrected stale-translator case plus eight corpus
cases (9/9 in 43.93 s). The stale test initially collided with a method sequence;
only its test metadata changed. Stale translator content is rejected before a
new proof record. The baseline captured at `57df794f` independently confirms
exact original C, anchors, all nine atomic C-model texts and naming-rule pin.
There is no added validity or initializedness assumption.

[Compact execution metadata](t24-atomic-operand-fix-20261015.json) retains source,
tool, native countercontrol and raw-output pointers. Existing remote `9b75f4a2`
and finite `e48a302e` evidence remains frozen historical evidence. Translator
content changes, so fresh method pins/replay and independent review are required
before current-source ticket closure. Active remote source/toolchains/jobs were
not modified. Overall ticket24 remains claimed.
