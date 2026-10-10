# T20 candidate builds (2026-09-27 ET): primary then diagnostic public dx100-compile of the
# context5 candidate, accelerated, complete-call ROI. Only valid after a candidate exists.
# A failed primary stops the job (the diagnostic ID stays unused); no retry or repair here.
CODE=$1 DISPATCH=$2 RAW=$3
source "$(dirname "$0")/lib.sh"
R=.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927/requests
NODE=$(lane) || exit 64
swdb pre-candidate 30 get bfs-campaign-preparation-20260925-a1.upstream-annotated-context5.candidate-1 --chain --format json || exit 1
swdb primary 270 dx100-compile "$R/t20-context5-primary-build.json" --runs-dir "$RAW" --lane "$NODE" --format json
rc=$?
swdb post-primary 60 get bfs-t20-context5-primary-build-20260927-c2 --chain --format json
[[ $rc -eq 0 ]] || exit $rc
swdb diagnostic 270 dx100-compile "$R/t20-context5-diagnostic-build.json" --runs-dir "$RAW" --lane "$NODE" --format json
rc=$?
swdb post-diagnostic 60 get bfs-t20-context5-diagnostic-build-20260927-c2 --chain --format json
exit $rc
