# Numeric value helper contribution

Created: 2026-10-15 ET. Ticket28 remains owned by its primary implementer.

Authorized seams: emitted C11/C++17 raw-bit numeric helper API and its public
Python contract-expression generator. Controls compile and execute the emitted
helpers with independently worked literal outcomes and rejected-domain cases.
They establish finite numeric behavior, not formal validity, source-header ABI
identity, device histories, ownership, memory/address semantics or hardware refinement.
All controls serialize through workerB and retain an8GiB/time watchdog.

The ABI follows the primary implementer's request: dtype0..5 and opcode match
the pinned interface; uint64 raw operand/result bits; comparisons return0/1;
legal memcpy conversions. Caller supplies already-settled values. Program
arithmetic guards invoke DX_NUM_CHECK before evaluation. Unsupported type/op or
unbound runtime invokes DX_NUM_REFUSE. Neither callback silently assumes success.
Runtime policy must be bound to actual source/runtime provenance before production
admission; prototype controls do not establish a Linux/x86 simulator identity.

## Frozen helper boundary

`numeric_values.py::render_header()` emits C11/C++17 with these public functions:

- `dxv_eval_bits(dtype,op,lhs,rhs,family,runtime,out)` evaluates settled raw-bit operands.
- `dxv_initializer_bits(dtype,op,runtime,out)` returns the source reduction initializer.
- `dxv_reduce_bits(dtype,op,values,active,count,runtime,out)` evaluates source1-op-accumulator in order; null active means all lanes.
- `dxv_indirect_offset_bits(word_size,index,out)` checks the source uint32 multiplication cannot wrap, then returns its widened byte offset.

Each returns `DX_NUM_OK=0`, `DX_NUM_UNSUPPORTED=1`, `DX_NUM_ARITHMETIC=2`, or
`DX_NUM_RUNTIME=3`. Output remains unchanged on any non-OK return, including
callbacks that return normally. Production callers must inspect the status;
there is no bits-only convenience that can hide failure. Null/invalid internal
storage is a model refusal. Buffer extents/lifetimes remain caller obligations.
Callbacks are mandatory: DX_NUM_CHECK receives arithmetic safety obligations;
DX_NUM_REFUSE identifies unsupported/model/runtime domains. Neither suppresses
undefined behavior by assuming an unchecked condition.

Dtype is the pinned uint32/int32/float/uint64/int64/double encoding0..5. ALU
family0 accepts integer operations0..15 and float0..5/11..15; RMW family1 accepts
ADD/MIN/MAX only. uint32 results normalize upper bits. Comparisons return raw
uint32 0/1. Integer division is truncating; signed ADD/SUB/MUL/DIV are guarded
before unsafe operations; unsigned wrap remains defined behavior. C++17 signed
left shift uses unsigned bits including the defined sign-bit case, and negative
right shift is reconstructed arithmetically only under an explicit bound policy.

The runtime struct has three independent flags. A flag1 is a caller assertion
about retained runtime/source evidence, not a fact discovered by the helper:
`signed_shift_cpp17_arithmetic`, `ieee_binary_rn`, and
`alu_minmax_unordered_first`. Unknown needed flags refuse. Floating evaluation
also checks the build's binary32/64 sizes/precision, FLT_EVAL_METHOD0, current
round-to-nearest mode and absence of recognized fast/finite-only macros. The
IEEE policy additionally needs ordinary nontrapping/subnormal semantics and
matching compiler behavior; these checks alone do not establish them. ALU
unordered min/max requires a separately bound actual stdlib selection policy;
RMW uses literal source ternaries. Full NaN payload behavior is not claimed from
finite controls. Mac arithmetic controls establish no Linux/x86 typedef identity
or actual simulator build context.

Python `operation_contract` emits typed integer ACSL guard/result expressions,
source lines and runtime requirements, never new original-unit preconditions.
They refer to already-decoded typed lhs/rhs/result and require a checked raw-bit
bridge. `offset_contract` supplies the active-lane no-wrap obligation, not object
validity or physical-line correspondence. Full floating IEEE bit-level ACSL
relations are explicitly absent (`result_acsl=None`); concrete C/native bodies
are available without introducing desired axioms or a real-arithmetic stand-in.
No ACSL parser or formal prover was run. Device histories, conditions before
settlement, pair storage, ownership, source imports and proof admission remain
owned by ticket28's primary implementer. This helper cannot close whole28.
