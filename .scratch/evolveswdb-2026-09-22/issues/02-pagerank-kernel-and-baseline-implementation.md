# 02 — Kernel and baseline implementation for gapbs PageRank

Created: 2026-09-22
**Type:** slice
**Status:** claimed
**Blocked by:** 01
**Spec:** `../spec.md` (ADRs 0001, 0003)

**What to build:** The database describes gapbs PageRank: a kernel defined by its
correctness check, and its baseline implementation with code, loops, access-pattern
chains, and semantics. `swdb validate` enforces the rules that keep those facts honest.

- [ ] gapbs is copied in from upstream GitHub at a pinned commit with a provenance note (URL, commit, date, license); MemAcc's local `pr_push.cc` is not included.
- [ ] Kernel schema and a PageRank kernel record: what it computes, its correctness check (verifier command plus tolerance), and its baseline implementation ID.
- [ ] Implementation schema and the baseline implementation record (`PageRankPullGS`): code copied with file and line range, loops with trip counts and parallelism, access patterns as chains of steps, semantics per access pattern with basis. It states the Gauss-Seidel loop-carried dependency.
- [ ] A test confirms the recorded code equals the copied source at the recorded lines.
- [ ] Vocabularies for address shapes (with their attributes), update kinds, basis, array roles, and count scopes, each value with a one-line meaning.
- [ ] Validator rules, each with a passing and a failing fixture: every reference resolves; IDs are unique; `basis: unknown` requires `value: null`; vocabulary values exist; step attributes match their address shape.

## Comments
