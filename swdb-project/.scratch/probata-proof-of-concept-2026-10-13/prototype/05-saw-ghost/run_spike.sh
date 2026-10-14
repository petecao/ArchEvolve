#!/bin/sh
# Ticket 05 spike (a) runner and check, 2026-10-14 ET. Throwaway.
# Usage: run_spike.sh [runs_dir]   (default /tmp/claude/probata-runs/t05)
# Builds the safe and -DBUGGY bitcode with clang++ 22.1.8, runs SAW 1.6 on each through the
# machine-wide verifier lock (verifier_run.py), then checks the pair:
#   safe   -> proven, no warning;
#   buggy  -> refuted with a counterexample, at the read call;
#   control (buggy bitcode, the read's ghost check replaced by True) -> proven,
#            so the ghost check is the only check that fails in buggy (negative control).
# Exit 0 = every check holds.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
RUNS=${1:-/tmp/claude/probata-runs/t05}
SAWBIN=$HOME/opt/verifiers/saw-1.6/saw-1.6-macos-15-ARM64-with-solvers/bin
CLANGXX=/opt/homebrew/opt/llvm/bin/clang++
CXXFLAGS="-std=c++17 -c -emit-llvm -g -O0"
VR=/tmp/claude/probata-tools/verifier_run.py
mkdir -p "$RUNS"
# Exact peak RSS of the job (getrusage; verifier_run.py samples every 0.5 s and these jobs
# finish in under 1 s). `/usr/bin/time -l` fails in the Claude sandbox (sysctl denied).
PEAK='import resource,subprocess,sys
r=subprocess.run(sys.argv[1:])
print("PEAK_RSS_MB %.1f" % (resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/2**20))
sys.exit(r.returncode)'

run() {  # run <name> <-DBUGGY or ""> <ghost check: keep|drop>
  d=$(mktemp -d "$RUNS/scratch-$1.XXXXXX")
  (cd "$HERE" && "$CLANGXX" $CXXFLAGS $2 fixture.cpp -o "$d/fixture.bc")
  cp "$d/fixture.bc" "$RUNS/fixture-$1.bc"
  if [ "$3" = drop ]; then
    sed 's/llvm_precond {{ g @ t == 0 }};/llvm_precond {{ True }};/' "$HERE/spike.saw" > "$d/spike.saw"
    grep -q '{{ True }}' "$d/spike.saw"
  else
    cp "$HERE/spike.saw" "$d/spike.saw"
  fi
  (cd "$d" && PATH="$SAWBIN:$PATH" "$VR" --log "$RUNS/saw_$1.log" --owner t05 --timeout 900 \
     -- python3 -c "$PEAK" "$SAWBIN/saw" spike.saw) || true
  rm -rf "$d"  # verifier scratch
}
run safe "" keep
run buggy -DBUGGY keep
run control -DBUGGY drop

READ_LINE=$(grep -n 'dx100::read(b, i)' "$HERE/fixture.cpp" | cut -d: -f1)
fail=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
S="$RUNS/saw_safe.log"; B="$RUNS/saw_buggy.log"; C="$RUNS/saw_control.log"
check "safe: proven"            "grep -q 'Proof succeeded! _Z6kerneliij' '$S' && grep -q 'SPIKE: kernel verified' '$S'"
check "safe: no warning"        "! grep -qi 'warning' '$S'"
check "buggy: proof failed"     "grep -q 'Proof failed' '$B' && ! grep -q 'SPIKE: kernel verified' '$B'"
check "buggy: counterexample"   "grep -q 'Counterexample' '$B'"
check "buggy: fails at read"    "grep -q 'Subgoal failed: _Z6kerneliij fixture.cpp:$READ_LINE:.*overrideBranches' '$B' && grep -q 'No override specification applies for _ZN5dx1004readEij' '$B'"
check "buggy: one failed goal"  "[ \$(grep -c 'Subgoal failed' '$B') -eq 1 ]"
check "control: proven"         "grep -q 'Proof succeeded! _Z6kerneliij' '$C'"
exit $fail
