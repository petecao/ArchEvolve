# p1 local release request author R3 — source only

Selected source: `/private/tmp/lanl17_finalize_p1_normal_release_request_20261008_a5_r3.py`, 18,274 bytes, SHA256 `47ec23095ba8ff40f98f1dffb720f387199240bba90d98f91f5545d33689df5c`, mode 0600.

Complete R2 derivation: `/private/tmp/lanl17-p1-local-release-finalizer-r3-complete-r2-derivation-20261008-a5.diff`, 1,565 bytes, SHA256 `38a923bed301c08aa6d545e566fff535de1e86bd1dafcb753e35b475032e2951`.

Use the exact CLI and input provenance instructions in preserved `/private/tmp/lanl17-p1-local-release-finalizer-r2-source-handoff-20261008-a5.md` (8,034 bytes, SHA256 `a188f594409e7602331d2aca35f4ac138a7cb3f00fccdee153fbc9651ed624b6`), substituting only selected author source basename `_r3.py` for `_r2.py`.

R3 changes only newly authored action config `source_pins`: exact producer32, copied H28 and staged native R2 query remain; native wrapper is omitted from the generic private-file pin list because its actual native mode is 0777. The generic 64fd `original()` reader refuses group/world writable files. Do not chmod the native wrapper.

The local wrapper source remains required and checked for exact 10,510-byte SHA256 `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`. M2 binding, the exact lane writer descriptor, wrapper read root, and original producer32 writer-source byte/hash checks and after-capture rehash remain unchanged. Scientific sources, controls, request schema, budgets and all other author logic are unchanged.

Immediately before actual release32, parent must obtain a fresh bounded read-only native wrapper exact-byte/hash/physical metadata observation. Preserve observed native mode; require size 10,510 and SHA above, exact frozen M2 route, native UID 114316761, regular nonsymlink single-link identity and stable stat/byte observations. The historical 14:29:42 query at `/private/tmp/lanl17-native-wrapper-physical-metadata-capture-20261008-a5/wrapper-original.json` reported mode 33279 (0777), dev 2097, inode 57279445; this is historical provenance, not a substitute for the fresh check. If actual source bytes, route or identity drift, refuse and preserve originals.

Fresh R2 selected lease/gen511/no-holder observations remain required immediately before release32 and before/after B08. Immutable query snapshots cannot detect subsequent reuse. Reserve node0 until release32 and AFTER custody complete. Explicit parent normal-trajectory review and finite live attestation interval 0 < duration <= 300 seconds remain required, with actual values supplied only after terminal facts exist.

AST syntax and exact inverse source substitution passed. No source import, author execution, tests, SSH, staging, producer/control execution or science occurred. R2 and older variants are preserved NOTRUN. No finalized request or action output has been authored.
