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
Landlock guard. SWDB first verifies the lane's full socket affinity and memory
binding, then confines the provider to one CPU from that socket. Reads are
confined to the workspace, toolchain, provider install, fresh provider home, and
selected runtime files, including the process's own memory/status metadata.
Persistent writes are confined to the workspace and fresh home; `/dev/null` is
also available as an output sink.

The CLI may make TCP connections on port 443. Claude shell commands pass through
one SWDB-owned executable prefix that applies an inner no-TCP layer and command
timeout. Codex has no verified shell-prefix setting: its commands inherit the
outer policy. An external connection trace rejects non-model-API TCP destinations
for either provider. Event audits also reject forbidden file access, login-file
commands, network commands, and unknown tools. ABI 4 leaves UDP unrestricted, and
the copied login file remains readable during the session; both residual risks
are recorded in the guard policy. The login copy is deleted after every session.
Real sessions fail closed when the guard or lane cannot be verified.

The tracer is a child subreaper outside Landlock, so it adopts detached descendants
even when helpers double-fork or start a new session. The observer pins PID plus
kernel start time, uses pidfds where available, and stops owned descendants before
the tracer. The 120-second tool timer excludes the tracer, recorded original CLI,
and, for native Codex, the exact installed `codex-code-mode-host` sibling while
directly parented by that original native process. Same-named copies and other
helpers keep the timer. The original CLI and service both count toward the full
16-thread and 32 GiB resident-memory caps; the overall provider-call budget still
applies. The policy records the selected installation root, and cleanup receipts
retain observed identities and any surviving descendants.

A required inherited seccomp filter protects the recorded evaluator/observer and
tracer identities against `kill`, `tkill`, `tgkill`, `rt_sigqueueinfo`,
`rt_tgsigqueueinfo`, and direct `pidfd_open`. The provider enters a separate session,
preserving ordinary helper signals, including `kill(0)`, without reaching supervisor
groups. Compatibility ABIs, including x32, are rejected. These narrow controls
protect supervisor continuity through the listed APIs; they do not provide general
hostile-process isolation.

Event auditing checks direct shell inputs, explicit nested shell bodies, Glob
search roots, executable paths and compiler file options. Unresolved substitutions,
delegated execution and opaque inline interpreter programs fail closed. Ordinary
workspace scripts and synthetic programs may run under the guard; auditing their
invocation does not prove the semantics of their source.

Both providers receive workspace guidance to use direct editing tools for source
changes and literal shell operands for workspace reads, builds, and synthetic runs.
It asks them to avoid inline interpreters, loops, heredocs, delegated execution,
and regex-based code transformations that cannot be safely audited. Guidance does
not guarantee compliance; the audit still fails closed.

On Linux, the adapter can replace the official single-command Codex npm wrapper
with its verified bundled native executable, including the pinned platform-package
alias. The receipt preserves the requested command and records the actual argv,
executable hash, and native CLI version. Custom commands retain their configured
launch path. Codex uses an empty, read-only `sqlite_home`; its unavailable-state
fallback avoids persistent SQLite state and worker pools even with `--ephemeral`.
Analytics and telemetry exporters are disabled. Apps, plugins, hooks, memory,
extra agents, and browser/computer access are disabled. Codex's bundled skills
and skill instruction catalog are disabled; host skill scanning is not asserted
to be disabled. Workspace guidance directs Codex to call the ordinary file and
shell functions directly. Code mode remains available, and any execution route
that exceeds the aggregate resource limits is rejected. Claude uses safe mode
and a limited local tool set.

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
model, effort, CLI version, workspace mode, guard policy, and audit result. Each
`attempts[].provider.workspace_manifest` records that attempt's derived workspace.
The proposal's `interpretation` retains the provider's explanation, generated patch, and unresolved
requirements. Raw stdout/stderr, events, computed diff, and connection trace remain
external artifacts linked by path and hash. `repair_budget` records the fixed repair limit, total provider-time
allowance, consumed provider seconds, and repair attempts already used. Each repair
also names its triggering evaluation and parent candidate; changing operator
configuration cannot increase the proposal's previously recorded limits.

An external deterministic provider is supported for contract tests and is explicitly
classified as a fixture. Its success does not establish general natural-language
understanding or an empirical gain. A real demonstration must include actual source
edits and independently checked native/simulated execution paths. A provider turn
or guard check alone does not satisfy those acceptance requirements.

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
limits the provider process tree, including its external `strace` launcher, to
16 aggregate threads and 32 GiB of aggregate resident memory. Tool commands have
a 120-second limit, and the workspace has a 5 GiB limit. Resource excess rejects
the attempt. Claude calls also carry a
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
