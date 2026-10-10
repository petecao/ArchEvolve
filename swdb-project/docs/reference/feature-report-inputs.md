# Import reported feature inputs

Updated: 2026-10-09 ET (sanitizer v2, internal and scope conflicts); 2026-10-06 ET.

`import-feature-report` creates a new workload characterization. It appends
`reported_inputs[]` and preserves every native count, source/input binding,
execution receipt and original record. Each input has basis `reported`; its
`features` retain Peter's field names and literal values. A report contributes
additional evidence without overwriting measured counts or calibrated rates.

```sh
python3 -m swdb import-feature-report \
  --records /path/to/copied/records \
  --characterization bfs.kron-g16.t4.characterization.a2 \
  --report ../examples/received/bfs-sparse.features.v1.2.yaml \
  --methodology ../examples/received/peter-measurement-methods.v1.2.yaml \
  --methodology-text ../examples/received/peter-measurement-methodology.v1.2.txt \
  --manifest ../examples/received/manifest.json \
  --array-alias VertexOffsets=g.out_index_ \
  --id bfs.a2.with-reported-sparse --format json
```

Run from `swdb-project/`. Import the fully connected file separately with a new
ID. The optional alias declares a comparison to a registered array; source
revision, ROI, input and concrete access equivalence remain separate questions.
Omitting it leaves arrays explicitly unmapped. Reusing a destination ID fails
before writing anything. Characterization IDs and YAML/JSON paths are accepted.

## Read the evidence scopes

The supplied filenames say v1.2, while both content `schema_version` fields say
`1.1`. `source_report` records both versions, the original byte hash, the sanitized
content hash and sanitizer version. No version is silently rewritten.

The counted a2 BFS covers DOBFS trial calls on upstream `2972aeb`, Kronecker g16
and four threads. The reports describe TDStep on DX100 source `e4fc4af`; sparse
profiling names g18, 16 threads and a Xeon Gold 6226R. Dense facts describe a
complete graph and preserve discovery/CAS behavior separately from the later
read phase. These facts do not bind to the native counted ROI merely by naming
BFS. Source/input/host differences are listed as scope conflicts.

An explicit `VertexOffsets=g.out_index_` alias exposes reported 4-byte offsets
versus the registered upstream array's 8-byte offsets. Both remain, with an
unresolved source/access scope. This is not permission to repair either source
or to substitute report statistics for native accesses.

## Overlapping fields

The literal report names remain under `reported_inputs[].features`; native v1
count-field names remain compatible with existing readers.

| Peter field | Native characterization counterpart | Comparison boundary |
|---|---|---|
| `kernel.function`, `source_file`, `source_revision` | coverage, source identity and binding | A reported helper or revision is not automatically the counted whole-call ROI. |
| `loop_structure.outer_level`, `inner_level` | region loop metadata and `dynamic_counts` | Symbolic domains stay symbolic; phase-specific trip counts are not whole-trial counts. |
| `indirect_access_distances[].array_name`, `index_stream` | access expression and array identity | Require an explicit array alias; concrete access binding is still unresolved. |
| `element_size_bytes` | `regions[].access_patterns[].element_bytes`; catalog `steps[].array.element_bytes` | Preserve each source's type/width; compare only within the stated scope. |
| `statistics.mean_index_distance`, `mean_byte_stride` | distance/stride observations | Absolute index jumps are not a constant signed LLVM stride. |
| `spatial_locality_distribution` | distance-threshold statistics | Threshold membership is not same cache-line/page membership or hit rate. |
| `data_structures` | logical array type/capacity metadata | Capacity is not an observed active working set. |
| `frontier_evolution_profile` | per-level frontier/loop facts | Reported traversal order does not observe runtime thread interleaving. |
| `operations` | `operation_counts` | Descriptions and symbolic frequencies are not dynamic operation counts. |
| `memory_streams` | address shape, update kind and stride | Preserve reported interpretations independently of compiler/count facts. |
| `working_set` | `footprint_bytes` and scoped working-set evidence | KB/MB prefixes remain ambiguous; logical capacity is not ROI live footprint. |

For example, adjacent 4-byte elements 15 and 16 have index distance 1, yet
addresses 60 and 64 cross a 64-byte line boundary. A small distance threshold
alone does not establish physical same-line or DRAM-row locality.

## Conflicts and units

`conflicts[]` records reasons and both compared values. The reader lists:

- filename/content version differences; `source_scope_mismatch` when the reported and
  counted function or source revision differ, otherwise `source_scope_unbound`;
- missing or unresolved aliases, and differing reported/catalog element widths;
- `reported_internal_conflict` when one report lists an array twice or its sections give
  different widths (every width is compared with the catalog; none is selected);
- stale manifest handling notes that contradict the selected updated report;
- structured methodology versus its text table's 4-byte/8-byte offset statements;
- KB/MB/GB ambiguity for every `*_kb`/`*_mb`/`*_gb` working-set field, retaining the raw
  value and unit label without conversion. Expected logical capacity is computed only for
  the BFS v1.2 per-array footprints (`parent`, `offsets`, `neighbors`, `queue`).

The stale-manifest-note and methodology-text checks match the BFS v1.2 wording and the
`VertexOffsets` table rows; other reports get no such conflict and need their own rule.

The sparse report's 262,143 parent elements at 4 bytes imply a logical capacity
of 1,048,572 bytes; its field says `1.05 MB`, while the methodology claims binary
units. The report keeps that label and value. Dense footprints resemble binary
scales, so one blanket conversion cannot reconcile the files. Expected capacity
is arithmetic over reported dimensions, not a measured footprint or an automatic
unit choice. Missing/non-numeric dimensions stay unknown; strings are not coerced
into sizes or counts.

Locality methodology identifies adjacent frontier/neighbor positions, excludes
cross-segment pairs and does not observe thread interleaving. Its reported
threshold percentages remain distinct from cache hit rate, temporal reuse or
actual address-block membership.

## Inputs for estimation

Sanitizer `swdb.feature-report-sanitizer.v2` (2026-10-09 ET) withholds complete PMU/performance
sections, recursively named timing/runtime/cycle/IPC/CPI/throughput fields, unit-suffixed
durations (`trial_sec`, `kernel_ms`, `latency_ns`), latencies, cache hit/miss rates, MPKI,
bandwidth/FLOP rates, and free-text performance outcomes. Boolean methodology flags such as
`measures_cache_hit_rate` stay. Redaction entries hold only `path` and `reason`. Version v1
(2026-10-06) matched a narrower name list; no stored record used it. It keeps index statistics and descriptive operation
frequencies. Original values stay in the evaluator-owned source files; redaction
metadata contains paths and reasons, not the removed values. Structured
methodology/manifest inputs also have original and sanitized hashes. Manifest
evidence retains the selected report entry and handling notes; other entries stay
in the original source. Full methodology prose stays outside the characterization; only concrete array/type
rows enter its sanitized evidence.

`validate` and characterization-file loading check sanitized hashes and reject
reintroduced timing/PMU fields even when record hashes are recomputed. A stored
parent's identity and native facts are checked against the imported record.
Native execution binding continues to certify counted facts only; it does not
promote reported facts or resolve their conflicts. Current analytic mechanism
models continue to use counted regions; consuming additional reported facts
requires an explicit applicable model/input scope.
