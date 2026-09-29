# 10 — Real smoke runs on mbit10, plus docs

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** 04, 05, 07, 08, 09
**Spec:** `../spec.md`

**What to build:** One real Codex run and one real Claude run in workspace mode on a small DX100 proposal
from the scalar-only snapshot, inside a socket lane. Then the worker documentation describes
the new provider boundary.

## Acceptance

- [ ] Both runs complete or fail with a recorded reason, and the audit passes on both.
- [ ] Evidence is committed with the other SWDB evidence; raw output stays on mbit10.
- [ ] The rewrite-worker reference and the BFS tutorial describe workspace mode and both kinds.
- [ ] ADR 0006 is marked implemented, with a pointer to the evidence.
