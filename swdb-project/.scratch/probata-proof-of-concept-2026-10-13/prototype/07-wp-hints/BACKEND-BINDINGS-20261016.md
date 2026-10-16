# Source-to-backend binding observer

2026-10-16 ET. Prospective preparation only; root owns compilation and formal
admission. The original b9 canonical C/header bytes and all retained actuals stay
unchanged. This observer adds no contract, goal, memory fact, or proof result.

`helper_backend_bindings.ml` observes the public `Wpo.add_modified_hook`, which
the pinned `Wpo.ml` invokes when adding a goal and updating its results. It keeps
the first available snapshot for each exact `Wpo.get_gid`, and exports every
current goal after the WP phase. The first snapshot records whether the goal was
already computed. It is not asserted to be universally unreduced. Source
property, function, file, line, smoke classification, short ID, and the exact
`WpPropId.get_propid` used by `ProverWhy3.prove_prop` bind both snapshots.

The observer reads `GOAL.get_descr`, then formats the returned sequent with
`Pcond.pretty` in the existing WP context. It never calls `compute_descr`,
`compute_proof`, `reduce`, `resolve`, `set_result`, or property-status updates.
Before/after computation, triviality, and result rows are checked for observer
stability. Public API and native compilation remain an actual-budget gate.
Current sequent formatting is diagnostic data, not a proof certificate or a
machine-checked source/Why3 equivalence theorem.

The primary scheduler matters: `register.ml` schedules all selected goals, while
`ProverTask.prove` calls `simplify` before `run_prover`. Qed can therefore close a
source goal before `ProverWhy3.build_proof_task` exports it. The latter builds an
actual Why3 task, then returns `NoResult` under `-wp-gen` before driver invocation,
driver task printing, or external solving. Every source row must be retained.
An absent backend export is acceptable for diagnostic closure only when its exact
observer row records internal Qed validity or an already trivial sequent. An
unclassified omission is a refusal, never a fabricated empty task. Any trivial
closure of a missing-store or wrong-cell payload initializedness goal is an
explicit potential qualification failure requiring source/formula diagnosis.

The next inert recipe uses unchanged positive/missing-store/wrong-cell C units,
all 20 helper bodies and each root, full RTE/initializedness/smoke inventories,
`Typed`, one worker, no cache, and a fresh CVC5 sentinel configuration under
`-wp-gen`. It imports no custom theory or lemma. No invariants, init assumptions,
mask resets, havoc facts, unrolling, or goal filtering are permitted. All task
text and exact warning continuations are retained. Source refinement, physical
alignment, normal-return summary ABI trust, initialization/lifetime qualification,
OpenMP scope, full TD proof, and counted-provider acceptance remain separate.
