# Map: Codex and Claude rewrite providers in a guarded workspace

Created: 2026-09-29 17:30 ET
Updated: 2026-09-29 18:40 ET
**Type:** ticket map
**Status:** in-progress
**Spec:** [spec.md](spec.md)

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Prefactor: one interface for all provider kinds](issues/01-prefactor-provider-adapters.md) | resolved | — |
| 02 | [Spike: both providers under a Landlock launcher on mbit10](issues/02-spike-providers-under-landlock.md) | claimed | final bounded-runtime spike queued after Linux suite |
| 03 | [Codex as a pinned rewrite provider (prompt-only mode)](issues/03-codex-pinned-provider.md) | resolved | — |
| 04 | [Repairs keep their provider; usage limits don't consume repairs](issues/04-repairs-keep-provider.md) | resolved | — |
| 05 | [Campaigns and the smoke script accept Codex](issues/05-campaigns-accept-codex.md) | resolved | — |
| 06 | [Workspace mode with the fixture provider](issues/06-workspace-mode-fixture.md) | resolved | — |
| 07 | [Audit of the provider event log](issues/07-provider-audit.md) | resolved | — |
| 08 | [Landlock guard for real providers](issues/08-landlock-guard.md) | claimed | Linux public tests pending |
| 09 | [DX100 scalar-only source snapshot](issues/09-dx100-scalar-only-snapshot.md) | resolved | — |
| 10 | [Real smoke runs on mbit10, plus docs](issues/10-real-smoke-runs-and-docs.md) | claimed | 02, 08 |

Frontier now: 02, 08, 10. Code and local fixtures are integrated. Linux guard tests passed;
the corrected Linux workspace/pin suite is running in node0 generation 408. Claude
completed a toy turn; its IPv6 UDP audit classification was corrected. Codex's wrapper
plus runtime exceeded 16 threads, so the next spike records a four-CPU subset of the
verified socket while retaining the aggregate cap. Real DX100 receipts remain pending.
A full local regression suite is running. Final code review and ticket reconciliation
follow those checks. The live node1 lease belongs to another job and is preserved.

## Context pointers

- Design settled in a grilling session on 2026-09-29; decisions are in the spec and
  [ADR 0006](../../docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md).
- Glossary terms added the same day: Rewrite provider, Provider workspace, Statement.
- Every ticket is verified through the public `swdb submit` / `swdb repair` seam.
- 2026-09-29: the scalar-only snapshot passed GCC 13 native uniform and Kronecker
  correctness checks on mbit10 node 0; metadata is in
  `records/source_snapshots/bfs-dx100-scalar-only-20260929-a1.source.yaml`.
