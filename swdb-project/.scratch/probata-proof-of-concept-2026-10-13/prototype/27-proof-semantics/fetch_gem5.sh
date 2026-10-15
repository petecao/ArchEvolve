#!/bin/sh
# Fetch the gem5 DX100 sources at e4fc4af that ticket 27's rules cite (read-only, outside the repo).
set -e
cd /tmp/claude/probata-runs/t27/gem5
BASE=https://raw.githubusercontent.com/arkhadem/DX100/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA
for f in IF.cc SPD.cc MAA.cc RangeFuser.cc IndirectAccess.cc StreamAccess.cc ALU.cc CpuSidePort.cc MAA.py; do
  curl -sSfL -o "$f" "$BASE/$f" || echo "FAIL $f"
done
curl -sSfL -o MAA_gem5.hpp https://raw.githubusercontent.com/arkhadem/DX100/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/API/MAA_gem5.hpp || echo "FAIL api"
wc -l ./*
