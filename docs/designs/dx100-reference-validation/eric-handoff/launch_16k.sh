#!/usr/bin/env bash
# Reviewed command template, not a Great Lakes execution receipt.
# Uses fresh output directories and unchanged pinned API memory mapping (16GB).
set -euo pipefail
if [[ $# != 8 ]]; then
  echo 'usage: launch_16k.sh checkpoint|restore DX100_ROOT GEM5_BINARY BFS_BINARY GRAPH OUTPUT CHECKPOINT_DIR GUEST_ENV_FILE' >&2
  exit 2
fi
phase=$1
dx_root=$(realpath "$2")
gem5=$(realpath "$3")
bfs=$(realpath "$4")
graph=$(realpath "$5")
output=$(realpath -m "$6")
checkpoint=$(realpath -m "$7")
guest_env=$(realpath "$8")
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ "$phase" == checkpoint || "$phase" == restore ]] || exit 2
[[ -x "$gem5" && -f "$bfs" && -f "$graph" && -f "$guest_env" ]] || exit 2
mkdir "$output" # Refuse reuse or accidental overwriting of another run.
export LD_LIBRARY_PATH="$dx_root/ext/ramulator2/ramulator2${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OMP_NUM_THREADS=4 OMP_DYNAMIC=FALSE OMP_PROC_BIND=false
options="-f $graph -r 0 -n 1 -v -l -a"
if [[ "$phase" == checkpoint ]]; then
  [[ "$output" == "$checkpoint" ]] || { echo 'Checkpoint phase requires OUTPUT=CHECKPOINT_DIR' >&2; exit 2; }
  command=("$gem5" "--outdir=$output" "$dx_root/configs/deprecated/example/se.py"
    --cpu-type AtomicSimpleCPU -n 4 --mem-size 16GB --max-checkpoints=1
    --env "$guest_env" --cmd "$bfs" --options "$options")
else
  : "${VERIFY_MAX_TICKS:?Set an explicit positive simulated-tick budget for post-ROI verification}"
  [[ "$VERIFY_MAX_TICKS" =~ ^[1-9][0-9]*$ ]] || exit 2
  [[ -d "$checkpoint" ]] || exit 2
  command=("$gem5" "--outdir=$output" "$here/continue_to_verifier.py"
    --dx100-source-root "$dx_root" --verify-max-ticks "$VERIFY_MAX_TICKS" --
    --cpu-type X86O3CPU -r 1 --checkpoint-dir "$checkpoint" -n 4 --mem-size 16GB
    --sys-clock 3.2GHz --cpu-clock 3.2GHz
    --caches --l1d_size=32kB --l1d_assoc=8 --l1d-hwp-type=StridePrefetcher --l1d_mshrs=16 --l1d_write_buffers=8
    --l1i_size=32kB --l1i_assoc=8 --l1i-hwp-type=StridePrefetcher --l1i_mshrs=16 --l1i_write_buffers=8
    --l2cache --l2_size=256kB --l2_assoc=4 --l2-hwp-type=StridePrefetcher --l2_mshrs=32 --l2_write_buffers=16
    --l3cache --l3_size=8MB --l3_assoc=16 --l3_mshrs=256 --l3_write_buffers=128 --l3_ports 4
    --cacheline_size=64 --mem-type Ramulator2 --ramulator-config "$here/ramulator.yaml"
    --mem-channels 2 --maa_ncbus_width 32 --maa --maa_num_maas 1 --maa_num_tile_elements 16384
    --maa_l2_uncacheable --maa_l3_uncacheable --maa_num_initial_row_table_slices 32
    --env "$guest_env" --cmd "$bfs" --options "$options" --prog-interval=1000)
fi
# Record argv as separate JSON strings, not an ambiguous shell-joined command.
python3 - "$output/command.json" "${command[@]}" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:],indent=2)+'\n')
PY
set +e
"${command[@]}" > "$output/run.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$output/exit-code.txt"
exit "$result"
