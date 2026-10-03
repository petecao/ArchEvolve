# 14 — Stream load, tile size and pointer, ALU-scalar, and the strict store

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 12
**Spec:** `../spec.md`

**What to build:** Stream load, tile size and tile pointer are lowered and certified, ALU-scalar gets its own entry, and the strict layer implements ALU-scalar and the indirect vector store so the authors' code can run through it.

## Acceptance

- [ ] Stream load, tile size, tile pointer and ALU-scalar have records, entries, lowerings, differential-test drivers and strict operations.
- [ ] The strict indirect vector store writes its result tile; waiting on the store's source tile does not cover the store.
- [ ] Tile size and tile pointer cite new operation records or list no hardware operation.
- [ ] The truncation control (stream load past tile capacity) is rejected.

## Comments
