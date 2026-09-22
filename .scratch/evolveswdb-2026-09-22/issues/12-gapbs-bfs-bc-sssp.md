# 12 — gapbs bfs, bc, sssp

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The database covers the gapbs traversal kernels, exercising the
compare-and-swap and add-update kinds.

- [ ] For each of bfs, bc, and sssp: a kernel record whose correctness check uses the gapbs verifier, and a baseline implementation record with access-pattern chains and semantics with basis.
- [ ] The compare-and-swap updates (`parent`, `depths`, `dist`) and bc's floating-point accumulation are recorded with the right update kinds.
- [ ] Profiles on mbit10 for the four pilot inputs (with a timeout per run) validate, and a view is generated for each pair.

## Comments
