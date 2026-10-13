#!/bin/bash
# Library-call rerun (attempt 2) from the checkout with the pilot-headroom fix.
# Usage: SRC=<fixed checkout>/swdb-project bash job-l.sh <node>
source "$(dirname "$0")/common.sh" "$1" job-l
envsnap job-l-start
step libcall-count-2 3600 python3 -m swdb cpu-service-calibrate --service-group library_call --records "$RAW/records" --output "$RAW/library-call-2.count" \
  --count-only "${TC[@]}" --max-wall-s 900 --format json || exit 51
step libcall-elapsed-2 3600 python3 -m swdb cpu-service-calibrate --service-group library_call --records "$RAW/records" --output "$RAW/library-call-2.elapsed" \
  "${TC[@]}" --repetitions 7 --min-trial-s .05 --max-wall-s 900 --format json || exit 52
envsnap job-l-end
