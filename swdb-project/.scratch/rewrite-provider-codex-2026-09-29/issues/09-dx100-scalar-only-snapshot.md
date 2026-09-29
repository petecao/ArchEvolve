# 09 — DX100 scalar-only source snapshot

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** A registered source snapshot of DX100 BFS without the authors' accelerator (`*MAA`)
functions, used by from-scratch proposals so the provider never sees that answer key. The
full snapshot stays for routes whose strategy reuses the authors' code.

## Acceptance

- [ ] The snapshot is registered, and its record states what was removed and why (ADR 0006).
- [ ] It builds with the DX100 BFS flags and passes the BFS correctness check on mbit10, in a socket lane.
- [ ] Record validation passes, and the full snapshot is unchanged.

## Progress

2026-09-29: `scripts/prepare_dx100_scalar_snapshot.py` materializes and registers a
25-file buildable source subset. It removes pinned BFS ranges 63–225 and 366–443
(the two accelerator functions and their tile/register globals), the MAA main branch,
and other benchmark translation units/API examples that expose accelerator code.
The scalar functions, exact verifier text, licenses and operation/build headers stay.
The derived record explains the removal under ADR 0006 and refers to the retained full
snapshot. Local preview validation passed with 313 records and no errors; full source
manifest identity was unchanged before and after materialization.

Remote registration/build/correctness are pending the root agent's owned mbit10 lane;
this ticket remains claimed until those results exist. The smoke checks source 0 on
small scale-10 Kronecker and uniform-random graphs at four threads with the DX100
`-std=c++11 -O3 -Wall -fopenmp -pthread -DFUNC` flags. It makes no performance claim.
