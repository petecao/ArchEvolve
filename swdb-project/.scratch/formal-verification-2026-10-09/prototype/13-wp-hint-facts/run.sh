#!/usr/bin/env bash
# Reproduces every result in ../../research/13-wp-hint-facts.md.
# Frama-C 33.0 (opam switch framac-33). One verifier at a time, each under a 120 s timeout.
# Usage: ./run.sh [q1|q2|q3|q4|q5|q6|q7|all]   (default: all). Logs go to logs/.
# Takes about 2 minutes. Alt-Ergo runs through a Why3 server Unix socket, so run it outside
# the Claude Code sandbox (inside it every prover call ends in "Connection error").
set -u
cd "$(dirname "$0")"
eval "$(opam env --switch=framac-33 --set-switch)"
mkdir -p logs
WP="-wp -wp-cache none -wp-timeout 5 -wp-prover alt-ergo"
FC() { gtimeout 120 frama-c "$@"; }

# run <log-name> <frama-c args...>: run once, keep the full log.
run() { local name=$1; shift; echo "== $name: frama-c $*" | tee "logs/$name.log"; FC "$@" >>"logs/$name.log" 2>&1; echo "exit=$?" >>"logs/$name.log"; }

q1() {  # ghost non-interference: kernel parse only, plus WP on cases 13-15
  for c in $(seq 1 15); do
    run "q1_case$c" q1_ghost.c -cpp-extra-args="-DCASE=$c" -print
  done
  for c in 14 15; do
    run "q1_case${c}_wp" q1_ghost.c -cpp-extra-args="-DCASE=$c" $WP -then -report
  done
  # the same interfering ghost write with the ghost:bad-use key downgraded to a warning
  run q1_case1_baduse_warning q1_ghost.c -cpp-extra-args=-DCASE=1 -kernel-warn-key ghost:bad-use=active -print
}

q2() {  # logic definitions: recursive, inductive; WP translation
  for c in $(seq 1 9); do
    run "q2_case$c" q2_logic.c -cpp-extra-args="-DCASE=$c" $WP -then -report
    # print the Why3 task WP sends to the prover: shows definition vs axiom
    run "q2_case${c}_task" q2_logic.c -cpp-extra-args="-DCASE=$c" -wp -wp-cache none -wp-gen -wp-prover alt-ergo -wp-msg-key print-generated
  done
  run q2_case3_smoke q2_logic.c -cpp-extra-args=-DCASE=3 $WP -wp-smoke-tests -then -report
}

q3() {  # check / assert / admit and their requires/ensures/lemma/invariant forms
  run q3_kinds q3_kinds.c $WP -then -report
}

q4() {  # consolidated statuses and JSON reports
  run q4_status q4_status.c $WP -wp-report-json logs/q4_wp_report.json -then -report -report-csv logs/q4_report.csv -report-classify -report-output logs/q4_classify.json
  # which lemmas are in the context of a function goal (incl. one declared after it)
  run q4_task_lemmas q4_status.c -wp -wp-cache none -wp-fct before_late,dep_lemma -wp-gen -wp-prover alt-ergo -wp-msg-key print-generated
}

q5() {  # tactics and JSON scripts
  echo "int x;" > logs/q5_x.c; run q5_tactics logs/q5_x.c -wp-tactic="?"; rm -f logs/q5_x.c
  bash q5_scripts.sh
}

q6() {  # smoke tests
  run q6_smoke q6_smoke.c $WP -wp-smoke-tests -wp-report-json logs/q6_smoke.json -then -report
  run q6_nosmoke q6_smoke.c $WP -then -report
}

q7() {  # other constructs that add unproved hypotheses
  for c in $(seq 1 9); do
    run "q7_case$c" q7_other.c -cpp-extra-args="-DCASE=$c" $WP -wp-smoke-tests -then -report
  done
  run q7_case3_nosmoke q7_other.c -cpp-extra-args=-DCASE=3 $WP -then -report
  run q7_case7_task q7_other.c -cpp-extra-args=-DCASE=7 -wp -wp-cache none -wp-gen -wp-prover alt-ergo -wp-msg-key print-generated
}

what=${1:-all}
if [ "$what" = all ]; then q1; q2; q3; q4; q5; q6; q7; else "$what"; fi
rm -rf .frama-c   # WP session folder; nothing in it is needed after the logs are written
