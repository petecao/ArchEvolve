#!/usr/bin/env bash
# Run `swdb profile` for one implementation and input on mbit10, inside a socket lane.
# Created 2026-09-22. Procedure: docs/mbit10-profiling.md. Rules: .claude/rules/remote_server.md.
#
# USAGE (on mbit10, from anywhere)
#   bash scripts/mbit10/profile_in_lane.sh <node> <implementation> <input> [swdb profile options...]
#
# It refuses to start (exit 3) when: this is not mbit10; the MemAcc lane script is stale;
# the lease of <node> is held; the runs disk is short of space; or tracked files outside
# records/ are modified. Otherwise it enters the lane through MemAcc's socket_lane.sh (which
# binds everything to <node>, takes the lease mbit10-evaluation-node<node>, and records
# affinity and load), and runs swdb profile under `timeout`.
#
# Environment:
#   EVOLVESWDB_RUNS       raw output folder (default /data/yanruj/EvolveSWDB_runs)
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
RUNS="${EVOLVESWDB_RUNS:-/data/yanruj/EvolveSWDB_runs}"
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
state="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' "$LEASES/mbit10-evaluation-node$NODE.meta.json")"
[ "$state" != held ] || die "lease mbit10-evaluation-node$NODE is held; pick the other lane or wait"

# 3. disks: /data1 must keep 20 GB; the runs folder needs room too
df -h /data1 /data
free_gb() { df -BG --output=avail "$1" | tail -1 | tr -dc '0-9'; }
[ "$(free_gb /data1)" -ge 20 ] || die "/data1 has under 20 GB free"
mkdir -p "$RUNS/lanes"
[ "$(free_gb "$RUNS")" -ge 20 ] || die "$RUNS has under 20 GB free"

# 4. the checkout: report it; refuse local edits outside records/
cd "$REPO"
echo "EvolveSWDB $(git rev-parse --abbrev-ref HEAD) $(git rev-parse HEAD)"
if git status --porcelain --untracked-files=no | grep -v ' records/' | grep -q .; then
  git status --short --untracked-files=no >&2
  die "tracked files outside records/ are modified"
fi

# 5. run inside the lane
JOB="evolveswdb-$IMPL-$INPUT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NOTE="raw output on ${RUNS%%/yanruj*}: agreed 2026-09-22 with the GPU campaign holding node 0 (/data1 near its 20 GB floor)"
set -x
exec bash "$LANE" "$NODE" "$JOB" --record "$RUNS/lanes/$JOB.$STAMP.json" -- \
  timeout --signal=TERM --kill-after=60 "$TOTAL_S" \
  python3 -m swdb profile "$IMPL" "$INPUT" mbit10 --runs-dir "$RUNS" \
    --lane "mbit10-evaluation-node$NODE" --runs-note "$NOTE" "$@"
