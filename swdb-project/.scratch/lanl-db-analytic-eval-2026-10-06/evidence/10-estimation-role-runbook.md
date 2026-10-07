# Frozen parameter-fill execution

Updated: 2026-10-06 21:59 ET. Ticket 10 remains claimed until its handoff is accepted.

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
