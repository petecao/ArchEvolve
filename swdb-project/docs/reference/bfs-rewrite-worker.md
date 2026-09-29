# BFS rewrite worker contract

Navigation updated: 2026-09-29 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-29 (Eastern Time)

The proposal producer or labeled test client selects the intent. The rewrite
provider interprets that intent using the identified
source/profile package, returns edits, and submits those edits to the existing
source/capability/protection checks. It does not select a different strategy after
a correctness failure or regression.

## Provider boundary

The operator must pass `--provider-config`, independently of the producer's
instruction text. Codex is the default kind (`gpt-5.6-sol`, `xhigh`); Claude is the
alternative (`claude-sonnet-5-5`, `high`). These model and effort settings are
fixed in code; configurations that override them are rejected.

Workspace mode is the default. SWDB derives the provider workspace from the
source snapshot, selected regions, profile package, selected strategy, required
operation headers, and explicitly named `visible_files`. It hides evaluator
inputs, workload files, records, other candidates, and project instruction files.
Exact protected verifier fragments mixed into source are replaced with immutable
placeholders and restored before candidate construction. The provider-visible
profile package is a labeled projection; the original sealed package is retained.

The provider may read, search, edit, build, and run small synthetic tests. Temporary
test sources must be removed before the session ends. The final response contains
only `interpretation` and `unresolved`; SWDB computes the source diff, discards
build outputs, and rejects unapproved new files or edits to immutable inputs.
Existing protected-input and actual-code-change checks still apply.

Real providers run only on mbit10 inside an owned socket lane, under SWDB's Linux
Landlock guard. Reads are confined to the workspace, toolchain, provider install,
and fresh provider home; writes to the workspace and fresh home. The CLI may make
TCP connections on port 443. Claude shell commands receive an inner no-TCP layer.
Codex has no verified shell-prefix setting: its commands inherit the outer policy,
and an external connection trace rejects non-model-API TCP destinations. Event
audits also reject forbidden file access, login-file commands, network commands,
and unknown tools. ABI 4 leaves UDP unrestricted; this accepted limitation is
recorded in the guard policy. A login-file copy is deleted after every session.
Real sessions fail closed when the guard or lane cannot be verified.

For DX100 from-scratch proposals, use the registered
`bfs-dx100-scalar-only-20260929-a1.source` snapshot. It removes `TDStepMAA` and
`DOBFSMAA`, their state, and the accelerator selection branch. The full snapshot
remains available for explicitly declared author-code reuse, including T17.

Set `workspace: false` to request the retained prompt-only patch/full-file route.
Codex complete-file output uses strict path/content pairs, converted to the existing
file mapping before diff construction. Prompt-only real sessions remain guarded;
any emitted tool activity is rejected. Codex prompt-only input is limited to
96 KiB because the prompt must be an argument with empty stdin.

The proposal's `provider` field records the selected configuration, resolved kind,
model, effort, CLI version, workspace manifest, guard policy, and audit result. Its
`interpretation` retains the provider's explanation, generated patch, and unresolved
requirements. Raw stdout/stderr, events, computed diff, and connection trace remain
external artifacts linked by path and hash. `repair_budget` records the fixed repair limit, total provider-time
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
are one generation attempt, at most two build/correctness repairs, 1200 seconds per
provider call (at most 1800), and a 3600-second total provider budget. The guard
limits sessions to 16 threads, 32 GiB of memory, 120 seconds per tool command,
and a 5 GiB workspace. Claude calls also carry a
five-dollar API budget cap where supported by the configured account. Codex records
`budget_usd_enforced: false`; a ChatGPT subscription does not provide that cap. These are
maximum attempts and provider time, not a promise of completion. Native builds and
executions have their own explicit budgets and remain independently retained.

A public repair request names a failed build/correctness evaluation. A
`provider_unavailable` outcome caused by a usage limit can also be retried using
the proposal ID when no candidate exists. Unavailable calls consume elapsed time
but do not consume a repair. Repairs retain the first attempt's kind, model, and
effort; a mismatch is refused. Historical receipts without model settings remain
valid and reusable, but a repair cannot assert a match to an unknown setting.
The provider receives the prior candidate and
failure evidence, preserves the original intent and edit scope, and creates a new
candidate identity. It records the trigger, interpretation, changed source, and
parent candidate. Budget exhaustion retains all prior candidates and evaluations.
A valid regression is returned as an outcome; it does not trigger tuning.

DX100 candidate compiler failures retain the originating proposal and candidate.
A failed `candidate_compile` subprocess can enter the same repair path only when
its request/source hash, source snapshot, complete-call adapter, nonzero compiler
return code and retained log identity agree. Model builds, source validation,
discovery failures, timeouts and resource exhaustion do not become compiler-repair
opportunities merely because they precede execution. The original failed record
remains unchanged and the repair still consumes the proposal's existing limit.

The evaluator-owned verifier, canonical graph input, trusted driver, and ROI
definition remain unchanged through generation and repairs. Passing a build or
producing a candidate is distinct from passing the structural correctness check;
profitability additionally requires the frozen comparison protocol.

## Unmodified baselines

The `baseline-candidate` command materializes a verified source snapshot without a
rewrite proposal or fabricated diff. Its `artifact_role` is `source_baseline`, and
its content hash must equal the starting snapshot. It remains `unverified` until
the independent evaluator checks actual timed results. The absence of `proposal`
means that repair and rewrite-route coverage do not apply to this artifact.
