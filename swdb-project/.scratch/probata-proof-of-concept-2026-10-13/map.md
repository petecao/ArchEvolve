# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.
- 03 (2026-10-14): SAW 1.6, CIVL 1.23 (JDK 21), GenMC 0.19.0 and Rocq 9.3.0 (switch `rocq-9`) pass their smoke tests on the Mac, no fallback; brew `llvm`/`lld`/`z3` pinned; ADR 0006 records the Mac exception. Branch `probata-poc/t03`.
- 56 (2026-10-14): the Mac lineup at the same versions on mbit10 under `/data1/yanruj/probata-verifiers/` (source its `env.sh`); all 23 smoke verdicts match the Mac; GenMC links a private RTTI LLVM 22.1.8; `$HOME` untouched; builds -j8 in lane node 1; Archer waits on 50; `/data1` now 18 G free. Branch `probata-poc/t56`.
