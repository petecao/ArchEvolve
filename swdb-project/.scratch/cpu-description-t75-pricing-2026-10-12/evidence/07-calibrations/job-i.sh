#!/bin/bash
# Import receipts and derive resources into a copied store. Each import commits through
# writer.commit (whole-store check inside, ~10-14 min), so imports are split over two store
# copies ($RAW/records and $RAW/records-b) that run in parallel; job-v.sh merges and validates.
# Not a measurement: run pinned to a socket with numactl (no lease needed) or inside a lane.
# Usage: bash job-i.sh <node label> <store dir> <item> [<item> ...]
#   items: memory allocator openmp libcall bulk
source "$(dirname "$0")/common.sh" "$1" "job-i"
S=$2; shift 2; P=mbit10.cpu.lanl20261006
imp() { step "import-$1" 2400 python3 -m swdb import-cpu-service-calibration --records "$S" --receipt "$RAW/$2/receipt.json" --id "$P.service.$3" --format json; }
envsnap "job-i-$1-start"
for item in "$@"; do
  case $item in
    memory) imp memory-v2 memory-v2.elapsed memory-v2.a1 || exit 31
            step resource-memory-v2 2400 python3 -m swdb.cpu_memory_resource --records "$S" --source-calibration $P.service.memory-v2.a1 --id $P.resource.memory-v2.a1 --format json || exit 32 ;;
    allocator) imp allocator-v2 allocator-v2.elapsed allocator-v2.a1 || exit 33
            step resource-allocator-v2 2400 python3 -m swdb.cpu_allocator_resource --records "$S" --source-calibration $P.service.allocator-v2.a1 --id $P.resource.allocator-v2.a1 --format json || exit 34 ;;
    openmp) imp openmp-a2 openmp-a2.elapsed openmp.a2 || exit 35 ;;
    libcall) imp library-call library-call-2.elapsed library-call.a1 || exit 36 ;;
    bulk)   imp bulk-a3 bulk.a3.elapsed bulk-total.a3 || exit 37
            step resource-bulk-a3 2400 python3 -m swdb.cpu_bulk_resource --records "$S" --source-calibration $P.service.bulk-total.a3 --id $P.resource.bulk-total.a3 --format json || exit 38 ;;
    *) log "unknown item $item"; exit 39 ;;
  esac
done
envsnap "job-i-$item-end"
