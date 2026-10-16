# Read-only lane and launcher preflight — 2026-10-16 ET

Use node 0 for ticket 25 and node 1 for ticket 28, subject to a fresh lease/load
check immediately before each root-owned launch. These are recommendations;
this agent acquired no lease, launched no compiler/test/evaluation, and changed
no remote source checkout. The only remote Git mutation was a safe fetch of
MemAcc's main remote-tracking ref.

## Current observations

The retained `mbit10-preflight-and-wrapper-snapshots.json` is a finite live
snapshot, not perpetual clearance. Both socket leases and the legacy lease
were released. Initial CPU sampling was 100% idle and load was 0.11/0.07/0.01;
about 118 GiB RAM was available. `/data1` had 23 GiB free, `/data` 69 GiB; use
`/data/yanruj/EvolveSWDB_runs/` for raw output and retain at least 20 GiB on each
mount. GPU inspection failed with an NVML driver/library mismatch (595.99);
GPU utilization is unknown, and CPU runs must retain this observation.
`perf_event_paranoid` remained 4.

Remote ArchEvolve primary was `yanrujhou_main` at
`c978393b119a3614229a37f0f2c8ca2a097c750b`, with only the preexisting untracked
`swdb-project/records/.retention.lock`. Do not change that retention artifact.
The proposed shared detached source is
`/data1/yanruj/probata-resume-20261016-c978393b`. No detached source was created
by this preflight.

The earlier `local-slots-snapshot.json` records active external Claude work:
slot 1 `t07f` PID 58501 and slot 2 `t07d` PID 63873; both owner processes were
alive. Policy was 2 slots, the queue was empty, and available RAM was about
9.7 GiB. Earlier snapshots had slot 2 free; do not reuse that earlier state.
Local process inspection required read-only sandbox escalation and succeeded
with no inspection denials. No owner process was signaled or modified. The final
12:56 ET refresh in `local-slots-final-review-snapshot.json` records only t07f
still holding slot 1; slot 2 and native B were absent, the queue was empty, and
available RAM was about 10.9 GiB. Admission remains atomic through the shared
runner; an observed empty slot is not a reservation.

## Reusable remote runner

`/data1/yanruj/Memacc-evolveswdb-lane` was clean, on `yanrujhou_main`, HEAD
`76cca359136794afa5ede975cfac8293cfa2ab9a`. Its two scripts were byte-equal to
freshly fetched MemAcc main `41f22f0ba765adcd4f4188aca91009ea0fe5a22b`:

| File | SHA256 |
|---|---|
| `AgenticRefiner/scripts/host/socket_lane.sh` | `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8` |
| `AgenticRefiner/scripts/host/hostlock.sh` | `50745f827bac2a3db4fc56fdedc95f6fb57fb4b39cf9b269796c77c0274dc996` |

The old primary `/data1/yanruj/Memacc` is dirty and at `a4521f3b`; it does not
contain `socket_lane.sh`. Preserve it. Reusing the verified lane checkout avoids
another runner worktree. The wrapper confines CPUs and memory before acquiring
the per-socket lease, verifies the hostlock protocol, and exports the live
parent PID and generation. Keep those attestations intact for child checks.
Use at most six test workers per leased lane and at most 16 physical threads.

## Preserved generic launcher and guards

`historical-probata-launch-reviewed-profile-v3.py` preserves the exact generic
launcher from `/private/tmp/probata-launch-reviewed-profile-v3.py`, SHA256
`e3992bcd0fc508963b6535bea42ab63629f5ce83ac8bb6402ccf1589536e1457`.
It must not execute unchanged: it fetches the retired integration ref and uses
old source/raw/session namespaces and the old production baseline.

The remote JSON contains exact source snapshots of the previously reused
`execute.py`, `watch.py`, `run.sh`, and `launch.json` in
`/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative`.
The first three files still matched their historical pins:

| File | SHA256 |
|---|---|
| `execute.py` | `ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612` |
| `watch.py` | `4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c` |
| `run.sh` | `650f815cb7562767829d94e8868da56990c98301376b999af6c659fbe499fcf3` |

Both watchdog layers use the source's `swdb/rss_watchdog.py` (SHA256
`8cbe4f803951cee080581862b69a0b7bf21e35c554dc5cfde4db7d9f2779e5b6`),
8 GiB per process tree and the configured timeout. The external socket command
adds `timeout --signal=TERM --kill-after=60 <seconds+120>`. Raw budget metadata
is a planning/polling limit, not a filesystem quota. The execution wrapper
imports SWDB and probes compiler/runtime provenance before running the command;
that is real compiler activity and remains subject to fresh runtime admission.

The local compiler worker B is preserved separately (SHA256
`873ac0b65eaa7edd4e0f624a86e68141c0e340f9ab1ca6816a07598538548a0e`).
Its `flock` at `/private/tmp/probata-mac-compiler-worker-b.lock` only serializes
compiler workers; it is not a verifier lease or RSS guard. The robust shared
runner is the frozen `counted_verifier.py` under
`/private/tmp/probata-resume-t07-private-array/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/`, SHA256
`c6f0d4b8c60fab912dd768c4c8c7e7737d8feca3a110d0de02dec4d38785db57`,
with sibling `staged_search.py`, SHA256
`125e2562342e6ba684d1189ca29fb48476b73bee30d0fd368f7f7c6b4c6b2419`.
It supports `--log`, `--cap-gb 8`, `--timeout`, `--queue-timeout`, `--owner`,
`--lock /tmp/claude/swdb-verifier.lock`, and `-- COMMAND ...`. It uses the
existing FIFO/two-slot policy, excludes occupied slots from admission, and
retains a quarantine when child cleanup cannot be confirmed. Do not replace
Claude's lock policy or clear a live owner.

Historical ticket 28 runtime metadata is at
`/private/tmp/probata-t28-initialized-u32-public-runtime-policy-template-v1-20261016.json`
(SHA256 `67804e55f69b188983493033ec8180f6c784b181831d0db12919b401bea7e0c0`),
with sibling `...public-runtime-template-context-v1-20261016.json`
(`f6127b7081b316874ad55e816588d5170e9dd23d6bda5ba3785ca157b954e86b`).
These are historical pin inventories, not fresh source/runtime admission for
the resumed public V3 run; rehash all pins/membership and build a new policy
bound to the chosen source, fresh cache prefix, command and output namespace.

## Initial V4 review

The proposed V3-to-V4 changes correctly use `yanrujhou_main`, the new shared
source/raw/session namespaces, baseline c978 and an independently checked
hostlock pin. The initial review requested two changes before execution:

1. Protect the embedded remote Python assertions from optimization as well as
   the local launcher. Reject `PYTHONOPTIMIZE`, execute remote Python with
   `-I -B`, and verify remote `sys.flags.optimize == 0` before admission.
2. Sanitize the environment in the actual tmux child. Checking SSH Python's
   ambient selectors does not inspect the existing tmux server environment.
   Supply direct tmux argv beginning with `/usr/bin/env -i` and a minimal
   reviewed whitelist before the lane wrapper, preserving the wrapper's later
   live attestations. Avoid a preliminary shell before this sanitization.

The 2 GiB detached-source reservation is needed only when the shared source
does not yet exist. Apply the 20 GiB mount floor to an already present admitted
source without reserving a nonexistent second checkout. Fresh actual-entry,
source-consumer/runtime/header, property/CSV/assumption and result admission
remains root-owned; no proof acceptance follows from this review.

The final `v4-final-independent-static-review.json` accepts the corrected V4
launcher SHA256 `46effb9a33fb0b93d3cb4f5a4922d2a2a1c5bc3a3e259cd06ce6737dfa821de4`.
All three requested changes were applied and both local and embedded Python
syntax parsed successfully. The launcher was not executed by this reviewer.
This accepts only the static main-source guarded-lane adaptation; root's fresh
actual command, source/runtime, resource and scientific result gates remain.

## Narrow preflight repair and runtime refresh — 2026-10-16 12:59 ET

Attempt 1 refused inherited SSH `PYTHONPATH` during metadata preflight, before
source/raw creation, lease acquisition, compiler or solver execution. Its root
receipt remains unchanged. The independent attempt-2 review accepts launcher
SHA256 `26e2833843b0b77a7e5390977bb70cfb499332b942282313cbeb637fa072a30d`.
Inverting the sole selector-handling change exactly reproduces the original
reviewed launcher hash. Remote metadata Python remains `-I -B` and must report
isolated/nonoptimized mode; only its ignored outer `PYTHONPATH` name is allowed.
The actual tmux child still starts through the closed `env -i` whitelist, and
the reviewed run script sets the admitted source path afterward. No selector
values are disclosed. See `v4-attempt2-pythonpath-independent-static-review.json`.

Fresh read-only metadata hashing matched all 4,489 runtime pins (371,183,650
bytes) and all six tree memberships, with no unstable files or errors, in
1.98 seconds. See `t28-runtime-template-fresh-physical-rehash.json`. This is
runtime inventory identity only; current source, public V3 entry/cache policy,
driver/header use and actual workflow admission remain separate.

At 12:59:25 ET, the attempt-2 local snapshot still had Claude t07f in slot 1,
slot 2/native B absent and an empty queue. Available RAM had fallen to 6.1 GiB;
this snapshot does not provide 8 GiB local headroom. Defer high-RSS local work
or select a smaller reviewed cap for the compiler/scripted control. No compiler,
guard, workflow or resource action ran during this follow-up review.

## Selected Python runtime and 4 GiB profile review — 2026-10-16 13:03 ET

`t28-cap4-and-python-package-runtime-review.json` accepts a finite positive
`--cap-gb 4` for the compiler/scripted-persistence control, with the original
240-second c6 limit, 220-second entry limit and unchanged acceptance criteria.
The guard compares sampled tree RSS against the selected argument and records
that cap; the entry has no hardcoded 8 GiB requirement. If propagated,
`SWDB_VERIFIER_RSS_CAP_BYTES` must also be `4294967296`. Root's proposed fresh
4.5 GiB available-memory floor and atomic shared-slot admission remain required.
OOM, timeout, inspection failure or unconfirmed cleanup remains unsuccessful.

The selected Python inventory imports only pytest/PyYAML/jsonschema/psutil and
their active metadata dependencies; it runs no tests, compiler or guard. It
uses the exact interpreter and public V3's closed environment, disabled plugin
autoload and a fresh explicit command-line bytecode-cache prefix with `-B`.
All 3,130 pins (94,433,709 bytes), 32 stdlib/package/metadata root inventories
and every observed module origin are retained in
`t28-python-package-physical-inventory.json`. The 13 selected distributions
include the complete active `Requires-Dist` dependency closure under this
interpreter with no optional extras. Startup `.pth` selectors are pinned too.
Native dynamic-library loader closure and arbitrary future imports remain
outside this snapshot; the stated OS/loader TCB is unchanged.

`t28-public-v3-runtime-policy-with-python-packages.json`, SHA256
`4171556ed48f8612eb364a88741831a3bfc9259d34c25750e8717dadeab408a1`,
merges the unchanged compiler policy and Python supplement into the exact
five-key runtime shape: 7,605 unique pins, 465,364,367 physical bytes, 14 identical
overlaps. Root still owns actual source/entry/policy selection and fresh checks.

The supplemental inventory excludes preexisting `__pycache__`/`.pyc` files.
Therefore B/c6 and isolated V3 entry interpreters also need an explicit
command-line `-X pycache_prefix=<fresh nonexistent prefix>` with `-B`, or a
separate inventory of their existing bytecode consumers. `-I -B` alone can read
old bytecode and ignores an environment-only prefix. The prospective pytest
child already supplies its own fresh prefix. No workflow was launched here.
