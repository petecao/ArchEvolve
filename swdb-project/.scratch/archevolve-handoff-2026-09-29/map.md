# Map: hand SWDB's BFS work to the ArchEvolve pipeline

Created: 2026-09-29 17:40 ET
Updated: 2026-09-29 23:20 ET
**Type:** ticket map
**Status:** in-progress
**Spec:** [spec.md](spec.md)

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| 01 | [Send the team chat reply](issues/01-send-team-chat-reply.md) | ready-for-human | — |
| 02 | [Annotate DX100 TDStep](issues/02-annotate-dx100-tdstep.md) | resolved | — |
| 03 | [Record the T17 comparison](issues/03-record-t17-comparison.md) | resolved | — |
| 04 | [Retire the Workload view](issues/04-retire-workload-view.md) | resolved | — |
| 05 | [Statement crosswalk](issues/05-statement-crosswalk.md) | needs-info | Peter's report/source binding and offset-width answer |
| 06 | [Adapter from Peter's spec](issues/06-peter-spec-adapter.md) | needs-info | 05, Peter's spec format, confirmed hardware candidate |
| 07 | [PR to main](issues/07-pr-to-main.md) | ready-for-human | — |

## Context pointers

- 2026-09-29: slide 9 and speaker notes for the 2026-09-30 meeting now put the handoff
  first (`weeklogs/2026-09-30/slides/evolveswdb-week-02-v4.pptx`).
- 2026-09-29: T17's strategy reuses the DX100 authors' `TDStepMAA`; see
  `records/proposals/bfs-campaign-preparation-20260925-a1.dx100-instructions.yaml:156`.
- 2026-09-29: annotation binds seven statement IDs to eight terminal array accesses;
  T17's pre-existing frozen protocol is preserved. Human and Peter-dependent tickets
  retain their ownership.
- 2026-09-29 21:46 ET: [ticket03's Answer](issues/03-record-t17-comparison.md#answer)
  records both completed public gain decisions: uniform18 3.0805868937958523× and
  kronecker18 2.7989783693430432× primary BFS ROI speedup. Source-0/repetition-0
  simulated author-path reuse has joint hardware/software attribution. The node1
  retry exited 0; both actual records were synced in `cadf16b2fe9a945ebfc066eeccd78357a9ad05a8`
  after validation of 352 records. See `records/comparison_results/bfs-t17-handoff-20260929-a1.{uniform18,kronecker18}.yaml`.
  All ten provider tickets and the independent whole-diff review are complete.
  Standards' one P3 duplication judgement was repaired at `8889e175`; both
  independent rechecks are clear. Final workflow QA passed 45 cases in 673.40 s.
  The PR draft is ready for human delivery. See the
  [review report](../rewrite-provider-codex-2026-09-29/validation/code-review.md).
