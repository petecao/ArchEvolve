# Unbounded finite readiness delay: source audit — 2026-10-16 ET

Recommendation: retain the present partial-correctness C/WP semantics and develop a separately identified WhyML conditional-termination VC. WhyML mathematical `int` state supplies an arbitrary finite rank without a C-integer ceiling. This is a prospective encoding recommendation, not a parser check or proof result. No compiler, version command, prover, formal fixture, SSH or actual evaluation was invoked. No repository file was changed.

## What the installed WP source establishes

The pinned Frama-C33 installation generates ordinary integer loop-variant obligations `0 <= old_rank` and `new_rank < old_rank` in `cfgAnnot.ml:441–451`. It does not require a finite global maximum. But a rank expression must denote real changing logical state; syntax alone does not supply one.

* ACSL model-field reads, updates and offsets explicitly stop as not implemented (`LogicSemantics.ml:114,129,147`; `RefUsage.ml:472`). That direct approach is unavailable in this WP implementation.
* A bare label-polymorphic declaration such as `logic integer rank{L}();` does not create mutable state: `LogicCompiler.ml:729–740` warns that a declaration with labels and no read dependencies is interpreted as reading nothing. A changing label is insufficient. Adding a dependency on unchanged finite C state cannot distinguish arbitrarily many repetitions of the same state either.
* Generalized variants call `check_variant_relation` (`cfgAnnot.ml:183–193`), which announces well-foundedness as a hypothesis. A custom relation therefore needs a separate well-foundedness proof; it is not a solution by itself.
* A machine-typed ghost countdown still imposes its finite type range. The ACSL specification permits logical types in ghost code, but the implementation manual explicitly warns about incomplete ghost/model support. This read-only audit has **not** established an accepted, mutable mathematical-integer ghost declaration through the installed C frontend and WP. Do not report that candidate as supported without a later narrowly admitted parser/VC control.

The [Frama-C33 ACSL implementation manual](https://www.frama-c.com/download/frama-c-acsl-implementation.pdf), §§2.5 and2.13, distinguishes integer variants, ghost language and implementation limitations. `terminates false`, assumed well-foundedness, `admit`, or desired-result axioms would not establish the requested theorem.

## A principled separate VC

Use an abstract WhyML transition system with a mathematical `int` rank and quantify over **every** finite initial nonnegative rank. The [Why3 language reference](https://why3.org/doc/syntaxref.html) distinguishes mathematical integers from machine integers and supports mutable state and variants. The installed `int.mlw` provides the integer theory; `ref.mlw` provides mutable references and decrement. This route has no global C-counter bound.

For a pending command/dependency closure, make the relied-on environment relation explicit:

1. A lifted initial state has a finite rank `n >= 0`.
2. Each unsuccessful poll transition has a lifted successor with `0 <= n_next < n`.
3. A successful poll satisfies the separately proved readiness/closure/visibility relation.
4. Source-to-model simulation preserves these relations, including dependency DAG, state ownership, inactive bytes, registration and mapping obligations.

The variant argument discharges termination from1–2. Step3 establishes the result from an actual ready observation, rather than assuming the desired source postcondition. Require a consistency/witness model for1–2 and a negative control that admits infinite-zero behavior when the liveness premise is absent. WhyML `any ... ensures ...` produces an existence VC; an abstract `val` contract assumes existence. Do not confuse a satisfiable arbitrary-natural choice with a prophecy witness for the source's future polls.

Arbitrary finite delay is compatible with a per-trace natural countdown: the number of remaining false observations. That is a witness/prophecy over future behavior, not generally a deterministic function of current concrete state. Bare weak fairness need not provide a single natural state-ranking for every infinitely branching system. The accepted environment premise must explicitly guarantee the lifted rank, or a separate temporal/fairness theorem must construct it. This is a disclosed rely condition, not a proved device fact.

Keep the model non-extracted, or enforce ghost noninterference: a ghost rank must not decide an observable C/WhyML readiness result. A finite acyclic dependency closure can use a finite tuple/sum of residual ranks, with separate proof of command issuance/dependency termination. A poll-loop rank alone does not prove an enclosing unbounded issuance loop terminates.

## Integration choices

| Option | Assessment |
| --- | --- |
| Stock WP variant over a genuinely supported mathematical mutable ghost | Best direct fit if later admitted parser/VC controls establish support; currently unconfirmed. Model fields and label-only logical functions do not supply it. |
| Separate WhyML rank VC plus checked source-transition correspondence | Recommended next prototype. Identify/hash translator, environment premise, witnesses, emitted VC, runtime and proof record. Keep C/WP safety evidence separate until the composition theorem is reviewed. |
| Extend WP with an explicit unbounded logical environment-state component | Principled but larger trusted implementation change; requires state-update/frame semantics and independent regression controls. |
| Bounded C counter or abstract eventual-success axiom | Does not satisfy the requested unrestricted finite-delay proof. |

The existing `t28-finite-progress-decision-20261016.md` already declares the assumption owner and pending ticket59 acceptance. Preserve that boundary: no established gem5 fairness theorem, ticket28 closure, current0.2 mapping or total public proof follows from this audit. Parser/model controls and any actual proof remain prospective and coordinator-admitted.
