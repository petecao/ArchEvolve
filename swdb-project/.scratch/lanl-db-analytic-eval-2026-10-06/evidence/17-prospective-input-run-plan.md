# Prospective ticket 17 inputs and runs

Updated: 2026-10-06 20:37 ET. Preparation only: no ticket claim, graph generation, remote dispatch,
report or statistical/population freeze. Parent and the ticket 17 implementer freeze the
actual population before any timed pair. No historical application timings or paper
speedups are inputs to this plan.

Eight proposed graph cases use scale 18, source 0 and fixed seed 27491095:

| Family | Edge factors | Generator flags |
|---|---|---|
| Kronecker | 14, 15, 17, 18 | `-g 18 -k FACTOR` |
| Uniform random | 14, 15, 17, 18 | `-u 18 -k FACTOR` |

These are prospective input choices. They do not themselves satisfy D30's minimum pair
population. Repetitions, SG32/SG64 copies and correctness companions are not new independent
pairs. Different configurations remain labeled configuration changes, not fresh graphs.

1. Check the source and future lane.

Use a clean Git-synced SWDB checkout in a parent-verified owned mbit10 socket lane. Parent
checks both socket/legacy leases, storage and other users before preparation. Preserve the
pinned DX revision `e4fc4afdf894f295442cef3604667a469fab8e62` and
[the generator/source hashes](17-prospective-input-plan-pins.json). The converter's
`CLBase` enables symmetrization for both synthetic families without an explicit `-s`.
The seed comes from `util.h`; block reseeding and vertex permutation remain unchanged.
Do not use the existing `bfs_generate_workload.py` CLI for this matrix: it hardcodes
edge factor 16. Its public `widen_sg` function is reusable and preserves the neighbors.

The following shell recipe is unexecuted preparation. Run it from `swdb-project/` only
when parent schedules the lane. Use fresh external directories; all generated data stays
on mbit10. The limiter caps each child at 48 GiB and kills its process group on timeout or catchable interruption. Parent still checks for
remaining descendants after an outer forced kill; SIGKILL cannot run cleanup handlers.
Stage caps total 3510 s per case, with a separate 180 s compile; parent also applies a 3600 s
outer case budget and cleanup reserve. Construction-time stdout stays raw on the host;
compact metadata exports only source, arguments, hashes and graph structure.

```sh
set -euo pipefail
export LANL_SWDB="$(pwd -P)"
export LANL_RAW=/data/yanruj/EvolveSWDB_runs/lanl17-prospective-inputs-20261006-a1
export LANL_BUILD=/data1/yanruj/EvolveSWDB_builds/lanl17-prospective-inputs-20261006-a1
export LANL_RECORDS="$LANL_RAW/records"
test ! -e "$LANL_RAW"
test ! -e "$LANL_BUILD"
mkdir -p "$LANL_RAW" "$LANL_BUILD"
cp -a records "$LANL_RECORDS"
(cd apps/dx100 && sha256sum -c SHA256SUMS > "$LANL_RAW/source-manifest-check.log")
python3 - <<'SOURCE'
from pathlib import Path
from swdb import artifacts
assert artifacts.identify(Path('apps/dx100/benchmarks/gapbs/src'))['sha256'] == (
    '9b15a2ad58d672d534a14c808320a5d666af62cbe017f14703d955bea2279cc1')
SOURCE
lanl_bound() {
  python3 - "$@" <<'LIMIT'
import os,resource,signal,subprocess,sys
seconds=int(sys.argv[1])
def memory_limit():
    amount=48*1024**3
    resource.setrlimit(resource.RLIMIT_AS,(amount,amount))
def interrupted(signum, frame):
    raise InterruptedError(f"stage interrupted by {signal.Signals(signum).name}")
for sig in (signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, interrupted)
child=None
try:
    child=subprocess.Popen(sys.argv[2:],start_new_session=True,preexec_fn=memory_limit)
    result=child.wait(timeout=seconds)
except BaseException:
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, signal.SIG_IGN)
    if child is not None:
        try:os.killpg(child.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait(timeout=5)
    raise
sys.exit(result)
LIMIT
}
lanl_bound 180 /usr/bin/g++-13 -std=c++11 -O3 -fopenmp \
  apps/dx100/benchmarks/gapbs/src/converter.cc -o "$LANL_BUILD/converter" \
  > "$LANL_RAW/converter-build.stdout" 2> "$LANL_RAW/converter-build.stderr"
/usr/bin/g++-13 --version > "$LANL_RAW/converter-compiler-version.txt"
command -v c++ > "$LANL_RAW/parser-compiler-path.txt"
c++ --version > "$LANL_RAW/parser-compiler-version.txt"
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE
for LANL_FAMILY in kronecker uniform_random; do
  export LANL_FAMILY
  case "$LANL_FAMILY" in kronecker) LANL_GEN_FLAG=-g;; uniform_random) LANL_GEN_FLAG=-u;; esac
  export LANL_GEN_FLAG
  for LANL_FACTOR in 14 15 17 18; do
    export LANL_FACTOR
    export LANL_CASE_ID="lanl17-prospective-20261006-${LANL_FAMILY}.g18.k${LANL_FACTOR}"
    export LANL_CASE="$LANL_RAW/$LANL_CASE_ID"
    export LANL_CASE_BUILD="$LANL_BUILD/$LANL_CASE_ID"
    test ! -e "$LANL_CASE"
    mkdir "$LANL_CASE" "$LANL_CASE_BUILD"
    lanl_bound 900 "$LANL_BUILD/converter" "$LANL_GEN_FLAG" 18 -k "$LANL_FACTOR" \
      -b "$LANL_CASE/graph-dx100.sg" \
      > "$LANL_CASE/generation.stdout" 2> "$LANL_CASE/generation.stderr"
    lanl_bound 180 python3 -c \
      'import sys;sys.path.insert(0,"scripts");from bfs_generate_workload import widen_sg;widen_sg(sys.argv[1],sys.argv[2])' \
      "$LANL_CASE/graph-dx100.sg" "$LANL_CASE/graph-upstream.sg"
    cat > "$LANL_CASE/prepare-request.py" <<'REQUEST'
from pathlib import Path
import json,os
from swdb import artifacts,bfs_protocol
case=Path(os.environ['LANL_CASE'])
representations=[{'id':os.environ['LANL_CASE_ID']+'.'+name,'application':app,
    'path':str(case/file),'format':fmt,'sha256':artifacts.file_hash(case/file)}
    for name,app,file,fmt in [('dx100','dx100-gapbs','graph-dx100.sg','gapbs_sg32le'),
                             ('upstream','gapbs','graph-upstream.sg','gapbs_sg64le')]]
command=[str(Path(os.environ['LANL_BUILD'])/'converter'),os.environ['LANL_GEN_FLAG'],
    '18','-k',os.environ['LANL_FACTOR'],'-b',str(case/'graph-dx100.sg')]
request={'message_version':'1.0','id':os.environ['LANL_CASE_ID'],'version':1,
    'kernel':'gapbs-bfs','family':os.environ['LANL_FAMILY'],
    'generator':{'name':'DX100 GAPBS converter',
        'revision':'e4fc4afdf894f295442cef3604667a469fab8e62','command':command,
        'parameters':{'scale':18,'edge_factor':int(os.environ['LANL_FACTOR']),
            'seed':27491095,'symmetrize':True,'explicit_symmetrize_flag':False,
            'compiler':'/usr/bin/g++-13','compile_flags':['-std=c++11','-O3','-fopenmp'],
            'compiler_version_sha256':artifacts.file_hash(Path(os.environ['LANL_RAW'])/'converter-compiler-version.txt'),
            'environment':{'OMP_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'},
            'binary_sha256':artifacts.file_hash(Path(os.environ['LANL_BUILD'])/'converter'),
            'source_sha256':artifacts.identify(Path('apps/dx100/benchmarks/gapbs/src'))['sha256']}},
    'sources':[0],'normalization':bfs_protocol.NORMALIZATION,'representations':representations,
    'parser':{'work_dir':os.environ['LANL_CASE_BUILD'],'compile_timeout_s':60,'timeout_s':900}}
(case/'register.json').write_text(json.dumps(request,indent=2)+'\n')
REQUEST
    lanl_bound 30 python3 "$LANL_CASE/prepare-request.py"
    lanl_bound 2400 python3 -m swdb register-workload "$LANL_CASE/register.json" \
      --records "$LANL_RECORDS" --format json \
      > "$LANL_CASE/registration.json" 2> "$LANL_CASE/registration.stderr"
  done
done
```

Source 0 stays exactly 0: do not request `source_policy` or `--artifact-default-source`.
Public registration checks bounds; before admission also require positive source 0
out-degree and `definition.sources == [0]`. If it fails, retain the failed case and
exclude it prospectively; do not silently replace the source. Both `.sg` suffixes are
required by the pinned loaders. Always request streaming registration: it verifies
normalized outgoing/inverse adjacency and equal canonical identity across both widths.
Do not declare realized vertices/arcs from scale × degree; the public parser supplies them.

2. Check genuine freshness before population freeze.

Project only identity metadata from prior workloads, candidates, protocols and
characterizations; do not expose metrics, durations, comparison ratios or summaries.
A new filename, requested record ID or later timestamp does not establish freshness.

| Identity | Required check |
|---|---|
| Graph | New canonical `swdb.bfs.adjacency.v1` SHA256 compared against every prior registered graph; both representation hashes reverified. Reject a repeated canonical graph from the fresh-input pool. |
| Input | Immutable workload fingerprint, generator/source/binary hash, scale/factor/seed, normalized adjacency, ordered `[0]` and representation mapping. Any typed input registration must be bound to this exact canonical graph. |
| Artifact | Baseline and candidate immutable tree/diff/source pins and exact built-binary identities; relabeling an old tree is not a new artifact. |
| Configuration | Full target/CPU/cache/memory/tile/thread/clock/model/runtime/compiler/instrumentation identity; freeze per role and retain disclosed differences. |
| ROI | Whole-call semantic ROI, accelerator setup, ordered run arguments and trial/source identity. `gapbs.trial_lambda.v1` is not automatically interchangeable with `bfs.complete_call.v1`. |
| Pair | De-duplicate the tuple of canonical input + baseline/candidate artifact + full configuration + ROI/protocol. Repetitions and file-width aliases stay within that pair. |
| Estimate | Frozen target, estimator/code bundle, exact characterization hash and outcome-free input projection, created before the corresponding timing exists. |

Registered representation identity must also cover the counted input. Count the verified
representation, or establish deterministic regenerated-adjacency equivalence under the
pinned generator/toolchain; equal realized node/edge counts alone are insufficient.
Do not treat the current built-in-generator adapter as proof that an arbitrary SG file
was counted. This is an admission dependency for the later implementer, not new runtime
work in this preparation. Existing canonical aliases may remain historical records, but
cannot become newly accepted fresh cases. If registration discovers a collision, retain
its audit and mark the proposed case excluded before any performance selection.

3. Keep companions and selection honest.

For BFS read-offload, freeze `correctness.companion_cases.parent_gather_race` with its
actual registered workload and source. Comparisons require explicit `companion_evaluations`
keys `timed` and `diagnostic`, exact candidate tree, verifier, protocol hash, target and
configuration; both executions follow the freeze. Diagnostic and timed companion binaries
remain distinct. Reusing a known correctness control is disclosed; it is not a fresh-input
pair. Full/tail/read-only/competing-update coverage requires actual typed observations,
not a guess from scale/factor. For BC, register the same two representations separately
with `kernel: gapbs-bc` and a distinct workload ID, preserving `[0]` and canonical identity;
this creates no additional fresh graph. BC has no parent-gather race companion. Separate SG-width
representations and kernel registrations share one graph and cannot inflate the population.

Preserve flow-A selection: certified artifacts precede uncertified ones, only evaluator
`gain` artifacts compete, and the existing selection baseline/lower-bound order remains
unchanged. Estimates never select candidates or change stop behavior. A completed
non-improving iteration advances plateau once, improvement resets it, and infrastructure
stops/pauses follow the existing ledger without an invented non-improvement. Preserve the
frozen campaign budgets and provider-call accounting. Graph generation/registration is
setup work, not a completed candidate-search iteration.

Parent and ticket 17 must choose/freeze eligible artifacts, configurations, campaigns,
pair unit, missing-case rules and uncertainty procedure before any timed pair. D30 stays
unchanged: at least 20 DX100 pairs, Kendall tau ≥ 0.6 with its 95% interval lower bound ≥ 0.3,
and gem5's best inside estimate top 3 in every campaign. This preparation chooses none of
those statistical-policy details and reports no agreement or speedup.

Source pointers: `scripts/bfs_generate_workload.py` (converter and widening),
`swdb/bfs_protocol.py::register_workload`, `swdb/sg_stream.py`,
`swdb/read_only_checks.py::companion_acceptance`, `swdb/campaign.py::select`,
`swdb/extensa/search.py::record_iteration`, and spec D16/D26/D30. The public CLI syntax
passed help-only checking. `bash -n` and all three embedded Python blocks passed
syntax checks without execution; actual graph/parser/freshness acceptance remains pending.
