# 08 — Can an off-the-shelf verifier tell a real DX100 wait bug from a safe one?

Created: 2026-10-09
Updated: 2026-10-09 (reframed after 14: the authors' wait is safe on gem5)
**Type:** prototype
**Status:** ready-for-human
**Blocked by:** 07, 14
**Map:** `../map.md`

## Question

Using the top bounded-tier verifier from 02 (ESBMC), on a harness of `TDStepMAA` plus the strict
layer, single-threaded, within small declared bounds (one tile, a graph of a few vertices):

1. Under a gem5-aligned wait rule (14: a wait on a tile covers every unfinished command that
   names it), is the authors' `TDStepMAA` proven within bounds?
2. Is a seeded real wait bug (wait removed, or a wait on a tile the store does not name) refuted
   with a counterexample?
3. Under the current strict-layer rule, is the authors' wait reported as a violation that only
   the stricter rule flags?

First test (from 02): does ESBMC accept the strict layer as written (`static State`,
`lock_guard`, `__atomic_*`, `_Exit`)? Record run time, bounds, and every harness edit. Throwaway
code stays in `../prototype/`.
