# Map: Codex and Claude rewrite providers in a guarded workspace

Created: 2026-09-29 17:30 ET
Updated: 2026-09-29 (Eastern Time)
**Type:** ticket map
**Status:** resolved
**Spec:** [spec.md](spec.md)

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Prefactor: one interface for all provider kinds](issues/01-prefactor-provider-adapters.md) | resolved | — |
| 02 | [Spike: both providers under a Landlock launcher on mbit10](issues/02-spike-providers-under-landlock.md) | resolved | — |
| 03 | [Codex as a pinned rewrite provider (prompt-only mode)](issues/03-codex-pinned-provider.md) | resolved | — |
| 04 | [Repairs keep their provider; usage limits don't consume repairs](issues/04-repairs-keep-provider.md) | resolved | — |
| 05 | [Campaigns and the smoke script accept Codex](issues/05-campaigns-accept-codex.md) | resolved | — |
| 06 | [Workspace mode with the fixture provider](issues/06-workspace-mode-fixture.md) | resolved | — |
| 07 | [Audit of the provider event log](issues/07-provider-audit.md) | resolved | — |
| 08 | [Landlock guard for real providers](issues/08-landlock-guard.md) | resolved | — |
| 09 | [DX100 scalar-only source snapshot](issues/09-dx100-scalar-only-snapshot.md) | resolved | — |
| 10 | [Real smoke runs on mbit10, plus docs](issues/10-real-smoke-runs-and-docs.md) | resolved | — |

All ten provider tickets are resolved. Production uses one CPU within the verified
socket while counting the full tree, including strace and any exact installed
persistent Codex service, against the aggregate caps.

| Acceptance evidence | Checkout / lane | Result |
|---|---|---|
| Linux A6 guard/pins/workspace | `4f5d152`; node0 generation 424; load 1.02 | 222 passed in 1428.56 s |
| Linux A7 literal-status cases and current-parser re-audit | `c8a666f`; node0 generation 425; load 2.55 | 42 passed in 132.56 s; toys and Claude failure pass; old Codex A1 refusal retained |
| Fresh public Codex DX100 A2 | `c8a666f`; node0 generation 426; load 2.61 | Candidate created; original/current audits, guard and cleanup pass; native sources 0/3/8 pass |
| Fresh public Claude DX100 A2 | Same A2 checkout/lane | Recorded OAuth-expired failure; original/current audits, guard and cleanup pass; no candidate or BFS result |

A2 ran on 2026-09-29 from 20:42:19 to 20:45:43 ET. Codex provider time was
50.610486 s; Claude's was 0.877012 s. The native g++ 13.3 checks use a 10-vertex,
8-directed-edge graph, one trial each for sources 0/3/8; `gain_claim=false`.
Ticket 10 expressly permits a recorded provider failure with passing audits.
The older Codex DX100 A1 log remains refused for an opaque `sed` regex
transformation and is not the current acceptance attempt. Metadata and raw
identities are in [guarded provider evidence](../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).

The full Mac regression passed 2798 tests with 31 skips in 4176.73 s; it began
at 19:14 ET while the tree was evolving. Separate focused checks validate the
final changes: workspace 195 passed (396.70 s), shared guidance 14 passed
(29.67 s), and literal-status compatibility 42 passed (83.03 s).
Standards/Spec findings were repaired, including probe-kind mapping, shell/Glob
and file-operand audit gaps, detached-helper accounting/cleanup and supervisor
continuity. Final independent code review remains pending until the separate
T17 evidence recheck completes; this map does not close that separate work.

## Context pointers

- Design settled in a grilling session on 2026-09-29; decisions are in the spec and
  [ADR 0006](../../docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md).
- Glossary terms added the same day: Rewrite provider, Provider workspace, Statement.
- Contract tests drive the public `swdb submit` / `swdb repair` seam; real A2
  proposals also use public submission, followed by independent native checks.
- 2026-09-29: the scalar-only snapshot passed GCC 13 native uniform and Kronecker
  correctness checks on mbit10 node 0; metadata is in
  `records/source_snapshots/bfs-dx100-scalar-only-20260929-a1.source.yaml`.
