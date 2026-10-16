# Conditional readiness rank VC — 2026-10-16 ET

This is an inert mathematical prototype. No Why3 parse/type check, VC generation,
prover, version probe, compiler, provider or SSH command has run for it. This promoted prototype directory contains prospective sources and plans only;
it establishes no ticket, source-wrapper or device theorem.

`readiness_rank.mlw` encodes a prospective proof of the conditional statement by ghost recursion
over mathematical integers. Its parameters are a fixed `ready: int -> bool`
observation sequence and a separate prophecy `rank: int -> int`. At every future
index the rank is nonnegative; a false observation strictly decreases the next
rank. The only branch is `if ready start`. The rank appears in premises,
the checked assertion and the variant, never in the readiness decision. The
conclusion is an existing true observation at some index at or after `start`.

The false branch supplies nonnegativity and strict decrease for recursion at
`start+1`; its future-tail premises follow by integer order. The recursive result
also lies after the original start. The true branch has witness `start`. A rank
of zero cannot coexist with a false observation and a nonnegative successor.
This is ordinary well-founded descent on nonnegative mathematical integers,
with no custom relation or assumed well-foundedness obligation.

`delay_family.mlw` supplies an explicit satisfiable family for every `n >= 0`:
`ready_n(k) = (n <= k)` and `rank_n(k) = max(0, n-k)`. There is no upper bound on
`n`. For `0 <= k < n`, the next residual rank is one smaller, including the final
step to zero. At `n` readiness is true. At `n=0` it is true immediately. The
rank is a witness for this independently defined sequence, not an implementation
that returns true because the rank reached zero. The family theorem is a
separate VC to prove; it is not declared as an axiom.

`no_progress.mlw` has two independent modules. One encodes a prospective proof
that the constant-false sequence has no future true observation. The other deliberately requests the
false unconditional eventual-readiness goal and must remain non-Valid. It imports
no conditional theorem, consistency lemma or desired-result assumption. This is
the absent-premise counterexample, not a hardware counterexample.

The environment must supply the lifted rank relation for the actual fixed future
observations. This artifact does not construct prophecy from weak fairness, prove
gem5 scheduling/memory fairness, establish MMIO/source correspondence, cover an
enclosing command-issuance loop, or discharge dependency, byte-preservation,
ownership, registration and visibility obligations. Those remain separate. The
declared liveness assumption and its pending ticket59 review keep their existing
boundary in `t28-finite-progress-decision-20261016.md`.

The installed primary sources give the syntax basis: `int.mlw` lines374–378 use
an `int -> bool` argument in an executable conditional, lines443–444 use an
`int -> int` function, and lines694–698 use `let rec lemma` with an integer
variant. `witness.mlw` lines49–57 demonstrate recursive ghost lemmas and branching
on a fixed predicate argument. This prototype imports only `int.Int`; it does
not import Witness, custom well-founded relations or their axioms. Exact source
and candidate runtime hashes are in `manifest.json`.

`type_only_commands.json` proposes three serial syntax/type-only calls, with the
18-line core first. `fresh_vc_commands.json` is a separate, later admission: prove
every generated core, consistency and all-false-counterexample VC in fresh calls,
then run the deliberately false goal alone and require a classified non-Valid
result. Reject empty selections, missing variant/postcondition tasks, parser/tool
failures, resource failures, unexpected imports or changed hashes. Dump and audit
the generated contexts before accepting the main proof; the recursive hypothesis
is justified only together with all generated variant obligations. A command's
exit status alone is not acceptance.

The command plans contain placeholders and are not launch scripts. The Mac
installation's read-only file hashes are a candidate context, not a pin for an
x86_64 run. Root must bind and review the actual Why3/config/stdlib/prover/driver
identities, exclusive slot/lane, one worker, 8 GiB RSS watchdog and remaining wall
budget before either stage. No cache/session replay, configuration detection,
execution or extraction is proposed. Read-only future task emission also remains
part of that formal-tool admission.

The [WhyML reference](https://why3.org/doc/syntaxref.html) describes ghost lemmas
and variants; the [Why3 tool manual](https://why3.org/doc/manpages.html) specifies
`--type-only`, selected theories, fresh `prove` calls, task printing and solver
result classes. The installed source files, rather than a claimed parser result,
are the basis for the present syntax choice. Type support and proof success are
still unverified.


The agreed TDD seam is the standalone Why3 type/VC workflow plus the explicit
arbitrary-delay witness and absent-premise negative. This promotion is authoring
only: no RED/GREEN test status is assigned before a coordinator-admitted run.
File-hash and lexical checks are metadata checks, not parser or proof acceptance.
The existing `prototype/28-proof-semantics/` implementation and current method
mapping are outside this prototype's scope.
