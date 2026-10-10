# How to test the loop and its prompt adaptation

## Stage A: validate the protocol without a model

Use hand-authored proposals and feedback to verify lineage, immutable core/task/policy pins, correct source-region identities, retention of failures, and explicit `needs_information` outcomes. Test that placeholder timing, missing cost, different workloads/model versions, incomplete correctness or a failed intended-path witness never become a performance winner. The small reference-policy tests cover part of this stage; they do not run an evolutionary search.

## Stage B: bounded structural search

Use the reviewed BFS hybrid as a guided reference and construct a small development set: sparse and dense frontier behavior, tails/empty ranges, long rows, duplicate destinations, and a separate synthetic two-chain access case. Dataset identities and the source-to-IR partition must be fixed. Real and synthetic workloads remain labeled.

Initially score protocol outcomes: representation validity, explicit operation/result matching, resource/ownership/completion coverage, useful requests for genuinely missing information, reproducible proposal deltas and progress to a reviewed software handoff. Reviewer feedback must distinguish an impossible mapping from missing data/tool failure. An LLM saying its proposal is good is not a correctness or performance result.

## Stage C: quantitative evolution when inputs exist

Use a non-placeholder performance model with a declared validity domain and parameterized cost model, then later matched target measurements. Require functional correctness and an intended-path witness before modeled ranking, and exact-target correctness/witness evidence for target-measured ranking. Compare fixed workload/root/thread/ROI/baseline cohorts. Include newly added host/transfer work and the modeled overlap/contending resources.

Do not build an impressive-looking Pareto curve from unknown area or assumed zero device time. Keep model-based planning and target-measured frontiers separate. Report uncertainty, repeats and invalid/inconclusive rates as well as retained candidate points.

## Ablations

| Arm | Strategy | Architecture space | Purpose |
|---|---|---|---|
| A | Fixed strategy, dynamic feedback context | Placement/composition/scheduling plus legal tuning | Main static-prompt baseline. |
| B | Adaptive strategy, identical feedback availability | Same as A | Test the incremental effect of persistent prompt changes. |
| C | Fixed strategy | Parameters only within fixed admitted architectures | Separate architectural search gains from knob tuning. |
| D | Adaptive strategy | Parameters only | Check whether prompt adaptation helps tuning differently. |
| E | Fixed strategy, reduced failure context | Same as A | Attribute gains from feedback retrieval itself; optional after A/B. |

Use the same total generation-token/call budget and evaluator budget, counting reflection and prompt-validation work in B/D. Fix model/settings and parent/task sampling schedules where possible; record nondeterminism and repeat runs. Keep the evaluation rules outside the evolving text. A prompt comparison should use a frozen parent/task snapshot so a lucky stronger parent is not credited to a new prompt.

Development examples may guide reflection. Validation tasks select versions with explicitly tracked repeated use. Final held-out tasks remain unseen until reporting and are never fed into prompt updates; once exposed, they cease to be held-out. Rediscovering a provided hybrid is a guided sanity check, not evidence of de novo discovery.

## Metrics and promotion

- Per unit search budget: valid proposal rate, reviewed feasible mappings, useful distinct proposals and executable/verified candidates.
- When eligible data exists: latency/area Pareto improvement under a fixed reference/normalization, area-budget performance and uncertainty. Hypervolume is optional and requires a declared common reference point.
- Prompt trials: change in those outcomes, regressions on mandatory checks, model/evaluator cost, and robustness across workload families. Do not reward prompt fluency, a single high-scoring child, or the number of claimed offloaded instructions.
- Keep a parent strategy until the revised strategy has sufficient matched evidence and passes initial human review. Record accepted/rejected revision IDs, feedback/trial pins, decision rationale and rollback target.

Small pilot budget proposal: four design proposals per epoch, three epochs, at most one proposed strategy revision between epochs. Stop earlier if all remaining work requires missing inputs; do not spend the budget repeating the same request. Tune these search-control budgets after observing costs.

## What is still needed

Peter's region-cost/run bindings, Eric's cost/parameter/model domains, software/evaluator feedback adapters, reviewed executable mappings, and an explicitly selected live runtime are needed for later stages. The current offline preference stays in effect. No performance improvement, prompt improvement or novelty is claimed by this design package.
