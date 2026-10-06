# Native BFS/BC unknown-object source diagnosis

Updated: 2026-10-06 ET. Read-only preparation for ticket11; no ticket claim, estimator/runtime/schema changes, provider call, application timing, or cost inference. Analysis branch base `121177dfe055435958a874660ea4561906ba6c8f`.

The largest missing counts are consistent with source stack wrappers, normalized local temporaries and outlined-worker captures, rather than missing heap payload sizes. Five candidate source-field/local-temporary partitions close exactly against each corresponding region’s unknown count in all five trials of both kernels (50/50 checks). This is arithmetic and source attribution evidence; the observer does not serialize per-access unknown-object membership. Exact root/type/extent attribution is pending the parent-run static projector below. Historical characterization payloads and seals remain unchanged.

## Pinned count evidence

Metadata commit `a15d9eade7d90e210fd4a37f30bbab9ab6612d72`, count source `eb1b2419f03c09d4ccbd97286fa7d1109f3f495b`, `source-normalized-v2`, Kronecker `-g16 -k16`, T1, five whole-call trials. BFS arguments are `-g 16 -k 16 -n 5`; BC adds `-i 1`. The wrapper explicitly states no uninstrumented application timings were collected and records 587 valid records. Its available-artifact source/input/ROI/runtime binding verification is retained as parent execution evidence, not rerun here.

| Kernel | Record identity | Count payload SHA256 |
|---|---|---|
| BFS | `515cdab3be689090a9d418c883fab6164dd29c98320c5cdce27f252d89ec15ab` | `96dd7f7d56582724dea74e1807afab339cfd9dc14cbab93dc029dd7eb0645eae` |
| BC | `5e4d4462e2b073a2cc0fe5c00b4d5cffd434cd4d917f4cd31b7d7165db22a8dc` | `7f36d46391a51a6e8f8d39734610ab3a61c67119c5cf000be0cb1c4e55d386b3` |

This diagnosis independently verifies both exported YAML byte hashes, source-file hashes, count/record identities, all ten wrapper trial totals, and every selected allocation/free/bulk-call bin against its execution count. Complete per-trial regions, source locations, candidate/data partitions and call-site size bins are retained in [the compact count projection](11-native-unknown-object-origin-counts.json). Every partial memory region reports only `object_identity_or_extent`; none reports state-budget or byte-overflow exhaustion in these records.

| Trial | BFS diagnostic unknown requests / partial regions | BFS five selected regions | BC diagnostic unknown requests / partial regions | BC five selected regions |
|---|---:|---:|---:|---:|
| 0 | 3,630,415 /24 | 3,611,066 | 17,262,809 /30 | 16,146,619 |
| 1 | 3,436,017 /21 | 3,370,845 | 19,223,858 /27 | 18,108,917 |
| 2 | 3,412,104 /21 | 3,333,651 | 19,176,267 /27 | 18,061,420 |
| 3 | 2,922,585 /21 | 2,698,060 | 18,056,066 /27 | 16,941,210 |
| 4 | 2,843,758 /21 | 2,536,534 | 16,410,382 /27 | 15,295,527 |

These are sums of diagnostic per-region requests, not footprint unions or seconds. Five selected regions cover 99.467% of BFS trial0 and 93.534% of BC trial0; later BFS trials have larger TDStep tails, so trial0 coverage must not be transferred to them.

## Dominant source origins

| Trial0 region | Unknown requests | Concrete source evidence and required producer facts |
|---|---:|---|
| BFS BUStep `loop:bfs.cc:1717:6e2a9b58e359bcfa` | 2,680,088 | Repeated `Neighborhood` fields/iteration temporaries (`graph.h:110–116`), parent wrapper (`pvector.h:116`), Graph `in_index_` field (`graph.h:220`), outlined bounds. Track local aggregate/frame lifetimes and caller-owned wrappers; keep separately indexed CSR/parent heap reads. |
| BFS InitParent `loop:bfs.cc:3354:4fc081ce5a20fcdd` | 355,575 | Graph `out_index_` field loads (`graph.h:206`) and parent wrapper; separately indexed CSR entries and parent writes close the data partition. Main’s `Graph g` is constructed before ROI and passed by reference. |
| BFS BUStep `loop:bfs.cc:1791:c91be0a18a4752c0` | 312,891 | Bitmap and parent pointer-field loads, the `int64_t awake_count` reduction local at `bfs.cc:56`, and bitmap wrapper loads. The bitmap backing array remains a separate heap object. |
| BFS BitmapToQueue `loop:bfs.cc:3093:d28ec09d2dd27686` | 131,438 | Outlined bounds, Bitmap pointer field and QueueBuffer fields (`sliding_queue.h:98–100`). QueueBuffer’s local backing allocation is separate from its local wrapper and shared queue wrapper. |
| BFS final parent loop `loop:bfs.cc:5199:82c2122db9c90924` | 131,074 | Outlined loop bound and pvector pointer field; indexed parent accesses excluded independently. |
| BC `gapbs-bc-brandes/pbfs-edge` | 6,933,943 | Depth/path-count pvector fields, source-level depth and compare-and-swap temporaries, QueueBuffer fields. CAS data addresses retain their read/write semantics; the temporary operand storage is separate. |
| BC `gapbs-bc-brandes/back-edge` | 4,694,474 | `g_out_start` capture storage, Bitmap and pvector pointer fields. Indexed successor bitmap/path-count/delta payload accesses are separate. |
| BC atomic bitmap helper `unmapped.gapbs-bc-brandes.PBFS.45.4.15975176246384606928` | 2,463,874 | Bitmap pointer-field reads and old/new CAS temporaries (`bitmap.h:46–48`, `platform_atomics.h:31`); the actual atomic bitmap address is excluded from the candidate local partition. |
| BC `gapbs-bc-brandes/back-vertex` | 1,073,852 | Neighborhood aggregate/iteration temporaries, Graph and output pvector wrapper fields, loop captures. |
| BC `gapbs-bc-brandes/pbfs-frontier` | 980,476 | Neighborhood aggregate/iteration temporaries, Graph pointer field and outlined loop bounds. |

Remaining regions include TDStep/QueueToBitmap local buffers, BC normalization/reduction and pvector fill wrappers, SourcePicker’s caller-owned `mt19937_64` state, and small serial/caller temporaries. The source-level candidates are not evidence that arbitrary globals or libomp allocations are known. The stable observer scans successful translation-unit allocator/free calls, including pre-ROI objects, but skips `AllocaInst` and has no global-registration hooks. Bulk calls retain lengths without contributing their source/destination ranges to the existing live-object service observer.

## Minimal bounded admission and honest residuals

Register source allocas throughout the translation unit, including main/callers before ROI, rather than only functions that emit ROI counts. Compute extent using target DataLayout allocation size times the actual array count with overflow/scalable checks; preserve distinct lifetime IDs, explicit lifetime starts/ends, normal and exceptional frame exits and stackrestore handling. A bounded module-defined global can have static storage; TLS needs per-thread storage/lifetime and alias handling. External declarations expose a declared range, not the entire external allocation. These distinctions follow [LLVM alloca semantics](https://llvm.org/docs/LangRef.html#alloca-instruction), [lifetime markers](https://llvm.org/docs/LangRef.html#llvm-lifetime-start-intrinsic), and [global definitions](https://llvm.org/docs/LangRef.html#global-variables).

Do not infer pointee extent from a wrapper pointer field, treat an observed address span as an allocation, or assign the first observed address as an object base. Source debug annotations identify variables; target IR types and producers establish allocation bounds. Preserve unknowns for unbounded dynamic/scalable storage, unsupported lifetime exits/aliases, opaque producer returns and inaccessible external allocation identity.

LLVM’s [microtask ABI](https://openmp.llvm.org/doxygen/group__PARALLEL.html) gives `kmp_int32*` global/bound thread IDs followed by shared-variable pointers. An explicitly labeled ABI view can cover the 4B typed ID referent during microtask execution. This is an inferred bounded-view contract, not proof of libomp’s complete allocation or lifetime. Such views must retain owner/epoch/worker scope, unify overlapping aliases with existing registered storage, retire at normal/unwind function exit, and leave accesses outside the view unknown. Runtime/schema labels must distinguish view-relative logical facts from full-allocation facts; neither establishes cache residency, physical first touch or allocator/cache costs. Shared capture referents should resolve to their caller storage when proven, not acquire guessed new allocations.

## Exact allocation and bulk-call facts for ticket11

All executed selected call bins have zero unknown lengths/free lifetimes. Counts below aggregate all five trials; per-site/per-trial data stay in the companion JSON.

| Kernel / operation | Exact bytes: executions |
|---|---|
| BFS new[] | 8192:10;65536:24;262144:10 |
| BFS delete[] lifetime size | 8192:10;65536:24;262144:5 |
| BC new[] | 65536:5;227416:5;262144:20;524288:5 |
| BC delete[] lifetime size | 65536:5;227416:5;262144:15;524288:5 |
| BC new/delete lifetime size | 8:5;16:5;32:5;64:5;128:2 each |
| BFS memcpy / BC memcpy | 8:47 /8:15 |
| BFS memmove / BC memmove | 16/51 events; full exact length union in companion JSON |

The new[]/delete[] 262144B imbalance follows the whole-call ROI boundary: a returned pvector backing buffer survives the call. It does not indicate an unknown free size. Source Timer::Start (`timer.h:23`) explains the 8B copy sites; QueueBuffer::flush (`sliding_queue.h:110–115`) explains bulk `std::copy`, and BC vector growth explains a separate relocation family. Those are source-origin inferences pending the parent static projection. The historical call records retain line/length but not source/destination alignment, overlap or allocation roots; do not silently use an allocation-size union or call name as those regime facts.

## Parent-run root projection

[11-normalized-root-projector.cpp](11-normalized-root-projector.cpp) reads `normalized.bc` and its actual `source.json` without mutating the module. It cross-checks every access/call number, access function/debug path/line/column, update kind, element width/lanes and call name/line before exporting selected facts. Diagnostic `static_analysis.optimized_facts` is a separate optimized map with different site IDs; it is not an input. [Selected IDs](11-native-origin-root-sites.json) cover all candidate sites in the ten dominant regions and their executed bulk calls.

The probe deduplicates underlying roots, records target-DL alloca/global extents, LLVM lifetime-marker counts, debug-variable annotations, direct-call and `__kmpc_fork_call` shared-argument producers, explicit 4B ABI-view facts, and bulk constant/runtime length, alignment and default-AA alias result. Loaded pointer storage and its unproved pointee are separate. AA facts are static normalized-IR proofs, not observed allocator/address regimes. No pointer addresses, raw instruction bodies or address expressions are exported. The [stored local proof](11-normalized-root-projector-local-proof.json) cross-checks O0:27 accesses/8 calls and O1:22 accesses/6 calls, preserves both input bitcode hashes, and refuses changed-source-map/missing-site cases with exit2 before writing output. It is compiler-only; actual BFS/BC root projections remain pending parent execution.

```bash
# Use the parent's verified LLVM22 bin path and GCC13 development environment.
llvm_bin=<verified-LLVM22-bin>
raw=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-t1-counts-20261006-a1
probe="$raw/root-projector"
"$llvm_bin/clang++" --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  .scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-normalized-root-projector.cpp \
  $("$llvm_bin/llvm-config" --cxxflags --ldflags --system-libs --libs core irreader analysis passes support) \
  -std=c++17 -O2 -Wl,-rpath,"$("$llvm_bin/llvm-config" --libdir)" -o "$probe"
python3 - "$probe" "$raw" <<'PY'
import json,subprocess,sys
from pathlib import Path
probe,raw=sys.argv[1],Path(sys.argv[2])
s=json.loads(Path('.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-native-origin-root-sites.json').read_text())
for k,v in s['kernels'].items():
    d=raw/(k+'-counted')
    subprocess.run([probe,str(d/'normalized.bc'),str(d/'source.json'),
                    str(raw/(k+'.normalized-root-projection.json')),
                    v['access_sites_csv'],v['call_sites_csv']],check=True)
PY
```

Local reproduction: `python3 .../11-root-projector-smoke.py --llvm-bin <LLVM22-bin> --output-directory <external-proof-directory>`. It compiles static O0/O1 fixtures, obtains the counting pass’s public source map, checks fixed/dynamic stack/global/declared/caller/ABI roots, lifetimes and bulk facts, and rejects a changed map or missing requested site before output. This source-only diagnosis provides no new CPU model or error result.
