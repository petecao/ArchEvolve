# Spec: hand SWDB's BFS work to the ArchEvolve pipeline

Created: 2026-09-29 17:40 ET
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** None for tickets 02–04; 05 and 06 wait on Peter.
Owner: Yan-Ru Jhou

## Problem

The 2026-09-24 team meeting (`../../../docs/meeting-2026-09-24.md` at the ArchEvolve root)
fixed a linear pipeline: Yan-Ru → Peter → Josh/Eric → Peter → Yan-Ru. SWDB still presents
itself to "SW and HW ensembles" that read profile packages, the head-of-pipeline deliverable
(annotated DX100 TDStep) does not exist, statement IDs differ across the three sides, and
the one positive simulated result (T17) is not recorded as a comparison.

## Solution

1. Answer Josh's request for the TDStep binding (revision, build, graph, logs), and ask
   Peter about the offset width and what his agent will request.
2. Annotate DX100 TDStep with Josh's 7 `bfs-td-*` statement IDs.
3. Freeze T17 protocol v2 and record the comparison. The claim must say the strategy reuses
   the DX100 authors' `TDStepMAA` path, covers source vertex 0 only, and is simulated.
4. Mark the SPARTA v0.1 "Workload view" pieces as replaced, and realign the old spec's roles.
5. After Peter answers: the statement crosswalk, then an adapter from his spec format.
6. Deliver through a PR from `yanrujhou_main` to `main` that Yan-Ru opens.

## Out of scope

- Exporting per-statement memory features from SWDB (Peter owns them).
