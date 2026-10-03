# 44 — BC gem5 completion witness and execution case

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 39, 40
**Spec:** `../spec.md`

**What to build:** BC correctness and coverage can be checked on gem5 even though gem5 exits before the program's own verifier runs.

## Acceptance

- [ ] A BC completion-witness plug-in works like BFS's v2 witness.
- [ ] A BC read-only execution case is defined for the forward pass.
- [ ] Fixture tests pass; BFS is unchanged.

## Comments
