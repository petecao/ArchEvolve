# Certification test fixture scope proposal — 2026-10-08 ET

SOURCE ONLY / UNAPPLIED / NOT RUN. Parent owns application, compiler diagnostics,
unsandboxed test execution, and retention of the interrupted broad run. Nothing
here establishes a scientific campaign cause or admission.

The retained first real process test failed after successful compilation because
all 10 positive evaluator invocations and 20 control invocations exited 95 with
exact `swdb certification evaluator: shm_open failed`. The 23 build/link logs,
6 legality preprocessing logs and 4 graph-generation logs exited 0. These are
bounded local unit-test JSON diagnostics. The error occurs before evaluator
prepare, fork or candidate execution (evaluator_core.inc 144–158). No errno is
recorded, so sandbox denial remains an inference; the tests do not identify an
R3 CandidateRefusal defect. Original failed logs and all unit-test files remain
unchanged. The metadata-only diagnostic inventory is
`/private/tmp/lanl17-certification-first-real-test-diagnostic-metadata-20261008-r1.json`.

The independent test-efficiency issue is repeated Store(ROOT / records), which
parses the full approximately 1 GiB catalog for source materialization and each
certification. A narrow genuine record closure is sufficient for these tests.
The existing testkit.record_subset helper scans bounded ID headers, rejects
symlinks/duplicate/missing roots, parses only the selected original-reference
closure, and copies byte-identical original files. It neither fabricates evidence
nor changes source context or public validation.

The prospective patch adds one testkit fixture plugin and threads its per-test
Store explicitly into eight certification test modules. One session template is
copied from original BFS and BC scalar source snapshots plus every normative
library entry's intrinsic_record, hardware_operations and strategies. This is
necessary because c.certify validates the whole original library before selecting
the command or entry. Current text inspection yields 41 explicit record roots:
2 scalar snapshots, 20 intrinsic records, 16 operation records and 3 strategies
(dx100_read_offload, packing, loop_tiling). The unchanged helper follows all their
original-ID references, including source implementations and semantic evidence;
closure file count and size are future measurements, not claimed here.

The three actual contract IDs (contract.bfs_read_offload,
contract.bfs_tdstep_frontier_staging and contract.bc_read_offload) are normative
library entries rather than catalog record IDs. The fixture explicitly requires
all three in the real Library and collects its current record references; it does
not mistakenly pass those normative IDs to the record-subset copier. Modified
lowering-library tests retain actual current code and reference hash mutation.

Each test receives a fresh copy and Store, isolating writer or in-memory changes.
The directory is outside that test's tmp_path, preserving the unknown-version
no-build assertion that tmp_path is empty. Helpers receive a required keyword-only
fixture argument and callers pass it explicitly; native **options stay intact.
No production code, library file, YAML record, schema, hash table, certificate,
expected verdict, check threshold, source path, compiler call, evaluator call,
negative control or original assertion is changed. All reconstructed Python files
parse via AST and every original Assert AST is identical. The existing forged
snapshot test still constructs its own indexed Store from a copied original
snapshot and tests the unchanged materializer's refusal.

The full BC library derived-state/shared/target-status test intentionally keeps
Store(ROOT / records). Procedure manifest digest assertions and every original
committed-certification/history/pin scan keep their full original scope. Legality
and feedback have no bulk Store fixture to replace. Extensa already uses the same
subset helper, original record closure and isolated per-test copy, so remains
unchanged. Remaining full-catalog work is intentional and should not be omitted
from final validation merely to get a fast result.

Prospective patch: /private/tmp/lanl17-certification-fixture-scope-prospective-r1-20261008.diff
37475 bytes; SHA256 cc936046da6a04346ea733e955af976e45cb50d746368bf24286a36a0ad581a8.
Static reconstruction/assertion receipt:
/private/tmp/lanl17-certification-fixture-scope-static-review-20261008-r1.json
4451 bytes; SHA256 9c5906ddde2684054a9c8637b8d48bc6715a6534cbcce7b10734a59caeb6994b.

Optional parent-owned local diagnostic source:
/private/tmp/lanl17-certification-posix-shm-diagnostic-20261008-r1.c
1907 bytes; SHA256 bcde8b870fa0cac830079d3ba3bb6ebe04c88a6ade78a44ee65dccbb9d640275.
It performs at most eight fresh O_EXCL name attempts using the evaluator's
/swdb15 PID/tag name shape, mode0600, and unlinks only its own successfully
created object. It probes ftruncate/shared mmap/read-write/cleanup and reports
errno if the OS refuses the call. No SWDB source is imported or executed; no
existing named shared object is removed. Future exact compiler argv on macOS:
`cc -std=c11 -O0 -Wall -Wextra /private/tmp/lanl17-certification-posix-shm-diagnostic-20261008-r1.c -o /private/tmp/lanl17-certification-posix-shm-diagnostic-20261008-r1`
Future run argv is that executable alone. Both are NOT EXECUTED here. The parent
may run the diagnostic and unchanged real integration unsandboxed. A passing
4096-byte arbitrary-address probe proves only basic POSIX availability, not the
full evaluator's fixed-address arena, process/RPC correctness or scientific
admission. Do not skip or mock failed real integration based on this probe.
