# T17 diagnostic build a2 (2026-09-27 ET): one public dx100-compile of the retained
# instruction candidate with diagnostic_regions:true; no provider, repair or guest run.
CODE=$1 DISPATCH=$2 RAW=$3
source "$(dirname "$0")/lib.sh"
REQ=.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/t17-acceptance/diagnostic-request-prospective.json
NODE=$(lane) || exit 64
swdb pre-candidate 30 get bfs-campaign-preparation-20260925-a1.dx100-instructions.candidate-1 --format json || exit 1
swdb pre-primary 30 get bfs-t17-build-only-20260926-a1 --format json || exit 1
swdb compile 270 dx100-compile "$REQ" --runs-dir "$RAW" --lane "$NODE" --format json
rc=$?
swdb post-chain 60 get bfs-t17-diagnostic-build-only-20260927-a2 --chain --format json
exit $rc
