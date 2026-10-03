# 07 — Prefactor: provider launcher runs every agent role

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** The provider launcher can run any agent role (rewriting, independent test generation, synthesis, profiling) with a workspace built from that role's own input, as ADR 0009 requires.

## Acceptance

- [x] A role has a name, a workspace input and an output schema; audit and model pins are shared by all roles.
- [x] Real (non-fixture) runs refuse to start outside an mbit10 socket lane.
- [x] No role's workspace exposes evaluator inputs, workload files, other candidate artifacts or the authors' accelerated code.
- [x] The rewriting role behaves exactly as today; existing provider workspace, guard and rewrite tests pass.
- [x] A fixture read-only role is tested end to end through the swdb command line.

## Comments

## Answer

Completed 2026-10-03 ET. Role-specific explicit inputs and output schemas share the guarded launcher, provider/model/effort pins and retained audit. Rewriting retains its existing path; independent test generation, synthesis and profiling use bounded role workspaces. Real roles require a verified mbit10 socket lane before workspace creation. Context projection and explicit input checks exclude evaluator/workload/candidate material and authors accelerated source. Public fixture annotation exercises the shared role end to end. Final regression coverage verifies all 3,679 current cases: 3,643 pass and 36 skip, including existing rewrite/workspace/guard tests. See [verification](../verification.json) and [code review](../code-review.md); no real provider/profile gain is implied.
