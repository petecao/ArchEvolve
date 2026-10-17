# 10 — Real smoke runs on mbit10, plus docs

Created: 2026-09-29 (Eastern Time)
Updated: 2026-09-29 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** None
**Spec:** `../spec.md`

**What to build:** One real Codex run and one real Claude run in workspace mode on a small DX100 proposal
from the scalar-only snapshot, inside a socket lane. Then the worker documentation describes
the new provider boundary.

## Acceptance

- [x] Both runs complete or fail with a recorded reason, and the audit passes on both.
- [x] Evidence is committed with the other SWDB evidence; raw output stays on mbit10.
- [x] The rewrite-worker reference and the BFS tutorial describe workspace mode and both kinds.
- [x] ADR 0006 is marked implemented, with a pointer to the evidence.

## Answer

2026-09-29 (Eastern Time)

Fresh public `swdb submit` smoke A2 used the registered scalar-only DX100 snapshot
at checkout `c8a666ff95b5e1c0cbd1a1c8f99197e7fa119e53`. Both runs were inside
node0 generation 426, starting load 2.61, during 2026-09-29 20:42:19–20:45:43 ET.

| Provider | Outcome / CLI return | Provider wall time | Original and current audits | Independent native result |
|---|---|---|---|---|
| Codex 0.153.0, `gpt-5.6-sol/xhigh` | `candidate_created` / 0 | 50.610486 s | Pass | g++ 13.3 structural checks pass for sources 0/3/8, once each |
| Claude Code 2.1.278, `claude-sonnet-5-5/high` | Authentication failure / 1 | 0.877012 s | Pass | No candidate or BFS correctness result |

Claude's exact reason is “Failed to authenticate: OAuth session expired and could
not be refreshed”; it emitted zero tokens. This satisfies the ticket's explicit
complete-or-recorded-failure criterion. Both attempts passed native guard and
supervisor-filter checks, completed cleanup with no survivors, and deleted their
mode-0600 login copies. Credentials were not changed.

Codex emitted 94987 input, 77440 cached input, 0 cache-write, 2008 output and 1059
reasoning output tokens. The independent 10-vertex, 8-directed-edge graph had
reachable counts 6/3/1 for sources 0/3/8. `gain_claim=false`: this is small-input
structural correctness, not a performance result. The older Codex DX100 A1 log
remains refused for an opaque `sed` regex transformation, with its original
receipt unchanged; A2 is the current acceptance attempt.

The [worker reference](../../../docs/reference/bfs-rewrite-worker.md) and
[BFS tutorial](../../../docs/tutorial/04-bfs-workflow.md) describe both kinds,
workspace derivation, guard/audit bounds and residual risks.
[ADR 0006](../../../docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md)
is implemented and links the consolidated
[evidence metadata](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).
Raw logs, receipt bodies and SHA-256 identities remain under
`/data1/yanruj/EvolveSWDB_runs/provider-dx100-smoke-20260929-a2/`; only metadata
belongs in the closeout commit. Final independent code review remains pending
until the separate T17 work completes.
