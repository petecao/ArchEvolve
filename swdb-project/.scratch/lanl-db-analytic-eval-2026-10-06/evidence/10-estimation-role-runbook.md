# Frozen parameter-fill execution

Updated: 2026-10-06 ET. Actual a2 fill and postfill acceptance are recorded below.

`fill-target-parameters` reads registered characterization facts, a matching profile, and a
base target description. It writes a new target version after strict output, guard/audit and
immutable-input checks. The original records stay unchanged. One successful output, including
an all-null output, freezes the base target ID/version; a changed note cannot reopen it.

The three provider files contain typed native counts, grouped widths/shapes, logical request
counts, hashed profile region structure and recognized mechanism parameters. Profile numeric
metrics, timings, PMU values/ratios, source text, evaluator material, paths, other candidates and
free-form annotations are omitted. Full-record identities, compact snapshots and omission hashes
stay in the sealed target receipt. The existing functional profile is source-structure context
for the same registered snapshot/base implementation, not a candidate measurement.

A CPU service binding with a failed aggregate or per-characterization compatibility premise
is refused before workspace creation or provider launch. A withheld transfer rate is a structural
gap; it cannot become an estimated value. Valid binding premises and numerical residual unknowns
remain distinct. The prepared DX target has no CPU service binding.

Unknown capacity/layout/window/admission facts that change observation policy cannot be filled
by this role. Unsupported parameter contracts are refused. Unresolved answers must explicitly
use null, basis unknown and a reason. Non-null values use basis estimated and a reason; their
fact source cites the immutable output hash. Structural missing costs, residency, worker-rate
transfer and overlap remain unknown. Estimates list filled facts and recompose halve/double
scenarios per complete trial before the median. Unknown totals have no numeric impact rank.

## Parent-owned mbit10 execution

Use a clean Git checkout at the handed-off source tip. The parent selects the free lane, verifies
leases/host capacity and runs this source-only provider job under the established lane wrapper.
Do not start native counting, collectors or timing. This runbook is lane-neutral. Use a fresh
provider process; never append this conversation, prior provider outputs, paper comparisons or
campaign feedback. The shared launcher creates a fresh home, enforces the mbit10 guard, disables
Codex memory/plugins/agents, uses the unchanged pinned model/effort and audits/cleans credentials.
Do not read or export authentication material.

Choose new raw paths for each failed attempt; keep failed receipts. The commands below use a1
only if unused. Set `LANL_ROLE_RAW` and `LANL_ROLE_CODEX` to the parent-selected raw root and
verified installed Codex executable. All helpers run from SWDB, with its explicit Python path.

```bash
cd "$LANL_SOURCE_CHECKOUT/swdb-project"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export LANL_ROLE_RAW LANL_ROLE_CODEX
mkdir -p "$LANL_ROLE_RAW"
python3 -m swdb fill-target-parameters --records records \
  --characterization bfs.functional.kron-g16.t4.characterization.objects.a2 \
  --profile bfs-functional-read-offload-20261006-a1.fixture-profile \
  --target-description dx100-e4fc4af-functional-analytic-v1.t4 \
  --id dx100-e4fc4af-functional-analytic-v1.t4.estimated.a1 \
  --prepare-only --output "$LANL_ROLE_RAW/prepared" --format json \
  > "$LANL_ROLE_RAW/preparation.json"
python3 - <<'PY'
import os
from pathlib import Path
import yaml
root=Path(os.environ['LANL_ROLE_RAW'])
(root/'provider.yaml').write_text(yaml.safe_dump({'kind':'codex',
    'command':[os.environ['LANL_ROLE_CODEX']], 'timeout_s':1200,
    'total_seconds':1200,'max_repairs':0,'workspace':True}))
PY
python3 -m swdb fill-target-parameters --records records \
  --characterization bfs.functional.kron-g16.t4.characterization.objects.a2 \
  --profile bfs-functional-read-offload-20261006-a1.fixture-profile \
  --target-description dx100-e4fc4af-functional-analytic-v1.t4 \
  --id dx100-e4fc4af-functional-analytic-v1.t4.estimated.a1 \
  --provider-config "$LANL_ROLE_RAW/provider.yaml" \
  --output "$LANL_ROLE_RAW/provider" --format json > "$LANL_ROLE_RAW/filled.json"
python3 - <<'PY'
import os
from pathlib import Path
import yaml
from swdb.store import Store
root=Path(os.environ['LANL_ROLE_RAW']); store=Store(Path('records'))
char=store.get('bfs.functional.kron-g16.t4.characterization.objects.a2','workload_characterization')
request={'message_version':'1.0','id':'bfs.functional.kron-g16.t4.estimated.protocol.llm.a1',
    'version':1,'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1',
    'target_description':'dx100-e4fc4af-functional-analytic-v1.t4.estimated.a1',
    'inputs':[char['input']],'roi':char['binding']['roi'],'threads':char['binding']['threads'],
    'input_run_arguments':{char['input']:char['source']['run_arguments']}}}
(root/'freeze.yaml').write_text(yaml.safe_dump(request,sort_keys=False))
PY
python3 -m swdb freeze-protocol "$LANL_ROLE_RAW/freeze.yaml" --records records \
  --format json > "$LANL_ROLE_RAW/protocol.json"
```

Read the actual frozen protocol ID from `protocol.json` (the writer may qualify it). Use that
exact ID as `LANL_ROLE_PROTOCOL` in the estimate command:

```bash
python3 -m swdb estimate --records records \
  --characterization bfs.functional.kron-g16.t4.characterization.objects.a2 \
  --target-description dx100-e4fc4af-functional-analytic-v1.t4.estimated.a1 \
  --protocol "$LANL_ROLE_PROTOCOL" \
  --id bfs.functional.kron-g16.t4.estimate.llm.a1 --format json \
  > "$LANL_ROLE_RAW/estimate.json"
python3 -m swdb validate --records records > "$LANL_ROLE_RAW/validate.txt"
```

Export only the three new canonical records plus compact provider/guard/audit/projection
identities and the filled/null parameter inventory. Raw provider streams and authentication
stay on mbit10. Verify all prior canonical record bytes and the base target's known facts,
registered count/source/control files, observation policy and original receipt hashes.
Report provider execution as real only when guard enforcement/result, event audit, pinned
model/effort, executable/version and login cleanup all passed. These are estimated assumptions,
not a performance measurement or an accuracy/error-band validation. Whole-call unknowns must
remain null even when numerical service premises are filled.

## Actual accepted fill and recovery

The a2 provider ran once at frozen source `a7a9b9e`, using Codex CLI 0.153.0 and
the existing pinned model/effort. Its guarded workspace contained the exact three
sanitized files (101,164 bytes). Seven numerical answers are `estimated`;
`floating_point_ops_per_s` and `seconds_per_event` remain null/`unknown`. Known
facts, observation policy, source/count/receipt identities and prior bytes are unchanged.

| Attempt | Provider | Runner / acceptance | Custody |
|---|---|---|---|
| a1 | Not launched | Failed before login | [Original failure](10-estimation-role-failed-mbit10-20261006-a1.json) |
| a2 | Completed successfully, passing guard/audit/cleanup | Original runner exited 1 after its postfill wrapper/native hash comparison | [Unchanged failure and completed-provider receipt](10-estimation-role-postfill-custody-mbit10-20261006-a2.json) |
| a2 postfill a1 | Existing a2 output; no provider repeat | Fresh leased freeze/estimate/validation exited 0 at 2026-10-07 02:55:16Z (2026-10-06 22:55 ET); 620 records valid | [Compact acceptance](10-estimation-role-mbit10-20261006-a2-postfill-a1.json) |

The lane wrapper removes the ambient provider configuration. The a2 dispatcher
passed the verified existing login-home location through a task-specific token and
restored the provider's own setting inside the runner. Account HOME stayed intact;
authentication contents were neither read by the dispatcher nor exported.

`CodexAdapter.launch_command` admits the official npm platform package and selects
its native executable. The configured JavaScript entrypoint SHA
`61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70` and the
actual native executable SHA
`fce635028842bfe9257140e8b7d53162732945e2f356fc35225be0702b4974be` are distinct
identities. Postfill verified each independently against the original receipts
and frozen adapter selection without calling the CLI/provider again. Original a2
exit-1/error artifacts remain verbatim and hash-preserved.

The first compact-export helper incorrectly treated integer audit counters as lists.
It failed before Git mutation. The corrected external helper accepted only nonnegative
integer counters (eight control checks), without changing source, provider output,
postfill acceptance or canonical records. Only the new target/protocol/estimate and
compact proof/custody were exported; raw provider streams, prompt, authentication,
IR and address streams remain remote.

The frozen target is `dx100-e4fc4af-functional-analytic-v1.t4.estimated.a2`. Its
protocol is `bfs.functional.kron-g16.t4.estimated.protocol.llm.a2.postfill.a1.3fef19dcd9d39c07`
and estimate is `bfs.functional.kron-g16.t4.estimate.llm.a2.postfill.a1`. Historical
bundle `b238c61b…` remains sealed. Later integrated code requires a fresh protocol
for new execution; it does not rewrite this receipt.

Whole-call seconds, ratio, error band and all five trial totals remain null. Each
of the seven estimated parameters has null half/base/double whole-call sensitivity
and impact rank because host memory, runtime and composition premises remain
unsupported. This acceptance freezes numerical assumptions; it establishes no
performance accuracy, CPU error band or hardware/gem5 agreement.
