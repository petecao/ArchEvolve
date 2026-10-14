#!/usr/bin/env bash
# Run one proof batch (`swdb prove-lane run`) on mbit10 inside a socket lane: up to 6 workers,
# each pinned to its own physical core, each under an 8 GB RSS watchdog.
# Created 2026-10-14 ET (Probata proof of concept ticket 57), after profile_in_lane.sh.
# Rules: .claude/rules/remote_server.md at the ArchEvolve root. Format: docs/reference/format-v0.4-proof.md.
#
# USAGE (on mbit10)
#   bash scripts/mbit10/prove_in_lane.sh <node> <plan.yaml> [--records <folder>]
#
# It refuses to start (exit 3) when: this is not mbit10; the MemAcc lane script is stale; the lease
# of <node> or the legacy lease is held (the states of all three are recorded first, by
# `swdb prove-lane leases`); the runs disk is short of space; or tracked files outside records/ are
# modified. Otherwise it enters the lane through MemAcc's socket_lane.sh and runs the batch under
# `timeout`. Inside, `swdb prove-lane run` checks again that socket_lane.sh started it and holds the lease.
#
# Environment:
#   EVOLVESWDB_RUNS       raw output folder (default: /data1/yanruj/EvolveSWDB_runs, or
#                         /data/yanruj/EvolveSWDB_runs when /data1 is short)
#   EVOLVESWDB_RUN_GB     room one batch needs, in GB (default 2)
#   EVOLVESWDB_LANE_REPO  MemAcc checkout holding the lane script (default /data1/yanruj/Memacc-evolveswdb-lane)
#   EVOLVESWDB_TOTAL_S    timeout for the whole batch (default 7200)
#   EVOLVESWDB_PYTHON     interpreter for swdb (default python3)
set -euo pipefail

die() { echo "prove_in_lane: $*" >&2; exit 3; }
[ "$#" -ge 2 ] || { sed -n '6,8p' "$0" >&2; exit 2; }
NODE="$1"; PLAN="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2
case "$NODE" in 0|1) ;; *) die "node must be 0 or 1, got '$NODE'" ;; esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LANE_REPO="${EVOLVESWDB_LANE_REPO:-/data1/yanruj/Memacc-evolveswdb-lane}"
LANE_BRANCH=yanrujhou_main
LANE="$LANE_REPO/AgenticRefiner/scripts/host/socket_lane.sh"
RUNS="${EVOLVESWDB_RUNS:-}"
TOTAL_S="${EVOLVESWDB_TOTAL_S:-7200}"
PY="${EVOLVESWDB_PYTHON:-python3}"

# 0. the host
[ "$(hostname -s)" = mbit10 ] || die "this is $(hostname -s), not mbit10"

# 1. the lane script must equal the repository version
git -C "$LANE_REPO" fetch -q origin "$LANE_BRANCH" || die "cannot fetch $LANE_BRANCH in $LANE_REPO"
git -C "$LANE_REPO" diff --quiet FETCH_HEAD -- AgenticRefiner/scripts/host/socket_lane.sh \
    AgenticRefiner/scripts/host/hostlock.sh || die "$LANE is stale; update $LANE_REPO first"
echo "lane script: $LANE at $(git -C "$LANE_REPO" rev-parse HEAD) = FETCH_HEAD $(git -C "$LANE_REPO" rev-parse FETCH_HEAD)"

# 2. disks: /data1 unless it has under 20 GB free plus this batch's room, then /data
df -h /data1 /data
free_gb() { df -BG --output=avail "$1" | tail -1 | tr -dc '0-9'; }
NEED_GB=$(( 20 + ${EVOLVESWDB_RUN_GB:-2} ))
if [ -z "$RUNS" ]; then
  if [ "$(free_gb /data1)" -ge "$NEED_GB" ]; then RUNS=/data1/yanruj/EvolveSWDB_runs
  else RUNS=/data/yanruj/EvolveSWDB_runs; fi
fi
mkdir -p "$RUNS/lanes"
[ "$(free_gb "$RUNS")" -ge "$NEED_GB" ] || die "$RUNS has under $NEED_GB GB free"

# 3. the checkout: report it; refuse local edits outside records/
cd "$REPO"
echo "ArchEvolve $(git rev-parse --abbrev-ref HEAD) $(git rev-parse HEAD)"
if git status --porcelain --untracked-files=no -- . ':!records' | grep -q .; then
  git status --short --untracked-files=no -- . ':!records' >&2
  die "tracked files outside records/ are modified"
fi

# 4. leases: both sockets and the legacy lease, recorded before dispatch
JOB="evolveswdb-prove-$(basename "$PLAN" .yaml)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LEASES="$RUNS/lanes/$JOB.$STAMP.leases.json"
"$PY" -m swdb prove-lane leases --node "$NODE" --out "$LEASES" || die "lease check refused (recorded in $LEASES)"

# 5. run inside the lane
set -x
exec bash "$LANE" "$NODE" "$JOB" --record "$RUNS/lanes/$JOB.$STAMP.json" -- \
  timeout --signal=TERM --kill-after=60 "$TOTAL_S" \
  "$PY" -m swdb prove-lane run "$PLAN" --runs-dir "$RUNS" --lease-check "$LEASES" --format json "$@"
