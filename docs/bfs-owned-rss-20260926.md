# RSS observation across process exit

Created: 2026-09-26 (Eastern Time).

The fixed coverage attempt `bfs-dx100-coverage-20260926-a1` failed after its
resource monitor reported `owned process RSS is unavailable` and signaled the
driver. Its sealed guest exit witness does not override that failed collection.
The old sampler read process state from `stat` and then RSS from `status`; a
process can exit between those reads. The failed PID was not retained, so this
interleaving is a supported hypothesis for that run, not a proven causal account.

The local deterministic reproduction at
`/private/tmp/bfs-rss-exit-repro-20260926.py` drives the old sampler through a
same-PID/start sleeping-to-zombie transition. It produces the exact error and
shows that the child identity was not added to its retained set. The new module
`scripts/bfs_owned_rss.py` is separate: measured historical clients and records
remain unchanged. New clients must explicitly pin and declare this observer.

The observer reads the PID, parent, start time, state and explicit RSS page count
from one `/proc/PID/stat` record. It records `rss_source`, `page_size_bytes`,
per-process `rss_pages` and the resulting bytes. The kernel's
[field 24 definition](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html)
describes an approximate resident page count. This remains a sampled guard;
it is neither true-peak memory nor a kernel resource quota, and summing process
RSS can count shared pages more than once. A single record avoids the specific
cross-file state/RSS race; it does not make the whole process-tree sample atomic.

No missing measurement becomes zero. A zero page count must be explicitly
present in the stat record. Missing or malformed live telemetry fails, and
an owned PID/start identity is retained before later RSS or task reads can fail.
All threads' child lists are traversed; known descendants remain observed after
reparenting or session changes. Reused PIDs are excluded, and parent identity is
rechecked before following child lists read during a PID's possible reuse and
again by PID and start time when adopting a newly discovered child. Known exact
child identities remain observable after reparenting. Retained identities,
sampled processes, pending observations, tasks per process and accumulated
children per process each have a 4,096-entry bound.

Synthetic proc-tree cases compare the old failure with the new observer and
cover genuine missing data, PID reuse, reparenting, task removal, and incorrect
PID fields. A separate Linux-only case observes four actual live children,
their zombie state and reaping under a 15-second test ceiling. Local macOS skips
that case; its presence is not evidence that it has run on Linux. All callers
still need their own bounded stage watchdog, sampled-memory ceiling, retained
observations, and independent terminal cleanup audit.

At 14:23 ET, independent review found and reproduced a parent-reuse race between
child discovery and adoption. The regression failed before the correction and
passed afterward; the focused suite is 12 passed and one Linux-only skip. The
reviewer independently repeated that result. The failure and corrected logs
remain under `/private/tmp/bfs-rss-parent-reuse-red-20260926.log` and
`/private/tmp/bfs-owned-rss-parent-fix-20260926.log`. Actual Linux verification is
still required before a new client is dispatched.
