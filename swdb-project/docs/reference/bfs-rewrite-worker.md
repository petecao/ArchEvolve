# BFS rewrite worker contract

Navigation updated: 2026-09-30 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-30 (Eastern Time)
Updated: 2026-10-05 (Eastern Time): split thread caps and lane CPU check (ticket 74)

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
operation headers, and explicitly named `visible_files`. Required-operation headers
are include paths, so `gem5/m5ops.h` matches a snapshot's `include/gem5/m5ops.h`; a
header absent from the snapshot must be a hash-identified regular file inside the
application tree. Named `visible_files` must already be snapshot files: they are
recorded declarations and cannot add author code that a snapshot (such as the
scalar-only DX100 snapshot) removed. It hides evaluator
inputs, workload files, records, other candidates, and project instruction files.
Exact protected verifier fragments mixed into source are replaced with immutable
placeholders and restored before candidate construction. The provider-visible
profile package is a labeled projection; the original sealed package is retained.

The provider may read, search, edit, build, and run small synthetic tests. Temporary
test sources must be removed before the session ends. The final response contains
only `interpretation` and `unresolved`; SWDB computes the source diff, discards
build outputs, and rejects unapproved new files or edits to immutable inputs. Build
outputs are classified before the editable patterns, so a pattern such as `src/*`
cannot admit a binary, and source helpers left under `build/` still fail.
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
are recorded in the guard policy. The login copy is deleted after every session,
together with any hard link or byte copy of it left in the provider home or workspace
(`login_copies_removed`). Real sessions fail closed when the guard or lane cannot be
verified, before any login file is copied. A fixture command that resolves to an
installed `codex` or `claude` CLI is refused.

Because Codex tool commands keep outer port-443 access, Codex sessions also refuse
`io_uring_setup` and `MSG_FASTOPEN` sends in the inherited seccomp filter: those
calls could open a connection without the `connect()` call the trace observes. The
model-API check matches IP addresses, so a shared CDN address cannot distinguish
hosts; this residual risk is recorded in the guard policy.

The tracer is a child subreaper outside Landlock, so it adopts detached descendants
even when helpers double-fork or start a new session. The observer pins PID plus
kernel start time, uses pidfds where available, and stops owned descendants before
the tracer. The 120-second tool timer excludes the tracer, recorded original CLI,
and, for native Codex, the exact installed `codex-code-mode-host` sibling while
directly parented by that original native process. Same-named copies and other
helpers keep the timer. Since ticket 74 (2026-10-05) the tracer, the original CLI
and that service form the provider runtime, capped at 64 threads; every other owned
process (tool commands and their descendants, detached or not) shares the 16-thread
cap. A runtime-cap overrun is recorded as a harness limit (`scope: runtime`), not as
the model's work. All owned processes share the 32 GiB resident-memory cap, and every
thread must stay on the lane's CPUs; the overall provider-call budget still applies. Only the first observed service instance is exempt; a tool shell that
later execs the same binary keeps the timer. The thread, memory and size caps are
polled every 0.1 s (`limit_enforcement` records how each is enforced); inner Claude
tool commands also get a kernel address-space limit of 32 GiB. The 5 GiB size cap
covers the workspace and the provider home together. The policy records the
selected installation root, and cleanup receipts retain observed identities and any
surviving descendants.

A required inherited seccomp filter protects the recorded evaluator/observer and
tracer identities against `kill`, `tkill`, `tgkill`, `rt_sigqueueinfo`,
`rt_tgsigqueueinfo`, and direct `pidfd_open`. The provider enters a separate session,
preserving ordinary helper signals, including `kill(0)`, without reaching supervisor
groups. Compatibility ABIs, including x32, are rejected. These narrow controls
protect supervisor continuity through the listed APIs; they do not provide general
hostile-process isolation.

Event auditing checks direct shell inputs, explicit nested shell bodies, Glob
search roots, executable paths and compiler file options. Shell words and Glob
patterns are brace-expanded first, and a wildcard word must have a static root inside
the workspace with no parent traversal and no dot-leading part that can match `..`;
a `cd` target must be one literal directory. Unresolved substitutions,
delegated execution and opaque inline interpreter programs fail closed. Quiet SED
with one literal decimal line/range print expression remains available for source
previews. Compilers accept checked file operands and a bounded set of literal
build options; unfamiliar routing, profile and configuration options are refused.
Compiler forwarding and response files, TAR commands, ripgrep preprocessing/configuration
selectors, unresolved execution/configuration wrappers, and filesystem-controlling
environment overrides are refused. Literal values in attached file options are
checked for known selectors; unfamiliar filesystem-bearing attachments, including
short forms without `=`, are refused. Git
output and DD input/output selectors are checked even for bare filenames, and
mutable file-list inputs are refused. Echo/printf data, compiler data flags and
known search-pattern positions retain their literal text semantics. Recognized
network utilities are classified at executable positions; quoted names remain
ordinary data. Package and dependency managers (for example npm, npx, cargo, go, gem,
uv, uvx, pipx) and versioned pip executables are refused on every subcommand. Named-remote Git queries and updates are refused, including
`ls-remote` and `remote update/show/prune`, even when particular flags could avoid
network access. The bounded remote-option grammar accounts for long-option
abbreviations and bundled short flags; unsupported remote mutations and archive
commands are refused. Python invocations use a bounded interpreter-prefix grammar
before checking the script operand: supported flags and their values are consumed,
network modules are refused, other modules outside a short offline list (such as
`json.tool`, `py_compile`, `unittest`, `pytest`) fail closed, and unknown prefix
controls fail closed. Arguments
after a checked script retain their data role. Ordinary local Git status/diff operations remain available. Ordinary
workspace scripts and synthetic programs may run under the guard; auditing their
invocation does not prove the semantics of their source. Claude content blocks
other than text, thinking, tool use and tool results (for example server-side tool
use) fail the audit. A completed session whose log is empty or lacks its terminal
event (`turn.completed` or `result`) also fails.

Both providers receive workspace guidance to use direct editing tools for source
changes and literal shell operands for workspace reads, builds, and synthetic runs.
It asks them to avoid inline interpreters, loops, heredocs, delegated execution,
and regex-based code transformations that cannot be safely audited. Compilers run
directly, with literal file options. Guidance does
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

The proposal's `provider` field records the latest attempt's configuration,
resolved kind, model, effort, CLI version, workspace mode, guard policy, and audit
result; it is replaced as a whole by each attempt, never merged across attempts.
A record without model or effort predates the pins: its model is unknown. Each
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
limits the tool commands the provider starts to 16 threads, its own runtime (the
external `strace` launcher, the CLI and its persistent service) to 64 threads, the
whole tree to 32 GiB of aggregate resident memory, and every thread to the lane's
CPUs (ticket 74). Tool commands have
a 120-second limit, and the workspace has a 5 GiB limit. Resource excess rejects
the attempt. Claude calls also carry a
five-dollar API budget cap where supported by the configured account. Codex records
`budget_usd_enforced: false`; a ChatGPT subscription does not provide that cap. These are
maximum attempts and provider time, not a promise of completion. Native builds and
executions have their own explicit budgets and remain independently retained.

A public repair request names a failed build/correctness evaluation. A
`provider_unavailable` outcome caused by a usage limit can also be retried using
the proposal ID when no candidate exists. Unavailable calls consume elapsed time
but do not consume a repair. Only a failed session is read for usage-limit errors: a
session that exits 0 with a valid result keeps its result even if it logged a
retried limit error. A campaign can reuse a candidate created after such retries. Repairs retain the first attempt's kind, model, and
effort, and its classification: a contract fixture that emulates a kind cannot
repair that kind's real proposal, or the reverse. A mismatch is refused. Historical receipts without model settings remain
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
