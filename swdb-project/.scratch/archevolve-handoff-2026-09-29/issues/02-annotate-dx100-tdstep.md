# 02 — Annotate DX100 TDStep with Josh's statement IDs

Created: 2026-09-29
**Type:** slice
**Status:** resolved
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

## Answer

2026-09-29: Added the seven IDs under the implementation's `extensions.statements`
with pinned revision, source line ranges, code, zero-based `(access pattern, step)`
pairs, and statement dependencies. Every code string was checked against the local
unmodified `e4fc4af` source at Josh's exact lines 240, 241, 242, 243, 247, 248, and 249.
The catalog now describes the frontier → CSR bounds → neighbors → parent read/CAS/store
chains. The row-bounds statement maps separately to the start read (identity) and the
end read (`u + 1`, affine), preserving one terminal expression per access pattern.
Queue insertion is a conditional thread-local stream whose successful CAS
dependency is retained; parent values do not supply queue storage addresses.

Assumption: Until Peter provides his format, the existing schema's experimental
`extensions` field carries the source annotation; this is source reading, not Peter's
feature extraction or an agreed external crosswalk.

Validation: `.venv/bin/python -B -m swdb validate` — 312 records valid.
`test_repo.py` and `test_view.py` — 13 passed, 1 skipped. No source bytes changed.
