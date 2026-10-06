# 05 — Dynamic counts and live address-stream counting from an instrumented native run

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 1 day

**What to build:** IR-level instrumentation of the pass's regions that counts trip counts, accesses per pattern and footprint on one input, counted at source level so counts do not depend on the machine (D12). It also counts the address stream live for a target's mechanisms (for example, distinct DRAM rows per reorder window under the target's address layout), storing no stream (D17, D24).

## Acceptance

- [ ] Counts fill the characterization's dynamic slots; host and compiler recorded.
- [ ] Element-count formulas from ticket 03 agree with the counts within a stated tolerance, or the difference is explained.
- [ ] Runs for BFS and BC on the small class graphs on the Mac; large graphs wait for mbit10.
- [ ] Address-stream counts are re-run per target description; no index stream is written to disk.
