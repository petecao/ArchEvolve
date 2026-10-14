# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.
- 03 (2026-10-14): SAW 1.6, CIVL 1.23 (JDK 21), GenMC 0.19.0 and Rocq 9.3.0 (switch `rocq-9`) pass their smoke tests on the Mac, no fallback; brew `llvm`/`lld`/`z3` pinned; ADR 0006 records the Mac exception. Branch `probata-poc/t03`.
- 07 (2026-10-14): spike (c) **fail**. First counted run: Frama-C parse rejected all 10 hint sets. Best run (run 3): 543 of 642 goals proven, 99 timeouts, budget spent. Every run and every harness fix (bug fix vs method change) is in the Answer. Branch `probata-poc/t07`.
