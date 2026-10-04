# 57 — gem5 Extensa campaign target

Created: 2026-10-03
Updated: 2026-10-04 ET (a6 rerun with the ticket 62 certifier); 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D4, D7)
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
| a6 | 1.93 | 11 | plateau | certify now runs on every applied edit (ticket 62); every edit fails the strict layer (`range_bounds`) |

a5 (lease generation 455, load1 1.51) is the acceptance run: 4 iterations, all audits passed, no
candidate reached gem5; per class `no_gain`, no best, "single graph per class", simulated. a2's
`stopped_by_yanru` is the STOP-file mechanism used by the agent (its `stop_detail` says so). Each harness
fix is committed with its attempt. Summaries are in `records/campaign_summaries/` (team store).
Provider sessions ran one at a time; a1's five sessions overlapped ticket 58's a2 sessions on the same
login before the coordinator's hold; no login failure was observed.

**Rerun a6 (2026-10-04 ET, agent-decided under Yan-Ru's 2026-10-04 delegation; revisable).**

- Run: campaign `extensa-gem5-bfs-20261004-a6`, the a5 file with the new ID
  (`campaigns/extensa/extensa-gem5-bfs-20261004-a6.yaml`). mbit10 node 0, lease generation 456,
  07:01–08:57 ET, load1 1.52. Commit `d56d972` in `/data1/yanruj/ArchEvolve-extensa` (git
  bundle, not pushed). Raw output in `/data/yanruj/EvolveSWDB_runs/extensa/`.
- Session lock: the setup call waited about 50 minutes on `swdb-session.lock` while ticket 58
  a3 ran. The 5 s poll lost every gap between a3's back-to-back sessions; now 0.2 s (`3965ca1`).
- Result: 4 iterations, stop `plateau`, 11 counted calls, 1.93 lane-hours, peak disk 0.46 GB.
  Every candidate applied a contract edit and every audit passed.

| Class | Iterations | Best | Point ratio | Verdict |
|---|---:|---|---|---|
| kronecker | 4 | none | none (no candidate reached gem5) | `no_gain`, single graph per class, simulated |
| uniform_random | 4 | none | none | `no_gain`, single graph per class, simulated |

- Certification now runs on every applied edit (11 certification runs; iteration 2's patch did not
  apply). Every edit fails the matrix on the strict layer's `range_bounds`, and 3–5 of 16
  controls are rejected. The control-site refusal from a5 is gone.
- Cause: every edit initializes the range loop's `last_i` register to -1. The strict layer and
  Peter v1.1 §3.3 require 0. The library entry `library/intrinsics/dxc_range_loop.yaml` does
  not state the initial values, and the campaign's feedback says only "Certification failed a
  named check", without naming `range_bounds`. So the provider could not correct it within 4
  iterations.
- Open (proposal, not done): state `last_i_reg = 0` and `last_j_reg = -1` in the
  range-loop entry's caveats, and name the failing strict-layer check in campaign feedback.
- Summary: `records/campaign_summaries/extensa-gem5-bfs-20261004-a6.summary.yaml` (team store;
  host commit `d5eabbb`).
