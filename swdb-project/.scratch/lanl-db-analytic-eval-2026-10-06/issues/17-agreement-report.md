# 17 — Agreement report

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 16
**Spec:** `../spec.md`
**Time estimate:** 3–4 h plus campaign lane time (about 13 h of gem5 for 20 pairs)

**What to build:** After the flow-A campaigns: rank agreement between estimate and timing, whether gem5's best candidate survives a top-3 cut by estimate, and where estimates go wrong. The rule fixed in D30 is applied as written. A research variant of the estimator may be calibrated with these pairs, versioned separately (D10).

## Acceptance

- [ ] D30 applied verbatim, with the number of pairs shown.
- [ ] Blindness verified for every pair (D26).
- [ ] Any research variant is refused by team protocols.
- [ ] A short recommendation for ticket 18.
