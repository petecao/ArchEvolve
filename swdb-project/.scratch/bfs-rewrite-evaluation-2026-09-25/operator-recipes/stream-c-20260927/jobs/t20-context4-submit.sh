# T20 R8 focused-context submission (2026-09-27 ET): exactly one public submit with the
# Claude Code provider (900 s per call, USD 10 per call, 1,800 s pool, <=2 later repairs).
# No build or measurement runs here; no retry. Outcome (candidate, unresolved or failed) is retained.
CODE=$1 DISPATCH=$2 RAW=$3
source "$(dirname "$0")/lib.sh"
P=.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927/prepared
ID=bfs-campaign-preparation-20260925-a1.upstream-annotated-context4
sha256sum "$P/context4.proposal.json" "$P/context4.provider.json" > "$DISPATCH/inputs.sha256"
/data1/yanruj/.npm-global/bin/claude --version > "$DISPATCH/provider.version" 2>&1
swdb pre-predecessor 30 get bfs-campaign-preparation-20260925-a1.upstream-annotated-context3 --format json || exit 1
swdb submit 960 submit "$P/context4.proposal.json" --runs-dir "$RAW" --provider-config "$P/context4.provider.json" --format json
rc=$?
swdb post-proposal 60 get "$ID" --chain --format json
exit $rc
