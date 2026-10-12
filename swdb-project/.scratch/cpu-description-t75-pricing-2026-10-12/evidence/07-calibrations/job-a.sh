#!/bin/bash
# Lane A: memory_v2, allocator v2, memmove bulk-total batch a3 (count proof, then elapsed, each).
source "$(dirname "$0")/common.sh" "$1" job-a
envsnap job-a-start
step memory-v2-count 3600 python3 -m swdb.cpu_memory_calibration --records "$RAW/records" --output "$RAW/memory-v2.count" --count-only \
  --group memory_v2 --operation write --element-bytes 1 --element-bytes 2 --footprint-bytes 8388608 "${TC[@]}" --max-wall-s 900 || exit 11
step memory-v2-elapsed 3600 python3 -m swdb.cpu_memory_calibration --records "$RAW/records" --output "$RAW/memory-v2.elapsed" \
  --group memory_v2 --operation write --element-bytes 1 --element-bytes 2 --footprint-bytes 8388608 "${TC[@]}" --repetitions 7 --min-trial-s .05 --max-wall-s 900 || exit 12
CELLS=(--cell malloc:64 --cell malloc:128 --cell malloc:6144 --cell malloc:2097152 --cell new_array:16777216 --cell new_array:16777220 --cell delete_array:16777216 --cell delete_array:16777220)
step allocator-v2-count 3600 python3 -m swdb cpu-service-calibrate --records "$RAW/records" --service-group allocator "${CELLS[@]}" "${TC[@]}" \
  --count-build-cap-mib 64 --max-wall-s 900 --format json --output "$RAW/allocator-v2.count" --count-only || exit 13
step allocator-v2-elapsed 3600 python3 -m swdb cpu-service-calibrate --records "$RAW/records" --service-group allocator "${CELLS[@]}" "${TC[@]}" \
  --count-build-cap-mib 64 --max-wall-s 900 --format json --output "$RAW/allocator-v2.elapsed" --repetitions 7 --min-trial-s .05 || exit 14
SIZES=(--size 140 --size 4388 --size 7300 --size 9044 --size 14496 --size 30164)
step bulk-a3-count 3600 python3 -m swdb.cpu_bulk_total_calibration --records "$RAW/records" --output "$RAW/bulk.a3.count" "${TC[@]}" \
  --repetitions 7 --min-trial-s .05 --max-wall-s 900 --count-only "${SIZES[@]}" || exit 15
step bulk-a3-elapsed 3600 python3 -m swdb.cpu_bulk_total_calibration --records "$RAW/records" --output "$RAW/bulk.a3.elapsed" "${TC[@]}" \
  --repetitions 7 --min-trial-s .05 --max-wall-s 900 "${SIZES[@]}" || exit 16
envsnap job-a-end
