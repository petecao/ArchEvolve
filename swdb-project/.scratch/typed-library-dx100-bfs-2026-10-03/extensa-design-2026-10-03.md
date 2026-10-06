# Extensa-mode design decisions (ticket 47)

Created: 2026-10-03 ET
Updated: 2026-10-05 22:30 ET (ticket 80 revisions to D7, D9 and D10)
**Type:** design decisions
**Status:** decided
**Ticket:** [47](issues/47-extensa-design-session.md)
**Spec:** [spec.md](spec.md), section "Extensa mode"

Every decision below is **agent-decided under Yan-Ru's 2026-10-03 delegation; revisable.**
Yan-Ru delegated ticket 47's decisions on 2026-10-03 ("make a reasonable choice, note it,
continue"). Each decision keeps the decisions already in the spec, ADR 0009, ADR 0010 and the
2026-10-03 speed-rule session. A revision changes this file and the tickets it names.

Extensa source pin for every port: `MaizeHPC/MemAcc`, commit
`af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, folder `AgenticRefiner/`. The same commit the
grammar port (ticket 10) used. The local checkout was read only.

## Summary

| # | Decision | Value |
|---|---|---|
| D1 | Port boundary | Port four groups: loop accounting, runtime-probe emission, certification profiles, BFS-relevant synthesis. Never port the agent runtime, timing, speed rule, A5 study gates, Z3/SMT, the clang instrumenter or non-CPU targets. |
| D2 | One target per campaign | A campaign names one hardware target (`native_cpu` or `dx100_gem5`). Native and gem5 are separate campaigns. |
| D3 | Native protocol | 10 paired repetitions, sources `[0, 1234, 7777]`, 1 thread, `bfs.complete_call.v1`, `-O3`, socket lane. A baseline A/A pilot gates the campaign. |
| D4 | Graph per class and target | Native: Kronecker scale 22 and uniform scale 22, edge factor 16. gem5: the ticket 29 graphs, Kronecker 18 and uniform 18, source 0. Labeled "single graph per class". |
| D5 | Campaign file | YAML, format `swdb.extensa-campaign.v1`, JSON schema `schemas/extensa_campaign.schema.json`, tracked under `campaigns/extensa/`. |
| D6 | Summary record | New record kind `campaign_summary`, one per campaign, written at stop. Shape below. |
| D7 | Provider-call accounting | One rewrite call per iteration makes one patch. That patch yields one candidate artifact per class through per-class knob values, so per-class artifacts cost no extra calls. Repairs, test generation and synthesis each cost one call. The cap is 3 per iteration, and unused calls do not carry over. |
| D8 | Rewrite workspace lineage | From iteration 2, the rewrite workspace may hold the campaign's own per-class best patches and the feedback. It never holds other campaigns' artifacts or evaluator inputs. |
| D9 | Native base source | The acceptance native campaign rewrites the fork's scalar TDStep. Upstream direction-optimizing BFS is timed and reported as the second comparison (Q61). |
| D10 | Record store | Records go to `<runs root>/extensa/<campaign-id>/records/` on mbit10, where `<runs root>` follows the disk rule (`/data1/yanruj/EvolveSWDB_runs`, or `/data/...` when `/data1` is low). |
| D11 | License (Q66) | Ported files carry `Apache-2.0 WITH LLVM-exception` under the accepted Q66 assumption, pending Peter's confirmation (ticket 02). Ticket 02 no longer blocks any ticket. |
| D12 | Effort | About 55–65 h of agent work plus about 25 lane-hours for the two acceptance campaigns and the experiment. |

## D1 — Port boundary

Ported files keep their logic but are rewritten onto SWDB's records, provider launcher and
`swdb certify`. Each gets an SPDX header, a provenance header (MemAcc commit and original path)
and an entry in a new `swdb/extensa/PROVENANCE.md`. The module names below are SWDB targets for
ticket 49 and may change if the code calls for it.

**Ported (ticket 49 unless noted):**

| Group | Extensa source (under `AgenticRefiner/`) | SWDB target | What is kept |
|---|---|---|---|
| Loop accounting | `refiner/a5/search.py` (`SearchBudget`, `SearchLedger`, feedback reasons, `plan_rollback`/`apply_rollback`); `refiner/a5/leakage.py`; the attempt-outcome and stop-reason types of `refiner/a5/outcomes.py` only | `swdb/extensa/search.py` | Every opened call is charged. Plateau advances once per completed non-improving iteration. Rejected candidates are rolled back in full. Feedback uses a closed reason set and no outcome claims. Budgets come from the campaign file and are never defaulted in code. |
| Runtime-probe contract checks | `refiner/legality_testing/contract_check.py` (`ContractPredicate`, `predicates_for_entry`, `family_of`, `emit_predicate`, `_negctl_mutation`, `emit_contract_probe`, `splice_probe(s)`, `contract_record_from_verdict`); `refiner/legality_testing/dsl_contract.py` (`runtime_checkable_predicates`) | `swdb/extensa/probes.py` | A contract's predicates (parsed by the ported grammar, `swdb/predicate_grammar.py`) become C++ probes deterministically, with one negative control per conjunct. Probes are compiled into certification builds only and never into timed builds. Bindings come from the rewrite contract's operands (call-bound). A provider-supplied binding is labeled model-bound and does not count toward certification. |
| Certification profiles | `refiner/a5_certification_profiles.py` (data model and validation only) | profile YAML in `library/`, read by `swdb certify --profile` | A profile names the matrix and control set an entry must pass. There is no second certifier and no profile runner. |
| Synthesis | `refiner/synthesis/certify.py` (two-binary reference/candidate build, post-hoc seed, sanitizer precondition); `mutants.py`; `families.py`; `spec.py`; `synthesize.py`; `testgen_backend.py` (mutation gate); `targets/base.py`, `targets/cpu_like.py`; from `shape_classes.py`, only the pack, regroup, gather and bin-drain case generators; `refiner/differential_oracle.py` | `swdb/extensa/synthesis/` | Synthesis runs through the provider launcher's `synthesis` role. A synthesized entry enters the experimental tier only after `swdb certify` passes its profile. |
| Driver templates | `refiner/synthesis/drivers/{pack,regroup,gather,gather_stream,bin_drain}_{ref,cand,run}.cpp.tmpl` | `library/library_operations/drivers/` | Pack templates are ported in ticket 50 and the rest in ticket 49. |
| Library seed bodies (tickets 50, 51) | `DataLayoutAPI/data_layout.hh`, `data_layout_impl.hh` (`PackExecutor`, `RegroupExecutor`); `update_binning.hh` (`UpdateBinningExecutor`); `vertex_relabel.hh` (`VertexRelabelExecutor`); `gather_staging.hh` (`GatherStagingExecutor`), with their `transformations/{pack/pack_executor,regroup/regroup_executor,binned/binned_update_executor,relabel/vertex_relabel_executor,staging/gather_staging_executor}.yaml` | one standalone C++11 header per entry under `library/library_operations/` | Only the base variant of each family and its dependencies. Range, tiled, fused and other variants are not ported. Each body must build with `-std=c++11` (the gem5 guest flag) and call no hardware API. |

**Not ported:**

- Agent runtime and providers: `refiner/agent_runtime.py`, `claude_invoke.py`,
  `codex_hook_bridge.py`, `broker.py`, `broker_session.py`, `launcher.py`, `host_controller.py`,
  `credential_custody.py`, `provider_limit.py`, `agent_tools.py`, `tools.py`. SWDB's provider
  launcher and role pins replace them, and SWDB's adapters detect usage limits and login failures.
- Timing and the speed rule: `refiner/measurement.py`, `measurement_guard.py`, `fitness.py`,
  `profitability.py`, `final_evaluator.py`, `refiner/a5/selection.py`, `refiner/a5/comparison.py`,
  `refiner/synthesis/perf.py`, `offload_threshold.py`, `DataLayoutAPI/memacc_bench_timing.hh`. SWDB's
  evaluator supplies every number (ADR 0010).
- A5 study machinery: `refiner/a5/loop.py` (scope gate, auditor, custody, declaration),
  `campaign.py`, `session.py`, `candidate_policy.py`, `adjudication.py`, `audit_bundle.py`,
  `refiner/a5_*` other than the profile data model, and all `prospective_*` modules. SWDB's frozen
  protocols and guarded workspaces cover their role. The loop structure is rewritten on
  `swdb/extensa/search.py`, not copied from `a5/loop.py`.
- Formal and static tooling: `refiner/predicate_dsl/smt_*`, `evaluator.py` (K3), `binding.py`,
  `pet_facts.py`, `dyn_check.py`, `dyn_provenance.py`; `refiner/predicate_dsl_runtime/` (L4);
  `dyncheck/` (clang instrumenter); `legality/`; `pet_dep/`. These stay out while the
  formal-verification question is open, and SWDB emits probes at the source level, so no clang
  plugin is needed.
- Region discovery and call scanning: `refiner/executor_calls.py`,
  `refiner/legality_testing/region_discovery.py`, `testgen.py`. SWDB's site finder (ticket 55)
  and rewrite-contract sites replace them.
- Non-CPU synthesis targets: `refiner/synthesis/targets/{avx512,cuda,metal,neon}.py`,
  `hardware_validation.py`, `emit.py`, `adopt.py`, `promote_backend.py`, `ledger.py`,
  `registry.py`. SWDB's library, `swdb promote` and the tiers replace them.
- Benchmark adapters (`adapters/`) and prompts (`prompts/`) serve as references only.

## D2 — One target per campaign

The spec's "names the targets" becomes one target per campaign file. The reasons:

- Each target has its own frozen protocol and its own evidence basis (measured or simulated).
- Provider-call accounting stays simple.
- One campaign then never holds two lanes.

The rule that "native timed repetitions never overlap a gem5 job" now applies across campaigns. A native campaign's timed blocks refuse to start while the other socket's lease is held by a gem5 job of any Extensa campaign. The two jobs share the memory link between sockets. Two concurrent campaigns still need Yan-Ru's approval for two lanes.

## D3 — Native repetition count and protocol

- **10 paired repetitions** per source, with sources `[0, 1234, 7777]`, 1 OpenMP thread, ROI
  `bfs.complete_call.v1`, and build flags `-std=c++11 -O3 -Wall -fopenmp -pthread`. Collection is
  `native_paired.v1` with the 2000-draw block bootstrap.
- Why 10: it matches the frozen native protocols and pair receipts of 2026-09-27
  (`records/evaluation_pairs/bfs-native-acceptance-20260927-*`), and the paired collector requires at
  least 5. The evaluator's spread is `(max − min) / median`. Its range grows with the sample count,
  so more repetitions cannot fix spread.
- Spread is fixed by graph size, not repetitions. At scale 18 with 1 thread, the 2026-09-27
  baseline spread was 0.13–0.14, which made every comparison inconclusive (for example
  `records/comparison_results/bfs-native-acceptance-20260927-dx100-patch-b2.kronecker.candidate-1.comparison.yaml`,
  lines 42–50). Hence D4's scale 22.
- **A/A pilot gate.** Before its first iteration, a native campaign times each baseline against itself on each class graph, with the full protocol. If any spread exceeds 0.1, the campaign stops with stop reason `baseline_unstable`, writes its summary and spends no provider call. The threshold is never loosened inside a campaign. A follow-up is a new protocol decided by Yan-Ru.
- 1 thread keeps the existing protocol and is least sensitive to other users' jobs. A multi-thread protocol is a later, separate protocol.

## D4 — Graph per workload class and target

| Class (workload `family`) | Native CPU | DX100 gem5 |
|---|---|---|
| Kronecker (`kronecker`) | Kronecker scale 22, edge factor 16. This is a new workload record from the DX100 GAPBS converter at `e4fc4afdf894f295442cef3604667a469fab8e62` (`-g 22 -k 16`), registered in ticket 56. | `bfs-20260928-kronecker18-s0.cf4283236c5cb50c`, source 0 |
| Uniform (`uniform_random`) | `bfs-20260925-uniform22.f23b09bb0c0601b5` (scale 22, edge factor 16) | `bfs-20260928-uniform18-s0.8c7e69dfa516e53c`, source 0 |

- One graph per class. There is no held-out graph and no cross-class average. Every verdict and
  best carries the label **"single graph per class"**.
- gem5 keeps ticket 29's graphs, so the campaign's baselines are comparable in kind with the
  first result (one run per source, point ratios, Q63). A run takes about 35–41 min and 32–34 GB.
- Native moves to scale 22 for timing stability (D3). The native and gem5 graphs differ by
  design, and their verdicts are never compared with each other.

## D5 — Campaign file format

YAML, validated by `schemas/extensa_campaign.schema.json` and tracked under
`campaigns/extensa/<campaign-id>.yaml`. The campaign file is an input and is small, so it is
committed. Campaign IDs look like `extensa-<native|gem5>-bfs-YYYYMMDD-<letter><n>`.

```yaml
format: swdb.extensa-campaign.v1
id: extensa-native-bfs-20261004-a1
created: 2026-10-04 09:00 ET
mode: extensa
kernel: gapbs-bfs
target: native_cpu            # or dx100_gem5
machine: mbit10
base_source: fork_scalar_tdstep   # the source the provider rewrites; selection uses its baseline
baselines:                    # native: both; gem5: fork_scalar_tdstep only
  - role: fork_scalar_tdstep
    candidate: <candidate record id>
  - role: upstream_do_bfs
    candidate: <candidate record id>
protocol:                     # frozen once per campaign by `swdb campaign`
  roi: bfs.complete_call.v1
  threads: 1
  repetitions: 10             # gem5: 1
  sources: [0, 1234, 7777]    # gem5: [0]
  region_pairs: false
  differences: <campaign-level differences text>
workload_classes:
  - class: kronecker
    workload: <workload record id>
  - class: uniform_random
    workload: bfs-20260925-uniform22.f23b09bb0c0601b5
label: single graph per class   # fixed value
library:
  allowed_tiers: [shared, experimental]
  contracts: [<rewrite-contract id>, ...]   # empty list: knob-free uncertified edits only
regions: query                 # or an explicit list of region IDs
provider: {name: codex, model: gpt-5.6-sol, effort: xhigh}   # or claude / claude-sonnet-5-5 / high
budgets:
  max_iterations: 8
  plateau_iterations: 4
  lane_hours: 24
  provider_calls_per_iteration: 3
  provider_calls_setup: 1     # the profiling agent, once, before iteration 1
  disk_gb: 20
  lanes: 1
runs_root: /data1/yanruj/EvolveSWDB_runs   # or /data/yanruj/EvolveSWDB_runs by the disk rule
approval: {by: Yan-Ru Jhou, date: 2026-10-03, scope: standing mbit10 dispatch approval}
```

The validator refuses these cases:

- a gem5 campaign with repetitions other than 1 or with more than one source;
- a native campaign with fewer than 5 repetitions;
- `region_pairs: true`;
- a label other than "single graph per class";
- a budget above the spec's defaults without an `approval` entry that names it;
- `lanes: 2` without an `approval` entry.

## D6 — Summary record shape

The new record kind is `campaign_summary` (schema `schemas/campaign_summary.schema.json`). It is registered in `vocab/record_kinds.yaml` and documented in the format reference. It is written once, when the campaign stops, and it is the only campaign record that is always copied to the team store. It carries `mode: extensa` and `campaign: <id>`.

```yaml
kind: campaign_summary
id: <campaign-id>.summary
mode: extensa
campaign: <campaign-id>
campaign_file: {path: campaigns/extensa/<id>.yaml, sha256: <hex>}
swdb_commit: <sha>
extensa_source: {repository: MaizeHPC/MemAcc, commit: af3d6d7f7a69a72facdc3b95b42e78c952f44a76}
target: native_cpu
evidence_basis: measured        # gem5: simulated
protocol: <frozen protocol id>
baselines: [{role, candidate, evaluation_ids_by_class}]
workload_classes: [{class, workload, sources}]
label: single graph per class
provider: {name, model, effort}
pilot: {spreads_by_class_and_role, passed}       # native only (D3)
iterations:
  - index: 1
    started: <ISO time>
    ended: <ISO time>
    regions: [{id, reason}]
    provider_calls:
      - {role, invocation, outcome, counted}   # counted is false for usage-limit and login failures
    candidates:
      - id: <candidate id>
        class: kronecker
        patch_sha256: <hex>
        knobs: {}
        contracts: [<id>]                       # empty means an uncertified edit
        certification: {record, outcome, level_at_summary}   # level is a snapshot; candidate records never store it
        comparisons:
          - {baseline_role, comparison, ratio, lower, spread, verdict}   # gem5: lower equals the point ratio
    feedback_reasons: [<closed reason codes>]
    improved_classes: [kronecker]
per_class:
  - class: kronecker
    verdict: gain               # gain | no_gain | inconclusive
    best: <candidate id or null>
    best_level: certified       # certified | uncertified | null
    best_selection_baseline: fork_scalar_tdstep
    best_other_baseline: {role: upstream_do_bfs, ratio, lower, verdict}
    faster_uncertified: [<candidate id>]
budgets:
  limits: {max_iterations, plateau_iterations, lane_hours, provider_calls_per_iteration, provider_calls_setup, disk_gb}
  used: {iterations, lane_hours, provider_calls_counted, provider_calls_uncounted, disk_gb_peak}
pauses: [{at, reason: usage_limit, resumed_at}]          # reason is usage_limit or login
stop_reason: plateau
artifacts: [{path, sha256, retained}]
retentions: [<retention record id>]
```

`stop_reason` is one of these values:

- `max_iterations`
- `plateau`
- `lane_hours`
- `provider_calls`
- `disk`
- `baseline_unstable`
- `infrastructure_failure`
- `stopped_by_yanru`

## D7 — Provider-call accounting

- **The rewrite call.** One rewrite call per iteration returns one patch and at most one knob assignment per workload class. The loop then builds one candidate artifact per class from that patch and its class's knob values. A class with no knob assignment uses the patch's defaults. Certification and evaluation run per class, so per-class artifacts cost no extra calls.
- **Knob values.** Knob values outside the contract's declared ranges reject that class's artifact before certification. They never cost a repair call.
- **Charged calls.** Each bounded repair is charged (build or certification failure only; the default repair limit is 2, as in ArchEvolve mode). So is each independent test-generation call: one per contract per campaign, made the first time an iteration uses the contract, with the inputs reused afterwards. So is each synthesis call.
- **The cap.** 3 counted calls per iteration. The loop refuses to open a call that would exceed the cap. The rest of the iteration then proceeds with the artifacts it already has. Unused calls do not carry over.
- **The profiling agent.** It runs once before iteration 1 and is charged to a separate setup allowance of 1 call. The site finder is a query and costs no calls.
- **Uncounted failures.** A usage-limit or login failure is recorded with `counted: false`. It pauses the campaign and releases the lane, and the iteration is retried from its start after resume. Any other provider failure (timeout, malformed output, guard refusal) is counted.
- **Worst case.** A campaign makes at most 1 + 3 × 8 = 25 counted calls.
- **Revision 2026-10-05 22:30 ET (ticket 80; agent-decided under delegation, revisable).** No independent
  test-generation call is made, and none is charged, until a certify command version accepts its inputs (none
  does). A capacity backoff or guard retry wait (tickets 73, 74) stays uncounted but is charged to the lane-hour
  cap, since the lane stays held during it; a wait past the cap stops the campaign `lane_hours`.

## D8 — What the rewrite workspace may hold

- From iteration 2, the workspace holds the base source, the rewrite contracts in scope, the campaign's own current per-class best patches (at most one per class) and the previous iteration's feedback.
- Feedback per class gives the certification outcome with failed check names, the verdict, the ratio and lower bound (point ratio on gem5) and the spread. It never gives raw timings, workload files, evaluator inputs, other campaigns' artifacts or the authors' accelerated code.
- This reads ADR 0009's "other candidate artifacts" as artifacts outside the campaign's own lineage.
- A rejected candidate is rolled back in full before the next call (ported `plan_rollback`).

## D9 — Native base source and selection baseline

- The acceptance native campaign (ticket 56) rewrites the fork's scalar TDStep, the same region the DX100 work targets. Selection uses the scalar-TDStep comparison (Q61).
- Upstream direction-optimizing BFS is timed in its own paired block for every candidate and reported next to it, so a native gain over the slower top-down-only baseline is never shown alone.
- A later campaign may set `base_source: upstream_do_bfs`. Its selection then uses that baseline.
  - Revision 2026-10-05 22:30 ET (ticket 80): only once an adapter builds candidate artifacts from upstream DO-BFS.
    Until then `swdb validate` refuses any `base_source` other than `fork_scalar_tdstep`.

## D10 — Campaign record store

- Records for a campaign go to `<runs root>/extensa/<campaign-id>/records/` on mbit10. They use the same record layout as the team store, with mode and campaign tags set at creation. They are kept and never pruned.
- Bulky raw output under `<runs root>/extensa/<campaign-id>/runs/` is pruned right after each comparison, with a retention record, unless a team claim cites it (ADR 0011).
  - Revision 2026-10-05 22:30 ET (ticket 80): a gem5 comparison's companion runs are pruned with it; the gem5
    class baselines, which serve every comparison, are pruned when the campaign stops.
- The disk cap counts everything under `<runs root>/extensa/<campaign-id>/`.

## D11 — License assumption (Q66)

- Ported MemAcc files carry `SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception`, matching
  MemAcc's `LICENSE`. This follows the accepted Q66 assumption: Yan-Ru authorized it on 2026-10-03,
  pending Peter's confirmation.
- Ticket 02 stays a human ticket. It no longer blocks tickets 49–51.
- If Peter names another license, a follow-up ticket relabels every file listed in
  `swdb/_vendor/PROVENANCE.md` and `swdb/extensa/PROVENANCE.md`.

## D12 — Effort estimate

| Ticket | Work | Lane time |
|---|---|---|
| 48 mode tags, boundary, promotion | ~4 h | — |
| 49 port machinery | ~12 h | — |
| 50 packing tracer | ~4 h | — |
| 51 seed families | ~8 h | — |
| 52 campaign skeleton | ~8 h | — |
| 53 speed rule and selection | ~6 h | — |
| 54 budgets and pruning | ~4 h | — |
| 55 query site finder | ~4 h | — |
| 56 native acceptance campaign | ~3 h | ~6–10 lane-h |
| 57 gem5 acceptance campaign | ~3 h | ~12–14 lane-h |
| 58 "is the specification enough?" | ~3 h | ~3 lane-h |

The total is about 59 h of work, inside the spec's 40–60 h range, plus about 25 lane-hours.

## Team messages

Two new ready-for-human send tickets carry drafts. Yan-Ru sends both manually; the agent never sends.

- Ticket 59 sends Peter this design and the license assumption it relies on.
- Ticket 60 sends Peter the "is the specification enough?" finding after ticket 58.
