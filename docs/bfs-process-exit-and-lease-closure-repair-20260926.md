# Process-exit and historical lease-closure repair

Prepared: 2026-09-26 (Eastern Time).

The T16 simulator batch failed when Linux returned ESRCH while reading an exiting
process through `/proc`. The T15 setup proof group independently failed because
another user acquired the socket after the fixture finished and before its audit.
Both original failures and all time/storage charges remain preserved. This repair
cannot promote those attempts or replenish their budgets.

The RSS observer now performs at most two reads after ENOENT or ESRCH. It accepts
only independently confirmed directory absence or a newly read actual stat/children
record. PID/start matching still prevents following a reused process. Unknown,
permission, malformed and repeated live-process telemetry errors fail closed;
there is no zero-RSS fallback. The [Linux kernel documentation](https://cdn.kernel.org/doc/html/latest/filesystems/proc.html) explicitly describes ESRCH from open proc descriptors after process exit. Task enumeration independently reopens the parent
identity before treating an exit or PID reuse as terminal.

The fixture auditor separates historical closure from fresh admission. Its original
lease generation must be released, or a strictly later generation must have been
acquired after the fixture helper ended. This relies on the helper incrementing
generations under the same exclusive lock with intact metadata. The installed helper
was read directly: `hostlock.sh` SHA-256 `50745f827bac2a3db4fc56fdedc95f6fb57fb4b39cf9b269796c77c0274dc996`; acquisition locks before incrementing, and release writes before unlocking. Its malformed-metadata fallback can reset the counter; a lower generation rejects here. The audit does not authenticate arbitrary external replacement of lease metadata or lock inodes. Both metadata/kernel snapshots remain
recorded; a successor job or legacy holder does not negate historical closure.
Every future dispatch still requires its own fresh free-lane/legacy admission.
The fixture's full PID/start union, runtime, settled cleanup budget, JUnit, immutable
pending record and helper/outer exits remain mandatory. Failed a4 stays failed.

Local audit and proof-reader verification: 110 passed, one Linux-only skip.
The affected RSS/ownership group passed 48 tests, with six Linux-only skips.
Independent review: five lease checks and fifteen RSS checks passed. Linux execution
of the repaired runtime and final full-task Standards/Spec reviews remain pending.
See the [independent scoped review](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/lease-rss-standards-review-20260926.json).
