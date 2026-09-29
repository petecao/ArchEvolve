# 02 — Annotate DX100 TDStep with Josh's statement IDs

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

## What to build

Add Josh's 7 statement IDs (`../../../examples/bfs.source-observations.yaml` at the ArchEvolve
root: `bfs-td-frontier` 240, `bfs-td-row-bounds` 241, `bfs-td-neighbor` 242,
`bfs-td-parent-read` 243, `bfs-td-parent-cas` 247, `bfs-td-parent-store` 248,
`bfs-td-queue-append` 249) to `records/implementations/dx100-bfs-scalar.yaml`, with the
access chain queue → VertexOffsets → out_neighbors → parent (read, CAS, store) → lqueue.
Each statement maps to an (access pattern, step) pair, per the glossary term Statement.

## Acceptance

- `python3 -m swdb validate` passes.
- Every ID lands on the line Josh chose at `e4fc4af`.
