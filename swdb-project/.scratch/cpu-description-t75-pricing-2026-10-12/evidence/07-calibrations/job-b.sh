#!/bin/bash
# Lane B: OpenMP set a2 (times class 22 only; count proof covers all 23), library_call family.
source "$(dirname "$0")/common.sh" "$1" job-b
envsnap job-b-start
step openmp-a2-count 1500 python3 -m swdb.cpu_openmp_calibration --records "$RAW/records" --output "$RAW/openmp-a2.count" --count-only "${TC[@]}" --max-wall-s 900 || exit 21
step openmp-a2-elapsed 1500 python3 -m swdb.cpu_openmp_calibration --records "$RAW/records" --output "$RAW/openmp-a2.elapsed" --profile 22 "${TC[@]}" \
  --repetitions 7 --min-trial-s .05 --max-wall-s 900 || exit 22
step openmp-a2-validate 600 python3 -m swdb.cpu_openmp_calibration --validate-receipt "$RAW/openmp-a2.elapsed/receipt.json" || exit 23
step libcall-count 1500 python3 -m swdb cpu-service-calibrate --service-group library_call --records "$RAW/records" --output "$RAW/library-call.count" \
  --count-only "${TC[@]}" --max-wall-s 900 --format json || exit 24
step libcall-elapsed 1500 python3 -m swdb cpu-service-calibrate --service-group library_call --records "$RAW/records" --output "$RAW/library-call.elapsed" \
  "${TC[@]}" --repetitions 7 --min-trial-s .05 --max-wall-s 900 --format json || exit 25
envsnap job-b-end
