# BFS rewrite worker contract

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

This is the implementation design for Tickets 04 and 05. The ensemble or labeled
test client selects the intent. The worker interprets that intent using the exact
source/profile package, returns edits, and submits those edits to the existing
source/capability/protection checks. It does not select a different strategy after
a correctness failure or regression.

## Provider boundary

The operator selects a provider configuration independently of the producer's
instruction text. A Claude Code adapter requests structured JSON with an
interpretation, a unified patch, and unresolved requirements. It supplies the
selected source, helper/header context, permitted files, protected inputs, and
original proposal. Claude runs without command or editing tools; only the checked
patch is applied by SWDB. The provider's stdout/stderr, command, version, elapsed
time, and result identity remain external artifacts linked from the proposal.

The proposal's `provider` field records the selected configuration, and
`interpretation` retains the provider's explanation, generated patch, and unresolved
requirements. `repair_budget` records the fixed repair limit, total provider-time
allowance, consumed provider seconds, and repair attempts already used. Each repair
also names its triggering evaluation and parent candidate; changing operator
configuration cannot increase the proposal's previously recorded limits.

An external deterministic provider is supported for contract tests and is explicitly
classified as a fixture. Its success does not establish general natural-language
understanding or an empirical gain. The real demonstration uses actual source edits
and the independently checked native/simulated execution paths.

Natural-language, structured-instruction, and annotated-source payloads share the
same worker. Structured instructions describe intent and requirements; they are
not a deterministic rewrite language. Annotated source must identify its source
path and include an annotation that requires an actual code change. Copying
comments unchanged is not a successful interpretation. Ambiguous source mappings
or unsupported requirements produce an unresolved result.

## Bounds and repairs

Operator-selected bounds are recorded before each provider call. Initial defaults
are one generation attempt, at most two build/correctness repairs, 300 seconds per
provider call, and a 900-second total provider budget. Claude calls also carry a
five-dollar API budget cap where supported by the configured account. These are
maximum attempts and provider time, not a promise of completion. Native builds and
executions have their own explicit budgets and remain independently retained.

A public repair request names a failed evaluation and its proposal. Only build or
correctness failures admit repairs. The worker receives the prior candidate and
failure evidence, preserves the original intent and edit scope, and creates a new
candidate identity. It records the trigger, interpretation, changed source, and
parent candidate. Budget exhaustion retains all prior candidates and evaluations.
A valid regression is returned as an outcome; it does not trigger tuning.

The evaluator-owned verifier, canonical graph input, trusted driver, and ROI
definition remain unchanged through generation and repairs. Passing a build or
producing a candidate is distinct from passing the structural correctness check;
profitability additionally requires the frozen comparison protocol.
