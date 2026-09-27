# Four unchanged scalar v2 builds

Prepared: 2026-09-26 (Eastern Time). Interface v1; actual outcome recorded below.

`scripts/bfs_scalar_v2_builds.py` consumes the exact four requests and
`scalar-v2-20260926-a1.preparation.json` under the BFS scratch requests directory.
It compiles unchanged DX100 and upstream `DOBFS`, primary then diagnostic for
each source, through public `dx100-compile`. These new original-adjacency v2
builds preserve all v1 and T17 artifacts. There is no provider, repair, guest
execution, strategy change, performance comparison, or protocol publication.

The fixed original outer allowance is 1,200 seconds: 1,170 work and one shared
30-second cleanup reserve. Each of four public compile processes has at most 240
seconds of work, including its 120-second compiler cap. The supervisor's subsequent
owned-child teardown uses the shared 30 seconds; it cannot extend public work.
Everything outside those four calls shares a 210-second ancillary allowance;
time spent in the shared cleanup ledger is also bounded by the same outer clock.
Unused compiler time does not
increase ancillary time. Discovery/preprocessor sub-stages remain inside each
240-second public cap. Failure stops the sequence; unstarted IDs stay unused.

## Interface and evidence contract

```sh
"$PY" -s "$CODE/scripts/bfs_scalar_v2_builds.py" \
  --expected-commit "$CODE_COMMIT" \
  --admission "$DISPATCH/admission.json" --admission-sha256 "$ADMISSION_SHA" \
  --lane "$NODE" --outer-started "$ORIGINAL_START" \
  --outer-deadline "$ORIGINAL_START_PLUS_1200" \
  --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START"
```

The new idle checkout supplies both code and its `records/`; there is no arbitrary
public command, records root, output root, request override, or resume option.
The admission is `swdb.bfs.scalar-v2-build-admission.v1`, carrying this run ID,
the fixed manifest SHA-256, exact `code_commit`, `campaign_runtime` result, a
hashed independently sealed `owned_cleanup` Linux fixture proof, `prepared_at`,
and the chosen node. Pin it before launch. The proof must match the exact reused
`bfs_owned_execution.py`, `bfs_owned_rss.py`, `bfs_process.py` and ownership-test
bytes and Python, and contain all four actual unskipped ownership cases. Retain
its original code commit separately from the new driver's commit. This is proof
of the unchanged lifecycle primitives, not proof of the new orchestration. It
does not force a new unrelated fixture-ID revision when these bytes are identical.
Local driver tests are contract fixtures and do not establish host build success.

Use the next available owned socket, node 0 or 1, as authorized for this preparation.
This supersedes only the original manifest's node-0 command example; the requests
contain no lane field. Never launch a third job or ignore the legacy lease.
The other occupied socket is recorded, not treated as an automatic prohibition.
Enter via a fresh current `socket_lane.sh` under a named tmux pane and an outer
timeout with TERM at 1,170 seconds and KILL no later than 1,200 seconds. Capture
the actual original clock and pane identity before timeout/helper startup;
compute remaining timeout from that clock, never from supervisor entry.
No absolute window has been instantiated here.

After choosing and pinning `PY`, `CODE`, `CODE_COMMIT`, `HELPER`, `NODE`, and the
admission hash, the named pane's bounded invocation is the following. `DISPATCH`
is the exact new sibling above; preparation of these variables is not part of a
hidden second attempt. Preserve the expanded command before entering it.

```sh
cd "$CODE"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE PYTHONOPTIMIZE PYTEST_PLUGINS
unset LD_PRELOAD LD_LIBRARY_PATH GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH
unset CPLUS_INCLUDE_PATH C_INCLUDE_PATH
PANE_PID=$BASHPID
read -r ORIGINAL_START ORIGINAL_END PANE_START TERM_AFTER < <(
  "$PY" -s - "$PANE_PID" <<'PY'
from datetime import datetime, timedelta
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
begin = datetime.now(ZoneInfo('America/New_York'))
fields = Path('/proc/'+sys.argv[1]+'/stat').read_text().rsplit(')', 1)[1].split()
end = begin + timedelta(seconds=1200)
print(begin.isoformat(), end.isoformat(), fields[19],
      max(0, (end-datetime.now(ZoneInfo('America/New_York'))).total_seconds()-30))
PY
)
timeout --signal=TERM --kill-after=30s "${TERM_AFTER}s" \
  bash "$HELPER" "$NODE" swdb-scalar-v2-builds --record "$DISPATCH/lane.json" -- \
  "$PY" -s "$CODE/scripts/bfs_scalar_v2_builds.py" \
  --expected-commit "$CODE_COMMIT" --admission "$DISPATCH/admission.json" \
  --admission-sha256 "$ADMISSION_SHA" --lane "$NODE" \
  --outer-started "$ORIGINAL_START" --outer-deadline "$ORIGINAL_END" \
  --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START" \
  >"$DISPATCH/outer.stdout" 2>"$DISPATCH/outer.stderr"
code=$?
printf '%s\n' "$code" >"$DISPATCH/outer.exit"
exit "$code"
```

Loader overrides must be removed before starting Python, including the clock
capture. The supervisor rejects their presence and removes them again from each
public/compiler child environment, retaining that policy in its receipt. Binary
file hashes alone are not a claim about an uncontrolled dynamic loader.

Capture the original clock/expanded arguments in the wrapper's retained launch
metadata. The supervisor independently clips every stage and all finalization to
the supplied original clock; helper/setup delay cannot create extra time. Wrapper
exit recording and the later independent terminal audit do not extend work or
cleanup. The external timeout must start promptly; refuse stale launch metadata.

Raw output is the manifest's new
`/data/yanruj/EvolveSWDB_runs/bfs-scalar-v2-preparation-20260926-a1` with an exact
sibling `.dispatch`. The wrapper must create the sibling, retaining admission,
command, helper/lane/outer logs and exits there. The raw directory and four exact
`/data1/yanruj/EvolveSWDB_builds/<evaluation-id>` directories must be unused.
Public queries use the explicitly accounted raw `swdb.sqlite`; temporary compiler
files use a new accounted directory on the build volume. Original artifacts are
read-only. Query/model/source/compiler hashes are retained before compilation.

One existing `SharedCleanup`/`Owned` instance supervises all public subprocesses
and adopted descendants. Identity is retained immediately after spawning; every
stage cleans and reaps its owned descendants before the next call. The existing
monitor samples through cleanup, nominally every five seconds with a maximum
30-second gap. It enforces 16 GiB sampled RSS, 16 GiB newly retained artifacts
including a 4 GiB build subset, and 30/10 GiB raw/build free-space reserves.
Admission requires 20 GiB estimated node and 24 GiB global available memory.
These are sampled guards, not kernel quotas or true-peak guarantees.

Storage includes raw, its exact dispatch sibling, all four new build directories,
the new build-volume temporary directory and four newly written canonical
evaluation records. No unrelated historical input is charged or removed. The
single common baseline-preparation cost must remain visible when T17/T20 later
reuse these binaries; it resets none of their prior provider or experiment limits.

The driver retains requests, exact public outputs and exits, fresh evaluation
chains, compiled binary/generated-driver/compiler/model/diagnostic bindings,
sampled resources, ancestry and every direct/observed/cleanup PID-start identity,
the final original-clock accounting and shared cleanup ledger. A completed build
still means correctness unverified, timing empty, and gain false.

After helper exit, an independent operator must verify the full retained process
union and lease release, reopen the final shared cleanup ledger, and recount
storage after its last persisted dispatch/audit write. The driver cannot attest
its own reap or later wrapper writes. Retain the final read-only count outside
both charged roots, with no later writes to them. Any missing identity, failed
stage, exhausted deadline, cleanup error or storage crossing keeps the attempt
unsuccessful. Do not retry under this ID or extend its allowance.

## Storage observation correction — 2026-09-26

The actual a1 preparation at the retained `6732` code pin failed during finalization
at 21:08:44 ET. All four public compile calls and their four fresh chain checks
returned zero, but the continuous monitor's `du -sk` child was killed during
owned-descendant cleanup. The failed driver lacks final accounting; successful
individual build records do not turn that preparation into a passed attempt.
The independent terminal audit retained the failure, closed the 31 observed
PID/start identities, and confirmed release of lease generation 413. The original
attempt, outputs, limits, and successful build records remain unchanged.

The prospective correction replaces storage subprocesses in the shared batch
allocation helper and series monitor with `scripts/bfs_storage.py`. It counts
`st_blocks * 512`, including directories and symlinks, without following symlinks;
hard links are deduplicated within each root and each root is rounded upward to
KiB, matching the previous separate `du -sk` calls. Directory-relative descriptors
and `O_NOFOLLOW` reject directory-to-symlink substitution. Missing or unreadable
entries fail the observation. The bounded walk checks elapsed time between
filesystem operations and remains subject to the original enclosing guard and
cleanup clocks; a blocking filesystem syscall is not a separately guaranteed
hard deadline. It creates no cleanup-owned process, allowing the existing monitor
to remain active during teardown. No storage or elapsed allowance changes.

Local tests compare allocated-byte totals with actual `du`, reproduce the killed
accounting child with real OS signals and the production cleanup algorithm, and
verify the replacement survives the same overlap without spawning an accounting
child. The portable identity adapter in that regression is contract evidence,
not an actual Linux ownership proof. Any future host use needs the final code
pin and its applicable actual Linux lifecycle evidence. Reuse of the four
successful builds requires independent reopening of their exact public records,
requests, artifacts and terminal provenance; it must retain the failed common
preparation cost and may not relabel or rerun a1.
