# 03 — Input and machine records

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** The database describes the four pilot inputs and the mbit10 machine,
so that later a profile can say exactly what data it used and where it ran.

- [x] Input schema: a generator (tool and arguments) or a file (path, format, checksum), never both; properties each wrapped with a basis.
- [x] Four input records: Kronecker and uniform graphs at scale 16 and 22, average degree 16. The node count is 2^scale (`basis: code_reading`), the edge count is `unknown` until profiled, the degree distribution is inferred, and the input density is recorded.
- [x] Machine schema and an mbit10 record captured read-only from the host (`lscpu`, `uname -r`, memory, NUMA layout, `perf_event_paranoid`), with the capture command and date. The capture starts no job and writes nothing on the host.
- [x] New validation rules each have a passing and a failing fixture.

## Comments

## Answer

Resolved 2026-09-22.

- Input schema: exactly one of `generator` / `file` (both or neither rejected); properties
  keyed by vocab `input_properties`, each a fact with a basis.
- `records/inputs/{kron-g16-k16,urand-u16-k16,kron-g22-k16,urand-u22-k16}.yaml` (degree 16,
  `-g`/`-u`). Correction found by the pilot: gapbs builds N = largest vertex ID + 1
  (`builder.h` 322-323), not 2^scale; kron-g22-k16 builds 4194302 vertices. So `num_nodes`
  is `measured` (scale 16, 65536) or `unknown` until profiled (scale 22). Edge counts start
  `unknown`; degree distribution `inferred`; input density `sparse_scattered` (inferred).
- Machine schema + `records/machines/mbit10.yaml` from `swdb capture-machine --id mbit10
  --ssh mbit10` (read-only: lscpu, `lscpu -C`, uname, /proc/meminfo, numactl --hardware,
  perf_event_paranoid, id -nG; nothing started or written on the host), captured
  2026-09-22 17:03 ET. `hardware_counters_available: false, basis: inferred`
  (paranoid 4, not in the vtune group).
- New rules with passing and failing fixtures: generator/file, property names, typed
  facts; the capture parser has a fixture test (`tests/test_machine_capture.py`).
