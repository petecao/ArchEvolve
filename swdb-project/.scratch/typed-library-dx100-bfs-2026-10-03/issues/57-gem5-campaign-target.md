# 57 — gem5 Extensa campaign target

Created: 2026-10-03
Updated: 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D4, D7)
**Type:** slice
**Status:** resolved
**Blocked by:** 53, 54, 55 (29 resolved)
**Spec:** `../spec.md`
**Needs go-ahead:** Granted. Yan-Ru approved mbit10 dispatch on 2026-10-03. One campaign within its budgets is one dispatch (Q62), and actual lane admission and receipts are still required.

**What to build:** An Extensa campaign can run BFS on DX100 in gem5.

## Acceptance

- [ ] Campaign file `campaigns/extensa/extensa-gem5-bfs-<date>-a1.yaml` is committed. Its target is `dx100_gem5` and its baseline is the fork's scalar TDStep. Its classes use `bfs-20260928-kronecker18-s0.cf4283236c5cb50c` and `bfs-20260928-uniform18-s0.8c7e69dfa516e53c`, with source 0, 1 run, D5 default budgets, `regions: query` and allowed tiers shared and experimental.
- [ ] One gem5 baseline evaluation per class serves every candidate artifact, and comparisons are reported as point ratios.
- [ ] Each candidate artifact's DX100 session begin is checked to run inside the timed BFS call (`bfs.complete_call.v1`). A fixture where it runs outside is refused.
- [ ] The dispatch preflight admits each gem5 job against the lane's memory node (about 36 GiB per run) before it starts.
- [ ] The acceptance campaign finishes within its budgets on one socket lane. Its `campaign_summary` is complete and copied to the team store, and every result is labeled "single graph per class" and simulated.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-04 06:05 ET by the agent under Yan-Ru's 2026-10-03 mbit10 dispatch approval (Q62).
Follow-up: [62](62-spelling-independent-certification-controls.md) (certification blocks contract edits).

**Built (Mac).** `swdb/campaign_targets.py` `Gem5Adapter` (target `dx100_gem5`):
- One frozen controlled-simulator protocol per campaign, copied from ticket 29's
  `typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0` (T17 v2 treatment, read-only and
  L3 companion cases), campaign differences text.
- One baseline evaluation per class (compile, execute, aggregate) serves every candidate artifact;
  comparisons are point ratios (`lower = ratio`, spread 0).
- Before certification, `session_begin_problem` refuses a candidate whose `__dxc_session_begin` is
  outside `DOBFS` (the call `bfs.complete_call.v1` times); an edit without a contract is refused (the
  protocol's read-only case needs one). Then `swdb certify`, guest builds, L3 companions, the timed run.
- `dispatch_preflight.check` admits each gem5 run against the lane's memory node at 36 GiB.
- `swdb campaign --baselines-only` runs setup and the baselines without a provider call.
- Legality facts: eight `legality:contract.bfs_read_offload:<clause>` statement facts on
  `dx100-bfs-scalar` (statements 241, 243, 240), each citing certification.1e4397e31d594245bc10bd80ff2107f5
  (ticket 18), the ticket 28 companion evaluations or the ticket 17 contract and its review; the site
  finder now picks `dx100-bfs-scalar/TDStep:240-243` on the real records.
- Tests: `tests/test_extensa_targets.py` (single baseline per class, point ratios, 36 GiB admission,
  knobs and header, session-begin refusals, no-contract refusal, baselines-only and resume) and
  `tests/test_site_finder.py` (repository facts select the region).

**Runs (mbit10 node 0, `/data1/yanruj/ArchEvolve-extensa`, raw output under `/data/yanruj/EvolveSWDB_runs/extensa/`).**

| Attempt | Lane-h | Counted calls | Stop | Cause |
|---|---:|---:|---|---|
| a1 | 0.02 | 5 | plateau | rewrite role schema rejected by the API (free-form `knobs`) |
| a2 | 1.37 | 3 | STOP file (agent) | both baselines evaluated; audit refused reads of absent `best/`, `FEEDBACK.json` |
| a3 | 0.29 | 5 | plateau | wrong hunk counts (git apply), one audited `sed` refusal, a no-contract edit |
| a4 | 0.34 | 5 | plateau | edits never began a DX100 session (workspace lacked the lowering header) |
| a5 | 0.86 | 11 | plateau | every applied contract edit: certify lacks control site `shared_context` |

a5 (lease generation 455, load1 1.51) is the acceptance run: 4 iterations, all audits passed, no
candidate reached gem5; per class `no_gain`, no best, "single graph per class", simulated. a2's
`stopped_by_yanru` is the STOP-file mechanism used by the agent (its `stop_detail` says so). Each harness
fix is committed with its attempt. Summaries are in `records/campaign_summaries/` (team store).
Provider sessions ran one at a time; a1's five sessions overlapped ticket 58's a2 sessions on the same
login before the coordinator's hold; no login failure was observed.
