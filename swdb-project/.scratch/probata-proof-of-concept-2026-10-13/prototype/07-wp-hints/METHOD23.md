# Method23 preparation: bounded inspection retry — 2026-10-15 ET

**Under construction; not a frozen method or actual launch authorization.**
Run25 and its producer `798e9bb3` remain immutable. Its terminal positive replay
stopped at 39.48 counted minutes after three environment-inspection denials spanning
32.239667 ms. The failed process's executable, ownership, parent lineage and OS or
exec cause are unknown. Neither a long-lived denial nor recovery within a longer
window is established by that experiment.

## Narrow availability policy

Only environment inspections receive a 200 ms continuous-clock retry deadline and
an independent cap of 21 attempts, with gaps of at most 10 ms. Other observations retain
the three-attempt policy. Every observation/retry still validates the immutable
captured PID/birth before and after the OS operation. Confirmed gone/reused
identities remain distinct from live or unknown denied observations. No lineage
fallback or denied-as-absent marker interpretation is added.

The 200 ms value is a prospective availability hypothesis, not a calibrated bound
on macOS startup or an explanation of run25's denial. The public controlled case
models 150 ms of denial on one live identity, which the old policy refused. Its
recovery under the new policy does not show the old unidentified process would
have recovered. A truly persistent live/unknown denial still fails closed and
uncertainty during cleanup still quarantines the private lease.

A newly admitted retry is checked against the deadline before identity inspection
and again immediately before the requested OS operation. A delayed sleep cannot
start a fresh retry after observed expiry. The original denied observation stays
immutable; a separate timestamped expiry decision records why no retry began.
An already admitted OS call may finish later; source-level admission is not an
atomic kernel start-time guarantee.

All inspection pauses remain inside the continuous resource clock and the same
experiment clock; none earns queue-wait exclusion. Mandatory known-scope RSS and
elapsed-time checks follow inspection, and can refuse an over-budget job after a
recovered denial. This extends an individual inspection pause and therefore the
possible sampling/stop latency. A 200 ms retry deadline limits the retry policy;
OS calls/scheduling may finish later. There is no hard realtime latency guarantee,
kernel memory quota or hostile-process containment claim.

Only matching run-marker presence is retained; unrelated environment values are
never logged. Fresh marker discovery and immutable original-root identity rules
are unchanged. A PID replacement lacking the exact run marker is not adopted or signaled.
Independent fresh marker-verified renewal of a nonroot identity remains allowed;
the original root identity is never replaced.

## Controls and remaining work

The pre-agreed public seam is the real counted_verifier CLI and its exit, retained
summary and lease result. OS inspection is injected at the psutil boundary; the
new controls do not call private ownership helpers. Real small Python children
provide lifecycle observations, and PID reuse is modeled at that system boundary
rather than forced in the kernel. No provider/solver is launched.

The retained old-policy RED is one 150 ms denial control. The repaired source passed a composed GREEN suite of 36 controls and one
additional permanent expiry regression. The suite covers 27 existing runner
controls, the new public cases and independent cleanup/deadline controls. The new cases cover transient recovery,
persistent live refusal/quarantine, unknown identity without signaling, PID reuse
with a foreign marker, an actual unmarked foreign process outside RSS/kill scope,
retained sampled RSS/deadline refusal after recovery, and refusal to start a new
retry after an injected OS sleep overshoot. Token values and private
fixture environment values are not persisted in reports.

Independent review of exact source bytes remains required. The real-format task
reader repair and same-run baseline-subset compatibility assessment remain
separate outstanding work. No full method23 protocol/flags or timing-sufficiency
claim is frozen here. Any future actual experiment still needs a clean published
source freeze, live preflight and coordinator admission, with zero mechanical
seeds, complete Codex-only origin/usage, full all-goal/smoke replay at 30 seconds positive and identical
hints covering-wait negative inside the original 60-minute clock.
