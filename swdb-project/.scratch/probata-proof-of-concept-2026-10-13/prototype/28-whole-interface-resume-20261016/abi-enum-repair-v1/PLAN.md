# ABI enum semantic reader proposal

2026-10-16 ET.

The complete offline census identifies the same enum shape in both retained ABI
artifacts: each of the 23 enum roots contains one unsigned-int `IntegralCast`
whose child is the initializer's typed `ConstantExpr`. The old reader examines
only direct ConstantExpr children and consequently refuses both observations.
The endianness initializer's own value is the bool spelling `true`; its comparison
operands separately contain integer values 1234. Those operands are never values
of the endianness enum.

`proposed/compiler_unit_adapter_v4.py` is a separately named semantic reader. The
five-edit inverse restores the exact 775ab2ec v3 source. All v3 functions except
`observed_abi` remain exact. All ABI domain checks, strict duplicate refusal,
complete 29-root census, type/layout validation, source-call/TU preparation,
resource limits and capture recipe remain exact. Unknown streams retain the old
direct-ConstantExpr path. The two new inlets require the exact role-derived byte
count/hash and matching original physical probe coordinate. They require the
exact 1,588-byte probe, ordered roots, source enum name/range, observed declaration
and expression types, one uint32 IntegralCast, one own ConstantExpr and closed
passive source-expression shapes. Decimal values must fit unsigned 32 bits, so
this exact cast preserves their values. Bool spelling is interpreted solely for
the exact endianness comparison; its unchanged domain gate still requires one.

The paired-Type helper remains a separate reversible transport. This repair does
not flatten or mutate any AST. Its semantic receipt separately records the
selected original ABI, derived strict input, physical probe and canonical
interpreted-constants hash. None of these hashes are interchangeable. The full
reader pin is declared in this packet and must enter the final promoted producer
manifest and each dependent adapter's physical consumer check. An informational
recipe ID or receipt alone cannot authorize imported code.

The exact release primary sources explain the observed wrapper and value
spelling. JSONNodeDumper emits ConstantExpr's own APValue/type; APValue prints bool
as true/false; Sema inserts an IntegralCast when changing enum initializer type.
The source-to-selected-binary correspondence and original compiler invocation,
runtime, source/dependency closure remain inherited, explicit trust boundaries.
This proposal establishes no hardware, source-call, public proof or complete
compiler/runtime refinement theorem.

Eleven no-child controls exercise both complete actual 29-root pipelines with a
disclosed diagnostic-only probe-path adapter over checked local transfer bytes.
The original raw JSON refuses in both readers. The v3 semantic reader refuses
both strict role-derived streams. The v4 reader accepts both ABI metadata and
calls the unchanged ABI validator. All 506 per-enum shape mutations refuse;
source ranges, value domains, exact stream/probe selection and extra expressions
have additional controls. A separate old-style direct-constant fixture produces
identical v3/v4 output. This is offline metadata interpretation, not scientific
reexecution. The initial test-only failures (a wrong expectation about the
validator's return value and a macro-location mutation assumption) remain in the
first log; production candidate semantics did not change for those corrections.

No frozen ABI transport, observer, production integration packet, source program
or actual refusal was changed. Parent review is required before a separate
successor rebinds dependent first/memory adapters to this explicit new module and
pin, updates source producer membership, observer module inventory and all derived
policy/envelope pins. Keep the original v3 file for its actual legacy/direct
route. Any fresh complete TU/body/source observation remains separately guarded;
no current observer packet is rendered runnable merely by this proposal.
