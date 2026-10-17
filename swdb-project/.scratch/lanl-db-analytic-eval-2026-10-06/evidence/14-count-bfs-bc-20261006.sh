#!/usr/bin/env bash
# Actual baseline work, with unsupported accelerator mapping retained. 2026-10-06 ET.
set -euo pipefail
[[ $# = 3 ]] || { echo 'usage: bash 14-count-bfs-bc-20261006.sh bfs-maple|bc-maple|bc-dx100 NEW_RAW LLVM_BIN' >&2; exit 2; }
case_id="$1"; raw="$2"; llvm_bin="$3"
case "$case_id" in
  bfs-maple) implementation=gapbs-bfs-do; kernel=bfs; threads=2; adapter=registered-gapbs; input=kron-g16-k16 ;;
  bc-maple) implementation=gapbs-bc-brandes; kernel=bc; threads=2; adapter=registered-gapbs; input=kron-g16-k16 ;;
  bc-dx100) implementation=dx100-bc-scalar; kernel=bc; threads=4; adapter=registered-functional; input=dx100-functional-kron-g16-k16 ;;
  *) echo 'unsupported case' >&2; exit 2 ;;
esac
[[ "$raw" = /* && ! -e "$raw" && "$llvm_bin" = /* ]]
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
python3 - "$raw" <<'PY'
import sys
from pathlib import Path
from swdb import paths
p=Path(sys.argv[1]).resolve()
assert p!=paths.HOME and paths.HOME not in p.parents and not p.exists()
PY
mkdir -p "$raw"
cp -R records "$raw/records"
extra=()
if [[ "$adapter" = registered-functional ]]; then
  snapshot="${implementation}-generality-20261006.t${threads}.a1.source"
  python3 -m swdb source-snapshot "$implementation" --records "$raw/records" \
    --db "$raw/index.sqlite" --runs-dir "$raw/sources" --id "$snapshot" --format json > "$raw/source-snapshot.json"
  extra=(--source-snapshot "$snapshot" --target-description dx100-e4fc4af-functional-analytic-v1.t4.estimated.a2)
fi
characterization="${kernel}.kron-g16.${case_id}.t${threads}.characterization.generality.a1"
python3 -m swdb characterize --records "$raw/records" --implementation "$implementation" \
  --adapter "$adapter" --input "$input" --threads "$threads" --trials 5 "${extra[@]}" \
  --counting-pipeline source-normalized-v2 --object-scopes --llvm-bin "$llvm_bin" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --run-library-path "$(dirname "$llvm_bin")/lib/x86_64-unknown-linux-gnu" \
  --id "$characterization" --output "$raw/counted" --timeout-s 600 --format json > "$raw/characterization.json"
python3 -m swdb validate --records "$raw/records" > "$raw/validate.txt"
