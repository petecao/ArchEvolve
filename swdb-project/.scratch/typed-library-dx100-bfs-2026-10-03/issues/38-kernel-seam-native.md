# 38 — Prefactor: kernel plug-in seam, native side

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The native side of the evaluator handles kernels through plug-ins, with BFS as the only one.

## Acceptance

- [ ] Workload registration and protocol-freeze identity checks, native evaluation, the native build adapter (source path, protected verifier, trusted driver and its oracle), native pairs, region discovery, profiling trial parsing and profile packages go through a kernel plug-in.
- [ ] BFS is the only plug-in; every BFS test and record is unchanged.

## Comments
