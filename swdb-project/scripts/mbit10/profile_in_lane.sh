#!/usr/bin/env bash
# Run `swdb profile` for one implementation and input on mbit10, inside a socket lane.
# Created 2026-09-22. Procedure: docs/mbit10-profiling.md. Rules: .claude/rules/remote_server.md at the ArchEvolve root.
#
# USAGE (on mbit10, from anywhere)
#   bash scripts/mbit10/profile_in_lane.sh <node> <implementation> <input> [swdb profile options...]
#
# It refuses to start (exit 3) when: this is not mbit10; the MemAcc lane script is stale;
# the lease of <node> or the legacy lease is held; the runs disk is short of space; or
# tracked files outside records/ are modified. Otherwise it enters the lane through MemAcc's socket_lane.sh (which
# binds everything to <node>, takes the lease mbit10-evaluation-node<node>, and records
# affinity and load), and runs swdb profile under `timeout`.
#
# Environment:
#   EVOLVESWDB_RUNS       raw output folder (default: /data1/yanruj/EvolveSWDB_runs, or
#                         /data/yanruj/EvolveSWDB_runs when /data1 is short; see step 3)
#   EVOLVESWDB_RUNS_NOTE  why EVOLVESWDB_RUNS was chosen (recorded in the profile)
#   EVOLVESWDB_RUN_GB     room one run needs, in GB (default 5)
#   EVOLVESWDB_LANE_REPO  MemAcc checkout holding the lane script
#                         (default /data1/yanruj/Memacc-evolveswdb-lane, branch yanrujhou_main)
#   EVOLVESWDB_TOTAL_S    timeout for the whole profile (default 14400)
set -euo pipefail

die() { echo "profile_in_lane: $*" >&2; exit 3; }
[ "$#" -ge 3 ] || { sed -n '5,7p' "$0" >&2; exit 2; }
NODE="$1"; IMPL="$2"; INPUT="$3"; shift 3
case "$NODE" in 0|1) ;; *) die "node must be 0 or 1, got '$NODE'" ;; esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LANE_REPO="${EVOLVESWDB_LANE_REPO:-/data1/yanruj/Memacc-evolveswdb-lane}"
LANE_BRANCH=yanrujhou_main
LANE="$LANE_REPO/AgenticRefiner/scripts/host/socket_lane.sh"
RUNS="${EVOLVESWDB_RUNS:-}"
RUNS_NOTE="${EVOLVESWDB_RUNS_NOTE:-}"
TOTAL_S="${EVOLVESWDB_TOTAL_S:-14400}"
LEASES=/data1/yanruj/lact-host-lease

# 0. the host
[ "$(hostname -s)" = mbit10 ] || die "this is $(hostname -s), not mbit10"

# 1. the lane script must equal the repository version
git -C "$LANE_REPO" fetch -q origin "$LANE_BRANCH" || die "cannot fetch $LANE_BRANCH in $LANE_REPO"
git -C "$LANE_REPO" diff --quiet FETCH_HEAD -- AgenticRefiner/scripts/host/socket_lane.sh \
    AgenticRefiner/scripts/host/hostlock.sh || die "$LANE is stale; update $LANE_REPO first"

# 2. leases: both sockets and the legacy lease
for f in "$LEASES"/mbit10-evaluation*.meta.json; do
  printf '%s: %s\n' "$(basename "$f" .meta.json)" \
    "$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["state"], d["lease"].get("acquired_at"))' "$f")"
done
lease_state() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' "$LEASES/$1.meta.json"; }
[ "$(lease_state "mbit10-evaluation-node$NODE")" != held ] || die "lease mbit10-evaluation-node$NODE is held; pick the other lane or wait"
# the legacy lease occupies an unnamed socket without excluding a socket lease: never add a job beside it
[ "$(lease_state mbit10-evaluation)" != held ] || die "the legacy lease mbit10-evaluation is held; at most two jobs may run"

# 3. disks: raw output goes to /data1 unless it has under 20 GB free (plus the room this
#    run needs, EVOLVESWDB_RUN_GB, default 5), then to /data. EVOLVESWDB_RUNS overrides
#    the choice; EVOLVESWDB_RUNS_NOTE then says why (both are recorded in the profile).
df -h /data1 /data
free_gb() { df -BG --output=avail "$1" | tail -1 | tr -dc '0-9'; }
NEED_GB=$(( 20 + ${EVOLVESWDB_RUN_GB:-5} ))
if [ -z "$RUNS" ]; then
  if [ "$(free_gb /data1)" -ge "$NEED_GB" ]; then
    RUNS=/data1/yanruj/EvolveSWDB_runs
    RUNS_NOTE="raw output on /data1: it had $(free_gb /data1) GB free, above 20 GB plus this run's room"
  else
    RUNS=/data/yanruj/EvolveSWDB_runs
    RUNS_NOTE="raw output on /data: /data1 had $(free_gb /data1) GB free, under 20 GB plus this run's room"
  fi
fi
[ -n "$RUNS_NOTE" ] || RUNS_NOTE="raw output in $RUNS, set by EVOLVESWDB_RUNS"
mkdir -p "$RUNS/lanes"
[ "$(free_gb "$RUNS")" -ge "$NEED_GB" ] || die "$RUNS has under $NEED_GB GB free"

# 4. the checkout: report it; refuse local edits outside records/
cd "$REPO"
echo "EvolveSWDB $(git rev-parse --abbrev-ref HEAD) $(git rev-parse HEAD)"
# 2026-09-29 ET: pathspec scoped to swdb-project/ (ArchEvolve monorepo); porcelain paths are
# repo-root relative, so records/ is excluded by pathspec rather than by grep.
if git status --porcelain --untracked-files=no -- . ':!records' | grep -q .; then
  git status --short --untracked-files=no -- . ':!records' >&2
  die "tracked files outside records/ are modified"
fi

# 5. run inside the lane
JOB="evolveswdb-$IMPL-$INPUT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
set -x
exec bash "$LANE" "$NODE" "$JOB" --record "$RUNS/lanes/$JOB.$STAMP.json" -- \
  timeout --signal=TERM --kill-after=60 "$TOTAL_S" \
  python3 -m swdb profile "$IMPL" "$INPUT" mbit10 --runs-dir "$RUNS" \
    --lane "mbit10-evaluation-node$NODE" --runs-note "$RUNS_NOTE" "$@"
