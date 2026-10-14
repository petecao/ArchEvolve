# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.
- 03 (2026-10-14): SAW 1.6, CIVL 1.23 (JDK 21), GenMC 0.19.0 and Rocq 9.3.0 (switch `rocq-9`) pass their smoke tests on the Mac, no fallback; brew `llvm`/`lld`/`z3` pinned; ADR 0006 records the Mac exception. Branch `probata-poc/t03`.
- 04 — `proof` record kind, `swdb prove` (scripted adapter, adapter interface in `swdb/proof.py`), optional route field, `swdb_proof*` tables, proven level on read in `swdb candidate-level`; interface in `docs/reference/format-v0.4-proof.md`. Commit `0fb758ee` (branch `probata-poc/t04`).
