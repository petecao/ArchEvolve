# DX100 v2 completion witness

Navigation updated: 2026-09-28 (Eastern Time).

Updated: 2026-09-26 ET.

`dx100.bfs.verifier.v2` is a prospective correctness mechanism. A new evaluation
may be `complete` when its declared observations are complete: the exact timed
ROI was sealed, its protected BFS structural check passed, its benchmark or
trusted candidate wrapper completed, and the simulator recorded the main
context's `exit_group(0)` call and zero return. `complete` does not assert normal
guest termination. The continuation retains the actual exit event, code, tick,
`normal_exit_observed`, and stopping reason. V1 and earlier incomplete records
are unchanged; no historical evaluation is promoted by this mechanism.

The unchanged pinned restore pipeline has a documented process teardown
limitation. These observations establish the finite graph/source structural
result and the sealed simulated ROI under that declared pipeline. They do not
prove general checkpoint restoration fidelity or real hardware performance.
See [the diagnosis](../archive/bfs-post-roi-termination-diagnosis.md). Only a prospectively
frozen protocol with the exact v2 checker and instrumentation can admit new v2
comparison evidence. Operational failures, host interruption, and absent
observations remain ineligible.

## Separate simulator trace

After durably sealing the ROI, the trusted driver redirects simulator tracing
to `simulation/post-roi-syscalls.log`, disables the ROI flags and conflicting
format flags, and enables `SyscallBase` plus `FmtFlag`. It resumes in chunks of
at most 10^9 ticks within the requested finite continuation limit. The parser
does not read guest stdout for an exit witness. This separates the evidence
channels; it is not a new adversarial sandbox claim.

`swdb.dx100_witness.parse_trace` uses only the Python standard library so the
pinned simulator can load it with `runpy`. It reads at most 32 MiB from a regular
file, rejects symlinks, truncation, control characters, out-of-interval or
decreasing ticks, unknown CPUs or hardware threads, unmatched returns, and
conflicting or duplicate exit calls. Its syscall state machine permits ordinary
futex retries and retains pending worker calls. The accepted pair is exactly
`system.switch_cpus0`, hardware thread 0, status 0, return 0, at the same tick.
These trace identities are CPU object/hardware-thread identities, not proof of
guest PID, TGID, or Process-pointer relationships. Worker activity after the
exit pair remains visible and does not invalidate the observed request.

The pinned simulator also emits unconditional CPU progress records through
`DPRINTFN` in `src/cpu/base.cc:107–110`. `src/base/trace.hh:238–242` does not gate
these records on the selected debug flags, and `src/sim/eventq.cc:83–86` names
their events `Event_<instance>`. The first actual v2 proof failed because four
such records shared the redirected stream; its failed record is preserved in
[the execution receipt](../evidence/bfs-dx100-witness-20260926-a1.yaml).

The parser recognizes only that exact additional grammar, validates the CPU,
tick interval/order, bounded nonnegative counters and finite IPC, and retains
the rows separately in `progress_records`. Progress cannot create, return, or
complete a syscall; a stream containing progress alone has no exit witness.
All other unknown formats still fail. Earlier receipts without progress keep
their original shape. This correction does not retroactively qualify the failed
proof; a new execution requires its own bounded plan and result identity.

A worker retry event may have been scheduled before trace enable. The first
observed non-exit `Retrying` on a stream is therefore retained explicitly in
`initial_partial_calls`; its later retry/return transitions remain checked.
The pinned `SyscallDesc::setupRetry` schedules that event, while `retrySyscall`
prints its retry and result synchronously. A bare initial return is rejected.
No partial pre-seal history can supply any portion of the exit witness.

`allow_incomplete=True` permits a well-formed stream with no exit request yet.
A partial exit pair or malformed stream still fails. The result records the
exact byte hash, byte count, interval, caller, call/return line numbers, later
event count, and pending calls. Stdout text cannot substitute for this file.

## Qualification and availability

`validate_completed_witness(evaluation, verify_artifacts=True)` checks one
component evaluation. It binds the request, checker, source, binary, simulator,
workload, execution digest, seal, parser, trace, and continuation. It requires a
clean simulator process and a passed protected completion sequence:

- Author execution: one post-seal PASS, then finite Verification Time and
  Average Time records in order, tied to the pinned verifier and harness.
- Candidate execution: one post-seal parent-result record for the exact source
  and parent count, then PASS, tied to the protected source and wrapper.

Each new v2 execution retains exact driver, parser, and host memory observer
bytes under its own `verification-runtime` directory. The authoritative
`verification_driver`, `verification_parser`, and `host_memory_observer`
references point to these copies. `instrumentation.verifier_runtime` contains
only their `driver_sha256`, `parser_sha256`, and `observer_sha256` digests, so a
frozen instrumentation policy binds the actual checker code without binding
per-run paths. Qualification requires all three digests to match the retained
references and the seal's driver, parser, and observer identities. The
`verification_runtime` copy receipt records original repository locations as
provenance; changing a later checkout does not change the retained runtime.

Available output is streamed with a 2 GiB bound and its completion observations
are reconstructed from the same bytes that are hashed. Trace bytes are reparsed;
seal JSON and source/wrapper/parser hashes are rechecked. Metadata-only mode
still checks typed fields, ordering, identities, tick accounting, and complete
observations. It makes no claim of re-reading unavailable files.

`validate_record_witness(evaluation)` applies the existing remote retrieval
policy and returns `witness` plus `availability`. Every present witness-chain
artifact is independently verified, even when another artifact is remote.
Missing artifacts are allowed only under `/data/` or `/data1/` on a different
named execution host and are explicitly `remote_unverified`. Missing local
files, inconsistent host identities, changed files, and symlinks reject the
record. A caller must preserve this availability distinction. Aggregates
validate their actual immutable components; an aggregate label cannot replace
their evidence.

`require_complete_evaluation=False` is reserved for the adapter's pre-finalization
check and permits submitted/running state only in addition to complete. It does
not permit failed evaluations. The shared report/comparison helper uses the
default complete-state requirement.

The tests in `tests/test_dx100_witness.py` and the public adapter tests are
contract fixtures. They provide no empirical BFS timing, accelerator coverage,
or gain evidence. A prospective real v2 run and independent audit remain
separate from implementing this contract.
