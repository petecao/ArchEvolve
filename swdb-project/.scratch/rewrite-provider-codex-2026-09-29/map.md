# Map: Codex and Claude rewrite providers in a guarded workspace

Created: 2026-09-29 17:30 ET
Updated: 2026-09-29 20:10 ET
**Type:** ticket map
**Status:** in-progress
**Spec:** [spec.md](spec.md)

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Prefactor: one interface for all provider kinds](issues/01-prefactor-provider-adapters.md) | resolved | — |
| 02 | [Spike: both providers under a Landlock launcher on mbit10](issues/02-spike-providers-under-landlock.md) | claimed | final Linux tests and fresh DX100 receipts |
| 03 | [Codex as a pinned rewrite provider (prompt-only mode)](issues/03-codex-pinned-provider.md) | resolved | — |
| 04 | [Repairs keep their provider; usage limits don't consume repairs](issues/04-repairs-keep-provider.md) | resolved | — |
| 05 | [Campaigns and the smoke script accept Codex](issues/05-campaigns-accept-codex.md) | resolved | — |
| 06 | [Workspace mode with the fixture provider](issues/06-workspace-mode-fixture.md) | resolved | — |
| 07 | [Audit of the provider event log](issues/07-provider-audit.md) | resolved | — |
| 08 | [Landlock guard for real providers](issues/08-landlock-guard.md) | claimed | exact-revision Linux A6 tests |
| 09 | [DX100 scalar-only source snapshot](issues/09-dx100-scalar-only-snapshot.md) | resolved | — |
| 10 | [Real smoke runs on mbit10, plus docs](issues/10-real-smoke-runs-and-docs.md) | claimed | 02, 08 |

Frontier now: 02, 08, 10. Both real providers completed guarded toy edit/build/run
turns. Production uses one CPU within the verified socket while counting the full
process tree, including strace, against the aggregate caps. The public scalar-only
DX100 Codex candidate passed native correctness for sources 0/3/8; gain_claim=false.
Claude's public DX100 call retained an OAuth-expired pre-tool failure with passing
guard and event audits. Its earlier successful toy is separate feasibility evidence.
The current stricter audit rejects the older Codex DX100 receipt because its shell
source transformation cannot be safely resolved; it is historical native correctness
evidence, not a currently admitted provider attempt. A fresh DX100 run will follow A6.
Metadata is in [guarded provider evidence](../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).

A full Mac regression and exact-revision Linux A6 public tests are running.
Independent Standards/Spec findings were repaired: probe-kind mapping, top-level
shell/Glob and file-operand audit gaps, detached-helper accounting and cleanup, and
supervisor signal continuity. Fresh workspace tests passed 195 cases; Linux runtime
verification of the final guard remains pending. The old Codex DX100 audit failure
is retained, without modifying its original receipt. Node1 now runs the separate
T17 evidence recheck after confirming no live evaluator descendants of the existing
controller; that controller is untouched and the existing load is recorded.

## Context pointers

- Design settled in a grilling session on 2026-09-29; decisions are in the spec and
  [ADR 0006](../../docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md).
- Glossary terms added the same day: Rewrite provider, Provider workspace, Statement.
- Every ticket is verified through the public `swdb submit` / `swdb repair` seam.
- 2026-09-29: the scalar-only snapshot passed GCC 13 native uniform and Kronecker
  correctness checks on mbit10 node 0; metadata is in
  `records/source_snapshots/bfs-dx100-scalar-only-20260929-a1.source.yaml`.
