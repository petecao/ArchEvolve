# 09 — DX100 scalar-only source snapshot

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** A registered source snapshot of DX100 BFS without the authors' accelerator (`*MAA`)
functions, used by from-scratch proposals so the provider never sees that answer key. The
full snapshot stays for routes whose strategy reuses the authors' code.

## Acceptance

- [x] The snapshot is registered, and its record states what was removed and why (ADR 0006).
- [x] It builds with the DX100 BFS flags and passes the BFS correctness check on mbit10, in a socket lane.
- [x] Record validation passes, and the full snapshot is unchanged.

## Progress

2026-09-29: `scripts/prepare_dx100_scalar_snapshot.py` materializes and registers a
25-file buildable source subset. It removes pinned BFS ranges 63–225 and 366–443
(the two accelerator functions and their tile/register globals), the MAA main branch,
and other benchmark translation units/API examples that expose accelerator code.
The scalar functions, exact verifier text, licenses and operation/build headers stay.
The derived record explains the removal under ADR 0006 and refers to the retained full
snapshot. Local preview validation passed with 313 records and no errors; full source
manifest identity was unchanged before and after materialization.

The smoke checks source 0 on small scale-10 Kronecker and uniform-random graphs at four
threads with the DX100 `-std=c++11 -O3 -Wall -fopenmp -pthread -DFUNC` flags. It makes no
performance claim.

## Answer

2026-09-29: Registered `bfs-dx100-scalar-only-20260929-a1.source`, 25 files, artifact
SHA-256 `2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af`.
The record carries the exact removal rationale and pinned ranges under ADR 0006;
the existing full DX100 snapshot and all 51 vendored manifest entries are unchanged.

The root agent built and checked it on mbit10 in node0, lease generation 399. Both
`-g 10 -k 4 -r 0 -n 1 -v` and `-u 10 -k 4 -r 0 -n 1 -v` printed `Verification: PASS`
at four threads. The retained native correctness receipt is
`/data1/yanruj/EvolveSWDB_runs/provider-scalar-20260929-a1/bfs-dx100-scalar-only-20260929-a1.source/correctness.json`,
SHA-256 `afb88d837f2645f378af6942d9c64116957c1097dcbc156ad6f00ca19082b427`.
The source record's context now reports `passed` and binds that receipt; the metadata
was committed on mbit10 and fetched locally in `729a089`. This smoke covers finite
small graphs/source 0, with no performance or accelerator-execution claim.

Validation: local preview plus public `swdb validate`; `test_add.py` — 8 passed.
