# Spec: BFS profiling, rewrite proposals, and hardware-aware evaluation

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** None — implementation and execution authorized by the user on 2026-09-25.
Owner: Yan-Ru Jhou
Requirements: Agreed in the 2026-09-25 design discussion.
Testing boundary: Public SWDB workflow, confirmed by the user on 2026-09-25.

The user explicitly authorized implementation and execution on 2026-09-25, superseding the earlier publication-only hold. Acceptance still requires the actual native and DX100 evidence defined below; authorization is not evidence of completion.

## Problem Statement

The Software Database describes kernels, implementations, source regions, access patterns, strategies, CPU intrinsics, and existing profiles. It cannot yet give an ensemble the complete, workload-specific evidence and source context needed to act on a measured bottleneck, then carry the ensemble's proposal through rewriting, independent correctness checking, comparable measurement, and retrievable results.

Peter's SW Ensemble needs to ask which regions are expensive, inspect the relevant application code, and select a strategy. Josh's HW Ensemble needs the same workload evidence together with executable hardware capabilities. Both need a result tied to the exact software, input, hardware configuration, and timing boundary. Source-level assumptions and aggregate kernel counters cannot establish where a particular BFS workload spends time or whether a proposed rewrite improves it.

2026-09-29 role update: The 2026-09-24 team meeting replaced these ensemble roles with the linear pipeline Yan-Ru → Peter → Josh/Eric → Peter → Yan-Ru. The older role names below describe the original workflow requirements; SWDB supplies annotated source to Peter and evaluates the resulting software returned through this pipeline. Peter owns per-statement memory feature extraction. The handoff is specified in `../archevolve-handoff-2026-09-29/spec.md`.

The current source and baseline relationships also assume one application origin for a kernel. Upstream GAPBS direction-optimizing BFS and DX100's top-down BFS compute the same kernel but have different source origins, build contexts, and evaluation conventions. Combining them without explicit provenance and comparison baselines would make rewrite targets and speedup claims ambiguous.

Neither live ensemble agent is available yet. Their development schedules must not prevent us from establishing and demonstrating the complete workflow. The first deliverable must use real BFS execution and DX100 simulation, while remaining extensible to future customized hardware-software co-design.

## Solution

Extend SWDB's public command/message interface to support this application-backed workflow:

1. Profile an identified implementation and workload; automatically discover hot functions and loops, collect dynamic memory evidence, and return their source and application context.
2. Let an ensemble select a strategy and submit a versioned rewrite proposal as instructions or supplied code.
3. Apply that proposal to an identified source snapshot, recording the candidate and bounded repairs without independently choosing another strategy.
4. Independently check correctness, measure the declared ROI, and profile the candidate on its declared native or simulated target.
5. Persist and return the exact proposal, candidate, comparison baseline, measurements, diagnostic evidence, and outcomes, including failures and regressions.

BFS is the complete first deliverable. DX100 scalar top-down BFS is first in execution order; upstream direction-optimizing BFS is required in the same deliverable.

| Dimension | Required coverage |
|---|---|
| Starting implementations | DX100 scalar top-down BFS and upstream GAPBS direction-optimizing BFS, sharing one kernel identity |
| Proposal routes | Instruction-based and annotated-source/patch-based proposals on each starting implementation |
| Payload examples | Natural language, structured instructions, annotated source, and patches represented across the route cases |
| Graph families | Kronecker and uniform-random for the resulting candidates from each route and starting implementation |
| Native evaluation | Real CPU execution, correctness checking, timing, and profiling for CPU-runnable code |
| Accelerator evaluation | At least one accelerator-using candidate from each starting implementation, correct and demonstrably using DX100 on both graph families |
| Comparison controls | Authors' artifact configuration pair plus controlled comparisons with matched CPU/cache/memory settings |
| Success | At least one correct candidate gain against an explicit, appropriate unaccelerated comparison baseline under the frozen protocol; all other outcomes retained |

This defines eight starting-implementation × proposal-route × graph-family coverage cells. Accelerator candidates may also satisfy those cells; every route and every BFS phase need not use acceleration. A speedup in every cell, or a speedup over the authors' accelerated version, is not required.

Small correctness cases and pilot-sized performance workloads serve the coverage matrix. The artifact-matched DX100 reference remains required separately, unless an existing case actually matches its inputs and configuration. Representative SW/HW submissions stand in for live agents while exercising the real downstream workflow.

## User Stories

### Finding and understanding bottlenecks

1. As the SW Ensemble Agent, I want to query BFS once and discover both starting implementations, so that application provenance does not fragment the computation's identity.
2. As the SW Ensemble Agent, I want a profile package for an exact implementation, graph, traversal source, target, threads, and ROI, so that I select strategies using the relevant workload.
3. As the SW Ensemble Agent, I want hot functions and loops discovered without mandatory source annotations, so that previously uncataloged work is visible.
4. As the SW Ensemble Agent, I want newly introduced hot helpers and loops discovered after rewriting, so that a changed bottleneck is not hidden by the baseline catalog.
5. As the SW Ensemble Agent, I want ranked timing contributions with inclusive/exclusive scope and attribution coverage, so that nested or unattributed work does not mislead me.
6. As the HW Ensemble Agent, I want execution- or simulation-derived memory observations, so that hardware proposals can respond to actual workload behavior.
7. As the HW Ensemble Agent, I want metric definitions, collection scope, and evidence basis, so that model results are not mistaken for native hardware observations.
8. As either ensemble agent, I want unsupported metrics and uncertain causal diagnoses stated explicitly, so that missing evidence does not become an asserted property.
9. As the SW Ensemble Agent, I want the selected region's code, helpers, types, headers, and application snapshot, so that I can propose a buildable rewrite.
10. As the SW Ensemble Agent, I want both region-to-strategy and strategy-to-region lookup, so that I can choose an action for a hotspot or locate code relevant to a proposed strategy.

### Describing and submitting a rewrite

11. As the SW Ensemble Agent, I want to submit natural-language instructions, so that useful strategies do not require a formal rewrite language.
12. As the SW Ensemble Agent, I want to submit structured instructions and parameters, so that intent and preconditions can be inspected consistently.
13. As either ensemble agent, I want to submit annotated source, so that an intended change can be expressed next to the affected code.
14. As either ensemble agent, I want to submit a patch, so that supplied edits receive the same evaluation as generated edits.
15. As either ensemble agent, I want a proposal to identify its exact source and input profile package, so that it cannot silently apply to stale code.
16. As either ensemble agent, I want to state correctness, ROI, edit-scope, and hardware requirements, so that execution preserves the intended experiment.
17. As the database owner, I want source-specific proposals kept distinct from reusable optimization strategies, so that strategy identity does not depend on a particular patch.
18. As either ensemble agent, I want a versioned handoff with producer and input references, so that interface changes and proposal provenance remain traceable.

### Applying proposals and retaining outcomes

19. As the rewrite worker, I want to retrieve the correct source and build context, so that upstream and DX100 code are never confused.
20. As the rewrite worker, I want to edit the selected regions and necessary supporting code, so that realistic rewrites can change helpers, data structures, headers, and build settings.
21. As the database owner, I want correctness checks and ROI instrumentation protected from worker changes, so that candidates cannot alter their own success criteria.
22. As the rewrite worker, I want bounded build and correctness repairs within the supplied intent, so that recoverable defects do not require an unrelated strategy search.
23. As the ensemble agent, I want failed and regressing proposals returned with evidence, so that I retain control over the next strategy.
24. As the database owner, I want every candidate and repair associated with its proposal and resulting diff, so that execution is auditable.
25. As the database owner, I want failed candidates retained without being presented as verified implementations, so that failure history remains useful and truthful.
26. As the experiment operator, I want timeouts and exhausted budgets to retain completed artifacts and reasons, so that expensive partial work is not silently lost.
27. As either ensemble agent, I want to retrieve an outcome in a later process, so that the result does not depend on the worker remaining alive.

### Checking correctness and measuring performance

28. As the evaluator, I want BFS structural correctness checks that permit different valid parent trees, so that legitimate parallel implementations are accepted.
29. As the evaluator, I want correctness evidence for every graph/source workload used in a successful timing claim, so that tested and timed workloads do not diverge.
30. As the evaluator, I want evidence covering the timed binary and accelerated path, so that a separate functional build cannot certify different executed code.
31. As the evaluator, I want an explicit correctness result independent of process exit status, so that a printed verifier failure is not mistaken for success.
32. As the experiment owner, I want ROI speedup as the primary metric, so that setup and verification outside the declared ROI do not determine performance success.
33. As the experiment owner, I want BFS-level ROI and selected-region timing reported separately, so that a local improvement is not mistaken for a complete BFS improvement.
34. As the experiment owner, I want named, versioned timing boundaries, so that DX100 traversal timing and Extensa whole-kernel-call timing remain interpretable.
35. As the evaluator, I want timed work to remain inside the declared ROI, so that moving computation into untimed setup cannot manufacture a gain.
36. As the evaluator, I want the comparison baseline explicitly selected, so that source ancestry does not silently determine a performance comparison.
37. As the experiment owner, I want native durations, simulated durations, and simulator host cost distinguished, so that unrelated timing quantities are never divided.
38. As either ensemble agent, I want missing, invalid, and incomplete measurements identified, so that they cannot appear as a neutral speedup.
39. As the experiment owner, I want the repetition and profitability policy fixed before candidate assessment, so that a gain is not selected using post-hoc rules.
40. As the experiment owner, I want every failure and regression retained alongside gains, so that the coverage report represents the full experiment.

### Using hardware interfaces and preserving reproducibility

41. As the HW Ensemble Agent, I want versioned contracts for supported DX100 operations, so that proposals use operations implemented by an executable model.
42. As the rewrite worker, I want signatures, memory effects, ordering, completion, resource, and build requirements for each operation, so that generated calls preserve its semantics.
43. As the rewrite worker, I want to generate wrappers or call sequences over existing operations, so that supported capabilities can be used without inventing hardware.
44. As the HW Ensemble Agent, I want unsupported operation requirements reported explicitly, so that a proposed interface is not presented as an available capability.
45. As the database owner, I want hardware model, software interface, evaluator backend, and host identities separated, so that future co-design is not tied to one simulator or API.
46. As the experiment owner, I want accelerator-using candidates from both starting implementations evaluated on both graph families, so that the capability extends beyond modifying the authors' source.
47. As the experiment owner, I want the authors' reference pair preserved alongside controlled comparisons, so that reproduction and attribution answer distinct questions.
48. As the evaluator, I want canonical graph identity and verified equivalent loaded adjacency across source implementations, so that serialization differences do not change the workload unnoticed.
49. As the evaluator, I want actual traversal source vertices recorded and replayed, so that repeated executions and source-vertex coverage remain distinct.
50. As the experiment owner, I want workload sizing based on baseline/reference feasibility before candidate evaluation, so that graph selection does not favor a candidate.
51. As the experiment owner, I want protocol changes versioned with corresponding reruns, so that changed inputs or settings cannot silently replace unfavorable results.
52. As the experiment operator, I want bounded resource use under the lab's host rules, so that evaluation can coexist with other users' work.

### Delivering and extending the workflow

53. As the database owner, I want versioned master records and reproducible query indexes, so that history remains reviewable and queries can be regenerated.
54. As either ensemble agent, I want a result linking source, proposal, candidate, target, comparison, correctness, and raw evidence, so that I can reconstruct its claim.
55. As the integrator, I want representative SW and HW submissions without live agent dependencies, so that the first deliverable can complete independently of collaborator schedules.
56. As the integrator, I want our own provisional message contract and realistic examples, so that Peter and Josh can review a concrete interface later.
57. As the maintainer, I want fast tests through the public workflow, so that internal refactoring does not invalidate behavior tests.
58. As the experiment owner, I want real BFS and DX100 acceptance evidence distinguished from fixtures, so that contract tests cannot be cited as performance results.
59. As the database owner, I want future hardware/model artifacts to attach to the same evaluation contract, so that customized hardware-software co-design can extend the system.
60. As the project owner, I want specification readiness separated from implementation authorization, so that publishing this spec does not start code changes or experiments.

## Implementation Decisions

### D01. Domain identity, source ownership, and comparison baseline

A kernel is a computation and its correctness check. Upstream and DX100 BFS share that identity; source regions, access patterns, code, and build/evaluator context belong to their actual implementations. Retain each exact application source and revision.

Distinguish three relationships: the source ancestor being rewritten, a baseline implementation found in an application's source, and the comparison baseline explicitly selected for an evaluation. They may coincide but are not interchangeable. ADR 0005 extends kernel identity across sources and supersedes the earlier implicit ancestry-based comparator. Concrete record layout and migration remain implementation-design choices.

Candidate artifacts may be incomplete or incorrect. An implementation must pass the kernel's correctness check, with the scope and evidence of that check retained; passing a finite workload set is not a proof for every possible graph.

### D02. Persistence and responsibility boundaries

YAML records in version control remain the master copy; SQLite remains generated. Extend the existing record-validation, query, profiling, and workload-view capabilities rather than establish a second authoritative database.

Persist proposal/candidate/evaluation metadata independently of successful performance profiles. A rejected proposal or incorrect candidate must remain retrievable even when no valid profile exists. Raw logs, binaries, simulator checkpoints, and large profiling artifacts remain externally stored with recorded identity and location.

The ensemble owns strategy selection. The rewrite worker applies the selected intent. The evaluator owns correctness and measurement. SWDB stores and returns the evidence. Logical responsibility boundaries do not mandate separate services or one module per stage.

### D03. Public workflow and query behavior

Extend the public SWDB command/message boundary to support profile-package retrieval, proposal submission, execution outcomes, and subsequent result queries. Exact command names and transport bindings remain design choices; a long-running simulation must not require one uninterrupted caller session to preserve its outcome.

A profile request identifies implementation, exact source, graph and traversal sources, native or simulated target, configuration, threads, and ROI. Returned rankings must not silently blend different workloads or configurations. Expose unavailable or stale evidence instead of guessing a match.

Support both implementation/profile-to-region/strategy lookup and strategy-requirement-to-implementation/region lookup. Applicability and unknown legality conditions do not promise a performance gain. BFS is the execution acceptance workload even when queries cover other stored records.

### D04. Automatic discovery and source context

Automatically discover and rank hot functions and loops within BFS and its helpers, both before and after rewriting. Existing annotations and catalogs may guide discovery but must not be required to find a new expensive helper or loop.

Return source identity and locations, surrounding code, caller/helper relationships, referenced types and headers, and access to the buildable application snapshot. Line numbers alone are insufficient after edits. Record source associations for changed, split, or fused regions without copying stale baseline properties onto candidate code.

Distinguish inclusive from exclusive contributions and report attribution coverage and unresolved work. The highest-ranked known region must not be presented as an exhaustive application bottleneck when coverage is partial.

### D05. Dynamic memory evidence and diagnostic profiling

Every accepted profile package includes timing and actual memory-behavior observations from execution or simulation, such as access counts or cache behavior. Static access patterns alone, or a package with every dynamic memory metric unavailable, do not satisfy the requirement.

For each metric retain its meaning, units, collector/model, source/binary and workload identity, collection scope, attribution granularity, and basis. ROI-wide observations are not loop-specific measurements. Preserve the existing basis distinctions: measured, simulated, code reading, reported, inferred, and unknown.

Profiling may use a separately instrumented execution. Record how that artifact and execution differ from the timed artifact; diagnostic runtime must not replace primary timing. Model-derived cache behavior must not be labeled native hardware measurement. Source-order traversal is not a substitute for a dynamic index stream when execution uses a different frontier order.

Full address traces and direct proof of every suspected bottleneck cause are not required. Missing metrics and uncertain explanations remain explicit. Refresh dynamic observations and source associations after rewriting.

### D06. Versioned handoff contract

Define three linked messages. These are our provisional contract, not an interface already negotiated with Peter or Josh.

| Message | Required content |
|---|---|
| Profile package | Exact implementation/source/workload/target identity; ROI; ranked regions and timing scope; dynamic memory observations; source/build context; correctness and edit constraints; applicable strategies and available hardware interfaces |
| Rewrite proposal | Producer and source profile package; exact target source and regions; strategy references or proposed strategy and parameters; instruction/code payload; semantic, correctness, ROI, edit-scope, and hardware requirements |
| Evaluation result | Proposal and candidate identities; actual source/binary and software-hardware pair; explicit comparison baseline and protocol; stage outcomes; correctness evidence; BFS ROI and region measurements; profiling changes; raw artifacts; failure or incompleteness reasons |

Every message has a format version, stable identity, producer/provenance, and references to its inputs. Message-format versions and database-record versions are independent. YAML and JSON may encode the same logical contract.

The result distinguishes a missing candidate from an incorrect candidate, a completed evaluation from incomplete measurement, and valid performance evidence from unsupported claims. Exact field spelling, enums, transport, and schema versions remain implementation-design choices.

### D07. Proposal forms and validation

Accept natural-language instructions, structured rules/contracts, annotated source, and patches. Structured instructions express intent and constraints; they are not automatically a deterministic rewrite DSL or proof of legality.

Both instruction-based and supplied-code routes receive the same source-identity, capability, build, correctness, and measurement checks. Preserve annotations, their interpretation, supporting edits, repairs, and the resulting diff.

Conflicting target identities, stale source references, unsupported required operations, and uninterpretable requirements produce explicit rejected or unresolved outcomes. Do not guess a source mapping or treat unknown hardware support as available.

### D08. Rewrite scope and bounded repair

Permit changes to the selected regions and the helpers, data structures, headers, and build settings needed for the declared target. Attribute supporting changes to the proposal.

Correctness checks and ROI instrumentation are evaluator-owned, protected inputs. A candidate cannot redefine the verifier, move the timing boundaries, or relocate required timed work into untimed setup to satisfy acceptance.

Allow bounded build/correctness repair within the supplied strategy. Record attempts, causes, repairs, and final outcomes. After failure or regression, return evidence to the ensemble; the worker does not independently substitute a different strategy. Attempt limits and time/resource budgets must be explicit before execution, with actual values selected during implementation design or the authorized pilot.

### D09. Hardware operations, intrinsics, and generated wrappers

Retain CPU intrinsics as ISA instruction-wrapper contracts. Represent DX100's accelerator operations with contracts that also cover resource and synchronization behavior; do not model those requirements as CPU ISA flags.

An operation contract includes its signature/types, memory effects, masks and repeated-index behavior where applicable, ordering and completion requirements, resources, headers/build dependencies, interface version, and implementing backend. Unknown facts remain unknown.

Initially catalog and use operations implemented by DX100. The worker may generate wrappers or call sequences over supported operations. A generated symbol or interface declaration alone does not create a hardware capability.

Separate hardware model/configuration, software interface, evaluator backend, and host identity. Future co-design may supply new contracts and executable model artifacts. Evaluation becomes possible only when matching executable support and checks exist.

### D10. Correctness evidence

Use BFS structural correctness: the source is its own parent; reachable vertices have valid predecessor edges at the preceding BFS depth; unreachable vertices are represented correctly. Different valid parent trees are allowed.

Check the graph/source workloads used in successful timing claims and the code actually executed for timing, including its accelerated path. Exercise full/tail tiles and competing parent updates as applicable to the rewrite. A small scalar-fallback case does not demonstrate accelerator correctness.

Require an explicit verifier outcome. A process exit code, simulator statistics file, or successful separate functional build is insufficient on its own. Functional API execution is useful for debugging but does not certify a different timed simulator binary.

The inspected DX100 path exits the simulation loop before the enclosing verifier. Continuing the same simulation after sealing ROI statistics is a possible implementation approach, still untested. This spec requires the evidence, not that particular mechanism.

### D11. ROI and selected-region measurement

Primary speedup is baseline ROI duration divided by candidate ROI duration under a declared comparison protocol. The first deliverable leads with the declared BFS-level ROI and also reports selected-region timing and profiling.

| Reference | Timing boundary | Work excluded by that boundary |
|---|---|---|
| DX100 BFS | Traversal levels, queue advancement, and final parent normalization between statistics reset and dump | Graph preparation; initial parent/frontier and accelerator/tile/register setup; verification |
| Extensa GAPBS convention | The complete BFS kernel call | Graph construction and verification; work inside the call remains timed |

Retain named, versioned boundaries. Within a comparison, baseline and candidate cover the same semantic work. Do not treat durations from the two conventions as interchangeable.

Selected-region timing states whether it is per invocation or accumulated across the BFS, and whether attribution is inclusive or exclusive. A changed or split region needs an explicit correspondence before reporting a region speedup. Report cases where region and BFS-level outcomes differ.

Setup and verification outside the ROI are not the performance objective. Whole-process or wrapper time extending beyond the declared ROI, if collected, is a named diagnostic. Initialization inside a chosen complete-BFS-call ROI remains timed and contributes to that ROI's primary result. Simulator host wall time is experiment cost; simulated elapsed time/ticks with clock configuration describe the target's performance. Instrumentation overhead must be assessed and handled by the frozen protocol.

### D12. Comparison protocols and claim limits

| Comparison | Required control and interpretation |
|---|---|
| Native candidate versus baseline | Same declared native target, workload, threads, and semantic ROI, with exact builds recorded |
| DX100 artifact reference | Preserve the authors' BASE/accelerated configurations and their disclosed differences |
| Controlled DX100 evaluation | Match CPU/cache/memory/workload settings, enumerate software and accelerator differences, and identify the exact pair being compared |

For the demonstration, explicitly select the appropriate unaccelerated starting implementation as comparison baseline. Unaccelerated does not automatically mean single-threaded; thread count is part of the protocol. Keep the authors' accelerated BFS as a separate reference.

The inspected artifact uses different LLC configurations for BASE and accelerated runs. Preserve those in reproduction while retaining the additional controlled comparison. A joint hardware/software gain is not an isolated software-rewrite gain; the latter requires software candidates compared on the same configured target.

Do not divide native runtime by simulated runtime. Do not infer measured gain from reported strategy benefit. Missing or invalid measurements are not a speedup of one. Correctness and the frozen repetition/profitability policy are prerequisites for a successful gain claim.

### D13. Workload identity and protocol freeze

Use small correctness cases and performance workloads covering Kronecker and uniform-random graphs. An authorized baseline/reference pilot selects feasible sizes and traversal sources using cost, coverage, and evidence of actual accelerator execution. It may use the authors' fixed accelerated reference; it must not select workloads based on gains of candidates being assessed.

Retain canonical graph identity, generator parameters and revision, normalization, realized graph properties, actual traversal source IDs, and hashes of each serialized representation. Verify equivalent loaded adjacency across applications; matching graph filenames or extensions are insufficient.

Repeated execution of one graph/source pair and coverage of different traversal sources are distinct dimensions. Replay the same ordered sources within each comparison.

Before candidate performance assessment, freeze workloads, threads, targets/configurations, ROI definitions, correctness coverage, instrumentation treatment, repetition/aggregation rules, and profitability criteria in a versioned protocol. A later change requires a new protocol and corresponding comparisons, not silent replacement of unfavorable evidence.

Retain the artifact-matched reference at its prescribed scale separately from the pilot-sized matrix, unless actual identity and configuration permit reuse. Pilot calibration does not waive any accepted coverage cell.

### D14. Execution outcomes and traceability

Retain proposal acceptance/rejection, source resolution, rewriting, build, correctness, timing, profiling, and persistence outcomes independently. Each available observation names the artifact and stage that produced it. Completed evidence remains accessible when a later stage fails or a budget expires.

A failed proposal need not have a candidate. An incorrect candidate must not be promoted to a verified implementation. An incomplete profile may be returned with reasons but cannot satisfy complete profiling acceptance. A correct regression remains a valid recorded outcome.

Results must allow a later query to recover the input profile package, proposal, candidate and repairs, software-hardware pair, comparison baseline, protocol, correctness evidence, timing/profiling outputs, and raw-artifact references.

### D15. Live-agent independence and extensibility

Provide representative submissions for both SW and HW producer roles. They exercise actual query, rewrite, build, correctness, profiling, evaluation, and retrieval work. Label them as fixtures or test clients; do not present them as live collaborator integration.

Deliver the provisional contracts and realistic example messages for later review with Peter and Josh. Keep interface and backend concerns separate so later integration or customized co-design does not require redefining kernels, provenance, or comparison semantics.

## Testing Decisions

### Confirmed test boundary

The user confirmed one primary external test boundary: drive the public SWDB workflow from profile/query through proposal submission, candidate creation, correctness, ROI/profiling, persistence, and result retrieval.

Prefer extending the existing subprocess command interface. The new workflow operations do not exist yet; expose them through that boundary during implementation. A workflow test may invoke several commands. It should not call private stages or assert internal module layout merely to exercise them.

A good test verifies observable behavior: returned messages, stable references, actual candidate artifacts, protected evaluation inputs, durable records, fresh-process query results, and defensible evidence. Internal helpers, exact call order, and self-confirming mock return values are not acceptance criteria.

### Existing prior art and test levels

Current tests already run SWDB in a separate process against temporary records and a generated query database. Existing scenarios cover adding a record and observing it through a later query; profiling and retrieving a later workload view; profile pairing; simulated metrics; timeout handling; invalid references; and separately gated real lab-host profiling.

Reuse those patterns for record validation/querying, profile packaging, proposal handling, rewriting, evaluator integration, comparison reporting, and hardware-capability checks through the single public workflow boundary.

| Level | Purpose and evidence limit |
|---|---|
| Fast workflow/contract tests | Use isolated records and deterministic external provider/benchmark fixtures to check messages, persistence, protection, failures, comparisons, and fresh-process retrieval. Fixture timings and simulated responses are not performance evidence. |
| Native acceptance | Use real BFS source changes, compilation, correctness, measurement, dynamic profiling, and result retrieval under the frozen native protocol. |
| DX100 acceptance | Use the actual executable model and candidate binary, prove accelerated-path execution and correctness, measure simulated ROI and regions, and retain real profiling evidence. Functional API runs and mock simulator output cannot satisfy this level. |

The existing profiling fixture prints predetermined timing values; it does not establish speedup. Existing profile-pairing fixtures establish joins, not measurement validity. Existing correctness-failure behavior can omit a profile; the new evaluation result must retain that failure without inventing a successful profile.

### Observable acceptance criteria

| ID | Required observation |
|---|---|
| AC01 | One BFS query returns both source implementations with their correct source/build/evaluator context. A proposal targeting one cannot silently use the other. |
| AC02 | For a declared workload, profiling automatically discovers/ranks BFS functions and loops and returns source context, timing scope, attribution coverage, and unresolved work. |
| AC03 | A rewritten candidate introduces an expensive helper or loop absent from the baseline catalog; reprofiling discovers and associates it without a person first adding an annotation. |
| AC04 | Each accepted profile package contains actual dynamic memory observations with collector/model, identity, basis, and scope. An entirely unavailable metric set or source-only description fails this criterion. |
| AC05 | Forward and reverse strategy/region queries return applicable records and unknown conditions without claiming guaranteed performance. |
| AC06 | Both proposal routes operate on each starting implementation and their resulting candidates are evaluated on both graph families. The examples collectively cover all four payload forms. |
| AC07 | A proposal produces a real changed candidate with supporting edits and bounded repairs recorded. A new process can retrieve the proposal, candidate, and result. |
| AC08 | Stale/conflicting source targets, unsupported required operations, and attempted changes to protected evaluator/ROI inputs produce explicit non-success outcomes. Invalid requests do not silently select substitutes. |
| AC09 | Build failure, explicit verifier failure despite successful process exit, timeout, exhausted budget, missing metrics, and regression remain retrievable with available evidence. Failed candidates are not verified implementations. |
| AC10 | BFS structural checks cover each workload supporting a timing claim, accept different valid parent trees, and link to the timed code. Applicable accelerated full/tail and parent-update cases are covered. |
| AC11 | At least one accelerator-using candidate from each starting implementation passes correctness and demonstrably uses DX100 on both graph families. Scalar fallback alone fails this criterion. |
| AC12 | Native execution produces actual correctness, timing, and profiling evidence for CPU-runnable code. Neither a stub benchmark nor the host runtime of a functional accelerator API substitutes for this or for DX100 performance. |
| AC13 | Results report the declared BFS ROI and selected-region durations separately, with scope and units. Native time, simulated time, diagnostic timing, and simulator host cost remain distinguishable. |
| AC14 | A comparison whose source ancestor differs from its comparison baseline uses the explicitly selected baseline and compatible evidence. Incompatible ROI/workload/target evidence cannot produce a valid speedup claim. |
| AC15 | Both the artifact reference pair and controlled simulator comparisons execute under recorded configurations. Software/accelerator differences and the resulting limits on attribution are visible. |
| AC16 | Workloads, source vertices, timing boundaries, configurations, repetitions, and profitability rules are frozen before candidate assessment. Graph representations are verified to load equivalent adjacency. |
| AC17 | At least one correct candidate demonstrates a gain against its appropriate unaccelerated comparison baseline under the frozen policy. No all-cell gain or win over the authors' accelerated version is required. |
| AC18 | Both graph families and all required cases appear in the coverage report, including failures and regressions. Missing evidence cannot appear as a neutral speedup or disappear from the report. |
| AC19 | Available hardware contracts resolve to supported operations and executable backends; a generated wrapper alone cannot satisfy an unsupported operation requirement. |
| AC20 | Representative SW/HW submissions exercise the real workflow; examples and results identify their test-client provenance and remain usable for later collaborator integration. |

Fast tests can establish contract and failure behavior for these criteria. Real native/DX100 execution is required wherever a criterion concerns correctness of actual BFS code, discovery on rewritten code, dynamic behavior, acceleration, or gain. Passing fixture tests alone does not complete the deliverable.

### Coverage accounting

| Starting implementation | Instruction route | Annotated-source/patch route | Graphs for each route | Additional accelerator minimum |
|---|---|---|---|---|
| DX100 scalar top-down BFS | Required | Required | Kronecker and uniform-random | One correct accelerated candidate on both families |
| Upstream direction-optimizing BFS | Required | Required | Kronecker and uniform-random | One correct accelerated candidate on both families |

Record the candidate, workload/protocol, evaluation IDs, and acceptance evidence covering each cell. One real artifact/run may satisfy multiple obligations only when identities and requirements actually match. No cell may be deferred by relabeling it future work.

## Out of Scope

- Completion or availability of Peter's or Josh's live agents, or claiming live integration from prepared submissions.
- New hardware-operation implementation, invented ISA instructions, or a new compiler backend in this first deliverable. Future co-design support remains a design requirement.
- Independently runnable extracted microkernels or general execution acceptance across applications beyond BFS.
- Independent strategy search by the rewrite worker after a failed or regressing proposal.
- Full address-trace collection or proof of every bottleneck's causal mechanism.
- Whole-process or wrapper speedup that includes work outside the declared ROI as the primary objective; initialization inside a declared BFS-call ROI remains timed.
- A required gain in every coverage cell, or a requirement to outperform the authors' accelerated implementation.
- Reproduction of the entire DX100 paper campaign.
- Code changes, builds, installations, benchmark/simulator runs, or implementation-ticket decomposition authorized merely by publication of this spec.

## Further Notes

### Decisions still to instantiate

These are implementation-design or empirical calibration tasks, not unresolved scope questions. Resolve them at the listed gate and record the result. Do not silently weaken the acceptance criteria.

| Item | Required gate |
|---|---|
| Record layout/versioning, migration of source ownership and comparison relationships, command/message bindings, compatibility rules | Document before implementing the affected interface or migration |
| Exact operation contracts, model/interface versions, toolchain/build definitions, unsupported-operation handling | Establish before executing an affected proposal |
| Attempt limits, time/resource budgets, artifact/checkpoint retention, and recovery behavior | Set before worker or pilot execution |
| Graph sizes and representations, actual source vertices, native threads, simulator configurations, correctness cases | Calibrate with baseline/reference evidence and freeze before candidate assessment |
| ROI instrument locations, attribution/collector methods, instrumentation treatment, repetitions/aggregation, profitability criteria | Establish and freeze before candidate performance assessment or a gain claim |
| Concrete allocation of the four payload forms, both producer roles, and accelerated candidates to coverage cells | Record in the acceptance run plan before claiming coverage |

The protocol must make a profitability claim assessable under observed timing variability. This spec does not guess repeat counts, a universal noise threshold, or simulator determinism before the pilot.

### Planned execution order, after explicit authorization

1. Establish source identity, automatic region discovery, profile packaging, dynamic memory evidence, and public retrieval.
2. Establish DX100 builds, correctness/ROI controls, baseline/reference pilot results, and the frozen workload/evaluation protocol.
3. Complete one real proposal-to-result workflow, including independent checking and durable retrieval.
4. Complete both starting implementations, both routes and graph families, required accelerated candidates, controls, and all acceptance evidence.
5. Deliver the coverage report, versioned handoff contracts/examples, reproducibility references, and limitations for later collaborator integration.

### Source-informed feasibility checks

The repository inspection established existing CLI/profile/record capabilities, not a working rewrite workflow. The approved source-identity/comparator design is recorded in ADR 0005; the current implementation still requires corresponding changes.

The inspected DX100 revision is e4fc4afdf894f295442cef3604667a469fab8e62. Its executed BFS path is top-down; a descriptive header alone must not establish algorithm identity. Its accelerator path is conditional, so workloads must actually exercise it.

Before accepting pilot results, verify the supplied runner's checkpoint argument mismatch, the parser's hardcoded tick conversion, and the first simulation exit interrupting the usual trial loop. Validate the selected exact-binary correctness mechanism; post-ROI continuation is one option requiring pilot validation. The source picker restarts its deterministic sequence in a new process, which does not create independent traversal-source coverage. Serialized graph offsets differ across source implementations; verify loaded adjacency rather than assuming interchangeability.

The planned lab host is mbit10, subject to live capability/resource checks and the existing host/lane rules. The local Apple Silicon machine and simulated X86 target are distinct environments. Authors' whole-artifact resource estimates are not measured requirements for our BFS-only runs. No working build, host availability, timing determinism, or new performance result is asserted here.

### References and document authority

This spec supersedes the working requirements draft in the same tracker entry. The accompanying map provides acceptance navigation and the 21 implementation tickets approved on 2026-09-25.

The project glossary and ADRs 0001–0005 govern domain terminology, persistence, strategy identity, and cross-source comparison semantics. Current source evidence includes the [pinned DX100 artifact](https://github.com/arkhadem/DX100/tree/e4fc4afdf894f295442cef3604667a469fab8e62), the inspected Extensa evaluation conventions, and live SWDB code/test inspection on 2026-09-25. Source inspection is not execution evidence.

The public workflow testing boundary was explicitly confirmed during spec refinement. Implementation and experiment execution were explicitly authorized by the user on 2026-09-25; host and evidence rules remain in force.
