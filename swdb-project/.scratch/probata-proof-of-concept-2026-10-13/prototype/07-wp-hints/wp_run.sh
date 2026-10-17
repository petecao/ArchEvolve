#!/bin/sh
# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Frozen WP invocation for the spike (map 13 item 7 flags): fresh run folder and session,
# -wp-cache none, default Frama-C warning levels, x86_64 machdep, no WP environment variables.
# Method18 (2026-10-15 ET): initialization filtering is disabled in EVERY invocation; no waived premises.
# Usage: wp_run.sh parse|wp-gen|wp|wp-smoke <run_dir> <file.c>  |  wp_run.sh round <run_dir> <file.c> <cache_dir> [timeout_s]
#   <run_dir> must already hold <file.c> and the stand-in headers; it must not hold .frama-c/.
# Run it through /tmp/claude/probata-tools/verifier_run.py, with the agent sandbox off (Why3 socket).
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
mode="$1"; dir="$2"; file="$3"
cd "$dir" || exit 2
[ -e .frama-c ] && { echo "refusing: $dir/.frama-c exists (stale session)"; exit 2; }
cache_arg="$4"; tmo_arg="${5:-10}"
set -- -machdep x86_64 -wp-no-filter-init "$file"
case "$mode" in
  parse) exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" -print -ocode printed.c ;;
  # VC generation only (no prover): catches WP user errors (e.g. an infinite range in loop assigns).
  wp-gen) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-cache none -wp-session session -wp-prover none ;;
  # t07c method change (a): hint-round runs. TDStep's goals plus global lemmas only, no smoke tests,
  # a shorter per-prover timeout, and a run-local cache. Never a verdict: the verdict is read only
  # from a fresh full `wp-smoke` replay (no cache). Usage: wp_run.sh round <run_dir> <file.c> <cache_dir> <timeout_s>
  round) [ -n "$cache_arg" ] || { echo "round needs <cache_dir>"; exit 2; }; rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-fct TDStep -wp-cache update -wp-cache-dir "$cache_arg" -wp-session session \
      -wp-prover alt-ergo,z3,cvc5 -wp-timeout "$tmo_arg" -wp-par 12 -wp-report-json goals.json \
      -then -wp-fct= -wp-prop=@lemma -wp-report-json lemmas.json -then -report -report-untried ;;
  # t07d method change (c): the same two runs with WP's strategy engine on, so `\wp::strategy` hints
  # (with their `\wp::proof` attachment) can prune a goal's hypotheses. `tip` adds the script prover;
  # `-wp-script dry` explores strategies from scratch and saves no script (fresh session, nothing reused).
  # Goals without a strategy hint go to the three provers exactly as before.
  round-s) [ -n "$cache_arg" ] || { echo "round-s needs <cache_dir>"; exit 2; }; rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-fct TDStep -wp-cache update -wp-cache-dir "$cache_arg" -wp-session session \
      -wp-prover tip,alt-ergo,z3,cvc5 -wp-script dry -wp-timeout "$tmo_arg" -wp-par 12 -wp-report-json goals.json \
      -then -wp-fct= -wp-prop=@lemma -wp-report-json lemmas.json -then -report -report-untried ;;
  wp-smoke-s) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-cache none -wp-session session -wp-prover tip,alt-ergo,z3,cvc5 -wp-script dry -wp-timeout 30 -wp-par 12 \
      -wp-smoke-tests -wp-report-json goals.json -then -report -report-untried ;;
  # Method21: full no-hint diagnostic baseline only. Final modes remain fixed at30s.
  baseline-smoke10) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 -wp-timeout 10 -wp-par 12 \
      -wp-smoke-tests -wp-report-json goals.json -then -report -report-untried ;;
  # Method20: full generation with no prover, then an explicitly diagnostic class run.
  # No result from these modes is an incumbent or final verdict.
  probe-gen) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-gen -wp-fct TDStep -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 -wp-report-json goals.json \
      -then -wp-fct= -wp-prop=@lemma -wp-report-json lemmas.json -then -report -report-untried ;;
  focused)
    case "$cache_arg" in
      '-wp-fct TDStep -wp-prop=@assigns'|'-wp-fct TDStep -wp-prop=@invariant'|'-wp-fct TDStep -wp-prop=@assert'|'-wp-fct TDStep -wp-prop=@check'|'-wp-fct TDStep -wp-prop=@ensures'|'-wp-fct TDStep -wp-prop=@variant'|'-wp-fct TDStep -wp-prop=@requires'|'-wp-fct TDStep -wp-prop=@terminates') ;;
      *) echo 'refusing unrecognized focused diagnostic selection'; exit 2 ;;
    esac
    rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp $cache_arg -wp-cache none -wp-session session -wp-prover tip,alt-ergo,z3,cvc5 \
      -wp-script dry -wp-timeout "$tmo_arg" -wp-par 12 -wp-report-json goals.json -then -report -report-untried ;;
  # t07e method change (c1): print one goal class after Qed (no prover, nothing proven, never a verdict),
  # for the in-call show_goal tool. $4 = WP selection, e.g. "-wp-fct TDStep -wp-prop=@invariant".
  print|print-exact) rm -rf session && mkdir session
    if [ "$mode" = print-exact ]; then
      # METHOD23: compile the pinned read-only exporter in this fresh task scope.
      # No local ARM build artifact is transferred or reused by another host.
      cp "$script_dir/Probata_task_export.ml" ./Probata_task_export.ml || exit 2
      env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- \
        ocamlfind ocamlopt -package frama-c-wp.core,yojson -shared -o task-export.cmxs Probata_task_export.ml || exit 2
      set -- "$@" -load-module ./task-export.cmxs
    fi
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp $cache_arg -wp-cache none -wp-session session -wp-prover none -wp-print ;;
  # Method24 (2026-10-16 ET): search rounds use a timeout ladder (the driver passes 3 s, then 10 s for
  # goals still open) and -wp-split-conj (sound: every conjunct is its own goal, so feedback names the
  # failing part). Never a verdict. The verdict is final24: the frozen full replay (all functions, 30 s,
  # -wp-cache none, fresh session, smoke tests) plus the same -wp-split-conj the rounds used.
  round24) [ -n "$cache_arg" ] || { echo "round24 needs <cache_dir>"; exit 2; }; rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-fct TDStep -wp-split-conj -wp-cache update -wp-cache-dir "$cache_arg" -wp-session session \
      -wp-prover alt-ergo,z3,cvc5 -wp-timeout "$tmo_arg" -wp-par 12 -wp-report-json goals.json \
      -then -wp-fct= -wp-prop=@lemma -wp-report-json lemmas.json -then -report -report-untried ;;
  # Method25 (2026-10-16 ET): round24 split into three concurrent WP processes over an exact partition of
  # TDStep's goals (104 + 209 + 304 = 617 on run 27's best set, checked), each -wp-par 4, inside ONE
  # verifier job (one slot, one RSS watchdog over the whole tree). WP's goal generation and Qed run
  # sequentially per process, so the partition shortens the wall time (run 27 best set: 360 s -> 219 s;
  # a 4-way split gave 215 s, CPU-bound). Never a verdict.
  round24p) [ -n "$cache_arg" ] || { echo "round24p needs <cache_dir>"; exit 2; }
    # Selector 2 excludes @invariant so a check-kind invariant cannot land in two parts (review 2026-10-16).
    k=0
    for sel in "@invariant" "@requires,@check,@terminates,-@invariant" "-@invariant,-@requires,-@check,-@terminates"; do
      k=$((k+1)); rm -rf "part$k" && mkdir -p "part$k/session" "$cache_arg/part$k" && cp ./*.c ./*.h "part$k/" || exit 2
    done
    pids=""; k=0
    for sel in "@invariant" "@requires,@check,@terminates,-@invariant" "-@invariant,-@requires,-@check,-@terminates"; do
      k=$((k+1)); sub="part$k"
      lem=""; [ $k -eq 3 ] && lem="-then -wp-fct= -wp-prop=@lemma -wp-report-json lemmas.json"
      ( cd "$sub" && exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
        -wp -wp-fct TDStep -wp-prop="$sel" -wp-split-conj -wp-cache update -wp-cache-dir "$cache_arg/part$k" -wp-session session \
        -wp-prover alt-ergo,z3,cvc5 -wp-timeout "$tmo_arg" -wp-par 4 -wp-report-json goals.json $lem > wp.log 2>&1 ) &
      pids="$pids $!"
    done
    rc=0; for p in $pids; do wait "$p" || rc=1; done
    for k in 1 2 3; do cat "part$k/wp.log"; done
    python3 -I -c 'import json,sys
g=[]
for k in (1,2,3):
    g+=json.load(open(f"part{k}/goals.json"))
names=[x["goal"] for x in g]
assert len(names)==len(set(names)), "goal in two parts"
json.dump(g,open("goals.json","w"))' || rc=1
    [ -f part3/lemmas.json ] && cp part3/lemmas.json lemmas.json
    exit $rc ;;
  final24) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-split-conj -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 -wp-timeout 30 -wp-par 12 \
      -wp-smoke-tests -wp-report-json goals.json -then -report -report-untried ;;
  # Negative control (covering wait removed): all of TDStep's goals with the same flags as final24, so the
  # hazard check's consolidated status accounts for the hints it depends on (review S2, 2026-10-16 ET).
  negctl24) rm -rf session && mkdir session
    exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
      -wp -wp-fct TDStep -wp-split-conj -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 \
      -wp-timeout 30 -wp-par 12 -wp-report-json goals.json -then -report -report-untried ;;
  wp) smoke="" ;;
  wp-smoke) smoke="-wp-smoke-tests" ;;
  wp-rte) smoke="-wp-rte" ;;
  *) echo "usage: $0 parse|wp|wp-smoke|wp-rte <run_dir> <file.c>"; exit 2 ;;
esac
rm -rf session && mkdir session
exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
  -wp -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 -wp-timeout 30 -wp-par 12 \
  $smoke -wp-report-json goals.json -then -report -report-untried
