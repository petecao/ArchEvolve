# Three-way scan: estimating performance without cycle-level simulation

Date: 2026-10-06 (Eastern Time)
Mode: ARS `deep-research` three-way-scan (WHY / HOW / WHAT). A shortlist, not a literature review.
Purpose: ground Proposal B, the analytic evaluator for SWDB (correctness runs natively, speed is
estimated), and the coming discussion of Extensa-mode evaluation.

## Bottom line (read this first)

1. **Every surveyed paper exists because simulation is too slow for design-space search.** The
   field's answer is a model that is cheaper than a simulator but checked against one.
2. **The best-validated recipe is hybrid**: simple analytic bounds per component, plus a learned
   correction (Concorde: about 2% CPI error, more than five orders of magnitude faster than its
   cycle-level reference).
3. **Irregular memory access is where pure static analysis stops.** MAPredict predicts regular
   patterns statically but needs empirical observations for random access, and Aladdin models
   memory with a cache model plus DRAMSim2.
4. **LLMs alone are weak numeric predictors but good readers of profiles**: 64% roofline
   classification from source code alone, 100% when given profiling data (Bolet et al.).
5. **Gap for us:** none of the eight papers models a shared, programmable indirect-access
   accelerator (DX100) on irregular graph kernels without a simulator. That gap is where
   ArchEvolve's evaluator sits.

## Shortlist (8 papers, grouped by HOW)

**Group A: Static analysis + first-principles models**

## Kerncraft: A Tool for Analytic Performance Modeling of Loop Kernels
Source: arXiv 1702.04653 (Hammer, Eitzinger, Hager, Wellein); earlier version at PMBS 2015 (arXiv 1509.03778) | Year: 2017 | Link: https://arxiv.org/abs/1702.04653

- WHY: building analytic loop performance models by hand needs deep hardware knowledge and is tedious.
- HOW: from loop source code, problem size and a machine description, it builds Roofline and
  Execution-Cache-Memory (ECM) models automatically, with layer-condition analysis and a cache
  simulator as fallback.
- WHAT: predicts single-core performance and multicore scaling for streaming and stencil loop
  nests; demonstrated on a 25-point long-range stencil.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## MAPredict: Static Analysis Driven Memory Access Prediction Framework for Modern CPUs
Source: ISC High Performance 2022 (Monil, Lee, Vetter, Malony; ORNL) | Year: 2022 | Link: https://www.osti.gov/servlets/purl/1887689

- WHY: a runtime or a design-space search needs a kernel's LLC-to-DRAM traffic before running it;
  simulators are too slow for that.
- HOW: builds Aspen application models from annotated source at compile time, combines them with
  cache- and prefetcher-aware machine models from measurements on Intel CPUs, and takes user hints
  for dynamic information.
- WHAT: on 130 workloads, 99% average accuracy for streaming, 91% for strided, 92% for stencil;
  random access reaches up to 97% only by coupling static and empirical methods.
  - **Method weaknesses** (empirical; read: abstract, §1)
    - checked: found: external validity, conclusion conservatism | checked: none found: research hypothesis clarity | not checked: variable operational definitions, internal validity, statistical reporting completeness
    - Machine models come from experiments on Intel micro-architectures; this distorts results when the target's memory path differs, such as requests issued by an accelerator rather than the core's caches and prefetchers. [author-acknowledged scope, section: §1 "four micro-architectures of Intel"; the accelerator case is reader-inferred]
    - "Up to 97%" for random access depends on empirical observations; this distorts the result when no prior run exists for the input. [author-acknowledged, quote: "By coupling static and empirical methods, up to 97% average accuracy is obtained"]

**Group B: Compiler IR + dynamic trace**

## Aladdin: A Pre-RTL, Power-Performance Accelerator Simulator Enabling Large Design Space Exploration of Customized Architectures
Source: ISCA 2014 (Shao, Reagen, Wei, Brooks; Harvard) | Year: 2014 | Link: https://people.eecs.berkeley.edu/~ysshao/assets/papers/shao2014-isca.pdf

- WHY: RTL and HLS flows take hours to days per accelerator design, which makes large
  design-space exploration infeasible.
- HOW: takes C code to LLVM IR, runs it on representative inputs to build a dynamic data dependence
  graph (DDDG), then applies hardware constraints to that graph to model an accelerator without RTL.
- WHAT: performance within 0.9%, power within 4.9% and area within 6.6% of RTL, more than 100×
  faster; integrated with a cache hierarchy model and DRAMSim2, it exposes memory/datapath co-design.
  - **Method weaknesses** (empirical; read: abstract, §1, §2–2.3)
    - checked: found: external validity, internal validity | checked: none found: research hypothesis clarity | not checked: variable operational definitions, statistical reporting completeness, conclusion conservatism
    - Validated on static datapath accelerators; this distorts results for a shared, programmable accelerator with its own ISA and DRAM request reordering, such as DX100. [author-acknowledged scope, quote: "we focus on static datapath accelerators"; the DX100 case is reader-inferred]
    - The graph comes from a dynamic trace of one input; for graph kernels, this distorts results when the evaluated graph differs from the traced one. [reader-inferred]
    - Realistic memory behavior comes from DRAMSim2, a simulator, which our ArchEvolve-mode rule forbids. [author-acknowledged, quote: "integrating Aladdin with a full cache hierarchy model and DRAMSim2"; the rule conflict is reader-inferred]

**Group C: Analytic model + mapping search for accelerators**

## Timeloop: A Systematic Approach to DNN Accelerator Evaluation
Source: ISPASS 2019 (Parashar, Raina, Shao, Chen, Ying, Mukkara, Venkatesan, Khailany, Keckler, Emer) | Year: 2019 | Link: https://research.nvidia.com/publication/2019-03_timeloop-systematic-approach-dnn-accelerator-evaluation

- WHY: DNN accelerator design spaces are large, and no single architecture is best across workloads.
- HOW: a unified description of hardware topologies plus a mapper that searches how to schedule
  operations and stage data on each architecture, then projects performance and energy.
- WHAT: shows that dataflow and memory-hierarchy co-design dominates energy efficiency; released
  as an open-source tool.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

**Group D: Hybrid: analytic bounds + machine learning**

## Concorde: Fast and Accurate CPU Performance Modeling with Compositional Analytical-ML Fusion
Source: ISCA 2025 (Nasr-Esfahany, Alizadeh, Lee, Alam, Coon, Culler, Dadu, Dixon, Levy, Pandey, Ranganathan, Yazdanbakhsh) | Year: 2025 | Link: https://arxiv.org/abs/2503.23076

- WHY: cycle-level simulators such as gem5 are too slow for large-scale design-space exploration.
- HOW: simple analytical models estimate the performance bound each microarchitectural component
  imposes; the resulting compact performance distributions feed an ML model that learns the rest.
- WHAT: about 2% average CPI error across SPEC, open-source and proprietary benchmarks, more than
  five orders of magnitude faster than the reference cycle-level simulator; about 150 million CPI
  evaluations in about an hour.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

**Group E: LLM as predictor**

## Can Large Language Models Predict Parallel Code Performance?
Source: AI4Sys Workshop at HPDC 2025 (Bolet, Georgakoudis, Menon, Parasyris, Hasabnis, Estes, Cameron, Oren) | Year: 2025 | Link: https://arxiv.org/abs/2505.03988

- WHY: GPU performance usually needs profiling on target hardware, and that hardware is scarce.
- HOW: frames prediction as roofline classification (compute-bound vs bandwidth-bound) and tests
  LLMs on 340 HeCBench kernels with profiling data, zero-shot, few-shot and fine-tuned.
- WHAT: 100% accuracy given profiling data; up to 64% from source alone with reasoning models;
  fine-tuning needs much more data than the authors had.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

**Group F: LLM agents driving the search loop**

## AgentDSE: Reasoning-Augmented Architectural Design Space Exploration
Source: MLArchSys Workshop at ISCA 2026 (Wang, Shi, Kong, Boning, Wan, Du, Janapa Reddi), arXiv 2606.21836 | Year: 2026 | Link: https://arxiv.org/abs/2606.21836

- WHY: conventional DSE treats the evaluator as a black box and needs tens of thousands of evaluations.
- HOW: a general-purpose LLM coding agent reasons about bottlenecks and data reuse inside a
  simulator-in-the-loop search, with no fine-tuning; evaluators include Timeloop/Accelergy,
  MAESTRO (an analytical cost model) and ChampSim.
- WHAT: competitive or better design quality with up to two orders of magnitude fewer evaluations,
  plus inspectable reasoning traces.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## Beacon: LLM Multi-Agent Driven Hardware Design Space Exploration for Heterogeneous Multi-Chiplet Deep Learning Accelerators
Source: arXiv 2608.30932 (Li, Zhu, Cao, Li, Zhou), venue not stated | Year: 2026 | Link: https://arxiv.org/abs/2608.30932

- WHY: one evaluation of a heterogeneous chiplet design takes tens of minutes, so only tens of
  search iterations are affordable.
- HOW: hierarchical LLM agents read the evaluator's detailed reports (timelines, utilization, memory
  accesses, communication) to locate bottlenecks and propose candidates, with a 13-tool analysis
  toolbox and RAG memory; the evaluator is a modified GEMINI framework.
- WHAT: under the same 100-round budget, 25.1%–93.5% lower latency-energy-cost objective than
  random search, Bayesian optimization and reinforcement learning.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## Cross-paper synthesis

- **Common WHY:** simulators and RTL are too slow, or the hardware is not available, for the number
  of evaluations a design search needs.
- **Divergent HOW:** static first-principles models (Kerncraft, MAPredict); compiler IR plus a
  dynamic trace (Aladdin); analytic model plus mapping search (Timeloop); analytic bounds fused with
  ML (Concorde); LLM as predictor (Bolet et al.); LLM as search driver over an evaluator (AgentDSE,
  Beacon).
- **Strongest WHAT:** Concorde (about 2% CPI error, more than five orders of magnitude faster) for
  CPU cores; Aladdin (0.9% performance error vs RTL) for datapath accelerators.
- **Unresolved global gap** (bounded by these eight papers): no surveyed model estimates a shared,
  programmable indirect-access accelerator on irregular graph kernels without a simulator. The
  mechanism DX100 claims (reordering, interleaving and coalescing requests to raise DRAM row-buffer
  hit rate; Khadem et al., ISCA 2025) is exactly what the surveyed static models leave to
  measurement (MAPredict) or to a DRAM simulator (Aladdin).

## What this suggests for Proposal B (reader-inferred, for discussion)

1. Use the hybrid shape: analytic bounds per region (compute, memory bandwidth, accelerator
   throughput), then an LLM or learned correction only where bounds disagree with measurements.
2. Keep the instrumented native run for counts (trip counts, footprint, access-pattern mix):
   the literature needs empirical input for irregular access too.
3. Give the LLM the profile, not just the source: classification jumps from 64% to 100% with
   profiling data.
4. Make the evaluator emit a per-region bottleneck report, not one number; report-reading agents
   (Beacon) and reasoning agents (AgentDSE) improve with few evaluations.
5. Treat the DX100 memory model (row-buffer hits, coalescing) as the open research piece.

## Context source (not in the shortlist)

- Khadem, A., Kamalakkannan, K., Zhu, Z., Poptani, A., Gu, Y., Dominguez-Trujillo, J. B.,
  Talati, N., Fujiki, D., Mahlke, S., Shipman, G., & Das, R. (2025). DX100: A programmable data
  access accelerator for indirection. *ISCA 2025*. https://arxiv.org/abs/2505.23073 — 2.6× over a
  multicore baseline and 2.0× over a state-of-the-art indirect prefetcher on 12 benchmarks.

## Search record (for reproducibility)

- Date: 2026-10-06 ET. Tool: web search (standard and extended) plus publisher and arXiv pages.
- Queries: Aladdin pre-RTL LLVM DDDG; Concorde analytical-ML fusion; Kerncraft ECM roofline;
  LLMs predict parallel code performance; LLM agent accelerator DSE analytical cost model;
  Timeloop ISPASS 2019; analytical model indirect memory access gather DRAM; MAPredict;
  analytical model irregular graph accelerator DSE (no usable hit); DX100 ISCA 2025.
- Kept: papers that estimate performance without a cycle-level simulator, or that put an LLM in an
  evaluation or search loop. Dropped: Mira (static source + binary models, Cluster 2017; overlaps
  Kerncraft and MAPredict) and graph-accelerator architecture papers with no estimation method.
- Every entry was checked against its arXiv, publisher or institutional page. Read scope is stated
  per entry; most entries were read at abstract level only.

AI disclosure: this scan was produced with AI assistance (Claude, ARS deep-research three-way-scan
mode); Yan-Ru has not yet reviewed the sources.
