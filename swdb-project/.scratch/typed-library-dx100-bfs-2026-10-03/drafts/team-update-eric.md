# Update for Eric — draft

Date: 2026-10-03 ET
Status: draft, not sent

The library pins your catalog design, revision and claim IDs. L3/L5 coherence and the wait coverage assumptions remain owned by you rather than upgraded to guarantees. The labeled parent-gather race case reports negative-hint CAS conflicts and explicit L3 violations, tied to the exact tree and workload; unrelated verifier failures remain inconclusive.

Repository pointers on `yanrujhou_main` (insert final commit when sending):

- `swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`: contract, provenance and all nine requirement discharges.
- `swdb-project/library/dx100/dxc_lowering.hpp`: lowerings and diagnostic hooks.
- `swdb-project/docs/reference/bfs-typed-library.md`: evidence and submit boundaries.
- `swdb-project/docs/adr/0007-typed-library.md` through `0011-raw-output-retention.md`: proposed decisions.
