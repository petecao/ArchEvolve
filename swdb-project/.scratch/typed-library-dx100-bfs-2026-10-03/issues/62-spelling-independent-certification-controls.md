# 62 — Spelling-independent BFS certification controls for campaign rewrites

Created: 2026-10-04 ET (by ticket 57)
**Type:** slice
**Status:** needs-triage
**Blocked by:** —
**Spec:** `../spec.md`

**What to build:** `swdb certify` can certify a provider-written BFS read-offload rewrite whose
text differs from ticket 20's patch.

## Finding (ticket 57, 2026-10-04)

The gem5 acceptance campaign `extensa-gem5-bfs-20261004-a5` (summary in
`records/campaign_summaries/extensa-gem5-bfs-20261004-a5.summary.yaml`) produced six contract edits that
applied and passed the session-begin check. `swdb certify` aborted every one with "candidate source lacks
a unique negative-control mutation site: shared_context", before running the matrix. The BFS negative
controls are exact-text mutations of ticket 20's spelling (`swdb/certification.py` `_rewrite_control`,
for example `dxc_context c=swdb_contexts[omp_get_thread_num()];`). Ticket 58 reported the same caveat.
Until this changes, no independently written contract edit can be certified, so an Extensa gem5 campaign
cannot reach gem5 evaluation with a contract edit.

## Options (agent proposal)

1. Controls as source-level probes from the contract's predicates (the ported
   `swdb/extensa/probes.py`, D1), which bind to call operands rather than to text.
2. Controls located by the intrinsic calls the candidate makes (for example the context argument of
   each `__dxc_*` call), with a refusal only when the call itself is absent.
3. Name the required spellings in the contract so a provider can follow them (weakest; leaks the
   control sites to the provider).

The evaluator's pass rule and the control set stay unchanged; only how a control finds its site changes.
