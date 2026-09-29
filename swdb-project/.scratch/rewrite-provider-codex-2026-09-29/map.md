# Map: Codex and Claude rewrite providers in a guarded workspace

Created: 2026-09-29 17:30 ET
Updated: 2026-09-29 18:30 ET (re-sliced into vertical tickets, approved by the user)
**Type:** ticket map
**Status:** ready-for-agent
**Spec:** [spec.md](spec.md)

| # | Ticket | Blocked by |
|---|---|---|
| 01 | [Prefactor: one interface for all provider kinds](issues/01-prefactor-provider-adapters.md) | — |
| 02 | [Spike: both providers under a Landlock launcher on mbit10](issues/02-spike-providers-under-landlock.md) | — |
| 03 | [Codex as a pinned rewrite provider (prompt-only mode)](issues/03-codex-pinned-provider.md) | 01 |
| 04 | [Repairs keep their provider; usage limits don't consume repairs](issues/04-repairs-keep-provider.md) | 03 |
| 05 | [Campaigns and the smoke script accept Codex](issues/05-campaigns-accept-codex.md) | 03 |
| 06 | [Workspace mode with the fixture provider](issues/06-workspace-mode-fixture.md) | 03 |
| 07 | [Audit of the provider event log](issues/07-provider-audit.md) | 02, 06 |
| 08 | [Landlock guard for real providers](issues/08-landlock-guard.md) | 02, 06 |
| 09 | [DX100 scalar-only source snapshot](issues/09-dx100-scalar-only-snapshot.md) | — |
| 10 | [Real smoke runs on mbit10, plus docs](issues/10-real-smoke-runs-and-docs.md) | 04, 05, 07, 08, 09 |

Frontier now: 01, 02 (needs a free lane), 09.

## Context pointers

- Design settled in a grilling session on 2026-09-29; decisions are in the spec and
  [ADR 0006](../../docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md).
- Glossary terms added the same day: Rewrite provider, Provider workspace, Statement.
- Every ticket is verified through the public `swdb submit` / `swdb repair` seam.
