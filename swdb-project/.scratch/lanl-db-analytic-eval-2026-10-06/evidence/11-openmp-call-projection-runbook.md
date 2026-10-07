# Exact-source OpenMP ABI call projection prerequisite

Updated: 2026-10-06 21:00 ET. Ticket 11 prerequisite only; ticket custody is unchanged.
The standalone public command reads existing characterization/source-map/normalized-IR
files. It compiles one read-only LLVM helper and does not instrument, recount, link or
execute an application. Raw IR remains on mbit10. Native projection is pending parent
execution; the local public static fixtures passed.

The new `swdb.openmp-call-projection.v1` output binds the full canonical characterization
hash, its declared identity and exact file bytes to `static_analysis.source_ir_sha256`
and `binding.execution_receipt.source_ir_sha256`; both must match the consumed IR.
`source.json` has its own exact byte hash. Every access and call site is re-enumerated and
cross-checked using the verified root-projector traversal, including unexecuted sites.
Observer-tagged scaffolding is skipped by the same rule as the current source pass.
This requires the complete saved translation-unit site map; a filtered map refuses if
its enumeration differs. Existing characterization records and counter/site IDs stay
byte-identical. Runtime/count receipt validity is a separate admission prerequisite.

Calls are the union of executed direct `__kmpc_*` sites across every observed trial.
Each retains the original site, callee and region, plus IR-derived function/location,
actual `argument_count`, declared `callee_parameter_count`, variadic status and all
indexed operands. Integer literals carry exact `bits` and signed decimal strings, never
JSON-number narrowing. SSA values remain `dynamic`; undef/poison and unsupported types
remain explicit. Pointer operands are redacted, including null pointers and static
symbols. No addresses or arbitrary IR expressions are serialized. An empty known call
inventory gives an empty verified projection; missing/unknown observations refuse.

`ident_flags` may be a constant only for an immutable direct five-field `ident_t`
initializer with four i32 fields and a final pointer, when LLVM proves its initializer
is definitive. Mutable, interposable, externally initialized, thread-local or indirect
referents remain unknown. This establishes a static initializer fact, not libomp runtime
state, prewarming, task-pool/cache residency, allocator regime or a cost. LLVM22
`GlobalVariable::hasDefinitiveInitializer` explicitly rejects externally changeable
initializers. Warm T1 transfer, if later supported by a measured model, remains inferred.

The receipt seals helper source/binary and wrapper hashes, exact helper/compiler/wrapper
argv, compiler binary hash/version and LLVM version. Its `identity_sha256` covers the
whole compact output. Do not bind a model from a filename or callee spelling alone.
No estimator, observer/runtime, source normalization, schema or historical record is
changed by this prerequisite.

## Parent's prospective source-only Linux command

Use a clean Git-synced checkout containing this source. Parent owns socket/legacy lease,
capacity and process checks, a bounded outer timeout and the actual dispatch. These
commands consume the four immutable count records from Git and original host-local IR;
they do not run graphs/applications. Use a fresh raw output root. Stage subprocesses have
180 s caps; parent should bound the whole four-case dispatch to 900 s including cleanup.
Preserve source/record hashes below; never overwrite the count folders.

```bash
set -euo pipefail
export LANL_OMP_PROJECTION_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-openmp-call-projections-20261006-a1
export LANL_OMP_PROJECTION_LLVM=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin
export LANL_OMP_COUNT_REF=e361e83b64578890003ac001e7d6e344556a1876
test ! -e "$LANL_OMP_PROJECTION_RAW"
mkdir -p "$LANL_OMP_PROJECTION_RAW"
git rev-parse HEAD > "$LANL_OMP_PROJECTION_RAW/source-commit.txt"
git status --porcelain > "$LANL_OMP_PROJECTION_RAW/source-status.txt"
test ! -s "$LANL_OMP_PROJECTION_RAW/source-status.txt"
for LANL_OMP_SCALE in 16 17; do
  case "$LANL_OMP_SCALE" in
    16) LANL_OMP_COUNT_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1;;
    17) LANL_OMP_COUNT_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1;;
  esac
  for LANL_OMP_KERNEL in bfs bc; do
    LANL_OMP_ID="${LANL_OMP_KERNEL}.kron-g${LANL_OMP_SCALE}.t1.characterization.objects.a1"
    LANL_OMP_CASE="$LANL_OMP_PROJECTION_RAW/${LANL_OMP_KERNEL}.g${LANL_OMP_SCALE}"
    mkdir "$LANL_OMP_CASE"
    git show "$LANL_OMP_COUNT_REF:swdb-project/records/workload_characterizations/$LANL_OMP_ID.yaml" \
      > "$LANL_OMP_CASE/characterization.yaml"
    python3 - "$LANL_OMP_CASE/characterization.yaml" "$LANL_OMP_ID" <<'PIN'
import sys
from swdb import access
proof = access.read_record('.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-openmp-call-projection-preparation.json')
case = next(row for row in proof['cases'] if row['characterization_id'] == sys.argv[2])
assert access.record_hash(sys.argv[1]) == case['record_file_sha256']
PIN
    python3 -m scripts.openmp_call_projection \
      --characterization "$LANL_OMP_CASE/characterization.yaml" \
      --source-ir "$LANL_OMP_COUNT_RAW/$LANL_OMP_KERNEL/counted/normalized.bc" \
      --source-map "$LANL_OMP_COUNT_RAW/$LANL_OMP_KERNEL/counted/source.json" \
      --llvm-bin "$LANL_OMP_PROJECTION_LLVM" \
      --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
      --timeout-s 180 --output-directory "$LANL_OMP_CASE/projection" \
      > "$LANL_OMP_CASE/receipt.stdout.json" 2> "$LANL_OMP_CASE/receipt.stderr"
  done
done
```

Run from `swdb-project/`. LLVM development headers/libraries are required for this helper;
no OpenMP runtime library is linked. Current public fixtures use the same LLVM22 API.
The exact four record file hashes and two IR hashes are in
[the preparation proof](11-openmp-call-projection-preparation.json), sourced from the
immutable `e361e83` metadata. Verify those record hashes after Git materialization, the
projection's complete-characterization hash against its canonical record, input byte
identity and every all-trial selected site before model admission. Export only the four
compact `projection.json` files and a compact lane/source/input verification wrapper
through Git; helpers, raw IR/source maps and temporary dense record copies stay on mbit10.
Keep source count and projection producer identities separate. No recount is necessary.

## Public validation and boundary

Seven public tests passed in 7.10 s. Five successive RED→GREEN slices covered the public
command, conflicting receipt hash, externally initialized ident, missing trial inventory,
and exact receipt compiler/wrapper pins. Regressions also cover changed IR, unknown count,
unexecuted source-map mismatch, known-zero calls, pointer redaction, dynamic operands,
all-trial union and unchanged input bytes. These are compiler hand fixtures, not native
application/runtime calibration evidence. The parent dispatch supplies actual g16/g17
static receipts; ticket 03 owns model admission and transfer uncertainty.

Source pointers: `scripts/openmp_call_projection.py`, `swdb/llvm/OpenMPCallProjection.cpp`,
`tests/test_openmp_call_projection.py`, verified root-projector commit `a9dbe11`, and the
count metadata commit `e361e83`. Ticket 09/10 merger/frontier work remains independent.
