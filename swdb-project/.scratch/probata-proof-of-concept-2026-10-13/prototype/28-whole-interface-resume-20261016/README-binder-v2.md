# Closed argument grammar repair

2026-10-16 ET. Source-only repair of the independent review finding. Use
`whole_interface_v2.py` for any future source-call admission. The frozen V1
binder is historical preparation and has an incomplete effect denylist.

`new int[2]` can contain no nested `CallExpr`; V1 therefore accepted it as a
packet argument. Delete, GNU statement expressions, inline assembly and other
unlisted effects had the same gap. No separate admitted producer closes that
gap, and production lowering supports some of these constructs elsewhere.

V2 replaces only the local argument predicate with an explicit expression-kind,
arity, operator and cast grammar. Basic literals, references, scalar arithmetic,
ordinary pointer/member/subscript expressions and selected conversions remain
available; unknown expressions and all allocation, calls, cleanup, asm, throw,
atomic, varargs and statement forms refuse. Original source/type/arity, byte
offset, provenance and final-replay checks remain identical.

Nine no-child synthetic controls pass: the original132 type/arity bindings and66
role cases remain valid;79 total refusal cases include the new grammar
mutations. A regression reproduces the original allocation gap and verifies V2
refuses it. Exact inverse substitution restores the V1 source hash. These are
consumer controls, not actual compiler evidence.

The original source/value packets and unexecuted native86 harness are unchanged.
Native86 does not use this source binder. Compiler/ABI/CPU-pointer integration
and public synthetic evaluation remain required under the owned MMIO premise.
