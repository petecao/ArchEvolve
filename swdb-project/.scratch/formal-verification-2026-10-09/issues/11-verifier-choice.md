# 11 — Which verifiers form the bounded and unbounded tiers?

Created: 2026-10-09
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 02, 08, 09
**Map:** `../map.md`

## Question

Which formal verifier (or verifiers) form the proven-within-bounds tier and the proven-unbounded
tier, and what is the fallback when the primary tool cannot read the code?

## Comments

- 2026-10-09: input from 02: only Clang/LLVM-based tools read our C++ unchanged; CBMC's C++
  support is "certainly spotty". Candidate tiers: bounded = ESBMC (then crux-llvm); unbounded =
  Frama-C/WP + RPP on a C port (then ESBMC k-induction). No single-thread tool models OpenMP:
  the concurrency phase needs VerCors, CIVL or a pthreads rewrite.
