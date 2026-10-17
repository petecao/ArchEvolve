# Read-stable physical input identity

2026-10-16 ET. Source-only successor; frozen model entry V2 and statement V1 remain unchanged.

The actual compiler capture V5 exposed an observational metadata issue: hashing a fresh staged input may update access time. Comparing complete stat tuples can reject that read even when bytes and identity are unchanged. The future model assembler and assertion-header consumer had the same pattern. Model entry V3 and source_statements_v2 add one exact stable_metadata helper and replace only their before/after comparison. The helper retains dev, inode, mode, hard-link count, uid, gid, size, nanosecond modification time and nanosecond change time. Only access time is excluded. Canonical regular-file and expected byte/hash checks stay intact.

Three new no-child controls exercise each exact read seam: the predecessor rejects an atime-only mock, the successor accepts it, and changing every retained identity/content field refuses. Exact textual inverses reconstruct both frozen predecessors. Twenty-two inherited pure model and statement controls also pass using the new modules. The model output, per-call contracts, assertion binding, pointer lifetime rules, state/ownership non-grants and source/public admission boundaries are unchanged. No compiler, native, solver, production edit or actual source/public acceptance is added.
