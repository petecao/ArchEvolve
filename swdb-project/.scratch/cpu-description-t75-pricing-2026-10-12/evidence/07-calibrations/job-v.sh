#!/bin/bash
# Merge the records-c imports (bulk a3, library-call) into the import store $RAW/records-b
# (a copy of the checkout's records/ plus the openmp, memory and allocator imports), then
# targeted and whole-store validation. Not a measurement.
# Usage: bash job-v.sh <node label>
source "$(dirname "$0")/common.sh" "$1" job-v
P=mbit10.cpu.lanl20261006
IDS="$P.service.memory-v2.a1 $P.resource.memory-v2.a1 $P.service.allocator-v2.a1 $P.resource.allocator-v2.a1 $P.service.openmp.a2 $P.service.library-call.a1 $P.service.bulk-total.a3 $P.resource.bulk-total.a3"
envsnap job-v-start
for f in cpu_service_calibrations/$P.service.library-call.a1.yaml cpu_service_calibrations/$P.service.bulk-total.a3.yaml \
         cpu_bulk_resource_calibrations/$P.resource.bulk-total.a3.yaml; do
  [ -e "$RAW/records-b/$f" ] && { log "refuse: $f already in records-b"; exit 41; }
  cp -p "$RAW/records-c/$f" "$RAW/records-b/$f" || exit 42
done
log "merged records-c imports into records-b"
step targeted-validate 1200 env PYTHONPATH="$SRC" python3 "$RAW/scripts/targeted_validate.py" "$RAW/records-b" $IDS || exit 43
step whole-validate 3600 python3 -m swdb validate --records "$RAW/records-b" --library "$SRC/library" || exit 44
envsnap job-v-end
