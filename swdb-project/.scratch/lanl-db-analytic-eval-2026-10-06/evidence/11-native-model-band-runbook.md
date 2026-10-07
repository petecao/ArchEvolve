# Frozen native T1 model and prospective band sequence

Created: 2026-10-06 ET. Parent owns mbit10 preflight, source deployment, named leases and all dispatch. This runbook is preparation, not evidence of successful application timing. Use the final clean combined source after every service receipt is admitted; the independent collector source `1703c987` remains immutable during its own calibration runs. Keep node1 idle during native application timing.

The scope is the original registered LLVM22/libomp BFS and BC baseline driver, serial T1, five advancing deterministic SourcePicker calls in one process. Exact source/runtime/control identity, graph-generation contract, observed graph metadata, all five printed times and separate verifier output are retained. This scope is separate from protected `evaluate`/`evaluate-pair`; historical GCC/libgomp/candidate records retain their explicit exclusions in `11-historical-native-scope-audit.json`.

## 1. Bind outcome-free counts and admitted services

Copy canonical records into a new external raw store. Set `LANL_CPU_STORE` to its `records/` directory. All service IDs below are required expected output IDs, not evidence that the pending services succeeded. Failed or missing receipts keep their parameters unknown. Use the final immutable source checkout's `swdb-project/` working directory.

```sh
python3 -m swdb.cpu_service_binding --records "$LANL_CPU_STORE" \
  --target-description mbit10.cpu.lanl20261006a2.v2.t1 \
  --characterization bfs.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g16.t1.characterization.objects.a1 \
  --scope-characterization bfs.kron-g17.t1.characterization.objects.a1 \
  --scope-characterization bc.kron-g17.t1.characterization.objects.a1 \
  --calibration mbit10.cpu.lanl20261006.service.clock.a2 \
  --calibration mbit10.cpu.lanl20261006.service.allocator.a1 \
  --calibration mbit10.cpu.lanl20261006.service.allocator-extra.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.memory.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.float-memory.a1 \
  --calibration mbit10.cpu.lanl20261006.service.byte-read.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --calibration mbit10.cpu.lanl20261006.resource.bulk-total.a2 \
  --calibration mbit10.cpu.lanl20261006.service.openmp.a1 \
  --memory-footprint-bytes 8388608 \
  --memory-cas-policy max_constructed_success_failure_median \
  --bulk-profile-policy max_constructed_profiles_median \
  --bulk-copy-calibration mbit10.cpu.lanl20261006.resource.bulk-total.a1 \
  --openmp-next-policy max_constructed_success_failure_median \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g16-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bfs.g17-projection-mbit10-20261006-a1.json \
  --openmp-projection .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-bc.g17-projection-mbit10-20261006-a1.json \
  --id mbit10.cpu.lanl20261006.t1.services.v1 --format json
```

The explicit 8MiB memory construction is a conditional inferred scenario. Logical bounded views establish neither full libomp allocation identity nor physical residency. Exact primitive/type/order guards remain active. BC floating64 monotonic fadd consumes its separate resource; integer seq_cst add and floating fadd in the same coarse bucket are partitioned by exact source sites before charging, with the sum cross-checked against the original observation. Original residual-null write8 records remain immutable; the separately typed gross resource includes retained loop work and composes with compute by maximum. Bulk profile maxima and legal warmed OpenMP state are inferred transfer, not physical latencies or proven application upper bounds. Duplicate copy measurements are selected explicitly, never pooled.

Freeze two per-kernel protocols against the same target, bundle, calibrations and four-characterization allowlist. BFS and BC have different original argv (BC has its `-i 1` argument), while `input_run_arguments` is keyed by input ID. One shared per-input argv map cannot represent both kernels. Set `LANL_CPU_PROTOCOL_DIR` to a new external raw subdirectory and generate each request directly from its immutable counted records:

```sh
python3 - <<'PY'
import json, os
from pathlib import Path
from swdb.store import Store
store = Store(Path(os.environ['LANL_CPU_STORE']))
folder = Path(os.environ['LANL_CPU_PROTOCOL_DIR'])
folder.mkdir(parents=True, exist_ok=False)
for kernel in ('bfs', 'bc'):
    observed = [store.get(kernel+'.kron-g'+str(g)+'.t1.characterization.objects.a1',
                          'workload_characterization') for g in (16, 17)]
    assert len({c['subject']['id'] for c in observed}) == 1
    arguments = {c['input']: c['source']['run_arguments'] for c in observed}
    request = {'message_version': '1.0',
        'id': 'lanl.cpu.'+kernel+'.t1.native-model.v1', 'version': 1,
        'settings': {'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1',
            'target_description': 'mbit10.cpu.lanl20261006.t1.services.v1',
            'inputs': list(arguments), 'input_run_arguments': arguments,
            'sources': [observed[0]['subject']['id']],
            'roi': 'gapbs.trial_lambda.v1', 'threads': 1}}
    (folder/(kernel+'.request.json')).write_text(json.dumps(request, indent=2)+'\n')
PY
for kernel in bfs bc; do
  python3 -m swdb freeze-protocol "$LANL_CPU_PROTOCOL_DIR/$kernel.request.json" \
    --records "$LANL_CPU_STORE" --format json > "$LANL_CPU_PROTOCOL_DIR/$kernel.frozen.json"
done
LANL_CPU_BFS_PROTOCOL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$LANL_CPU_PROTOCOL_DIR/bfs.frozen.json")"
LANL_CPU_BC_PROTOCOL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$LANL_CPU_PROTOCOL_DIR/bc.frozen.json")"
```

`freeze-protocol` returns a content-suffixed immutable ID. Use these returned IDs in all subsequent commands; the unsuffixed request IDs are not persisted protocol IDs. Estimate the two BFS characterizations with `--protocol "$LANL_CPU_BFS_PROTOCOL"`, and the two BC characterizations with `--protocol "$LANL_CPU_BC_PROTOCOL"`. Use fresh estimate IDs `lanl.cpu.{bfs,bc}.g{16,17}.t1.estimate.v1`. No application executes during estimation.

Both protocols pin the same final model and recursive typed closure. Persist both exact protocol IDs/hashes, all four estimate hashes and the exact per-input argv in the model acceptance receipt. Later development/holdout phases retrieve each kernel's protocol ID from its unchanged immutable estimate and verify it against the model receipt before any native command. The CPU band compares target/bundle/thread/target/evidence identities across pairs; distinct per-kernel protocols do not relax source/runtime scope or holdout chronology. No CPU error-band pin exists yet.

Before application timing, retain a sealed preregistration with source tip, Python bundle hash, target/protocol hashes, all four characterization hashes, all calibration hashes and explicit conditional recipes. Check every complete whole-call result is positive and every structural compatibility missing list is empty. Unknown per-region union/page/lifetime facts remain retained; they cannot be filled as physical facts. If a whole-call estimate is null, retain the exact failed completeness report and fix only defensible independent missing service prerequisites before a new prospective freeze. No application outcome may select or fit those costs.

## 2. Development timing after model freeze

Set `LANL_CPU_RAW` to a new external raw directory. Under the named node0 lease, for BFS then BC, run the matched collector with a separate new output directory and ID. It verifies source/runtime correspondence, executes a separate `-v` five-call correctness process, then the original no-v five-call timing process. Keep the same source/model and both frozen protocols unchanged through both collectors.

```sh
python3 -m swdb collect-cpu-native-validation --records "$LANL_CPU_STORE" \
  --characterization bfs.kron-g16.t1.characterization.objects.a1 \
  --estimate-protocol "$LANL_CPU_BFS_PROTOCOL" \
  --id lanl.cpu.bfs.g16.t1.validation.v1 --output "$LANL_CPU_RAW/bfs.g16" \
  --machine mbit10 --lane mbit10-evaluation-node0 \
  --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
  --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu \
  --max-wall-s 900 --format json
```

Repeat with BC's exact characterization, ID, output and `--estimate-protocol "$LANL_CPU_BC_PROTOCOL"`. The collector derives the compiler flags, runtime environment and run arguments from the counted binding; do not inject a different graph/source policy. It pins only the child binary to the first core, while the collector retains full socket lease affinity. Retain all five printed TrialTime values with 10us resolution and +/-5us intervals. Their median is one workload-pair observation; the five advancing/state-sharing trials are not five independent error samples.

Freeze the development width immediately after both matched validations:

```sh
python3 -m swdb freeze-cpu-error-band --records "$LANL_CPU_STORE" \
  --estimate lanl.cpu.bfs.g16.t1.estimate.v1 --validation lanl.cpu.bfs.g16.t1.validation.v1 \
  --estimate lanl.cpu.bc.g16.t1.estimate.v1 --validation lanl.cpu.bc.g16.t1.validation.v1 \
  --id lanl.cpu.t1.development-band.v1 --format json
```

The frozen width is the maximum rounding-aware absolute log error across the two independently scoped workload pairs. A failed or null width does not authorize holdout timing or an agreement/gain claim. Preserve any failure honestly. No rate, recipe, target or implementation adjustment may use these application outcomes.

## 3. Prospective holdout with the unchanged width

Only after a known native development band is frozen, run the same matched collector for both g17 characterizations, supplying `--development-band lanl.cpu.t1.development-band.v1` as well as that kernel's unchanged returned estimate protocol ID. Use fresh IDs `lanl.cpu.{bfs,bc}.g17.t1.validation.v1` and new raw directories. The collector refuses a previously used input, changed source/runtime/ROI scope, or timing before the frozen width. Never re-estimate width from g17.

```sh
python3 -m swdb validate-cpu-error-band --records "$LANL_CPU_STORE" \
  --development-band lanl.cpu.t1.development-band.v1 \
  --estimate lanl.cpu.bfs.g17.t1.estimate.v1 --validation lanl.cpu.bfs.g17.t1.validation.v1 \
  --estimate lanl.cpu.bc.g17.t1.estimate.v1 --validation lanl.cpu.bc.g17.t1.validation.v1 \
  --id lanl.cpu.t1.heldout-band.v1 --format json
```

A failed holdout remains failed with the original width. A validated record grants confidence only to the exact supported held-out characterizations and frozen T1 target/model/runtime. It supplies no unseen-candidate, kernel, thread or target generalization. Any final estimate protocol that uses `cpu_error_band: lanl.cpu.t1.heldout-band.v1` must be newly frozen without changing the target or implementation; the band pin is separate from target calibration closure.

### Public verdict-reader replay after the completed held-out phase

Use the same final source, target, estimates and completed held-out Store. This is a reporting replay of immutable counts, with no additional native timing. Preserve the pre-outcome protocol/estimate records. Freeze two new report protocols using the original raw per-kernel requests and the persisted band ID; capture their returned content-suffixed IDs again. If the held-out band failed, the replay must retain `validated: false`; it cannot claim confidence or change the width. If development failed and held-out timing was prohibited, use that persisted failed development band instead and label the missing held-out observation explicitly.

```bash
export LANL_CPU_MODEL_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a1
export LANL_CPU_REPORT_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a1
export LANL_CPU_BAND=lanl.cpu.t1.heldout-band.v1
mkdir "$LANL_CPU_REPORT_RAW"
python3 - <<'PY'
import json,os
from pathlib import Path
for kernel in ('bfs','bc'):
 request=json.loads((Path(os.environ['LANL_CPU_MODEL_RAW'])/(kernel+'-protocol-request.json')).read_text())
 request['id']='lanl.cpu.'+kernel+'.t1.report-model.v1'
 request['settings']['cpu_error_band']=os.environ['LANL_CPU_BAND']
 (Path(os.environ['LANL_CPU_REPORT_RAW'])/(kernel+'-request.json')).write_text(json.dumps(request,indent=2)+'\n')
PY
for lanl_kernel in bfs bc; do
  python3 -m swdb freeze-protocol "$LANL_CPU_REPORT_RAW/$lanl_kernel-request.json" \
    --records "$LANL_CPU_STORE" --format json > "$LANL_CPU_REPORT_RAW/$lanl_kernel-protocol.json"
  lanl_report_protocol=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["id"])' "$LANL_CPU_REPORT_RAW/$lanl_kernel-protocol.json")
  python3 -m swdb estimate --records "$LANL_CPU_STORE" \
    --characterization "$lanl_kernel.kron-g17.t1.characterization.objects.a1" \
    --target-description mbit10.cpu.lanl20261006.t1.services.v1 \
    --protocol "$lanl_report_protocol" --id "lanl.cpu.$lanl_kernel.g17.t1.report.v1" \
    --format json > "$LANL_CPU_REPORT_RAW/$lanl_kernel-estimate.json"
done
```

Check each report's exact characterization and target/bundle hashes against the pre-outcome estimate; seconds and per-region costs must be unchanged. The report's `error_band` must pin the actual persisted band digest, state and unchanged width. `validated` is true only for a validated native band and its exact held-out characterization; a failed/development/fixture band grants no confidence. Export the two new protocol and two estimate records with their compact reporting receipt through Git, preserving all prior bytes. There is no new application outcome or retuning in this step.

Export canonical validation/band/estimate/protocol records and compact preregistration/context/hash/trial summaries through Git. Raw binaries, logs and LLVM artifacts remain remote. Report whole-call errors and the predicted per-region contributions/assumptions. There are no measured region timing/error claims. Existing CPU native timing selection is unchanged; historical unsupported comparisons retain their explicit null/exclusion reports. Until a validated band exists, D25's `within_error` token with null error_band/seconds is not evidence of agreement.

### Prepared bounded reporting automation

The separate parent-owned helpers are prepared at `/private/tmp/lanl-dispatch-cpu-band-report-a1.py` (SHA256 `302f45f765db493d23858174601c551d6bc38f45cb03cd814cfcb0ec31224f6a`) and `/private/tmp/lanl-export-cpu-band-report-a1.py` (SHA256 `9a67e381ee1997adff1ce53630238c365e182df5f3ff609c631b1bcfe005820f`). Each takes the same final immutable source SHA used by the model/development/held-out phases. Parent stages these exact helper bytes on mbit10; neither has been dispatched.

The dispatcher requires mbit10, the unchanged clean model checkout, successful model/held-out exits, the current verified socket wrapper, all released owned leases, the other owned lane idle, load <=32 and free space >=21GiB on `/data1` and >=10GiB on `/data`. Its fresh raw folder is `/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a1`. It verifies sealed model/held-out receipts, exact target/calibration/four-characterization/four-estimate/two-kernel protocol pins and the unchanged development width before any public command. Limits are 3300s runner, 3400s outer, 600s per public stage and 700s validation, with active child-group cleanup on interruption.

The exporter waits for release and exit0, independently rechecks all four new records and every retained held-out YAML byte, then exports exactly two new protocols and two estimates plus one compact receipt and prior additive typed closure from the same source. Raw logs/builds/LLVM remain remote. Branch `codex/lanl-cpu-band-report-evidence-a1` contains the compact receipt `11-cpu-band-report-mbit10-20261006-a1.json`.

[Mocked preparation proof](11-band-report-dispatch-mocked-proof-20261006.json) covers both validated and failed bands, exact argv/IDs/cost preservation, changed source/calibration/count/protocol/width refusals, extra export and protected-byte refusals, ten mocked preflight cases, and a bounded Python child-process SIGTERM cleanup regression. It is preparation evidence only; no live remote state, native application execution or agreement has been measured by these tests.

### Actual OpenMP prerequisite admission (2026-10-06 ET)

The immutable `mbit10.cpu.lanl20261006.service.openmp.a1` record passed local replay of the full native ABI/count/probe/runtime admission. All 22 parameters retain seven positive paired residuals; minimum gross and driver windows are 0.078387 s and 0.072232 s. All four exact characterization hashes pass service compatibility. The read-only binder replay also admits all 106 executed static OpenMP sites from the four sealed projections, with 22 raw and 6 derived success/terminal envelope parameters; none is unknown. The largest retained relative range is 0.562 (`openmp.14`, `__kmpc_end_single`); no spread or trial is dropped. This is a legal selected-event construction with inferred warmed serial T1 transfer, not a physical latency or application accuracy claim.

[The compact admission review](11-openmp-elapsed-admission-review-20261006.json) pins the typed record, original receipt and full characterization digests separately from the counted-payload identities. It also verifies that each kernel's g16/g17 normalized source/runtime band scope matches. Extra allocator and floating atomic admission still gate the final model; no application timing has started.
