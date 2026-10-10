# Strategy reflection request — draft template

Inputs: the fixed core/task/policy hashes, parent strategy, a frozen batch of candidate deltas and attributed feedback, and the proposal-validation budget. This is a future model request, not an executable step in the offline prototype.

Identify a recurring failure or missed opportunity supported by the batch. Distinguish hardware incompatibility, an absent interface/domain/model input, software-lowering error, evaluator/infrastructure failure and a completed negative result. Do not infer a general rule from one result or penalize an architecture for a tool failure.

Propose a small change only to `search_focus`, `mutation_preferences`, `reasoning_guidance` or `example_refs`. Preserve core/task/policy content pins. Cite the feedback IDs and describe the expected effect, possible regression and a matched test that could falsify the proposal. If feedback is insufficient, recommend retaining the current strategy.

Avoid benchmark-answer copying and rules such as “offload more because placeholder accelerator time is zero.” Preserve counterexamples and source scope. Do not edit correctness checks, evaluator scoring, model/cost units, comparison cohorts, budgets or the held-out task set.

Return a child strategy envelope and a separate trial proposal. Its status is pending review and paired evaluation; you do not promote yourself or certify that the new strategy is better.
