# Normalized complete-TU ingress proposal

Date: 2026-10-16 ET.

This is a source-only, fixed-fixture consumer proposal. The passive byte transform
has actually completed once, but this ingress has never decoded its AST or called
`prepare_unit`. No source, declaration, ABI, call, model, native, public proof or
ticket acceptance is asserted here. The original V10 duplicate-key refusal stays
unchanged, as does the measured refusal to retain 178,924,116 normalized bytes in
one 128 MiB plain file.

Promote the four files in `proposed/` into `swdb/_dx100_whole/`. Add all four actual
module identities to the closed producer manifest. In `dx100_checked_source`,
change the single `compose` call site to invoke
`normalized_capture_ingress_v1.complete_capture(policy, reads, project)`. Preserve
the existing `complete_capture` function byte-for-byte. The new module calls that
function for the old capture kind, so this must be a call-site integration rather
than replacement or rebinding of the legacy function. Its six returned values
have the existing meaning: captured source path/bytes, complete location-resolved
TU, declarations, unit preparation and stream binding receipt.

The source policy keeps its existing outer shape. Its new closed `capture` object
has `kind: complete-original-tu-paired-type-gzip-2`, `original`, `transform` and
`prepared`. The exact required role sets are recorded in `capture-schema-v1.json`.
Each role is an ordinary physical Pin or an already supported portable library
reference where the code allows it. The original roles must refer to the preserved
V10 root; the new physical result/output roles must refer to the separately owned
V2 output root. Author command/bootstrap and bounded stdout/stderr may be staged
as exact byte copies. Their original paths remain in the root execution receipt;
the consumer compares byte count and SHA, then separately rehashes each selected
physical copy. It never opens a Mac author path on Linux.

The new route requires the exact published V10 policy, its four exact zero-exit
compiler observations, its exact duplicate refusal, original raw/gzip identity,
all source/control/dependency inputs and independently reparsed Make dependency
membership. It binds the complete 116-role census, exact actual transform result,
settled root-observed exit receipt, flushed publication, ten closed output pins
and 36 exact selected input pins. It verifies the full normalized gzip through EOF
and the complete inverse manifest back to the original minified token identity.
The original `type` and emitter-specialized desugared type remain distinct roles;
the derived stream is not represented as token-identical to Clang's original.

Current Python surfaces are checked by the byte-identical reviewed
`closed_python_surface.py`; current compiler/runtime files, alias/absence rules,
native tree membership and both header surfaces are rehashed before and after
decoding/preparation. All regular files enter the final physical read set. A cheap
fixed gzip/manifest shape check runs per stream chunk; full codec hashes, EOF and
all input hashes bracket it. This is the same physical pre/post timing premise,
not an assertion that mutable host files are atomically frozen for the duration.

Only after these gates does the consumer decode at the explicit 192 MiB expanded
limit and run the unchanged complete-TU/ABI/call preparation. The complete actual
TU retains original same-parse IDs and source coordinates. It compares the source
SHA and bytes to both the exact captured policy and the selected proof buffer;
this V10 record cannot admit a different memory fixture. Unknown, partial or
other failed captures refuse. The 128 MiB compressed-file and 256 MiB retained
limits remain. DOM memory and consumer time are unmeasured; a future actual
consumer must retain the root-owned 4 GiB/time guard and fail on exhaustion.

The capture observation and root-owned execution receipt are provenance premises,
not self-authenticating theorems. The source-to-selected-Clang-binary attestation,
compiler observations, OS loader and the explicitly owned MMIO semantics remain
TCB. The separately checked source/model/receiver/native contracts remain required.
No hardware-body theorem is introduced as an additional acceptance requirement.

The nine pure controls execute only AST-projected gate functions against literal
fixtures. They check refusal/identity/publication rules, exact legacy call-through
and the copied helper origin. They do not import the proposed project package or
consume actual AST records.
