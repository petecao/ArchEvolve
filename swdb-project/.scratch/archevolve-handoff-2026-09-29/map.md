# Map: hand SWDB's BFS work to the ArchEvolve pipeline

Created: 2026-09-29 17:40 ET
Updated: 2026-09-29 18:02 ET
**Type:** ticket map
**Status:** in-progress
**Spec:** [spec.md](spec.md)

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Send the team chat reply](issues/01-send-team-chat-reply.md) | ready-for-human | — |
| 02 | [Annotate DX100 TDStep](issues/02-annotate-dx100-tdstep.md) | resolved | — |
| 03 | [Record the T17 comparison](issues/03-record-t17-comparison.md) | claimed | retained ROI trace recheck running |
| 04 | [Retire the Workload view](issues/04-retire-workload-view.md) | resolved | — |
| 05 | [Statement crosswalk](issues/05-statement-crosswalk.md) | needs-info | 02, Peter |
| 06 | [Adapter from Peter's spec](issues/06-peter-spec-adapter.md) | needs-info | Peter |
| 07 | [PR to main](issues/07-pr-to-main.md) | ready-for-human | 02, 03, 04 |

## Context pointers

- 2026-09-29: slide 9 and speaker notes for the 2026-09-30 meeting now put the handoff
  first (`weeklogs/2026-09-30/slides/evolveswdb-week-02-v4.pptx`).
- 2026-09-29: T17's strategy reuses the DX100 authors' `TDStepMAA`; see
  `records/proposals/bfs-campaign-preparation-20260925-a1.dx100-instructions.yaml:156`.
- 2026-09-29: annotation binds seven statement IDs to eight terminal array accesses;
  T17's pre-existing frozen protocol is preserved while public comparison qualification
  rechecks its retained trace. Human and Peter-dependent tickets retain their ownership.
