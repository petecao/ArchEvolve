#!/usr/bin/env bash
# Spike (d), Probata PoC ticket 08: sums over reals with Frama-C/WP 33.0 (opam switch framac-33).
#
# Usage: [T08_PROVERS=z3] [T08_TIMEOUT=10] ./run.sh <stage> [out-root]
#   gen     tip run: the \wp::strategy hints generate Wp.induction scripts; copies them to scripts/
#   lemmas  fresh run (-wp-cache none, new session holding only a copy of scripts/): replay
#   false-lemma, false-fn
#           \false check: WP must NOT prove \false from the definitions and lemmas alone
#   unit    the CSR pull-sum fixture's unit, with smoke tests, fresh run
#   bug     negative control: the fixture with -DSEEDED_BUG (one edge range off by one)
# Output: <out-root>/<stage>/ (default out-root /tmp/claude/probata-runs/t08): frama-c.log
#   (with the per-property report), wp_report.json (per goal), report.csv, verdicts.txt
#   (check_verdicts.py). The WP session folder is verifier scratch and is removed.
#
# Run every stage through /tmp/claude/probata-tools/verifier_run.py (one verifier job at a time,
# 8 GB RSS watchdog) and OUTSIDE the agent sandbox: Alt-Ergo runs through a Why3 server Unix
# socket that the sandbox blocks (WP then reports [Failure]).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE=${1:?stage}
ROOT=${2:-/tmp/claude/probata-runs/t08}
OUT="$ROOT/$STAGE"
eval "$(opam env --switch=framac-33 --set-switch)"
rm -rf "$OUT"; mkdir -p "$OUT"
cd "$HERE"

# Frozen flags: real model, no cache, x86_64 machdep, warning levels at default.
COMMON=(-machdep x86_64 -wp -wp-model +real -wp-cache none -wp-timeout ${T08_TIMEOUT:-30} -wp-par 4
        -wp-report-json "$OUT/wp_report.json")
PROVERS=${T08_PROVERS:-alt-ergo,z3,cvc5}   # override for one-prover runs
REPORT=(-then -report -report-csv "$OUT/report.csv")
RC=0
fc() { frama-c "$@" 2>&1 | tee "$OUT/frama-c.log"; RC=${PIPESTATUS[0]}; }
fresh_session() { mkdir -p "$OUT/session/script"; cp scripts/*.json "$OUT/session/script/"; }

case "$STAGE" in
  gen)
    fc lemmas.c "${COMMON[@]}" -wp-prover tip -wp-session "$OUT/session" "${REPORT[@]}"
    rm -rf scripts; mkdir -p scripts
    cp "$OUT"/session/script/*.json scripts/
    ;;
  lemmas)
    fresh_session
    fc lemmas.c "${COMMON[@]}" -wp-prover script,$PROVERS -wp-session "$OUT/session" \
      "${REPORT[@]}"
    ;;
  false-lemma|false-fn)
    # One prover at a time: with -wp-par 4 a solver passed the 8 GB watchdog in 29 s
    # (2026-10-14 02:15 ET). The two goals run apart (see false_check.c).
    DEF=(); [ "$STAGE" = false-lemma ] && DEF=(-cpp-extra-args=-DFALSE_LEMMA)
    PROP=FALSE_FROM_CONTEXT; [ "$STAGE" = false-lemma ] && PROP=FALSE_FROM_LEMMAS
    fc false_check.c ${DEF[@]+"${DEF[@]}"} "${COMMON[@]}" -wp-par 1 -wp-prop "$PROP" \
      -wp-prover $PROVERS -wp-session "$OUT/session" -wp-msg-key print-generated "${REPORT[@]}"
    ;;
  unit|bug)
    fresh_session
    DEF=(); [ "$STAGE" = bug ] && DEF=(-cpp-extra-args=-DSEEDED_BUG)
    fc csr_pull_sum.c ${DEF[@]+"${DEF[@]}"} "${COMMON[@]}" -wp-rte -wp-smoke-tests \
      -wp-prover script,$PROVERS -wp-session "$OUT/session" "${REPORT[@]}"
    ;;
  *) echo "unknown stage $STAGE" >&2; exit 2 ;;
esac
echo "frama-c exit=$RC"
rm -rf "$OUT/session"
[ "$STAGE" = gen ] && exit "$RC"
python3 "$HERE/check_verdicts.py" "$STAGE" "$OUT" "$HERE/sum_logic.h" > "$OUT/verdicts.txt"
CHECK=$?
cat "$OUT/verdicts.txt"
exit $(( RC != 0 ? RC : CHECK ))
