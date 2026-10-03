# 07 — Prefactor: provider launcher runs every agent role

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The provider launcher can run any agent role (rewriting, independent test generation, synthesis, profiling) with a workspace built from that role's own input, as ADR 0009 requires.

## Acceptance

- [ ] A role has a name, a workspace input and an output schema; audit and model pins are shared by all roles.
- [ ] Real (non-fixture) runs refuse to start outside an mbit10 socket lane.
- [ ] No role's workspace exposes evaluator inputs, workload files, other candidate artifacts or the authors' accelerated code.
- [ ] The rewriting role behaves exactly as today; existing provider workspace, guard and rewrite tests pass.
- [ ] A fixture read-only role is tested end to end through the swdb command line.

## Comments
