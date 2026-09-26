# Simulator trial identity

Updated: 2026-09-26 ET.

An execution request can identify its experimental cell with
`protocol_trial: {source_position: <integer>, repetition: <integer>}` even before
a comparison protocol is frozen. Both values are nonnegative integers; booleans,
floating-point numbers, missing keys, and extra keys are rejected. An explicit
trial requires a registered workload. Its `source_position` indexes the entire
registered ordered source list, and that entry must equal
`request.workload.source`. Selecting a one-source subset never renumbers the
registered position.

The adapter validates this identity before checkpoint creation or restoration
and retains it in `context.protocol_trial`. The actual primary timing and
correctness rows carry the same source, position, and repetition. A frozen
protocol additionally checks the repetition against its declared sample grid
and enforces all existing build, source, instrumentation, and model identities.
An unfrozen repetition is a declared cell label, not evidence that other
repetitions occurred. Distinct execution records and raw observations remain
necessary for actual repeated samples.

Legacy standalone requests without an explicit trial retain their existing
behavior. They do not acquire a global source position retroactively. Diagnostic
series must explicitly identify both primary and diagnostic executions and
compare their actual retained cell identities before linking observations.
Checkpoint compatibility continues to identify the modeled state, binary,
graph, source, and configuration; changing only the repetition label does not
require regenerating identical checkpoint state.

`tests/test_dx100_trial.py` drives the public adapter with a deliberately
reordered registered source list. It checks a nonzero position/repetition and
rejects malformed or mismatched labels before any simulator stage. These are
contract fixtures and provide no empirical timing or correctness evidence.
