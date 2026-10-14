# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.

- 01 — Guard refuses `PBFSMAA`, `BrandesMaa`, `PageRankPullMAA`, `DeltaStepMAA` (plus `TDStepMAA`, `DOBFSMAA`); dead names dropped; 18 per-name tests in `tests/test_provider_authors_guard.py`. `cffe20e1` (`probata-poc/t01`).
- 03 (2026-10-14): SAW 1.6, CIVL 1.23 (JDK 21), GenMC 0.19.0 and Rocq 9.3.0 (switch `rocq-9`) pass their smoke tests on the Mac, no fallback; brew `llvm`/`lld`/`z3` pinned; ADR 0006 records the Mac exception. Branch `probata-poc/t03`.
- 04 — `proof` record kind, `swdb prove` (scripted adapter, adapter interface in `swdb/proof.py`), optional route field, `swdb_proof*` tables, proven level on read in `swdb candidate-level`; interface in `docs/reference/format-v0.4-proof.md`. Commit `0fb758ee` (branch `probata-poc/t04`).
- 05 (2026-10-14): SAW 1.6 is the bounded verifier: on clang++ 22.1.8 `-g` bitcode it proves the safe fixture and refutes the seeded bug at the read's ghost check (`[8][8]` ghost array kept across issue/wait overrides); quirks for 22: `llvm_field` fails on namespaced structs, preconditions over ghost-bound variables must precede the ghost line (else a false refutation). `9e676226` (`probata-poc/t05`).
- 56 (2026-10-14): the Mac lineup at the same versions on mbit10 under `/data1/yanruj/probata-verifiers/` (source its `env.sh`); all 23 smoke verdicts match the Mac; GenMC links a private RTTI LLVM 22.1.8; `$HOME` untouched; builds -j8 in lane node 1; Archer waits on 50; `/data1` now 18 G free. Branch `probata-poc/t56`.
