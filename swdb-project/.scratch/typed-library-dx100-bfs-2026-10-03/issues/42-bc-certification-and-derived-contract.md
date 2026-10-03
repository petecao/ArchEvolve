# 42 — BC certification and the derived BC contract

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 18, 17, 28, 40
**Spec:** `../spec.md`

**What to build:** A derived BC contract applies the BFS read-offload contract to BC's forward-pass region and certifies on the Mac.

## Acceptance

- [ ] The certification matrix and pass rule become a kernel plug-in; BFS is unchanged.
- [ ] BC's instance uses BCVerifier PASS, the forward pass's per-level frontier sizes and an accelerated-chunk witness.
- [ ] The derived contract has its own ID, cites the BFS contract, and adds BC-L1 (the path-count test reads the depth on the CPU after the compare-and-swap).
- [ ] A BC-L1 violation control is rejected, and the BC forward-pass patch certifies.

## Comments
