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
  wp) smoke="" ;;
  wp-smoke) smoke="-wp-smoke-tests" ;;
  wp-rte) smoke="-wp-rte" ;;
  *) echo "usage: $0 parse|wp|wp-smoke|wp-rte <run_dir> <file.c>"; exit 2 ;;
esac
rm -rf session && mkdir session
exec env -i HOME="$HOME" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" SWDB_VERIFIER_RUN_TOKEN="${SWDB_VERIFIER_RUN_TOKEN-}" opam exec --switch=framac-33 -- frama-c "$@" \
  -wp -wp-cache none -wp-session session -wp-prover alt-ergo,z3,cvc5 -wp-timeout 30 -wp-par 12 \
  $smoke -wp-report-json goals.json -then -report -report-untried
