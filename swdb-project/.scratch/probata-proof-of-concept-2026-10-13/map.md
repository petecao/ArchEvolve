# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.
- 03 (2026-10-14): SAW 1.6, CIVL 1.23 (JDK 21), GenMC 0.19.0 and Rocq 9.3.0 (switch `rocq-9`) pass their smoke tests on the Mac, no fallback; brew `llvm`/`lld`/`z3` pinned; ADR 0006 records the Mac exception. Branch `probata-poc/t03`.
- 05 (2026-10-14): SAW 1.6 is the bounded verifier: on clang++ 22.1.8 `-g` bitcode it proves the safe fixture and refutes the seeded bug at the read's ghost check (`[8][8]` ghost array kept across issue/wait overrides); quirks for 22: `llvm_field` fails on namespaced structs, preconditions over ghost-bound variables must precede the ghost line (else a false refutation). Branch `probata-poc/t05`.
