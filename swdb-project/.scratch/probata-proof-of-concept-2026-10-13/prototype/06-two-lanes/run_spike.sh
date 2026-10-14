#!/bin/sh
# Ticket 06 spike (b) runner and verdict check, 2026-10-14 ET. Throwaway.
# Usage: run_spike.sh [job ...]   (no job = every job in the table; RUNS overrides the runs folder)
#        run_spike.sh --check [job ...]   (check existing logs only)
# Each job: build the unit's bitcode (clang++ 22.1.8, -std=c++17 -g -O0; TILE_SIZE 2, NUM_CORES 1,
# chunk 2), run SAW 1.6 on the harness entry with the per-call summaries as overrides, ONE job at a
# time through the machine-wide verifier lock (verifier_run.py, 8 GB cap). Then check each job's
# verdict against the table. Exit 0 = every check holds.
# Modes: l1 = lever 1 (all inputs symbolic, one job, 15-minute budget);
#        sA-B = lever 2, shapes [A, B) of shapes.py, one llvm_verify per shape in one SAW process
#        (each shape's own wall time is SAW's `time`; the 15-minute bar applies per shape).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
SWDB=$(cd "$HERE/../../../.." && pwd)
RUNS=${RUNS:-/tmp/claude/probata-runs/t06}
SAWBIN=$HOME/opt/verifiers/saw-1.6/saw-1.6-macos-15-ARM64-with-solvers/bin
CLANGXX=/opt/homebrew/opt/llvm/bin/clang++
CXXFLAGS="-std=c++17 -c -emit-llvm -g -O0 -I$SWDB/library/dx100"
VR=/tmp/claude/probata-tools/verifier_run.py
BUDGET=900          # seconds per bounded job (map 19 item 8)
# SAW settings for every job (dev experiments override them with SAW_SETTINGS=...). Default
# memory model (the SMT-array model made loop bounds symbolic: attempt 4 hit the 8 GB cap);
# yices answers the path-satisfiability queries.
SAW_SETTINGS=${SAW_SETTINGS:-set_path_sat_solver \"yices\";}
mkdir -p "$RUNS"
# Exact peak RSS of the job (getrusage of the SAW child; verifier_run.py samples every 0.5 s).
PEAK='import resource,subprocess,sys
r=subprocess.run(sys.argv[1:])
print("PEAK_RSS_MB %.1f" % (resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/2**20))
sys.exit(r.returncode)'

# name | unit | extra clang flags | wait rule | mode | expected verdict | expected failing check
# Controls run on shape 95 (nf2_f01_o0133: frontier {0,1}, edges 0->2, 1->2, 1->x), map 19's
# hand-derived minimum scope.
JOBS='peter_l1|peter||gem5|l1|timeout|-
maa_l1|maa||gem5|l1|timeout|-
peter_cal|peter||gem5|s84-86|proven|-
peter_s95|peter||gem5|s95-96|proven|-
maa_s95|maa||gem5|s95-96|proven|-
peter_dropped_wait|peter|-DSWDB_DXC_FAULT_DROPPED_WAIT|gem5|s95-96|refuted|override:_Z13get_tile_sizei
peter_read_before_wait|peter|-DSWDB_DXC_FAULT_READ_BEFORE_WAIT|gem5|s95-96|refuted|override:_Z20swdb_probe_tile_readi
peter_index_wrap|peter|-DSWDB_DXC_FAULT_INDEX_WRAP|gem5|s95-96|refuted|override:_Z21swdb_ps_stream_boundsiii
peter_forged_frontier|peter|-DSWDB_DXC_FAULT_FORGED_FRONTIER_V2|gem5|s95-96|refuted|assert:P2_reached_pushed_exactly_once
peter_dropped_continuation|peter|-DSWDB_DXC_FAULT_DROPPED_CONTINUATION|gem5|s95-96|refuted|assert:P2_reached_
peter_chunk_off_by_one|peter|-DSWDB_DXC_FAULT_CHUNK_OFF_BY_ONE|gem5|s95-96|refuted|override:_Z23swdb_ps_stream_capacityiii
peter_skipped_cas_recheck|peter|-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK|gem5|s95-96|refuted|assert:P2_reached_pushed_exactly_once
maa_wait_deleted|maa|-DMAA_CONTROL=1|gem5|s95-96|refuted|override:_Z20swdb_probe_tile_readi
maa_old_wait_rule|maa|-DMAA_CONTROL=2|old|s95-96|refuted|override:_Z20swdb_probe_tile_readi
maa_cpu_read_parent|maa|-DMAA_CONTROL=3|gem5|s95-96|refuted|override:_Z14swdb_probe_cpuii
maa_wait_tile6|maa|-DMAA_CONTROL=4|gem5|s95-96|refuted|override:_Z20swdb_probe_tile_readi
maa_wait_tile7|maa|-DMAA_CONTROL=5|gem5|s95-96|refuted|override:_Z20swdb_probe_tile_readi'

field() { echo "$1" | cut -d'|' -f"$2"; }
job_line() { echo "$JOBS" | grep "^$1|" ; }

run() {  # run <name>
  line=$(job_line "$1"); [ -n "$line" ] || { echo "unknown job $1"; exit 2; }
  unit=$(field "$line" 2); flags=$(field "$line" 3); rule=$(field "$line" 4); mode=$(field "$line" 5)
  d=$(mktemp -d "$RUNS/scratch-$1.XXXXXX")
  (cd "$HERE" && "$CLANGXX" $CXXFLAGS $flags "unit_$unit.cpp" -o "$d/unit.bc")
  cp "$d/unit.bc" "$RUNS/$1.bc"
  cp "$HERE/ghost.cry" "$HERE/summaries.saw" "$HERE/units.saw" "$d/"
  old=false; [ "$rule" = old ] && old=true
  case "$unit" in
    peter) entry=_Z15swdb_unit_peterii; extra='';;
    maa) entry=_Z13swdb_unit_maai; extra='ovm <- make_maa_overrides m gh;';;
  esac
  fault=''; case "$flags" in *INDEX_WRAP*|*CHUNK_OFF_BY_ONE*|*DROPPED_CONTINUATION*) fault='ovf <- make_fault_overrides m gh;';; esac
  ovl=ovs; [ -n "$extra" ] && ovl="(concat $ovl ovm)"; [ -n "$fault" ] && ovl="(concat $ovl ovf)"
  timeout=$BUDGET
  {
    echo 'enable_experimental;'
    echo 'enable_what4_hash_consing;'
    if [ -n "${PROFILE:-}" ]; then echo "enable_crucible_profiling \"$PROFILE\";"; fi
    echo "$SAW_SETTINGS"
    echo 'import "ghost.cry";'
    echo 'include "summaries.saw";'
    echo 'include "units.saw";'
    echo 'gh <- declare_ghost_state "dx100";'
    echo 'm <- llvm_load_module "unit.bc";'
    echo "ovs <- make_overrides m gh $old;"
    echo "$extra"
    echo "$fault"
  } > "$d/driver.saw"
  case "$mode" in
    l1) echo "t <- time (llvm_verify m \"$entry\" $ovl true (${unit}_spec gh) z3);" >> "$d/driver.saw";;
    s*) a=${mode#s}; first=${a%-*}; last=${a#*-}
        python3 "$HERE/shapes.py" driver "$unit" "$first" "$last" "$d/shapes.saw" --overrides "$ovl"
        cat "$d/shapes.saw" >> "$d/driver.saw"
        timeout=$(( BUDGET * (last - first) ));;
  esac
  echo 'print "SPIKE: unit verified";' >> "$d/driver.saw"
  (cd "$d" && PATH="$SAWBIN:$PATH" "$VR" --log "$RUNS/$1.log" --owner t06 --timeout "$timeout" \
     -- python3 -c "$PEAK" "$SAWBIN/saw" driver.saw) || true
  cp "$d/driver.saw" "$RUNS/$1.driver.saw"
  rm -rf "$d"  # verifier scratch
}

# Shape jobs over budget: "Time:" lines (SAW `time`, seconds) above BUDGET.
over_budget() { grep -o 'Time: [0-9.]*s' "$1" | tr -d 's' | awk -v b="$BUDGET" '$2 > b' | wc -l | tr -d ' '; }

check() {  # check <name>: verdict and failing check against the table
  line=$(job_line "$1"); mode=$(field "$line" 5); want=$(field "$line" 6); site=$(field "$line" 7)
  L="$RUNS/$1.log"; ok=1
  case "$want" in
    timeout)
      grep -q '"timed_out": true' "$L.summary.json" || ok=0;;
    proven)
      grep -q 'SPIKE: unit verified' "$L" || ok=0
      if [ "${mode#s}" != "$mode" ]; then
        a=${mode#s}; n=$(( ${a#*-} - ${a%-*} ))
        [ "$(grep -c '^SHAPE_PROVEN' "$L")" -eq "$n" ] || ok=0
        [ "$(over_budget "$L")" -eq 0 ] || ok=0
      fi;;
    refuted)
      grep -q 'Proof failed' "$L" && grep -q 'Counterexample' "$L" && ! grep -q 'SPIKE: unit verified' "$L" || ok=0
      kind=${site%%:*}; what=${site#*:}
      nfail=$(grep -c 'Subgoal failed' "$L" || true)
      if [ "$kind" = override ]; then
        nhit=$(grep -c "No override specification applies for $what" "$L" || true)
      else
        nhit=$(grep -A3 'Subgoal failed' "$L" | grep -c "$what" || true)
      fi
      # every failed subgoal is the expected check (the negative control is attributable)
      [ "$nfail" -ge 1 ] && [ "$nhit" -ge "$nfail" ] || ok=0;;
  esac
  if [ "$want" != timeout ]; then
    grep -q '"timed_out": true' "$L.summary.json" && ok=0
    grep -q '"killed_by_watchdog": true' "$L.summary.json" && ok=0
  fi
  if [ $ok = 1 ]; then echo "PASS $1 ($want)"; else echo "FAIL $1 (want $want, $site)"; fi
  [ $ok = 1 ]
}

check_only=0; if [ "${1:-}" = --check ]; then check_only=1; shift; fi
if [ $# -eq 0 ]; then set -- $(echo "$JOBS" | cut -d'|' -f1); fi
[ $check_only = 1 ] || for j in "$@"; do run "$j"; done
fail=0
for j in "$@"; do check "$j" || fail=1; done
exit $fail
