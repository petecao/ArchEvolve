#!/bin/bash
# cpud ticket 10, LR-06 (created 2026-10-13 ET): identity, size/hash and no-use evidence for the
# kept ticket-03 binaries and this ticket's raw output on mbit10, then removal.
# Usage: bash lr06.sh identity   (prints evidence; deletes nothing)
#        bash lr06.sh remove     (re-checks no-use, deletes, prints what is left)
# Manifest = sha256 of `sha256sum` over the folder's files, paths sorted with LC_ALL=C
# (ticket 03's table used en_US.UTF-8 order; both are printed for the kept folders).
set -u
KEPT=/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1
RAWS="/data/yanruj/EvolveSWDB_runs/cpud10-20261013-a1 /data/yanruj/EvolveSWDB_runs/cpud10-20261013-a2 /data/yanruj/EvolveSWDB_runs/cpud10-precheck-20261012"
BUILDS=$(ls -d /data1/yanruj/EvolveSWDB_builds/cpud10.* 2>/dev/null)
ALL="$KEPT $RAWS $BUILDS"
manifest() { (cd "$1" && find . -type f | LC_ALL=$2 sort | xargs -r sha256sum | sha256sum | cut -d' ' -f1); }
nouse() {
  echo "## no-use check $(TZ=America/New_York date '+%F %T ET')"
  echo "leases: $(grep -ho '"state":"[a-z]*"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json | tr '\n' ' ')"
  for p in $ALL; do
    n=$(lsof +D "$p" 2>/dev/null | tail -n +2 | wc -l)
    q=$(ps -eo args | grep -F "$p" | grep -v -e grep -e lr06.sh | wc -l)
    echo "$p open_files=$n processes_naming_path=$q"
  done
}
case "${1:-}" in
identity)
  echo "## identity $(TZ=America/New_York date '+%F %T ET')"
  for d in "$KEPT"/a2/*/; do
    d=${d%/}
    echo "$d files=$(find "$d" -type f | wc -l) bytes=$(du -sb "$d" | cut -f1) manifest_en_US=$(manifest "$d" en_US.UTF-8) manifest_C=$(manifest "$d" C)"
    (cd "$d" && find . -type f | LC_ALL=C sort | xargs -r sha256sum | sed 's/^/    /')
  done
  echo "$KEPT total files=$(find "$KEPT" -type f | wc -l) bytes=$(du -sb "$KEPT" | cut -f1)"
  for p in $RAWS $BUILDS; do
    echo "$p files=$(find "$p" -type f | wc -l) bytes=$(du -sb "$p" | cut -f1) manifest_C=$(manifest "$p" C)"
  done
  nouse ;;
remove)
  nouse
  for p in $ALL; do rm -rf -- "$p"; done
  echo "## after removal"
  for p in $ALL; do [ -e "$p" ] && echo "STILL PRESENT $p" || echo "removed $p"; done
  df -h /data1 /data | tail -2 ;;
*) echo "usage: bash lr06.sh identity|remove" >&2; exit 2 ;;
esac
