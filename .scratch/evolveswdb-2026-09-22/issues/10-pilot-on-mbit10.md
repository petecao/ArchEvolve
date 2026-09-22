# 10 — Pilot on mbit10

Created: 2026-09-22
**Type:** slice
**Status:** claimed
**Blocked by:** 05, 08, 09
**Spec:** `../spec.md`

**What to build:** The PageRank baseline and Jacobi implementations are profiled on all
four pilot inputs on mbit10, and the pilot answers whether one implementation behaves
differently across inputs.

- [ ] The repo is cloned to `/data1/yanruj/EvolveSWDB` on mbit10 through git only.
- [ ] Both lane leases and the legacy lease are checked before each run. Runs go through the socket-lane procedure. `df -h /data1` is checked before starting.
- [ ] Eight profiles (2 implementations × 4 inputs) validate. Their raw files exist at the recorded paths, and a workload view is generated for each pair.
- [ ] The input records carry measured edge counts.
- [ ] A short answer on this ticket, per input: thread scaling, footprints versus the 24 MiB L3, index features, and simulated misses. It says whether the inferred bottleneck differs between scale 16 and scale 22, and whether that confirms keeping implementations and profiles separate.
- [ ] Records are committed and pushed.

## Comments
