# 08 — Can an off-the-shelf verifier tell a real DX100 wait bug from a safe one?

Created: 2026-10-09
Updated: 2026-10-11 18:58 ET (resolved: yes at one lane, via crux-llvm on a port; ESBMC failed)
**Type:** prototype
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-11 15:02 ET)
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

## Work log (2026-10-11 18:50 ET)

**Checkpoint.** Code and logs are in [`../prototype/08-wrong-tile/`](../prototype/08-wrong-tile/);
each run has one line in `logs/summary.txt`.

- **First test: no.** ESBMC 8.5 does not accept the strict layer as written.
  - It needs a `std::_Exit` shim to parse.
  - Even then, a one-command program does not finish in 240 s: its `std::vector` model blows up
    on the nested vector copies in the operation log.
  - Building the State alone takes 11 s.
  - crux-llvm 0.12 cannot run the header's libc++ 22 code: operand bundles, then `memmove` on
    null in vector copies.
- **The port.** [`port/strict_port.hpp`](../prototype/08-wrong-tile/port/strict_port.hpp) has
  the same functions, checks and both wait rules, with fixed arrays and no STL.
  - Evidence that it matches: `run_port_diff.sh` runs all 11 scenarios of
    `tests/fixtures/strict_wait_rule.cc` against both headers, both rules, and `TILE_SIZE`
    4, 16 and 1024. 0 diffs out of 66 runs.
- **The harness.** [`tdstep_harness.cpp`](../prototype/08-wrong-tile/tdstep_harness.cpp) is the
  authors' TDStepMAA MAA path, one thread, over the port.
  - P1 (hazard): the CPU reads only finished tiles.
  - P2 (function): one BFS level step.
  - Every edit to the authors' code is marked `EDIT`.
  - Shape mode (`-DDEGREES`) fixes the frontier to vertices 0..F-1 (without loss of generality,
    by relabeling) and fixes their out-degrees.
- **ESBMC on the port: times out**, every shape and both rules, 300–600 s. Symbolic execution
  never reaches the end, because the operation log's counters look symbolic to ESBMC.
- **crux-llvm on the port, 1-lane tile, 1 edge: the answer the ticket asks for.** All runs
  use the gem5 rule unless marked old.

  | Variant | Verdict | Goals | Time |
  |---|---|---|---|
  | Authors' wait | Valid | 19/19 | 21 s |
  | Wait on the result tile | Valid | — | 27 s |
  | Authors' wait, **old rule** | refuted (P1) | — | 6 s |
  | Wait removed (seeded) | refuted (P1) | — | 16 s |
  | Wait on tile6 (seeded) | refuted (P1) | — | 16 s |
  | Wait on tile7 (seeded) | refuted (P1) | — | 16 s |

- **crux-llvm, 2-lane tile.**
  - P2 alone still finds counterexamples for all three seeded bugs. The wait-on-tile7 bug needs
    a vertex repeated within one tile.
  - No safe variant finished in 600–900 s with z3 or cvc5, with or without `--path-sat`.

**Blocker.** Running crux jobs in parallel (up to 6 at once) exhausted the Mac's 36 GB of RAM,
and the Mac had to be restarted. A `timeout` limits time, not memory. On macOS, `ulimit -v`
and ESBMC's `--memlimit` do not work, and `ps` is blocked inside the sandbox.

**Next action.**

1. Decide with Yan-Ru whether the 1-lane result answers questions 1–3, or whether 2 lanes must
   prove too.
2. If 2 lanes are needed, run them one at a time on mbit10 under `ulimit -v` (one lane, leased).
   Never run them in parallel on the Mac.

## Answer

2026-10-11 18:58 ET. Yan-Ru accepted the 1-lane result as the answer.

**Yes: an off-the-shelf verifier tells the bug from the safe wait. That verifier is crux-llvm
0.12, not ESBMC, and only on a port of the strict layer.** Bounds: one thread, a 1-lane tile,
one edge, every value of `parent[]` and `neighbors[]`. Detail is in the work log above; code is
in [`../prototype/08-wrong-tile/`](../prototype/08-wrong-tile/).

1. **Q1 (proven within bounds?): yes.** Under the gem5 rule, the authors' `TDStepMAA` is proven.
   Both properties hold: 19 of 19 goals in 21 s. P1 says the CPU reads only finished tiles; P2
   is the BFS step's postcondition.
2. **Q2 (seeded bugs refuted?): yes**, each with a counterexample in about 16 s:
   - wait removed;
   - wait on tile6, a tile the store does not name;
   - wait on tile7, which names the compare, not the store.

   On 2-lane tiles, P2 alone still refutes all three.
3. **Q3 (does only the stricter rule flag the authors' wait?): yes.** Under the old rule the
   authors' wait is refuted on P1 in 6 s. Under the gem5 rule it is proven.
4. **First test (does ESBMC accept the strict layer as written?): no.**
   - ESBMC parses the header after a `std::_Exit` shim, then times out (240 s) on a one-command
     program.
   - On the port it times out (300–600 s) at every size and under both rules.
   - crux-llvm cannot run the header's libc++ 22 code.

**What this means for later tickets:**

- **Verifier choice (ticket 11):** ESBMC is not the bounded tier for DX100 code.
- **Proof semantics (ticket 12):** proofs run over a port, so the port needs an equivalence
  argument. Today that argument is a differential test: 66 runs, 0 diffs.
- **Bounds:** the bound that proves today is 1 lane. At 2 lanes, no safe variant finished in
  15 minutes.
- **Harness assumption:** shape mode assumes relabeling symmetry (frontier = vertices 0..F-1).
  A reviewer may question it.
