# 39 — Prefactor: kernel plug-in seam, gem5 side

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 23
**Spec:** `../spec.md`

**What to build:** The gem5 side of the evaluator handles kernels through plug-ins, with BFS as the only one.

## Acceptance

- [ ] The gem5 build adapter's driver and oracle, the verifier binding, the completion witness, and the accelerator cases with their extractors go through a kernel plug-in.
- [ ] BFS is the only plug-in; every BFS test and record is unchanged.

## Comments
