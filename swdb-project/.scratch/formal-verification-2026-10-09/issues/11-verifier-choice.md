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
- 2026-10-11: input from 08: ESBMC 8.5 timed out on DX100 code: the strict layer as written
  (its `std::vector` model) and the array port (300–600 s, every size). crux-llvm 0.12 proved
  and refuted at one lane on the port, but cannot run libc++ 22 code, and no safe 2-lane run
  finished in 15 minutes. CBMC cannot parse libc++ 22 headers. Running 6 crux jobs at once
  exhausted the Mac's 36 GB of RAM: run one at a time, or on mbit10 under `ulimit -v`.
- 2026-10-12 22:25 ET: input from 09: the tiers must also cover (1) machine-checked lifting
  lemmas (induction over a kernel's driver loop, with the proof unit replaced by its claim);
  (2) equality over real arithmetic for floating-point kernels (PR, BC), rounding in the
  assumption set; (3) for proven unbounded, a proof for any thread count, since thread count is
  a bound. The evaluation covers other GAPBS kernels, not only BFS.
