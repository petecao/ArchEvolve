# FINALIZE parent host reader R2 — 2026-10-08 20:28 ET

SOURCE-ONLY / NOTRUN. R1 originals are unchanged. No SSH, imported/executed reader/control, tests, native chmod/locks, or repository changes. This reader produces future readiness metadata, never scientific admission. Parent independent source review and all four actual root+peer normal terminal/release32/AFTER custody PASS are required before any runtime.

Selected artifacts:

- `/private/tmp/lanl17_finalize_parent_host_readonly_20261008_a5_r2.py` — 17019 B, SHA256 `229909573e4952ee2e21f9a64ccbc6bc886ee114e346f6c4304481763666d87f`.
- `/private/tmp/lanl17-finalize-parent-host-readonly-action-SOURCE-ONLY-draft-20261008-a5-r2.json` — 18261 B, SHA256 `7b6e1c9c7242eb954501d40e73be399d9bc557e38c0bd222a5a533b51fc5c545`.
- `/private/tmp/lanl17-finalize-parent-host-readonly-r2-complete-r1-derivation-20261008-a5.diff` — 45469 B, SHA256 `9023b0bdc2aaa63a82c61272fb44d49ded23156d414e1952774fb3ae2c49479e`.


R2 addresses the R1 peer findings:

- The config adds one argument after native Python `-c`: the externally supplied SHA256 of exact embedded source bytes. The source contains no self-hash literal. It bounds/reads its own cmdline, hashes its actual source token, and compares with this argument. It then proves the immediate parent is exactly `/usr/bin/timeout --signal=TERM --kill-after=60s 60s /usr/bin/python3.12 -I -B -c <same source> <same SHA>`, including owned UID, exact exe route, proc inode, start ticks and PPID. Both command/stat/exe identities are read twice and rechecked at the end. Only this exact transport parent and the reader itself are skipped in the consumer scan; arbitrary timeout/Python/scientific processes are not exempted.
- `kernel_bytes` and `locks` are AST-exact copies from the reviewed P4 observer1b7a3446. Kernel read is bounded before allocation, root-owned O_NOFOLLOW, stable full stat; every normal/waiter row parses numeric major/minor/inode. The selected identity comes from lpin.stat, not a subsequent independent lstat. Any matching holder/waiter prevents ready output.
- `daemon` is AST-exact except replacing the global LEASE route with identity['path']. It proves owned PID/proc inode/start continuity and exact FD9 route/stat. The caller retains the reviewed conservative rule that a foreign/deleted FD9 route is unknown, never released. Same per-lease identity/proof is rechecked after the full metadata query; unreadability or change fails closed.
- Native hostlock metadata uses its exact known closed key schema, writer/host/name/mode binding, finite integer generation/PID and bounded start token, canonical whole-second UTC chronology, and null auxiliary/session fields. Node0 must still match actual P4 acquired generation514, avoiding later reuse. Only bounded scalar projections and original full-stat/hash pins are returned; original metadata remains0666, unchanged.

Original R/M2/PRIMARY/origin, all four stop-source guards, fresh FINALIZE routes, serial80/21/24GiB floors, comm-only CPU/GPU/process status and original control pin are retained. F6/control/native/proof checks still belong to the original FINALIZE bootstrap. Reader45-second alarm, generic child GNU60/K60, remote whole130/K15 and local180 envelope are unchanged. Failure emits host_metadata_ready=false/state=unknown with only exception class/reason digest. Do not admit readiness from SSH/inner exit0 alone.

Static checks passed: complete source AST, exact config embedding/source descriptor/hash argument, unchanged six R1 helper ASTs, exact reused kernel/lock parser ASTs, only route parameterization in daemon AST, no stage/collect action,0600 modes, and prior node0/node1/legacy original schema compatibility. Prior schema observation is historical; actual P4 terminal/generation514 release facts remain future. No runtime outcomes claimed.

Parent must independently inspect source/diff, verify exact capture source64fd and command envelope, then supply actual future all-four custody and exclusive no-reuse gate. R2 observations remain point-in-time; no source/lease reuse or consumer start may occur between fresh observation and final parent admission. Capture/config are source preparation only.
