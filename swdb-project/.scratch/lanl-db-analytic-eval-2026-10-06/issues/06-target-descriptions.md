# 06 — Target descriptions for mbit10, DX100 and MAPLE

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md`
**Time estimate:** 3–4 h

**What to build:** Write each target's description: its mechanism models and parameter values, each with basis and source (D21, D23). mbit10 from its machine record (plus ticket 07's measurements); DX100 from its hardware-target record, its pinned configuration (D18), Eric's catalog (`catalog/hardware-v0.1.yaml` at the ArchEvolve root, read-only) and the DX100 paper; MAPLE from Eric's catalog (`maple-isca2022`) and its paper.

## Acceptance

- [ ] One description per target, versioned by sha256, citing Eric's claims where it uses them.
- [ ] Mechanisms keyed to a design's operations and parameters, never to its mechanism family alone.
- [ ] No gem5 output appears (D3); accelerator values are `code_reading`, `reported` or `unknown`.
- [ ] A list of `unknown` parameters per target, ranked by how much each moves a BFS estimate.
- [ ] The format is written so the HW team could own it later (D23).
