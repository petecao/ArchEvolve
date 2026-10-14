# Spec: Extensa Probata evaluation

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:07 ET (cut-edge rule)
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** [proof-of-concept ticket 59, method-version review and freeze](../probata-proof-of-concept-2026-10-13/issues/)
Owner: Yan-Ru Jhou
Design: [the formal-verification map's spec](../formal-verification-2026-10-09/spec.md), section
"Evaluation design". Every decision lives there or in the map ticket it links (18 and 23 above all).
Tickets: [`issues/`](issues/), 01–12, numbered so blockers come first. Prose elsewhere calls them
"evaluation 01" and so on, to keep them apart from the proof-of-concept tickets.

## Summary (read this first)

1. **Destination:** a results report answering RQ1–RQ5 against the pass bars committed at the freeze.
2. **Starts only after the freeze.** The method version, budgets and pass bars are fixed there; a later
   method change makes a new method version, re-runs every held-out kernel, and both runs are reported.
3. **Held-out kernels:** BC, PR and SSSP. Their contracts are drafted blind to the authors' DX100 code.
4. **Values these tickets cite** (budgets, pass bars, k, minimum bounds) are the frozen ones in the
   method-version file, not the design spec's starting values.

## Rules for every ticket

- Final runs on mbit10 only, inside socket lanes; up to 6 proof workers per lane job.
- LLM configurations run 3 times; non-LLM configurations once. Provider pins come from the run plan.
- Codex is the default provider; Claude appears only in ticket 11.
- Cut order if time runs short: ticket 11, then ticket 10, then PR (ticket 03 and its share of 05–09). BFS, BC and SSSP are
  the floor; BC is never cut; if SSSP cannot finish, the submission waits. A "Blocked by" edge marked
  "drop if cut" disappears with the cut ticket.
- Internal findings about the authors' code are never sent to the authors or the team without Yan-Ru.

## Out of scope

Everything the design spec puts out of scope. Building the method: that is the proof-of-concept effort.
