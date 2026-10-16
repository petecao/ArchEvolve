# Native inspection exception policy

Date: 2026-10-15 ET. Scope: ticket07's resource runner only; no new proof method or
actual-run admission.

Run26's final replay refused execution on the exact message
`SystemError: <built-in function proc_environ> returned a result with an exception set`.
The original summary contains no traceback or original failing PID/phase. Its
nullable `inspection_failure` field does not establish absence of an error.
Neighboring cleanup denials cannot identify that lost context or the OS cause.

The pinned local psutil implementation calls `Process.environ` through
`_psosx.Process.environ` to `cext.proc_environ`. Its wrapper translates
`PermissionError` and process lookup/zombie errors but does not translate
`SystemError`. The old runner retries `psutil.AccessDenied` only, so this exact
exception bypasses that path and loses its operation/identity context at the
outer class/message fallback. This is an exception-routing diagnosis; no native
OS cause, expected recovery frequency or real-run availability guarantee is claimed.

The feedback loop uses the actual public runner CLI, a private lease and an inert
Python child. The authorized boundary injection raises the retained native error
for 150 ms on one real PID/birth. It fails on immutable pre-repair `ac6bb42e`
with and without a synthetic cause (two failures in 0.24 seconds). It succeeds
under the revised runner. The final test bytes additionally cover an implicit
exception context: all three chain variants fail on frozen old source in 0.38
seconds. The first sandboxed probe failed an unrelated process
`sysctl` permission check before injection; it is retained separately and is not
counted as reproducing the native exception.

| Observation | Admission |
|---|---|
| AccessDenied during a requested environment inspection | Existing continuous 200 ms admission window / 21-attempt cap |
| AccessDenied for another requested operation | Existing three attempts separated by 10 ms |
| SystemError with the exact retained signature, raised by the actual requested `environ` operation | Same continuous 200 ms admission window / 21-attempt cap |
| Other native signature, another exception class or SystemError in an identity/status operation | Contextual failure; no native-environment retry |

The immutable captured PID/birth is checked before and after each admitted
operation. Retry admission checks the same continuous deadline at loop entry and
after identity revalidation. A late retry never starts. The original failure
timestamp and the later expiry decision remain separate. Every pause counts;
the existing sampled RSS and active-deadline checks remain mandatory afterward.
An individual synchronous OS call has no forced per-call timeout; the admission
window is not a hard inspection-latency guarantee.
No denied or failed observation becomes an absent marker. Persistent live or
unknown failure refuses execution and retains quarantine when cleanup discovery
is incomplete. Reused identities are neither adopted nor signaled.

Native errors join the existing cleanup inspection catches only to record
unconfirmed discovery and continue the existing independently verified owned
group cleanup. They do not certify absence or release the lease. If the root's
identity cannot be independently revalidated, the group is not signaled.

Diagnostics record stage, requested and actual operation, numeric PID, immutable
expected birth, snapshot birth, independently observed birth/state, and retry
times. Exception chains contain only class/module, relation and numeric PID/errno;
traceback entries contain only code path/function/line. No argument strings,
cause/context messages, source lines, locals or environment values are retained.
Only the fixed known native signature may appear as inspection error message text.
Chains, frames, cleanup contexts and events are bounded at 6, 8, 16 and 128 entries.
Primary and cleanup failure contexts are retained separately, including handled
cleanup discovery failures. Native error events are not labelled AccessDenied.

The controlled composition passed 49 checks in 20.80 seconds. After adding only
the implicit-context/numeric-errno case, seven affected checks passed in 3.70
seconds; the runtime bytes were unchanged. New checks use the
public CLI and OS/clock boundaries. They cover transient errors with/without a
cause, persistent quarantine, unknown/reused identity, foreign-process protection,
RSS/deadline enforcement, retry expiry, wrong native signature, other exception
class, and identity/status native errors. A pre-existing persistent test now
checks the actual expiry decision rather than treating an earlier last-failure
timestamp as the decision time. The shell-environment lifecycle test substitutes
a complete inert `opam`; it does not delegate to real Frama-C. No provider,
solver, compiler, Frama-C version/parser or proof job ran for these controls.
The final secondary identity-diagnostic refinement additionally passed nine
affected checks in 4.33 seconds; it labels the validation birth/status operation
without making another OS observation. Independent review of the final bytes
and their complete composition remains required before integration.

Initial independent review passed 50 existing checks but reproduced a secondary
identity-validation native error incorrectly recovering to exit 0. It also found
that a different secondary exception could escape without context and expose its
raw message. Eight public regressions covering birth/status validation, both
original exception families and SystemError/RuntimeError reproduced these gaps
(eight failures in 5.88 seconds). After correction, all eight passed in 3.34
seconds. Independent validation AccessDenied retains its existing bounded
unknown-state handling; every other secondary validation exception immediately
fails closed with the original environment failure and the actual secondary
operation separately recorded. No extra OS observation is added. The original
review finding and source snapshot remain retained for final re-review.

The resource boundary remains finite, sampled and non-atomic. Trusted descendants
must preserve the run marker. This policy is neither a hard quota nor hostile
process containment. It cannot upgrade run26 or infer a complete final verdict:
that run retained 58 partial timeout lines and no complete positive or negative.
The separate queue-capacity/caller-domain and helper-summary soundness findings
must be repaired and independently reviewed before any future actual admission.
Old concrete hints, outputs and conversations remain excluded from fresh providers.
