# Ticket 14 early-exit7 fixture — independent source review

2026-10-07 ET. Full 388b source, complete 15f3 a848 derivation, original a848 source, full handoff and preparation JSON read. The selected R1 503f context/function boundaries were checked against the prior full independent source review. File hashes match the supplied pins. No control import, compile, main, test, SSH, staging, Git mutation, source edit or actual host/input inspection occurred.

**No concrete source blocker found.** This is source acceptance for one prospective synthetic lifecycle case, not a Linux result or permission to infer scientific/report admission.

## Observable case and boundaries

- Context lines 89–101 bind own fixture source, exact R1, original 31e/bcc9, native Python/cwd and C185/F6. The only supervisor invocation is `supervise(..., 'exporter', timeout_s=18000, fixture=True)`. It does not import or invoke 928/690 main. Imported R1 loads only the original cleanup/process modules; the harness invokes no Store, validator, compiler, evaluator, provider or Git path.
- Owned child lines 74–87 captures its leader, forks a same-group child that ignores TERM, then forks a second child inheriting TERM-ignore and calling `setsid()`. Its private fsynced marker is atomically renamed before the leader exits exactly 7. Marker captures actual PID/UID/start/state/PPID/process-group/session, with explicit False seal and fixture source hash. The test models the early returned-leader boundary, not an observed Git transport failure.
- Harness enables its own subreaper before launch (115). Its sleep sibling is directly parented by the harness and starts a separate session; the worker also starts a new session. Lines 131–138 check original UID, exact leader→same-group→escaped ancestry, matching same-group identity, escaped session identity and sibling separation.
- Lines 139–152 require worker7 and supervisor `child_failed`, returned/final/supervisor exits7, non-success, no timeout/signal/error, exact source/native/account/F6/cap fields, original False receipt seal, full unsealed cleanup byte pin and zero survivors. Expected child failure is not relabelled production success.
- Lines 153–158 capture every owned PID after cleanup and require the original PID/start identities to be absent; a reused PID is distinguished by its start time. The sibling must still be alive with original start/UID/harness PPID and non-zombie state **before** harness cleanup. Both before/after group/session snapshots are retained for parent inspection.
- Finally lines 161–176 cancels the alarm, ignores repeated interruptions, calls frozen group cleanup for both exact Popen handles even after leader return, and independently calls original 31e cleanup after any group-cleanup exception. This harness subreaper catches descendants adopted after exceptional worker termination. The sibling is retired only after the separate worker-cleanup survival assertion. Own/source/F6 rechecks and cleanup errors/survivors prevent `passed:true`.

## Privacy, policies and limits

R1 supplies a fresh owned/private 0700 root and exclusive 0600 original streams/JSON; the worker subfolder is 0700. Marker, supervisor receipt and final fixture receipt use canonical **False**; preparation uses canonical **True**. Full cleanup snapshots remain original **unsealed** JSON with exact bytes/SHA, not retroactively sealed. Compact final receipt is capped at 16384 bytes, excludes original argv/environment/auth/stream bodies, and states scientific admission false, selected main not invoked and reader-mode runtime proof false.

Exactly one `early_nonzero7` case exists. Old returned0/timeout/external-TERM cases are not repeated. Worker wait100, harness alarm240 and proposed GNU outer360/KILL60 are distinct unproved administrative allowances; production exporter18000/reader14400 and science/validation/codec remain unchanged. Marker waits and context/source/proc/I/O/cleanup add time. Source review proves no total duration, actual cleanup, host-wide exclusion or real native context. SIGKILL, startup/I/O failure or exhausted outer budget can prevent receipt publication; partial private outputs must remain failure evidence. Concrete future argv/native/cwd/paths, delivery and no-overlap/lane/capacity facts remain parent-owned invocation checks.

## Exact packet pins

| `/private/tmp/` file | Bytes | SHA-256 |
|---|---:|---|
| `lanl14_export_reader_early_nonzero_linux_fixture_20261007_a1.py` | 16418 | `388b9b1be3ce29c3d677ab2796c049793bf763504d4be7ad8e9f399c94354624` |
| `lanl14-early-nonzero-linux-fixture-complete-a848-derivation-20261007-a1.diff` | 24846 | `15f302bcf37c9bb709e0eab3ec23a3794fdb2ab674b93bae3c61505ae3baabed` |
| `lanl14-early-nonzero-linux-fixture-source-handoff-20261007-a1.md` | 8212 | `106bd9a649162fc453a8aeb072d91120e926972b98b0375b525ace590ca9418f` |
| `lanl14-early-nonzero-linux-fixture-source-preparation-20261007-a1.json` | 3517 | `5dc57cd463a608a7944fe82f27cc24b453b98661338cb3c5d928e6d6ef4b488c` |

Preparation declares original True seal `5f366ba78bd70ccec771e74ae8914f9e6eb1d5139b07d2696aa8136c5996566c`. Original a848 is `a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f`; selected R1 is `503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f`. Earlier f339, fb5b and final R1 4c82 review notes remain unchanged. No runtime proof is appended by this review.
