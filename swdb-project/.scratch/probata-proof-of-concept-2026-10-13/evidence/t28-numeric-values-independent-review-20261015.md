# Ticket 28 numeric contribution: independent review

Reviewed: 2026-10-15 23:13 ET. Read-only review; no tests, compiler, verifier, provider, remote jobs, or repository edits were executed by this reviewer. Scope is the standalone numeric contribution in `/private/tmp/probata-resume-t28-numeric`; state transitions, instruction admission, ABI/provenance admission, and hardware refinement remain the primary implementer's responsibility.

**Result: no actionable defect found in the reviewed contribution.** This is source review of a prototype, not ticket-28 completion or formal proof evidence.

## Reviewed bytes

| File | SHA-256 |
|---|---|
| `prototype/28-proof-semantics/numeric_values.py` | `f49ebff7a85a88d93c20c78ad313b67a3459f0620254bba9b3cd91fcbd3ba018` |
| `prototype/28-proof-semantics/numeric-values-design.md` | `c7b57a4c61099557909375a77c433d6202957640b46ca5ea39493647efc57de0` |
| `tests/test_dx100_numeric_values.py` | `c06d61f35b417c2d1f2ee2192cb6a2dff1f000f3281ea554b442bf98ac671b15` |

The prototype paths are relative to `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/`; the test path is relative to `swdb-project/`.

Pinned upstream revision: `e4fc4afdf894f295442cef3604667a469fab8e62`. Directly checked retained source bytes: `ALU.cc` SHA `3eab45bf9847d5b1a97df2149ad2aa67b46f8e72c000d54bd01c384fa608e0e6`; `IndirectAccess.cc` SHA `7e238a370f25ff5a7a1211548630a291d6358c32d8a199fc58bfacd37d1d35db`; `IF.hh` SHA `9dee4c4803a1780a41fb30b760775169000785019e6f5848689fc3f3034a1795`; `IndirectAccess.hh` SHA `276bf31afe38c5877020ca706b4bce1922a1d6ae4cde387a1301a78d4c026249`. Also consulted the dated typed numeric-domain research matrix.

## Checks and conclusions

- **Integer arithmetic and raw bits:** all four integer dtypes normalize to the source width; legal `memcpy` decodes signed operands and re-encodes results. Unsigned ADD/SUB/MUL preserve defined modulo behavior. The signed ADD/SUB/MUL guards avoid overflowing in the check itself; multiply divisions are reachable only with safe nonzero divisor/sign combinations. DIV checks zero and signed MIN/-1 before evaluation. Comparisons produce 0/1, and negative signed bitwise values retain their admitted fixed-width image.
- **Shifts:** the count guard precedes every shift. Signed left shift rejects negative lhs and checks representability in the corresponding unsigned width, preserving the documented C++17 sign-bit boundary rather than accidentally applying stricter C11 signed-shift semantics. Negative right shift is reconstructed with unsigned operations only after the explicitly bound arithmetic-right policy; the zero-count branch avoids a width-sized mask shift. No source/runtime policy is inferred from operand values.
- **Floating values:** all six dtypes and exact opcode restrictions are represented. The native floating slice requires the declared runtime profile and refuses unsupported bitwise/shift combinations. ALU MIN/MAX select first on ordered ties, while RMW ternaries select the second operand on ties/unordered comparison; the explicit ALU NaN policy gate avoids claiming an unpinned library expansion. These preserve the reviewed signed-zero and NaN selection distinctions. Actual simulator/compiler/stdlib, denormal, trap and NaN-arithmetic behavior still need the promised runtime/provenance binding; the finite controls do not establish that binding.
- **Reduction and failures:** initializers match the pinned source, including positive min-normal float MAX initialization and rejection of unsupported XOR/shift/comparison reductions. The recurrence is `values[i] op acc`; inactive entries bypass operand evaluation. Output is written only after success, including reduction completion; returning error callbacks preserve the non-OK status. This statement assumes valid caller storage and callbacks honoring the interface, not arbitrary adversarial callback side effects.
- **Metadata and offsets:** decoded integer operand bounds, guards, modulo subtraction normalization, signed sign-bit decode, comparisons, truncating division, source branch pointers and runtime requirements agree with the executable slice by inspection. ACSL parse/type/proof admission remains explicitly unexecuted. Float `result_acsl=None` correctly exposes the missing IEEE relation instead of assuming real arithmetic. Offset checks expose the source uint32 product no-wrap obligation and retain separate object, address and cache-line correspondence duties.

## Retained finite controls

Read, without rerunning, `/private/tmp/probata-t28-numeric-final-native/{command.json,control.log,junit.xml,resources.json}`. They report nine passing controls, zero failures/errors/skips, including C11/C++17 opcode golden tables and 486 signed ADD/SUB/MUL boundary cases. Recorded guard: exit 0, peak RSS 130088960 bytes, wall 2.337765333999414 seconds, no OOM or timeout. The reviewed test includes sanitizer builds, output preservation on nonfatal errors, source-specific float selection, reduction order, invalid domains, and offset edges.

These are finite native/compiler and metadata controls. They do not discharge ACSL obligations, establish a complete IEEE logical relation, certify simulator build identity, or demonstrate state/history refinement. Those are declared boundaries, not findings against this narrowly scoped contribution.

Final delta reviewed at 23:13 ET: the design now states all four statuses, caller storage duties, runtime flags and nontrapping/subnormal boundaries explicitly. The test harness adds retained compiler command/hash/version/platform, compile status/output, and native command/status/output/binary hash. These additions do not change the emitter or numeric control inputs/expectations. The previously retained nine-pass run predates these evidence-retention additions; it must not be presented as execution of the newly pinned test-file bytes. The implementer plans a fresh guarded final profile. No defect found in the additions by inspection.
