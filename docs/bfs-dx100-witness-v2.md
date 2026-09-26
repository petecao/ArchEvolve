# DX100 v2 completion witness

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
See [the diagnosis](bfs-post-roi-termination-diagnosis.md). Only a prospectively
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
