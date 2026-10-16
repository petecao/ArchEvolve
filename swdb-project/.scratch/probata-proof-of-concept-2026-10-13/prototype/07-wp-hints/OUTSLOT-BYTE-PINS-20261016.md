# Output-slot source admission: physical byte repair

2026-10-16 ET. Successor to the unchanged Git freeze
`1c018f1162cdef8fa97d70908a44f1a9bd2f7d5b`. The independent review found that
`Path.read_text()` normalized CRLF before hashing, so physically changed source
could pass the exact-byte admission claim. The retained public CLI RED control
reproduced this: CRLF header SHA-256
`14d5f2392f87bfde7f9bebcaa3774362f63bb7d3858503d9bc7b654166ca6c1e`
was admitted although the declared LF header hash was
`eccc1c111f32698043682509be8effad02e8cec82957a889f7a4fb6c54ff490c`.
The old CLI returned zero and emitted output; that is a real admission defect,
not a compiler or environment failure.

The generator now reads each input once as raw bytes, verifies its physical
SHA-256 before decoding, then strictly decodes UTF-8 without newline conversion.
The exact decoded snapshots are reused for the source/contract/occurrence maps;
there is no later text re-read. Generated files and JSON are written as explicit
UTF-8 bytes. Refresh already checked generated payloads with `read_bytes()`;
the new public control confirms a CRLF-edited payload is refused before mutation.
Refresh's JSON is bookkeeping, not a cryptographic signature: the source pins
remain fixed in the generator and all emitted content is regenerated from those
verified source snapshots.

The four generated C/header files and `abi-map.json` remain byte-identical to
the original output-slot freeze. No source contract, executable hand-model body,
real C++ unit, TDStep functional postcondition, result type, span qualification or
proof goal setting changes in this repair.

The successor profile passes 44 controls under the shared B lease and the
8 GiB/120-second guard. Added cases reject CRLF mutations in each of four input
files, one altered byte, non-UTF8 bytes, and a physically edited refresh payload.
Exact LF input still reproduces all five artifacts, and the original native,
compiler and source-family controls still pass. Raw outputs are retained at
`/private/tmp/probata-t07-outslot-byte-pins-green-20261016`; the failing old CLI
receipt remains at `/private/tmp/probata-t07-outslot-physical-byte-red-20261016`.
The compact successor evidence pins these records separately from the historical
30-control evidence; the latter is not rewritten.

All earlier boundaries remain: spans are an explicitly stronger source-qualified
domain, not derived from the old same-base predicate; bodyless output stores trust
the source operation's defined normal-return ABI; source correspondence,
alignment and future TD loop-anchor remapping remain unproved. Allocator
correspondence is still refused, as are full TD/source and counted admissions.
No Frama-C, Why3, solver, provider or SSH process was run for this repair.
