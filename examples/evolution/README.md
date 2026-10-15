# Synthetic offline evolution example

`demo-summary.json` is a compact summary of the deterministic fixture in
`archevolve/evolution_demo.py`. Every timing, token receipt, hardware component,
review and generated response is synthetic. The reported trial gains are chosen
fixture values, not performance results or evidence of autonomous learning.

The full trace is intentionally generated locally instead of committing a large
database. See [runtime instructions](../../docs/designs/evolution-loop/offline-runtime.md).
Its content-addressed objects resolve the summary's references. Re-running the
same source with a fresh store produces the same object references and outcomes.
The demo refuses to initialize an existing campaign rather than overwriting it.

The fixture exercises these transitions:

1. Development search records successes and unhelpful candidates.
2. A conditional rule is proposed and explicitly admitted as search guidance.
3. A fixed-reflector strategy revision shows no benefit and remains inactive.
4. An alternative reflector produces a better strategy under the toy evaluator
   and is activated following an explicitly synthetic review.
5. The active reflector authors a strategy revision and its own next revision.
6. The next reflector revision shows no extra benefit and is not activated.
7. Rollback restores the original reflector while keeping all experiment memory.

For non-synthetic work, connect trusted proposal/evaluation adapters, supply
actual content-bound evidence, and record a real semantic review. No model API,
benchmark executable, hardware simulation or catalog mutation occurs here.
