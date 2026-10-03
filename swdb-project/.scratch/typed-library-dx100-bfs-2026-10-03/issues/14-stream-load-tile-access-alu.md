# 14 — Stream load, tile size and pointer, ALU-scalar, and the strict store

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 12
**Spec:** `../spec.md`

**What to build:** Stream load, tile size and tile pointer are lowered and certified, ALU-scalar gets its own entry, and the strict layer implements ALU-scalar and the indirect vector store so the authors' code can run through it.

## Acceptance

- [x] Stream load, tile size, tile pointer and ALU-scalar have records, entries, lowerings, differential-test drivers and strict operations.
- [x] The strict indirect vector store writes its result tile; waiting on the store's source tile does not cover the store.
- [x] Tile size and tile pointer cite new operation records or list no hardware operation.
- [x] The truncation control (stream load past tile capacity) is rejected.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. Stream load, tile-size access, tile-pointer access, and ALU-scalar lowerings each have an executed receipt: stream_load: `certification.a660bf4c01ea415396d29caa4a925088`, tile_size: `certification.92223db31dc24d6d95f481f77a0f3423`, tile_pointer: `certification.afefcbfc52d4457fb638061eb5ac7f8f`, alu_scalar: `certification.f6494a61d8bb4c96899e45f29463a074`. The strict indirect vector store returns the old-value result tile and retains a distinct writer: waiting on its source tile leaves the result unpublished. The wait receipt `certification.a246311c98194743b142f3dac3868cae` includes real store positives and wrong-store-wait controls at both capacities. Stream truncation is rejected; size and pointer access have no hardware-operation claims.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 94 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.
