#!/usr/bin/env bash
# Outcome-free registered Jacobi counts. Created: 2026-10-06 ET.
# Parent owns source checkout, socket lease/wrapper, bounds, disk reserve, and export.
set -euo pipefail
if [[ $# != 3 ]]; then
  echo 'usage: bash 14-count-pagerank-20261006.sh cpu|dx100|maple NEW_RAW LLVM_BIN' >&2
  exit 2
fi
case "$1" in
  cpu) threads=1 ;;
  dx100) threads=4 ;;
  maple) threads=2 ;;
  *) echo 'unsupported case' >&2; exit 2 ;;
esac
case_id="$1"
raw="$2"
llvm_bin="$3"
[[ "$raw" = /* && ! -e "$raw" && "$llvm_bin" = /* ]]
[[ -f apps/gapbs/src/pr_spmv.cc && -f records/implementations/gapbs-pr-jacobi-analytic-v1.yaml ]]
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
python3 - "$raw" <<'PY'
import sys
from pathlib import Path
from swdb import artifacts,paths
p=Path(sys.argv[1]).resolve()
assert p!=paths.HOME and paths.HOME not in p.parents
assert not p.exists()
assert artifacts.file_hash(paths.HOME/'apps/gapbs/src/pr_spmv.cc')=='ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70'
PY
mkdir -p "$raw"
cp -R records "$raw/records"
snapshot="pagerank-jacobi-20261006.${case_id}.t${threads}.a1.source"
characterization="pagerank.jacobi.kron-g16.${case_id}.t${threads}.characterization.generality.a1"
python3 -m swdb source-snapshot gapbs-pr-jacobi-analytic-v1 \
  --records "$raw/records" --db "$raw/index.sqlite" --runs-dir "$raw/sources" \
  --id "$snapshot" --format json > "$raw/source-snapshot.json"
python3 -m swdb characterize --records "$raw/records" \
  --implementation gapbs-pr-jacobi-analytic-v1 --source-snapshot "$snapshot" \
  --adapter registered-functional --input kron-g16-k16 --threads "$threads" --trials 5 \
  --counting-pipeline source-normalized-v2 --object-scopes --llvm-bin "$llvm_bin" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --run-library-path "$(dirname "$llvm_bin")/lib/x86_64-unknown-linux-gnu" \
  --id "$characterization" --output "$raw/counted" --timeout-s 600 --format json \
  > "$raw/characterization.json"
python3 -m swdb validate --records "$raw/records" > "$raw/validate.txt"
