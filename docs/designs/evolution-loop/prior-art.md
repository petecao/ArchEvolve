# Prior work and the claim we should test

Reviewed October 8, 2026. Repository revisions are recorded in `sources.json`; none of these packages was installed or executed. Their code was inspected as reference material, not copied into ArchEvolve.

## Correction to the meeting assumption

**Prompt evolution is established prior work.** The claim that our distinguishing feature is simply “prompts change based on results” is not supportable. These sources make the distinction clear:

| Source | What was verified | Implication for ArchEvolve |
|---|---|---|
| [AlphaEvolve paper, §2.2 and ablation discussion](https://arxiv.org/html/2506.13131v1) | Describes meta prompt evolution: model-suggested instructions/context co-evolve in a separate database. It also distinguishes fixed context, stochastic formatting and rendered evaluation feedback. | Two linked candidate/prompt populations already have precedent. |
| [OpenEvolve README at 9196d876](https://github.com/algorithmicsuperintelligence/openevolve/blob/9196d8763300d1e46cc8b48cb0dc987966db3d48/README.md) | Custom/stochastic templates, artifact-aware context and a meta-evolution section are documented. The separate “self-modifying prompts” research-direction checkbox remains unchecked. | Do not claim all prompting is static; also do not infer that the unchecked default-loop feature is implemented from the example alone. |
| [OpenEvolve prompt-optimization example](https://github.com/algorithmicsuperintelligence/openevolve/blob/9196d8763300d1e46cc8b48cb0dc987966db3d48/examples/llm_prompt_optimization/README.md) | Demonstrates evolving prompt text as the optimization target. The [sampler](https://github.com/algorithmicsuperintelligence/openevolve/blob/9196d8763300d1e46cc8b48cb0dc987966db3d48/openevolve/prompt/sampler.py) assembles current program, metrics, history and artifacts. | Prompt optimization and changing context are usable baselines, with their scope stated. |
| [CodeEvolve README](https://github.com/inter-co/science-codeevolve/blob/c077959e1ab24b060aaa6d4c563bca2e9cbe8617/README.md) and [evolution engine](https://github.com/inter-co/science-codeevolve/blob/c077959e1ab24b060aaa6d4c563bca2e9cbe8617/src/codeevolve/evolution.py) | The engine maintains `prompt_db`; exploration can call `run_meta_prompting` when enabled and add a child prompt. The [sampler](https://github.com/inter-co/science-codeevolve/blob/c077959e1ab24b060aaa6d4c563bca2e9cbe8617/src/codeevolve/prompt/sampler.py) conditions prompt revision on a program/result. | Co-evolution is not unique to our proposed loop. This audit does not verify the framework's reported benchmark results. |
| [GEPA paper](https://arxiv.org/abs/2507.19457) and [project](https://github.com/gepa-ai/gepa/tree/fb1ed589fd83372caef499cffc2c73173d3b096b) | Reflective prompt evolution uses execution feedback and evaluation to propose/test improvements. | Reflection and Pareto-inspired prompt optimization are relevant comparison methods. |
| [OpenAI prompt-optimization guidance](https://developers.openai.com/api/docs/guides/prompt-optimizer) | Recommends specific feedback/graders and evaluation plus manual review of revised prompts, since some inputs can regress. | Adopt the evaluation principle. The proposed system has no dependency on the hosted optimizer or a specific provider/API. |

## Working research hypothesis

**An evidence-aware hardware co-design loop may produce useful, legally expressible compositions more efficiently when its search strategy adapts to structured hardware/software feedback.** That is a hypothesis to test, not a novelty or performance result.

The hardware-specific work is concrete: preserve source/edition and typed-library pins; reason over placement, dataflow, finite storage, response identity and synchronization; separate unknown model coverage from failure; compare area/performance only within compatible cohorts; and learn from implementation feedback without changing the evaluator or inventing hardware support.

A new hybrid or component modification may be novel relative to the current catalog. Record that delta and the nearest seeds explicitly. Claims of novelty relative to the research literature require a broader review of the actual resulting design; this short framework review cannot establish them.

## What to borrow and what to keep local

Borrow the concepts of explicit mutation regions/deltas, lineage, archived failure feedback, diverse parent selection, cascaded checks and separate prompt evaluation. Keep ArchEvolve's proposal records and existing Peter → Josh/Eric → Peter → Yan-Ru → evaluator handoff. Avoid taking on an entire framework, database, model backend or benchmark execution system before their interfaces are needed.

Any later code reuse needs the relevant license/attribution review. This contribution contains original reference-policy code and design documents; there is no vendored OpenEvolve/CodeEvolve/GEPA code.
