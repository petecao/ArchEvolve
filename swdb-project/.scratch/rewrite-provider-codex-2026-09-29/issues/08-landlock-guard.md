# 08 — Landlock guard for real providers

Created: 2026-09-29 (Eastern Time)
Updated: 2026-09-30 (Eastern Time)
**Type:** slice
**Status:** resolved
**Blocked by:** None
**Spec:** `../spec.md`

**What to build:** On Linux, real Codex and Claude sessions run in workspace mode inside an SWDB-owned
Landlock guard: reads limited to the workspace, the toolchain, the provider's install
directory, and the per-run home; writes limited to the workspace and the per-run home; TCP
only to port 443; an inner layer with no TCP for each tool command; and the session limits
(16 threads, 32 GB, 120 s per command, 5 GB workspace). The guard's policy is recorded with
each attempt.

## Acceptance

- [x] Linux-only tests through `swdb submit` on mbit10: the fixture's forbidden read, forbidden write, and TCP connection are each blocked and reported, and a connection on an allowed port succeeds.
- [x] The resource limits apply, and the full guard policy appears in the attempt's record.
- [x] Real kinds run in workspace mode only under the guard; where the guard cannot run, they refuse.
- [x] Tests run inside a socket lane.

## Answer

2026-09-29 (Eastern Time)

Implemented `swdb/provider_guard.py`. Real workspace and prompt-only sessions fail
closed without verified Linux Landlock ABI >= 4 and an owned mbit10 socket lane.
The launcher verifies full socket affinity and memory binding, then uses one CPU
from that socket. It confines reads to derived inputs, selected provider/toolchain
roots and narrow runtime files, and persistent writes to the workspace/home, with
`/dev/null` as an output sink. Policy and independent connection-audit receipts are
retained with each attempt.

Claude's verified executable shell prefix applies an inner no-TCP layer. Codex has
no verified prefix override and uses the specified outer TCP443/model-API trace
and event-audit fallback. The whole provider tree, including strace and any exact
installed persistent Codex service, remains under the 16-thread and 32-GiB RSS
caps. Tool commands have 120 seconds and the workspace 5 GiB; the original CLI
and its exact, directly parented installed service retain the overall call budget.
The RSS cap is enforced by observation; no 32-GiB allocation stress test is claimed.

An outside-Landlock tracer subreaper adopts detached descendants. Cleanup uses
PID plus kernel start time and pidfds where available, stopping descendants before
the tracer. The inherited native seccomp filter protects recorded evaluator/tracer
identities against the listed signal APIs and direct `pidfd_open`, rejects compat
ABIs, and preserves ordinary helper signals through a separate provider session.
This is narrow supervisor continuity protection, not general hostile-process
isolation. UDP and session-time login readability remain declared residual risks.

| Validation | Checkout / lane | Result |
|---|---|---|
| Linux A6 guard, pins, workspace | `4f5d152`; node0 generation 424; starting load 1.02 | 222 passed in 1428.56 s |
| Linux A7 status parser and compatibility cases | `c8a666f`; node0 generation 425; starting load 2.55 | 42 passed in 132.56 s |
| Fresh real DX100 A2, both providers | `c8a666f`; node0 generation 426; starting load 2.61 | Guard, supervisor filter, original/current audits and cleanup pass; no survivors; mode-0600 login copies deleted |

Public Linux submissions verify allowed reads, denied outside reads/writes,
allowed outer TCP443, forbidden outer TCP80 and inner TCP443, resource overrun,
tool timeout, detached-helper accounting/cleanup and supervisor signal continuity.
The A6 retained-log subprocess exposed a harmless Claude `echo "exit=$?"` label
rejection; the narrow data-position fix and A7 re-audit resolve that issue without
admitting the older Codex DX100 A1 opaque `sed` transformation. See
[guarded provider evidence](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml)
and [ticket 02](02-spike-providers-under-landlock.md) for commands and raw identities.

## Spec re-review repair (2026-09-30 ET)

- Codex sessions refuse `io_uring_setup` and `MSG_FASTOPEN` sends in the inherited
  seccomp filter (`untraced_network_filter`), since those can connect on port 443
  without the `connect()` call the trace records.
- Inner Claude tool commands get a kernel `RLIMIT_AS` of 32 GiB; `limit_enforcement`
  records how each limit is enforced. The 5 GiB size cap covers the provider home too.
- Only the first observed `codex-code-mode-host` instance is exempt from the tool timer.
- A fixture whose command resolves to an installed `codex` or `claude` is refused.
- IP-based model-API matching and polled thread/memory caps are recorded residual risks.
