#!/usr/bin/env bash
# Q5: can a JSON script, a strategy or the WP cache close a false goal without proof?
# Called by run.sh (q5). Works in q5_work/ and removes it at the end.
set -u
cd "$(dirname "$0")"
eval "$(opam env --switch=framac-33 --set-switch)"
W=q5_work; rm -rf "$W"; mkdir -p "$W" logs
FC() { gtimeout 120 frama-c "$@"; }
run() { local name=$1; shift; echo "== $name: frama-c $*" >"logs/$name.log"; FC "$@" >>"logs/$name.log" 2>&1; echo "exit=$?" >>"logs/$name.log"; }
AE="-wp-timeout 3"

# 1. Strategy-driven induction under the tip prover: how a scripted goal is reported.
run q5_1_tip q5_script.c -wp -wp-cache none $AE -wp-prover tip -wp-session $W/tip \
    -wp-report-json logs/q5_1_tip.json -then -report
cp $W/tip/script/lemma_SUM_NONNEG.json logs/q5_1_saved_script.json

# 2. Planted script with a fake "valid" prover verdict for the false goal BAD.
#    2b replays it with script,alt-ergo (the manual's "consolidating" mode).
mkdir -p $W/fake/script
echo '[ { "prover": "Alt-Ergo:2.6.4", "verdict": "valid", "time": 0.01 } ]' \
  > $W/fake/script/bad_ensures_BAD.json
run q5_2_fake_verdict q5_script.c -wp -wp-fct bad -wp-cache none $AE \
    -wp-prover script -wp-session $W/fake -then -report

run q5_2b_fake_verdict_ae q5_script.c -wp -wp-fct bad -wp-cache none $AE \
    -wp-prover script,alt-ergo -wp-session $W/fake -then -report

# 3. Planted script that applies an unregistered tactic "Wp.admit".
mkdir -p $W/fake3/script
echo '[ { "tactic": "Wp.admit", "header": "Admit", "select": null, "children": {} } ]' \
  > $W/fake3/script/bad_ensures_BAD.json
run q5_3_fake_tactic q5_script.c -wp -wp-fct bad -wp-cache none $AE \
    -wp-prover script -wp-session $W/fake3 -then -report

# 4. Planted script: a real tactic (Wp.absurd on the goal) with no children scripts.
mkdir -p $W/fake4/script
echo '[ { "tactic": "Wp.absurd", "header": "Absurd", "select": { "select": "clause-goal", "target": "false", "pattern": "F" }, "children": {} } ]' \
  > $W/fake4/script/bad_ensures_BAD.json
run q5_4_tactic_nochildren q5_script.c -wp -wp-fct bad -wp-cache none $AE \
    -wp-prover script -wp-session $W/fake4 -then -report

# 5. Tampered cache: record BAD's timeout, flip the stored verdict to "valid", replay offline.
run q5_5a_cache_fill q5_script.c -wp -wp-fct bad -wp-cache update -wp-cache-dir $W/cache $AE -wp-prover alt-ergo
for f in $W/cache/*.json; do sed -i '' 's/"timeout"/"valid"/' "$f"; echo "edited: $(cat "$f")" >> logs/q5_5a_cache_fill.log; done
run q5_5b_cache_offline q5_script.c -wp -wp-fct bad -wp-cache offline -wp-cache-dir $W/cache $AE -wp-prover alt-ergo -then -report
run q5_5d_cache_update q5_script.c -wp -wp-fct bad -wp-cache update -wp-cache-dir $W/cache $AE -wp-prover alt-ergo -then -report
run q5_5c_cache_none q5_script.c -wp -wp-fct bad -wp-cache none $AE -wp-prover alt-ergo -then -report

# 6. -wp-prover none: no prover runs at all.
run q5_6_prover_none q5_script.c -wp -wp-cache none -wp-prover none -then -report

rm -rf "$W"
