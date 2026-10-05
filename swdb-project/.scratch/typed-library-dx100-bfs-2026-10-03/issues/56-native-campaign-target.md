# 56 — Native-CPU Extensa campaign target for BFS

Created: 2026-10-03
Updated: 2026-10-05 15:00 ET (a8 addendum: best certified and re-evaluated, ticket 75); 2026-10-05 10:45 ET (a8 erratum, ticket 74); 2026-10-05 10:00 ET (a8 result: uniform gain, uncertified; Kronecker inconclusive); 2026-10-05 03:15 ET (a7 erratum; a8 pre-registered); 2026-10-05 02:50 ET (a7 addendum: speed rule ci_width.v2, uniform no_gain at plateau, Kronecker baseline_unstable); 2026-10-04 23:10 ET (a6 addendum: CI-width gate pilot, both classes baseline_unstable, follow-up 72); 2026-10-04 21:30 ET (isolation test a5 result; closed baseline_unstable for Kronecker, follow-up 66); 2026-10-04 12:40 ET (isolation test pre-registered); 2026-10-04 12:15 ET (campaign a4, Answer update); 2026-10-04 10:55 ET (evaluator v2 pilot, Answer update); 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D3, D4, D9)
**Type:** slice
**Status:** resolved
**Blocked by:** 51, 53, 54, 55
**Spec:** `../spec.md`
**Needs go-ahead:** Granted. Yan-Ru approved mbit10 dispatch on 2026-10-03. One campaign within its budgets is one dispatch (Q62), and actual lane admission and receipts are still required.

**What to build:** An Extensa campaign can run BFS on native CPU.

## Acceptance

- [ ] A Kronecker scale-22 workload record is registered through the public workflow. It uses the DX100 GAPBS converter at `e4fc4afdf894f295442cef3604667a469fab8e62` with `-g 22 -k 16` and the same normalization as `bfs-20260925-kronecker18.48de8267ac2098d5`. The uniform class uses `bfs-20260925-uniform22.f23b09bb0c0601b5`.
- [ ] Campaign file `campaigns/extensa/extensa-native-bfs-<date>-a1.yaml` is committed. Its target is `native_cpu`, with `base_source: fork_scalar_tdstep` and both baselines. It uses D3's protocol, the D5 default budgets, `regions: query` and allowed tiers shared and experimental.
- [ ] The A/A pilot runs first on both graphs. If it stops with `baseline_unstable`, the summary is committed and a needs-info ticket proposes a new protocol for Yan-Ru, with no threshold change.
- [ ] Each candidate artifact is timed in its own paired blocks against both baselines, as separate comparisons. Selection uses the fork scalar TDStep comparison (Q61), and the upstream DO-BFS comparison is reported beside it.
- [ ] The acceptance campaign finishes within its budgets on one mbit10 socket lane through `socket_lane.sh`, with load and commit recorded. Its `campaign_summary` is complete and copied to the team store, and every result is labeled "single graph per class" and measured.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-04 06:05 ET by the agent under Yan-Ru's 2026-10-03 mbit10 dispatch approval (Q62).
The native protocol itself is blocked: follow-up [61](61-native-scale22-protocol.md) (needs-info).

**Built (Mac).** `swdb/campaign_targets.py` `NativeAdapter`, selected by `swdb campaign` when the target
is `native_cpu` and no `--fixture` is given:
- One frozen native protocol per baseline role (`<campaign>.protocol.fork_scalar_tdstep`,
  `.upstream_do_bfs`); a frozen protocol names one baseline build (dx100_scalar_func vs gapbs_native).
  D3 flags, 10 repetitions, sources [0, 1234, 7777], 1 thread, lane frozen from the verified lane.
- A/A pilot: each baseline timed against itself on each class (`swdb evaluate-pair`, then
  `compare-evaluations`); any spread above 0.1 stops with `baseline_unstable`.
- Each candidate artifact gets its own paired block against each baseline, compared separately;
  selection uses the `base_source` (fork scalar TDStep) comparison, upstream reported beside it (Q61).
- Candidate artifacts: scalar-only snapshot `bfs-dx100-scalar-only-20260929-a1.source` plus the
  provider patch (`git apply --recount`), class knobs as `SWDB_KNOB_*` defines, protections checked,
  a tagged proposal and candidate record. Child commands inherit the campaign tags
  (`SWDB_EXTENSA_CAMPAIGN`, `swdb/workflow.py`).
- Native timed blocks refuse while the other socket's lease is held by an Extensa gem5 job (marker
  under `<runs root>/extensa/active-lanes/`).
- Tests: `tests/test_extensa_targets.py` (native: two protocols, four separate paired blocks, fork
  selection with upstream beside it, pilot stop with zero calls, scale-22 stop, lane conflict).

**Run (mbit10, separate clones `/data1/yanruj/ArchEvolve-extensa{,-native}`, git bundles, not pushed).**
- Workloads (node 1, lease generation 510, 02:44-02:47 ET, load1 2.02):
  `bfs-20261004-kronecker22.3dc69be403db57e9` (converter e4fc4af, `-g 22 -k 16`, sources 0/1234/7777)
  and `bfs-20261004-uniform22.facb16e6260c3a82` (the f23b09bb graph files with D3's sources; f23b09bb
  registers source 2796003 only, which D3's protocol cannot use).
- Campaign `extensa-native-bfs-20261004-a1` (node 1, generation 511, 02:48 ET, load1 2.57): stopped at
  setup, `infrastructure_failure`: the scale-22 graphs exceed the native evaluator's materialization
  limits (2 M vertices, 32 M directed edges). No pilot block, no provider call, 0 lane-hours.
  Summary `records/campaign_summaries/extensa-native-bfs-20261004-a1.summary.yaml` (team store).

**Assumptions (agent-decided, revisable).** One protocol per baseline role (not one per campaign);
the uniform class uses a new three-source registration of the same graph; the campaign stops rather
than raising the evaluator's limits (an evaluator change is Yan-Ru's call, ticket 61).

### Update 2026-10-04 10:55 ET: A/A pilot under native evaluator v2 (tickets 61, 63)

Ticket 61 was decided as option 1 (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable) and
implemented in ticket 63: native evaluator `swdb.native.evaluator.scalable.v2` with the compiled verifier
`swdb.bfs.structural.compiled.v2`. D3/D4 are unchanged. Run on mbit10 from the clone
`/data1/yanruj/ArchEvolve-native` (git bundles, not pushed), runs root `/data/yanruj/EvolveSWDB_runs`
(`/data1` had 40 GB free), node 1 through `socket_lane.sh` (Memacc checkout current with its origin), each
time with `--baselines-only` so no provider call could run before the shared Codex login has a session lock.

- `extensa-native-bfs-20261004-a2` (generation 516, 09:08 ET, commit 36e7544): first pilot block passed
  correctness on every trial; it stopped with `infrastructure_failure` at the upstream A/A block ("actual
  build differs from frozen settings"). Ticket 56's adapter timed the upstream baseline as the candidate side
  of a protocol whose candidate build is the DX100 fork's. Fixed in fd983a6: roles whose builds differ get
  an A/A protocol `<campaign>.protocol.<role>.aa` with the baseline build on both sides.
- `extensa-native-bfs-20261004-a3` (generation 517, 09:31-10:31 ET, load1 1.1-2.1, commit fd983a6): all four
  pilot blocks completed, every trial verified by the compiled verifier. Stop reason **`baseline_unstable`**.
  Max spread per class and role: Kronecker fork 0.161, Kronecker upstream 0.012, uniform fork 0.057, uniform
  upstream 0.134. 0 provider calls, 0.99 lane-hours, 2.36 GB peak disk. Summary
  `records/campaign_summaries/extensa-native-bfs-20261004-a3.summary.yaml` (a2's beside it).
- Main cause found: source 7777 is isolated in the Kronecker 22 graph; its ROI is only initialization,
  bimodal at about 49 or 58 ms. Per D3, no threshold changed; the protocol follow-up is needs-info ticket
  [64](64-native-scale22-pilot-unstable.md).

No candidate was timed, so there is no verdict per class ("single graph per class", measured: not reached).

### Update 2026-10-04 12:15 ET: campaign a4 (ticket 64 workloads, per-class gate)

Ticket 64 (agent-decided under Yan-Ru's delegation; revisable; 0.1 threshold unchanged) re-registered both
scale-22 workloads with the recorded source policy (Kronecker sources 0, 1234, 7778; 7777 had out-degree 0;
uniform unchanged), made the A/A gate per class, and admitted native blocks beside another campaign's gem5 job
when the campaign file approves it (`approval.gem5_other_socket`, other socket recorded per block).

`extensa-native-bfs-20261004-a4` ran at full scope (provider calls allowed through the Codex session lock) on
node 1 (lease generation 522, 10:59-12:01 ET, load1 1.8-3.6, commit 67c671c) while gem5 campaign
`extensa-gem5-bfs-20261004-a7` held node 0 (recorded for every pilot block). Every trial passed the compiled
verifier. Pilot max spread per class and role:

| Class | Fork scalar TDStep | Upstream DO-BFS | Class result |
|---|---|---|---|
| Kronecker 22 (sources 0/1234/7778) | 0.225 | 0.153 | baseline_unstable |
| Uniform 22 (sources 0/1234/7777) | 0.147 | 0.014 | baseline_unstable |

Both classes failed, so the campaign stopped with **`baseline_unstable`**: 0 iterations, 0 provider calls,
1.04 lane-hours, 2.68 GB peak disk. Summary `records/campaign_summaries/extensa-native-bfs-20261004-a4.summary.yaml`.
No candidate was timed, so no class has a verdict about a candidate ("single graph per class", measured: not reached).

What the per-repetition data show (no trial removed): upstream DO-BFS switches between two regimes about 15%
apart (Kronecker 157.8 / 134.6 ms; uniform 143.5 / 125.1 ms in ticket 64's diagnostics). In a4 the uniform
upstream blocks stayed in one regime (0.014), while the Kronecker upstream blocks switched (0.15); in a3 it was
the reverse. The fork baseline (0.7-1.5 s ROI) spreads 0.05-0.22 without a clear regime. a4 ran beside the a7
gem5 job and a3 partly did; whether the other socket's work drives the regimes is untested. Pinning and membind
are already in force, and no further legitimate control is available without counters or frequency control
(ticket 64). Re-running in the hope of a quieter host would select on the outcome, so no further attempt was
made; a protocol change is Yan-Ru's.

### Pre-registration 2026-10-04 12:40 ET: one isolation test (written before the run)

Decision by the coordinating agent under Yan-Ru's delegation (agent-decided; revisable).

- **Hypothesis.** A gem5 job on the other socket drives the two speed regimes seen in a3/a4.
- **Test.** Exactly one A/A pilot, both classes and both roles, under the same frozen protocol settings as a4
  (evaluator v2, D3 sources with ticket 64's recorded replacement, 10 paired repetitions, 1 thread, `-O3`),
  as campaign `extensa-native-bfs-20261004-a5` on node 1. The a4 approval flag (`gem5_other_socket`) is off.
  The campaign file sets `protocol.isolation: other_socket_free`: every native block starts only while node 0's
  lease is released (bounded wait, 2 h), and the other socket's state and the host load are recorded at the
  start and end of every block. The run script records other users and load at the start and end.
- **Start rule.** Start only after gem5 campaign a7 has finished and node 0's lease is released, checked
  every 15 min; a7 is not touched.
- **Decision rule.** Gate unchanged: every A/A spread at most 0.1 per class.
  - Both classes pass: the same run continues straight into the full-scope campaign (Codex calls through the
    session lock), isolated the same way.
  - A class fails: it gets `baseline_unstable`; ticket 56 closes with that Answer; a needs-info ticket proposes
    protocol options to Yan-Ru.
- **The result is reported whatever it shows. No further reruns.**

### Result 2026-10-04 21:30 ET: isolation test a5. Kronecker is `baseline_unstable` and uniform is `inconclusive`. Ticket closed; follow-up [66](66-native-protocol-after-isolation-test.md)

**Run.** Campaign `extensa-native-bfs-20261004-a5`:

- Host: mbit10 node 1, entered through `socket_lane.sh`, lease generation 523.
- Time: 18:04–20:24 ET (`2026-10-04T22:04:35Z`–`2026-10-05T00:24:23Z`).
- Load: load1 1.0–2.4. Users: `yanruj` only, at start and at end.
- Code: commit `aa245de` in `/data1/yanruj/ArchEvolve-native` (branch `t56-iso`).
- Launch: a waiter checked node 0 every 15 min and started the run when a7 released node 0. Node 0
  stayed released for every block. The adapter (`NativeAdapter.isolated`) enforces this, and the
  pilot blocks record it at start and end.
- Governor and turbo files: absent on this host.
- Lane exit code: 1. This comes from the run script's last `pgrep` finding no codex process. The
  campaign itself exited 0.

**A/A pilot (pre-registered gate: every spread at most 0.1).** Max relative spread over the three
sources, baseline side / candidate side, with a4 (other socket held by gem5 a7) beside it:

| Class | Role | a5 spread (isolated) | a4 spread (gem5 on node 0) | a5 class result |
|---|---|---|---|---|
| Kronecker 22 | fork scalar TDStep | **0.131** (0.131/0.108/0.083 and 0.081/0.098/0.088) | 0.225 | `baseline_unstable` |
| Kronecker 22 | upstream DO-BFS | 0.008 | 0.153 | |
| Uniform 22 | fork scalar TDStep | 0.084 | 0.147 | passed |
| Uniform 22 | upstream DO-BFS | 0.012 | 0.014 | |

**Campaign.** One class failed the gate, so per the pre-registration Kronecker gets
`baseline_unstable` and is not timed. The uniform class went straight on to full scope:

- Stop: `plateau`. 4 iterations, 5 counted provider calls (setup 1 and 4 rewrites; no repair or
  synthesis call).
- Use: 2.29 lane-hours and 6.04 GB peak disk. Raw output is in `/data/...` because `/data1` had
  40 GB free.

| Class | Iterations | Best | Measured candidates (ratio vs fork scalar TDStep, 95% CI, max spread) | Upstream DO-BFS beside it | Verdict |
|---|---:|---|---|---|---|
| kronecker | 0 | none | not timed | — | `baseline_unstable`, single graph per class, measured |
| uniform_random | 4 | none | it1.a0: 1.284 [1.270, 1.307], spread 0.117; it3.a0: 1.318 [1.291, 1.355], spread 0.159 | 0.127 and 0.133 (about 8× slower than upstream) | `inconclusive`, single graph per class, measured |

- Both measured candidates are scalar edits without a contract (`uncertified`). Each comparison is
  `inconclusive` only because a spread exceeds 0.1. There is no `gain`, so there is no best
  candidate to re-certify.
- Iteration 2's patch did not apply.
- Iteration 4 named `operation.gather_staging_executor`, which is outside the campaign's contracts,
  so it was refused as `provider_output_invalid`.

**Answer to the pre-registered hypothesis.**

- **Upstream DO-BFS.** With the other socket free, the pilot spreads fell from 0.153 to 0.008
  (Kronecker) and stayed low (uniform, 0.012). This fits the hypothesis. But later in the same
  isolated run, the uniform upstream baseline blocks of iterations 1 and 3 spread 0.132–0.136 on
  every source. Upstream's two speed regimes therefore occur without any gem5 job on node 0.
- **Fork scalar TDStep.** The spread shrank (0.225 to 0.131 and 0.147 to 0.084) but still fails on
  Kronecker. In the uniform candidate blocks it reached 0.055–0.133 on the baseline side and
  0.104–0.159 on the candidate side.
- **Conclusion.** Other-socket isolation reduces the spread. It is not enough for the 0.1 range
  gate at 10 repetitions on this host.

**Review findings (a5 ran on pre-review code `aa245de`).** None affects a5:

- Leakage scan of repaired patches (`d895705`): a5 made no repair call. Both measured patches also
  pass the scan on the fixed code.
- Synthesis usage-limit handling (`d895705`): there was no synthesis call.
- The `certify` fail-open and the control matching (`f304e5c`, `8040609`): no candidate was
  certified or reached certification.
- `_evaluate` ignoring `approval.gem5_other_socket` (`f304e5c`): the approval was off in a5, and
  the refusal path is the same without it.
- The unfixed `int32_t` parent cast in the v2 driver: neither patch changes the parent element
  type. The pilot timings are baseline-only.

**Records.**

- Summary `records/campaign_summaries/extensa-native-bfs-20261004-a5.summary.yaml` (team store). It
  was copied from the host with matching sha256 `f82f0875…`.
- Compact block evidence: [`evaluation/native-a5-isolation-2026-10-04.json`](../evaluation/native-a5-isolation-2026-10-04.json).

**Closed** as `baseline_unstable` (Kronecker), per the pre-registration. No rerun was made. The
protocol options for Yan-Ru are in needs-info ticket [66](66-native-protocol-after-isolation-test.md).

### Addendum 2026-10-04 23:10 ET: campaign a6 under the CI-width gate. Both classes are `baseline_unstable`; follow-up [72](72-native-upstream-two-level-trials.md)

**Rule.** Ticket 66 was decided by Yan-Ru ("go with the recommendation") and its gate was pre-registered
before this run (commit `84e44e1`): relative 95% CI width at most 0.05 from a circular block bootstrap over
20 repetitions (blocks of 4), and an A/A interval strictly inside (1/1.05, 1.05). Candidates would have been
timed with native evaluator v3 (ticket [71](71-native-evaluator-v3-parent-width.md)).

**Run.** Campaign `extensa-native-bfs-20261004-a6` (`campaigns/extensa/extensa-native-bfs-20261004-a6.yaml`):

- Host: mbit10 node 1 through `socket_lane.sh` (Memacc checkout `76cca35`, equal to its origin), lease
  generation 524. The node 0 and legacy leases were released at launch and at the start and end of every
  block.
- Time: 21:06-23:04 ET (`2026-10-05T01:06:16Z`-`03:04:45Z`). Load1 1.3-2.3. Users: `yanruj` only.
- Code: commit `ce42a45` in `/data1/yanruj/ArchEvolve-native` (branch `t56-a6`, from a git bundle).
- Runs root `/data/...` (`/data1` had 40 GB free). Governor and turbo files: absent.
- Lane exit code 1 comes from the run script's last `pgrep` (as in a5); the campaign exited 0.

**A/A pilot (pre-registered gate).** Ratio, 95% CI, relative width; the old range statistic is shown only for
comparison.

| Class | Role | Ratio [95% CI] | CI width / ratio | Inside (0.952, 1.05)? | Range (old statistic) | Pass? |
|---|---|---|---|---|---|---|
| Kronecker 22 | fork scalar TDStep | 0.983 [0.968, 1.007] | 0.040 | yes | 0.131 | **pass** |
| Kronecker 22 | upstream DO-BFS | 1.002 [0.927, 1.052] | 0.125 | no | 0.180 | **fail** |
| Uniform 22 | fork scalar TDStep | 0.998 [0.991, 1.010] | 0.019 | yes | 0.103 | **pass** |
| Uniform 22 | upstream DO-BFS | 0.999 [0.954, 1.047] | 0.093 | yes | 0.162 | **fail** |

**Result.** A class passes only if both roles pass, so both classes are `baseline_unstable` and the campaign
stopped with `baseline_unstable` before iteration 1: 0 iterations, 0 provider calls, 1.97 lane-hours, 0.33 GB
peak disk (v3 kept 3 parent copies per side instead of 60). No candidate was timed, so there is no gain and
nothing to re-certify. Summary `records/campaign_summaries/extensa-native-bfs-20261004-a6.summary.yaml`
(team store; sha256 `1ba2a707…` on host and Mac). Compact evidence:
[`evaluation/native-a6-ci-gate-2026-10-04.json`](../evaluation/native-a6-ci-gate-2026-10-04.json).

**What the data show (descriptive, not verdicts).**

- The fork scalar TDStep baseline, the selection baseline (Q61), now passes in both classes: widths 0.040 and
  0.019, although its range spread (0.131 and 0.103) would fail the old gate.
- Upstream DO-BFS fails because of its trial-level bimodality, not slow drift. On both sides of each A/A
  block, every source's 20 times sit on two levels about 15% apart (Kronecker 135/159 ms, uniform 124/143
  ms), with 7 to 12 of 20 trials on the slow level, switching every few repetitions. With the levels mixed
  about half and half, each side's median falls on either level, so the per-source A/A ratio jumps to 0.87,
  0.93, 1.08 or 1.15. Pairing cannot cancel this, because the two sides of a pair land on different levels
  independently.
- No rerun was made. The protocol question is Yan-Ru's: needs-info ticket
  [72](72-native-upstream-two-level-trials.md).

### Addendum 2026-10-05 02:50 ET: campaign a7 under speed rule ci_width.v2. Kronecker is `baseline_unstable`; uniform is `no_gain` at plateau

**Rule.** Ticket [72](72-native-upstream-two-level-trials.md), decided 2026-10-04 23:15 ET under Yan-Ru's delegation
and pre-registered before the run (commit `3147b31`): the same per-comparison CI-width rule as a6, but the A/A
pilot gates each class on the fork scalar TDStep (the selection baseline) only. Upstream DO-BFS is reported beside
it with its own verdict and a per-side level mix. a6 is not re-judged.

**Run.** Campaign `extensa-native-bfs-20261004-a7`:

- Host: mbit10 node 1 through `socket_lane.sh` (Memacc `76cca35`, equal to its origin), lease generation 525.
  The node 0 and legacy leases were released at launch and at the start and end of every block.
- Time: 2026-10-04 23:33 to 2026-10-05 02:43 ET (`03:33:13Z`-`06:43:57Z`). Load1 1.3-2.5. Users: `yanruj` only.
- Code: commit `8aea84f` (branch `t56-a7`, from a git bundle). Runs root `/data/...`.
- Lane exit code 1 comes from the run script's last `pgrep`; the campaign exited 0.

**A/A pilot (pre-registered gate).**

| Class | Role | Ratio [95% CI] | CI width / ratio | Gates? | Block passes? |
|---|---|---|---|---|---|
| Kronecker 22 | fork scalar TDStep | 1.006 [0.985, 1.041] | 0.055 | yes | **no** |
| Kronecker 22 | upstream DO-BFS | 1.000 [0.999, 1.001] | 0.001 | no | yes |
| Uniform 22 | fork scalar TDStep | 1.004 [0.998, 1.011] | 0.014 | yes | **yes** |
| Uniform 22 | upstream DO-BFS | 1.000 [1.000, 1.001] | 0.002 | no | yes |

Kronecker is therefore `baseline_unstable` (in a6 the same fork block measured 0.040). Uniform was timed.

Upstream level mix in the pilot (reporting only): every upstream source was on one level except uniform
baseline source 0 (19 of 20 slow). The regimes that broke a6's upstream blocks did not recur in these blocks.

**Campaign (uniform only).**

| It. | Candidate | Fork scalar TDStep: ratio [CI], width, verdict | Upstream DO-BFS: ratio [CI], width, verdict | Upstream slow share (baseline / candidate) |
|---|---|---|---|---|
| 1 | rejected: the patch changed the protected verifier region of `bfs.cc` | — | — | — |
| 2 | `it2.uniform_random.a0`, uncertified (no contract) | 1.004 [0.995, 1.017], 0.022, `no_gain` | 0.089 [0.085, 0.093], 0.092, `inconclusive` | 0.40 / 0.00 |
| 3 | none: the rewriting call failed (see below) | — | — | — |
| 4 | none: the rewriting call failed (see below) | — | — | — |

- Stop: `plateau` after 4 iterations. 5 counted provider calls (setup 1, rewriting 4), 0 uncounted. 3.15 lane-hours,
  0.52 GB peak disk.
- Per class: Kronecker `baseline_unstable`; uniform `no_gain`, no best, nothing faster listed. Label "single
  graph per class", measured. **No gain**, so nothing was re-certified (certify 1.3 was merged on the Mac and
  stood ready).
- **Provider outage counted against the budget.** Calls 4 and 5 (iterations 3 and 4) ended after about 3.5 s
  with the Codex error "Selected model is at capacity". The harness counted them as failed rewriting calls
  (`provider_output_invalid`) instead of uncounted usage-limit pauses (D7), and they completed the 4-iteration
  plateau. Per the pre-registration there is no rerun. The classification is a harness defect to fix before the
  next campaign.

Summary `records/campaign_summaries/extensa-native-bfs-20261004-a7.summary.yaml` (team store; sha256 `93935b26…`
on host and Mac). Compact evidence:
[`evaluation/native-a7-ci-gate-v2-2026-10-05.json`](../evaluation/native-a7-ci-gate-v2-2026-10-05.json).

**Erratum 2026-10-05 03:15 ET (ticket [73](73-provider-capacity-and-protected-regions.md)).** a7's plateau was
reached partly through two miscounted calls. Calls 4 and 5 failed because Codex was at capacity, a provider-side
outage. Under D7 they should have been uncounted pauses, not counted failed rewrites ending iterations 3 and 4
as `provider_output_invalid`. Uniform's `no_gain` is therefore **budget-contaminated**: the campaign spent two
of its four plateau iterations without a rewrite. Its measured comparison (iteration 2) stands as measured. The
a7 records and summary are left unedited. Iteration 1's rejection is also explained: REGIONS.json numbered the
full fork source, and its lines 240-241 fall inside `BFSVerifier` in the scalar-only workspace copy (ticket 73).

### Pre-registration 2026-10-05 03:15 ET: native campaign a8 (written before the run)

(Committed in `b45c56a` at 03:18 ET; a8 started at 03:19 ET. The campaign file's own comment says 03:20 ET,
written ahead of the clock; the commit time is authoritative.)

Decision by the coordinating agent under Yan-Ru's delegation (agent-decided; revisable).

- **Why a8.** a7's budget accounting was invalid because of an infrastructure bug (ticket 73), not because of
  its outcome. **a8 is the last native run under speed rule `swdb.speed_rule.ci_width.v2`**, and its result is
  reported whatever it shows.
- **Rule and protocol.** Exactly ticket 72's pre-registration: per-comparison CI-width gate 0.05 from the
  circular block bootstrap (20 repetitions, blocks of 4, 2000 resamples, seed 20260925); A/A pilot gating each
  class on the fork scalar TDStep only (CI width at most 0.05 and inside (1/1.05, 1.05)); upstream DO-BFS
  reported with its own verdict and level mix; gain only if the lower bound is strictly above 1.05; selection on
  the fork comparison. Evaluator v3. A fresh A/A pilot; a7's pilot is not reused.
- **Campaign file** `campaigns/extensa/extensa-native-bfs-20261005-a8.yaml`: the same as a7 except its ID and the
  harness from ticket 73 (capacity is an uncounted pause with backoff, at most 1 h, then
  `infrastructure_failure`; `PROTECTED.json` and workspace region lines). D5 default budgets: at most 8
  iterations, plateau 4, 24 lane-hours, 3 calls per iteration plus 1 setup call through the Codex session lock,
  20 GB disk, 1 lane. `isolation: other_socket_free`.
- **Host.** mbit10 node 1 through MemAcc's `socket_lane.sh` from an up-to-date checkout, started only while the
  node 0, node 1 and legacy leases are released; runs root by the 20 GB rule.
- **No rerun chosen by outcome.** As before, an `infrastructure_failure` before the first pilot block completes
  may be fixed and restarted once. A stop for persistent provider capacity is reported as such.
- **A class with a `gain`:** its best candidate is re-certified on the Mac with `swdb certify` 1.3 if it used a
  contract (verdict recorded beside the in-campaign one); a best without a contract is reported as `uncertified`.

### Result 2026-10-05 10:00 ET: campaign a8. Uniform has a `gain` (uncertified); Kronecker is `inconclusive`

**Run.** Campaign `extensa-native-bfs-20261005-a8`, as pre-registered above:

- Host: mbit10 node 1 through `socket_lane.sh` (Memacc `76cca35`, equal to its origin), lease generation 526. The
  node 0 and legacy leases were released at launch and at the start and end of every block.
- Time: 03:19-09:56 ET (`07:19:01Z`-`13:56:23Z`). Load1 1.5-2.5. Users: `yanruj` only.
- Code: commit `b45c56a` (branch `t56-a8`, from a git bundle). Runs root `/data/...`.
- Lane exit code 1 comes from the run script's last `pgrep`; the campaign exited 0.

**A/A pilot.** Both classes pass on the fork scalar TDStep (the only gating role):

| Class | Role | Ratio [95% CI] | CI width / ratio | Gates? | Block passes? |
|---|---|---|---|---|---|
| Kronecker 22 | fork scalar TDStep | 0.999 [0.979, 1.006] | 0.027 | yes | yes |
| Kronecker 22 | upstream DO-BFS | 1.001 [0.999, 1.001] | 0.002 | no | yes |
| Uniform 22 | fork scalar TDStep | 0.999 [0.993, 1.018] | 0.025 | yes | yes |
| Uniform 22 | upstream DO-BFS | 0.953 [0.914, 1.025] | 0.117 | no | no (reported only) |

Upstream slow share in the pilot: Kronecker 0.00 / 0.32, uniform 0.43 / 0.48 (baseline / candidate side).

**Campaign.**

| It. | Outcome | Kronecker vs fork: ratio [CI], width, verdict | Uniform vs fork: ratio [CI], width, verdict |
|---|---|---|---|
| 1 | one uncertified scalar rewrite of TDStep (`it1.kronecker.a0`, no contract) | 1.345 [1.265, 1.364], 0.074, `inconclusive` | **1.457 [1.450, 1.472], 0.015, `gain`** |
| 2 | rejected: named `operation.gather_staging_executor`, outside the campaign's contracts | — | — |
| 3 | rejected: the patch did not apply | — | — |
| 4 | the same artifact again (identical sha256), re-measured in new blocks | 1.299 [1.256, 1.331], 0.057, `inconclusive` | **1.450 [1.441, 1.464], 0.015, `gain`** |
| 5 | the rewriting call was refused by the provider guard (see below) | — | — |

- Against upstream DO-BFS the artifact is far slower (Kronecker 0.24-0.25, `inconclusive`; uniform 0.141, `no_gain`).
- Stop: `plateau` after 5 iterations. 6 counted provider calls, 0 uncounted (no capacity event). 6.53 lane-hours,
  0.89 GB peak disk.
- **Per class:** uniform `gain`, best `it1.kronecker.a0` (level `uncertified`; selection baseline fork scalar
  TDStep; upstream beside it 0.141, `no_gain`). Kronecker `inconclusive` (both of its measurements had a CI wider
  than 0.05), no best. Label "single graph per class", measured.
- **The best patch** stages frontier vertices of TDStep in batches of 16, keeps their IDs and row offsets in
  aligned local arrays, uses an `SGOffset` edge index, and drops the redundant `parent[v] = u` after a successful
  CAS. Its artifact sha256 is `7acca955…`. Every timed trial passed the compiled structural verifier v2.
- **Re-certification with `swdb certify` 1.3: not applicable.** The best names no contract, so there is no library
  entry to certify it against. It is reported as an **uncertified** gain, as pre-registered.
- **Guard refusals counted.** Calls 1 (setup profiling) and 6 (iteration 5) stopped after about 1 s with "provider
  resource limit exceeded: threads=17" and were counted as `guard_refused`. Iteration 5 was the fourth
  non-improving iteration, so the plateau was reached through it. The uniform gain does not depend on it.
- The ticket 73 workspace changes were in effect: no patch touched the protected verifier.

Summary `records/campaign_summaries/extensa-native-bfs-20261005-a8.summary.yaml` (team store; sha256 `8e8e5099…` on
host and Mac). Compact evidence:
[`evaluation/native-a8-ci-gate-v2-2026-10-05.json`](../evaluation/native-a8-ci-gate-v2-2026-10-05.json). This was
the last native run under `ci_width.v2`. No rerun.

**Erratum 2026-10-05 10:45 ET (ticket [74](74-provider-guard-runtime-threads.md)).** a8's plateau was reached
partly through two miscounted guard stops. Calls 1 and 6 were stopped by the harness's own aggregate 16-thread
cap about 0.5 s after launch, before any tool command: strace plus Codex's own runtime (16 threads, 12 of them
tokio threads). Under D7 neither was a real attempt, and both should have been uncounted infrastructure pauses
with the call retried. Iteration 5 instead ended without a rewrite and completed the 4-iteration plateau, so the
stop is partly **infrastructure-driven**. Uniform's measured `gain` (iterations 1 and 4) and Kronecker's
`inconclusive` stand as measured. The a8 records and summary are left unedited.

**Addendum 2026-10-05 15:00 ET (ticket [75](75-certify-a8-frontier-staging.md)).** a8's uniform best `it1.kronecker.a0` is now
**certified**: contract `contract.bfs_tdstep_frontier_staging` (frontier staging plus post-claim store
elimination) certifies the exact a8 tree (`7acca955…`) under certify 1.3 and 1.4 (22/22 cells, 8/8 controls, every
1.4 rejection attributed) and is shared. After candidate promotion (ticket 48), its team re-evaluation on uniform22
under team protocol `bfs-native-scale22-ci-team-20261005` (a8's fork settings, CI-width rule) measured **1.454
[1.442, 1.464]** against the fork scalar TDStep (width 0.015, `gain`; A/A 0.996 [0.989, 1.001]). This replicates
a8's 1.457 and 1.450. The upstream DO-BFS comparison was not re-timed (a8: 0.141). Label "single graph per class",
measured.

