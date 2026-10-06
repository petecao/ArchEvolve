# 09 — DX100 estimate

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 05
**Spec:** `../spec.md`
**Time estimate:** 1.5–2 days

**What to build:** The pass recognizes accelerator commands from the intrinsic records, not from a hard-coded list. The counted run counts the address stream live for a target's reorder window and DRAM address layout, storing no stream (D17, D24). The DX100 target description is written from its hardware-target record, its pinned configuration (D18), Eric's catalog and the DX100 paper (D23). The remaining version-1 mechanism models exist: offload setup, tile staging, reorder-window row counting and fetch queue. The DX100 BFS candidate artifact gets an estimate with a per-region report.

## Acceptance

- [ ] No gem5 output is read (D3), and no address stream is written to disk.
- [ ] A fixture with a known address pattern gives the hand-computed row-buffer hit rate.
- [ ] DX100's unknown parameters are listed and ranked by how much each moves the estimate.
- [ ] Nothing DX100-specific exists outside the target description (D21, D22).
