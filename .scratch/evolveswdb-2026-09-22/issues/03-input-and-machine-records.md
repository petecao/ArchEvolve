# 03 — Input and machine records

Created: 2026-09-22
**Type:** slice
**Status:** claimed
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** The database describes the four pilot inputs and the mbit10 machine,
so that later a profile can say exactly what data it used and where it ran.

- [ ] Input schema: a generator (tool and arguments) or a file (path, format, checksum), never both; properties each wrapped with a basis.
- [ ] Four input records: Kronecker and uniform graphs at scale 16 and 22, average degree 16. The node count is 2^scale (`basis: code_reading`), the edge count is `unknown` until profiled, the degree distribution is inferred, and the input density is recorded.
- [ ] Machine schema and an mbit10 record captured read-only from the host (`lscpu`, `uname -r`, memory, NUMA layout, `perf_event_paranoid`), with the capture command and date. The capture starts no job and writes nothing on the host.
- [ ] New validation rules each have a passing and a failing fixture.

## Comments
