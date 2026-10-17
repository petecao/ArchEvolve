# 02 — Which existing formal verifiers can check our C++ code as-is?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

Which existing formal verifiers can check our C++11 code without a parser or AST of our own?
The code: baseline `TDStep` and the candidate artifacts in
`apps/dx100/benchmarks/gapbs/src/bfs.cc`, plus the DX100 functional model
(`apps/dx100/benchmarks/API/MAA_functional.hpp`) and the strict layer
(`library/dx100/strict/MAA_functional.hpp`).

For each tool: input language (C, C++, LLVM IR); bounded or unbounded; two-program (relational)
support; ghost code, loop invariants and lemmas; C++11 and OpenMP support; what it reports on
timeout; maintenance status in 2026; install footprint on macOS arm64.

Cover at least: CBMC (with code contracts), ESBMC, SeaHorn, SMACK, Frama-C/WP, VeriFast, CN,
SAW/crux-llvm, Alive2 (re-check Extensa's 2026-06 rejection: "TSVC integer-only"), llreve/REVE,
CPAchecker, Ultimate Automizer, KLEE, VerCors.

Output: a comparison table and a ranked shortlist of 2–3 tools for the bounded tier and for the
unbounded tier.

Known facts: z3 4.16.0 and cvc5 1.2.1 are installed on the Mac; the others are absent.
Certification builds with GCC `-std=c++11 -O1 -fopenmp`; clang 22.1.8 is available.

## Answer

Resolved 2026-10-09 14:27 ET. Full findings: [`../research/02-verifier-landscape.md`](../research/02-verifier-landscape.md).

- **Nothing reads `bfs.cc` whole.** The formal verifier gets a harness: `TDStep`, one candidate
  artifact, and the strict layer, built without `-fopenmp`. Only Clang/LLVM-based tools read it
  as C++ without changes: ESBMC, crux-llvm/SAW, KLEE, SeaHorn, Alive2. CBMC (its C++ support is
  "certainly spotty", issue #8663), Frama-C/WP, CN, SMACK, CPAchecker and Ultimate need a C port.
- **Bounded tier:** 1 ESBMC 8.5 (Clang front end, library models, SUCCESSFUL/FAILED/UNKNOWN,
  brew arm64) · 2 crux-llvm 0.12 / SAW 1.6 (LLVM bitcode; SAW compares two functions; concrete
  loop bounds only) · 3 CBMC 6.11 (on a C port).
- **Unbounded tier:** 1 Frama-C/WP 33.0 + RPP 0.0.4 (full hint vocabulary, verdict per proof
  goal including timeouts, smoke tests; C only) · 2 ESBMC k-induction / `--loop-invariant-check`
  (same C++ input; weak on array-quantified invariants) · 3 VerCors 2.4.0 (only unbounded tool
  that reads OpenMP; for the concurrency phase).
- **Alive2 re-check:** the "integer-only" objection does not apply (BFS is all `int32_t`), but
  Alive2 stays out: it cannot follow function calls, it only unrolls loops a fixed number of
  times, and OpenMP code becomes runtime calls.
- **Affects ticket 01 and later tickets:** the hint vocabulary depends on the tool (the ESBMC/CBMC
  family has no lemma construct; WP admits `axiom` and `admit` with no proof, so the checker must
  reject them). Unbounded proofs will trust `maa_*` contracts rather than the strict layer's C++.
  No single-thread tool models OpenMP.
