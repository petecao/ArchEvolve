# 05 — Statement crosswalk

Created: 2026-09-29
**Type:** slice
**Status:** needs-info
**Blocked by:** Peter's confirmed report/source binding and offset-width answer
**Spec:** `../spec.md`

One row per `bfs-td-*` ID: file:line at `e4fc4af` → Peter's array name → Josh's `access-0N` →
SWDB access pattern and step → containing SWDB region IDs (from the kron18 profile
package's `ranked_regions` line ranges). Every row must resolve.

## Progress

2026-09-29: Ticket 02 is resolved. The seven statement IDs now bind the unchanged
DX100 `e4fc4afdf894f295442cef3604667a469fab8e62` TDStep source to explicit SWDB
access patterns and zero-based steps in `records/implementations/dx100-bfs-scalar.yaml`.
The row-bounds statement names both offset expressions, and the parent read, CAS,
store, and local queue append keep their source update/dependency semantics.

The available Kronecker package is
`bfs-native-pilot-20260925-dx10018-a1.kronecker.package.v1.1d44ec6b44f05000`.
Its public `handoff-message` projection supplies `content.ranked_regions`; the stored
package keeps these rows under `regions` and their rankings under `evidence.rankings`.
All seven statements belong to `function:bfs.cc:10396:92351720b886b03a`
(lines 227–259) and `loop:bfs.cc:10980:784979f83d8fbb08` (239–253).
The statements at lines 241–249 also belong to
`loop:bfs.cc:11105:4abc496fc9c3ddd0` (241–252).

The remaining prerequisite is Peter's source/build binding and offset-width answer:
the received v1.1 report names `DataLayoutAPI/benchmarks/gapbs/src/bfs.cc` and
64-bit `VertexOffsets`, while the pinned DX100 `SGOffset` is `int32_t`
(`apps/dx100/benchmarks/gapbs/src/graph.h:90`). The team must confirm which report
and Josh `access-0N` assignment apply to this exact source before completing every
crosswalk row. Ticket 01 remains human-owned and has no recorded reply. This ticket
stays `needs-info`; source similarity and matching graph size do not settle the binding.

2026-10-03: The current intrinsic specification pins the e4fc4af TDStep and statement mapping. Mapping delivery belongs to [typed-library ticket 01](../../typed-library-dx100-bfs-2026-10-03/issues/01-send-decision-note-and-mapping.md). The crosswalk remains pending until that human send receipt exists; no message is invented.
