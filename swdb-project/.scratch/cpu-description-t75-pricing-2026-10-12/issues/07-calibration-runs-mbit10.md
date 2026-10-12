# 07 — Calibration runs on mbit10

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** claimed
**Blocked by:** 01, 02, 04, 05, 06
**Spec:** `../spec.md` (C5–C8, C10, C12; user stories 20, 22)
**Code map:** `../notes/ops.md`, `../notes/bulk.md`

**Time estimate:** about 2–3 hours of lane time.

## What to do

From a clean, pushed commit, in a free lane, raw output under `/data/yanruj/EvolveSWDB_runs/`
(`/data1` is near 20 GB), measure only the gaps that ticket 01 confirmed:

- `memory_v2` cells (write 1, write 2);
- allocator v2 cells (malloc sizes, 16 MiB `new[]`/`delete[]` bins);
- OpenMP a2 (`_8u`);
- library-call family and `indirect-call`;
- one new bulk-total batch for the six `llvm.memmove` sizes (no code change, `../notes/bulk.md`).

Microbenchmarks only: never run a t75 binary (C12). Export compact receipts as records with their
machine record and load; raw output never enters git. Write a runbook like the `services.v1` runbook.

## Acceptance

- [ ] Every new receipt is a committed record with its lane record and load.
- [ ] Targeted `swdb validate` of the new records passes; the whole-store check runs once on mbit10.
- [ ] Runbook saved in `evidence/07-calibrations/`.
