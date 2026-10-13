# Reflector revision request

This template describes the `revise_reflector` operation. It is not a live model
connection. An adapter receives the current reflector sections, fixed core,
current search strategy, development observations with candidate/evaluation
payloads, the strategy decisions that produced them, and reviewed learned rules.

Propose a child of the current reflector. Output exactly these text fields:
`evidence_selection`, `diagnosis`, `generalization`, `revision_method`.

Use downstream evidence to identify a weakness in the improvement procedure
itself. The requested change may concern which observations to compare, how to
diagnose a failure, or how narrowly to generalize a lesson. Do not merely copy a
successful hardware design into the procedure. The current reflector's editable
`revision_method` guides this proposal, so an accepted version can participate in
producing its successor. Envelope validation and acceptance remain external.

The core, task splits, hardware catalog, evaluator, correctness checks, mutation
scope, budgets and promotion criteria are fixed. Do not invent a measured benefit.
A candidate revision is only data until an independent paired trial and recorded
semantic review approve it. No generated Python is imported or executed.
