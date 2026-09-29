# 09 — DX100 scalar-only source snapshot

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** A registered source snapshot of DX100 BFS without the authors' accelerator (`*MAA`)
functions, used by from-scratch proposals so the provider never sees that answer key. The
full snapshot stays for routes whose strategy reuses the authors' code.

## Acceptance

- [ ] The snapshot is registered, and its record states what was removed and why (ADR 0006).
- [ ] It builds with the DX100 BFS flags and passes the BFS correctness check on mbit10, in a socket lane.
- [ ] Record validation passes, and the full snapshot is unchanged.
