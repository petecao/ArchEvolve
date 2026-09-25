# Map: BFS profiling, rewrite proposals, and hardware-aware evaluation

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** ticket map
**Status:** claimed
**Blocked by:** None — user authorized implementation and execution on 2026-09-25.
**Spec:** [Refined specification](spec.md)

The user authorized autonomous implementation of all 21 tickets and all necessary builds, installations, benchmark/simulator runs, external access, Git, and Claude Code on 2026-09-25. This supersedes the publication-only hold. The two-lane mbit10 rules and evidence requirements remain in force.

## Approved tickets

The user approved this 21-ticket decomposition on 2026-09-25. Each link is one independently reviewable ticket. Blockers are ticket dependencies. Status and evidence are synchronized as work proceeds; acceptance is not inferred from fixture tests.

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | [Shared BFS identity and explicit baselines](issues/01-shared-bfs-identity-and-baselines.md) | None | resolved |
| 02 | [Patch proposal to durable candidate](issues/02-patch-proposal-to-candidate.md) | 01 | resolved |
| 03 | [Native BFS evaluation](issues/03-native-bfs-evaluation.md) | 02 | resolved |
| 04 | [Instruction-based rewriting and bounded repair](issues/04-instruction-rewriting-and-repair.md) | 03 | resolved |
| 05 | [Annotated-source rewriting](issues/05-annotated-source-rewriting.md) | 04 | resolved |
| 06 | [Automatic function hotspot discovery](issues/06-function-hotspot-discovery.md) | 03 | claimed |
| 07 | [Loop discovery and changed-region profiling](issues/07-loop-discovery-and-reprofiling.md) | 06 | claimed |
| 08 | [Dynamic memory observations](issues/08-dynamic-memory-observations.md) | 06 | claimed |
| 09 | [Complete profile packages and strategy lookup](issues/09-profile-packages-and-strategy-lookup.md) | 07, 08 | claimed |
| 10 | [Queryable DX100 operation contracts](issues/10-dx100-operation-contracts.md) | 02 | resolved |
| 11 | [Reproducible workloads and comparison protocols](issues/11-workloads-and-comparison-protocols.md) | 03 | resolved |
| 12 | [DX100 build and execution path](issues/12-dx100-build-and-execution.md) | 03 | claimed |
| 13 | [Correctness of the timed DX100 binary](issues/13-dx100-timed-binary-correctness.md) | 12 | claimed |
| 14 | [DX100 region timing and memory profiling](issues/14-dx100-region-and-memory-profiling.md) | 09, 12 | claimed |
| 15 | [Baseline pilot and protocol freeze](issues/15-baseline-pilot-and-protocol-freeze.md) | 11, 13, 14 | claimed |
| 16 | [Artifact reference and controlled comparisons](issues/16-artifact-reference-and-controls.md) | 11, 13, 14 | claimed |
| 17 | [DX100 BFS: instruction-route acceptance](issues/17-dx100-instruction-route-acceptance.md) | 04, 10, 15 | claimed |
| 18 | [DX100 BFS: patch-route acceptance](issues/18-dx100-patch-route-acceptance.md) | 15 | claimed |
| 19 | [Upstream BFS: instruction-route acceptance](issues/19-upstream-instruction-route-acceptance.md) | 04, 15 | claimed |
| 20 | [Upstream BFS: annotated-source route acceptance](issues/20-upstream-annotated-route-acceptance.md) | 05, 10, 15 | claimed |
| 21 | [Coverage, ROI gain, and collaborator handoff](issues/21-coverage-roi-gain-and-handoff.md) | 16, 17, 18, 19, 20 | claimed |

Tickets 01–05, 10, and 11 are resolved; the current empirical frontier is native profiling and simulator verification. Later independent branches may proceed once their own blockers are resolved; list order alone is not an additional dependency. Runtime scheduling must also follow the lab's host and resource rules.

### Assigned acceptance cases

| Ticket | Starting implementation | Payload / producer | Execution requirement | Graph coverage |
|---|---|---|---|---|
| 17 | DX100 scalar top-down BFS | Natural-language instructions / SW test client | Correct candidate with proven DX100 accelerator execution | claimed |
| 18 | DX100 scalar top-down BFS | Supplied patch / test client | Real native CPU evaluation and reprofiling | claimed |
| 19 | Upstream direction-optimizing BFS | Structured instructions / test client | Real native CPU evaluation and reprofiling | claimed |
| 20 | Upstream direction-optimizing BFS | Annotated source / HW test client | Correct candidate with proven DX100 accelerator execution | claimed |

These four cases cover all eight source/route/graph cells, all four payload forms, and both source-specific accelerator minima. Ticket 16 separately supplies the actual artifact reference and controlled comparison evidence. A candidate or result may cover multiple obligations only when its source, workload, protocol, target, and required evidence match.

### Important dependency boundaries

- Ticket 14 may collect simulator profiling independently of ticket 13. Its output must remain explicitly unverified until correctness of the timed binary is established; ticket 15 joins those capabilities.
- Ticket 16 does not depend on the pilot-sized protocol in ticket 15. It owns and freezes its artifact/control protocol before the associated reference comparisons.
- Instruction and annotation development may use contract fixtures before complete profile-package generation is available. Such fixtures do not satisfy real BFS acceptance or performance criteria.
- Ticket 07 must demonstrate discovery on actual changed BFS/helper code, not only fabricated profiler output.
- Ticket 21 closes only when the spec's acceptance obligations, including at least one policy-qualified correct ROI gain, are evidenced. Otherwise it retains the incomplete report and returns the unmet requirement to the proposal owner; it does not launch an unbounded strategy search.

## Acceptance ownership

| Spec criterion | Principal tickets |
|---|---|
| AC01 — Shared kernel, correct source context | 01, 02, 19, 20 |
| AC02 — Automatic functions/loops and source attribution | 06, 07, 09 |
| AC03 — Newly introduced hot helper/loop | 07; candidate reprofiling in 17–20 |
| AC04 — Actual dynamic memory observations | 08, 09, 14; real evidence in 17–20 |
| AC05 — Forward/reverse strategy queries | 09 |
| AC06 — Both routes, sources, graphs; four payload forms | 04, 05, 17–20 |
| AC07 — Actual candidate and durable retrieval | 02–05, 17–20 |
| AC08 — Source/capability/protection rejection | 02–05, 10, 11 |
| AC09 — Retained failure, timeout, budget, missing data, regression | 03, 04, 12–14, 17–21 |
| AC10 — Structural correctness of timed code | 03, 13, 17–20 |
| AC11 — Acceleration from both source implementations | 13, 17, 20 |
| AC12 — Actual native evaluation | 03, 18, 19 |
| AC13 — Distinct BFS ROI, region, native/simulated/diagnostic quantities | 03, 07, 11, 14, 17–20 |
| AC14 — Explicit comparator and compatible evidence | 01, 11, 16–21 |
| AC15 — Artifact and controlled comparisons | 11, 16, 21 |
| AC16 — Frozen protocol and equivalent graph/source workloads | 11, 15, 16, 17–20 |
| AC17 — At least one correct ROI gain | Evidence from 17–20; final gate in 21 |
| AC18 — Full coverage including failed/regressing cases | 17–21 |
| AC19 — Executable capabilities and honest wrapper support | 10, 17, 20 |
| AC20 — Real workflow with labeled SW/HW test clients and handoff | 17–21 |

## Review navigation

| Review question | Spec destination |
|---|---|
| What is the deliverable, including every agreed coverage dimension? | Solution; Testing Decisions → Coverage accounting |
| What must Peter, Josh, the worker, and evaluator be able to do? | User Stories 1–60 |
| What are the source, proposal, hardware, and evaluation contracts? | Implementation Decisions D01–D15 |
| What proves completion? | Testing Decisions AC01–AC20 |
| What remains to be chosen, and when? | Further Notes → Decisions still to instantiate |

## Requirement traceability

| Requirement group | User stories | Decisions | Acceptance criteria |
|---|---|---|---|
| Shared kernel identity, exact application provenance, source context | 1–2, 9, 15, 19, 36, 48–49 | D01, D03–D04, D12–D13 | AC01, AC02, AC08, AC14, AC16 |
| Automatic discovery, new hot helpers/loops, dynamic memory evidence | 3–8, 10 | D03–D05 | AC02–AC05 |
| Four payload forms, two routes, worker ownership and bounded repair | 11–24 | D06–D08 | AC06–AC08 |
| Failure retention, independent correctness, durable retrieval | 25–31, 38, 40, 54 | D02, D08, D10, D14 | AC07–AC10, AC18 |
| Primary BFS ROI, region results, explicit comparator, protocol freeze | 32–39, 47–51 | D11–D13 | AC13–AC18 |
| DX100 operation contracts, both-source acceleration, future co-design | 41–46, 59 | D09–D10, D12, D15 | AC08, AC10–AC12, AC15, AC19 |
| Workload coverage, native execution, real gain, resource discipline | 29, 39–40, 46–52, 58 | D10–D14 | AC06, AC10–AC13, AC15–AC18 |
| Master records, collaborator fixtures, public workflow tests, authorization | 26–27, 53–60 | D02–D03, D14–D15 | AC07, AC09, AC18, AC20; publication gate |

## Context pointers

- 2026-09-25: [Ticket 10](issues/10-dx100-operation-contracts.md) resolved: seven pinned source-backed operation contracts and 14 passing public capability/proposal tests. [Capability contract](../../docs/bfs-capabilities.md) separates model/interface support from executable readiness; no DX100 execution is yet claimed.

- 2026-09-25: [Ticket 02](issues/02-patch-proposal-to-candidate.md) resolved with 10 passing public subprocess tests: actual patch materialization, protected-source rejection, stable candidate identity, and fresh-process/index retrieval. [Workflow format](../../docs/format-v0.4.md) and `schemas/messages/rewrite-proposal.schema.json` define the provisional contract; no correctness or performance claim follows from candidate creation.

- 2026-09-25: [Ticket 01](issues/01-shared-bfs-identity-and-baselines.md) resolved: additive 0.4 source/evaluator ownership, scoped verification, and explicit comparison baselines. See [source contract](../../docs/bfs-source-identity.md), `tests/test_bfs_identity.py` (22 passing public workflow tests), and `apps/dx100/PROVENANCE.md` for the pinned unmodified import. DX100 source remains unchecked until real evaluation.

- 2026-09-25: Execution authorized; [implementation plan](implementation-plan.md) records assumptions and module ownership. Ticket 01 claimed. Review baseline: `1bdb7d4037916dea782c40239a6415b61a47f3c1`. A thread heartbeat checks progress, worker health, and evaluation state every 30 minutes.

- 2026-09-25: The user approved publication of 21 vertical-slice tickets. One file per ticket records exact blockers, externally observable acceptance, verification, and the execution hold. No ticket was started, claimed, or resolved.

- 2026-09-25: Requirements synthesized from the design discussion; both BFS starting implementations, both proposal routes, both graph families, native and DX100 evaluation, ROI priority, and future hardware/software co-design are retained.
- 2026-09-25: [Glossary](../../CONTEXT.md) distinguishes kernel, implementation, region, candidate artifact, rewrite proposal, hardware target, ROI, and comparison baseline.
- 2026-09-25: [ADR 0005](../../docs/adr/0005-kernel-identity-spans-sources-and-comparisons-name-their-baseline.md) records shared semantic kernel identity across source applications and explicit comparison baselines. It supersedes ADR 0004's implicit ancestry-based comparison rule; the code has not yet implemented this design.
- 2026-09-25: The user confirmed the full public SWDB workflow as the primary test boundary. Existing subprocess CLI tests supply the prior art; no new HTTP service or internal-module test boundary is mandated.
- 2026-09-25: Spec refinement completed with 60 user stories, 15 implementation decisions, 20 observable acceptance criteria, and explicit gates for pilot settings. This is documentation readiness, not completed functionality or performance evidence.

## Evidence pointers for future implementation design

These are navigation aids for the inspected checkout, not stable API requirements. SWDB HEAD inspected: a38dfac2e4849235158ec2cdfb2d2623ffe6b963. All sources below were inspected during the 2026-09-25 session; no new builds or experiments were run.

### Current SWDB behavior and testing prior art

| Evidence | Relevance |
|---|---|
| [Public command interface](../../swdb/cli.py) | Existing query, view, add, and profile entry points; no current full proposal/rewrite/evaluation workflow |
| [Subprocess test harness](../../tests/conftest.py) | Fresh processes, temporary records, isolated generated query database |
| [Profile tests](../../tests/test_profile.py) | Profile-to-later-view retrieval, incomplete metrics/timeouts, correctness failure, and gated real lab-host execution |
| [Record-add tests](../../tests/test_add.py) | Persist, validate, rebuild, and observe through a later public query |
| [Implementation/strategy comparison tests](../../tests/test_applies.py) | Current ancestry-based pairing and missing profile cases; relabeled fixtures are not performance evidence |
| [Benchmark fixture](../../tests/fixtures/profile/stub_bench.py) | Predetermined times used for contract behavior, not speedup claims |
| [Profiler](../../swdb/profile.py) | Current whole-call timing and configured-symbol Cachegrind aggregation; not the required automatic ranked-region workflow |
| [Application resolution](../../swdb/store.py) | Current inherited application context that must accommodate the accepted cross-source design |
| [BFS implementation record](../../records/implementations/gapbs-bfs-do.yaml) | Existing code/loop/access-pattern catalog and the limitation of static index-stream assumptions for BFS traversal |
| [CPU intrinsic schema](../../schemas/intrinsic.schema.json) | Existing ISA-wrapper semantics; accelerator resource/synchronization requirements need an appropriate contract |
| [Upstream GAPBS provenance](../../apps/gapbs/PROVENANCE.md) | Local upstream source is revision 2972aeb2703165bafd921222f4ed7196f542d3a8, not the DX100 source |

### DX100 artifact evidence

Pinned artifact revision: e4fc4afdf894f295442cef3604667a469fab8e62.

| Evidence | Relevance |
|---|---|
| [Artifact README](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/README.md) | Build/model description and artifact-wide resource estimates, not measured BFS-only costs |
| [BFS source](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc) | Actual top-down execution, conditional accelerator use, ROI boundaries, and simulator exit before enclosing verification |
| [Accelerator API](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/API/MAA_gem5.hpp) | Supported operations and memory-mapped API behavior to inspect for contracts |
| [Simulator runner](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py) | Artifact BASE/accelerated configuration differences and checkpoint automation requiring pilot validation |
| [Statistics parser](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/parse.py) | Existing statistics interpretation and hardcoded ticks-to-cycles conversion |
| [Benchmark harness](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/benchmark.h) | Source selection, trial loop, timer, and verifier result handling |
| [Graph generator](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/generator.h) | Available graph families and seeded generation |
| [Simulation exit implementation](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/pseudo_inst.cc) | Simulator-loop exit semantics; continuation is an untested correctness option |

### Extensa evaluation references

| Evidence | Relevance |
|---|---|
| [Primary measurement definitions](/Users/yanrujhou/CLionProjects/MemAcc/AgenticRefiner/refiner/measurement.py) | Primary target-operation quantity versus diagnostic timing |
| [GAPBS benchmark harness](/Users/yanrujhou/CLionProjects/MemAcc/DataLayoutAPI/benchmarks_vanilla/gapbs-master/src/benchmark.h) | Timer around the complete kernel call, with verification outside it |
| [BFS adapter](/Users/yanrujhou/CLionProjects/MemAcc/AgenticRefiner/adapters/gapbs-bfs.yaml) | Protected source surfaces and kernel timing scope |

The spec preserves these evidence boundaries. It does not import historical timings, fixed noise thresholds, or unverified current host capabilities as new results.

### Native evaluation acceptance — 2026-09-25

Ticket [03](issues/03-native-bfs-evaluation.md) is resolved: evaluator-owned native
ROI and structural correctness, durable failure stages, 17 contract cases, and a
real three-source mbit10 lane-1 DX100 scalar diagnostic. See
[native evaluator design](../../docs/bfs-native-evaluator-design.md) and metadata
commit `283467878fcce65a988f7dc28f151cc6d022d520`. This is pre-freeze diagnostic
evidence; automatic function/loop/memory collection remains tickets 06–09.

- 2026-09-25: [Ticket 11](issues/11-workloads-and-comparison-protocols.md) resolved with 27 protocol tests, 8 compiled streaming-SG tests, and 12 add/document checks. [Protocol contract](../../docs/bfs-protocol.md), `swdb/bfs_protocol.py`, `swdb/sg_stream.py`, and `tools/bfs_native/sg_identity.cc` define immutable workload identity and comparison enforcement. This is contract acceptance, not a candidate gain or empirical protocol freeze.

### Instruction and annotated-source acceptance — 2026-09-25

Tickets [04](issues/04-instruction-rewriting-and-repair.md) and [05](issues/05-annotated-source-rewriting.md) are resolved: real Claude source changes for natural-language, structured, and annotated inputs each have a three-source independently verified native diagnostic. The ten-test bounded rewrite suite passes, and earlier failed attempts remain linked. See [handoff](../../docs/bfs-handoff.md) for exact record IDs. Tickets 17–20 remain separate frozen-workload acceptance obligations.
