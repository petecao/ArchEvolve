# Finite receiver V3: exact JSON type identity

2026-10-16 ET. Narrow source-only successor. One comparison changes from Python dictionary equality to equality of canonical JSON bytes. V2 could equate a nested integer `bytes` field with the equal-valued float despite different serialized identity. V3 refuses that mutation even after the owned-selection file and policy pins are rebased.

`inverse-v3.json` restores the exact V2 module with one substitution. Every other helper function/class and the receiver C renderer is unchanged. The shared physical entry, six invariant rules, separate exact owned-selection binding, complete recorded base assumptions and remaining actual public Library/owner/TraceUnit gates are unchanged. There is no type coercion, extra authority Boolean, reset, ownership/payload grant, new backend behavior or resource relaxation.

Fourteen pure controls pass. The full repinned equal-float regression first confirms Python dictionary equality would accept the changed document, then confirms V3 rejects it. A second control executes the exact retained comparison AST for `bytes=1` versus `bytes=true`; no complete trace pin has extent1, so this Boolean boundary is tested as a literal type-identity control rather than invented physical input evidence.

The 18-case rebind reuses the exact V2 physical entry/context/receiver/trace/draw/resource/integration artifacts. Only the composition policies' composer pin and the resulting composition certificates change. All generated model C remains byte-identical. Both earlier frozen versions and their boundaries are preserved. No compiler, native/model execution, verifier, solver, SSH, original C++/ABI claim or public acceptance occurs here. Independent source review remains required before integration.
