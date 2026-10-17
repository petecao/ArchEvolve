# 10 — Pilot on mbit10

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 05, 08, 09
**Spec:** `../spec.md`

**What to build:** The PageRank baseline and Jacobi implementations are profiled on all
four pilot inputs on mbit10, and the pilot answers whether one implementation behaves
differently across inputs.

- [x] The repo is cloned to `/data1/yanruj/EvolveSWDB` on mbit10 through git only.
- [x] Both lane leases and the legacy lease are checked before each run. Runs go through the socket-lane procedure. `df -h /data1` is checked before starting.
- [x] Eight profiles (2 implementations × 4 inputs) validate. Their raw files exist at the recorded paths, and a workload view is generated for each pair.
- [x] The input records carry measured edge counts.
- [x] A short answer on this ticket, per input: thread scaling, footprints versus the 24 MiB L3, index features, and simulated misses. It says whether the inferred bottleneck differs between scale 16 and scale 22, and whether that confirms keeping implementations and profiles separate.
- [x] Records are committed and pushed.

## Comments

## Answer

Resolved 2026-09-22.

- Repo cloned to `/data1/yanruj/EvolveSWDB` by git only; runs from commits 677346d (scale 16)
  and c55aaee (scale 22), recorded in each profile (`build.swdb_commit`).
- Every run went through `scripts/mbit10/profile_in_lane.sh 1 ...` (MemAcc `socket_lane.sh`,
  lease `mbit10-evaluation-node1`; node 0 was held by the retarget GPU campaign; leases and
  `df -h` printed and checked before each run). Raw output: `/data/yanruj/EvolveSWDB_runs`
  (agreed with the GPU campaign; `/data1` had 24 GB free).
- Eight profiles (2 implementations x 4 inputs) validate; all raw files exist at the recorded
  paths (358 checked, 0 missing); `swdb view` succeeds for every pair. The input records now
  carry measured sizes (kron-g22-k16: 4,194,302 vertices, 128,311,450 directed edges;
  urand-u22-k16: 4,194,304 and 134,217,158; kron-g16-k16: 65,536 and 1,819,292;
  urand-u16-k16: 65,536 and 2,096,552).

Per input (Gauss-Seidel / Jacobi; time = median of 5 trials by gapbs's timer; efficiency at
16 threads; footprint over one socket's 24 MiB L3; features of the gather's index stream;
cachegrind kernel-only, 1 thread):

| Input | 1 thread | 16 threads | Eff. 16 | Footprint / L3 | Dup. ratio | Seq. fraction | Degree Gini | Sim. D1 miss | Sim. LL miss | Sweeps | Inferred bottleneck |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kron-g16-k16 | 25.4 / 20.4 ms | 9.0 / 5.2 ms | 0.18 / 0.25 | 0.33 | 0.974 | 0.0098 | 0.87 | 0.33 / 0.33 | 0.0000 | 10 / 8 | parallelism_bound |
| urand-u16-k16 | 7.2 / 11.2 ms | 2.4 / 2.8 ms | 0.19 / 0.25 | 0.37 | 0.969 | 0.0005 | 0.10 | 0.40 / 0.40 | 0.0000 | 4 / 6 | parallelism_bound |
| kron-g22-k16 | 2.18 / 2.54 s | 0.134 / 0.190 s | 1.02 / 0.83 | 23.1 | 0.981 | 0.0009 | 0.93 | 0.47 / 0.46 | 0.038 / 0.041 | 6 / 7 | memory_bound (latency) |
| urand-u22-k16 | 1.74 / 2.59 s | 0.122 / 0.180 s | 0.90 / 0.90 | 24.0 | 0.969 | 0.0000 | 0.10 | 0.48 / 0.47 | 0.032 / 0.034 | 4 / 6 | memory_bound (latency) |

- Scale 16: the whole footprint (8.3-9.3 MB) fits the L3 and simulated LL misses are ~0.
  Scaling stops at 4 threads because `schedule(dynamic, 16384)` over 65,536 vertices makes
  only 4 chunks (pr.cc line 45): efficiency 0.18-0.25 = at most 4 of 16 threads busy.
- Scale 22: footprint 23-24x the L3 (about 580-600 MB), simulated LL miss rate 3-4 % of data
  references, and time still falls near-linearly to 16 threads (efficiency 0.83-1.02), so the
  inference is memory_bound with latency (not bandwidth) as the limit.
- Index features: the Kronecker graph is highly skewed (Gini 0.87-0.93) with slightly more
  sequential and same-line index steps than the uniform graph; both repeat ~97 % of indices
  within a sweep.
- **Answer: yes, the inferred bottleneck differs between scale 16 and scale 22** for both
  implementations on both input kinds (parallelism_bound versus memory_bound). The same
  implementation record gets different profile verdicts per input, which confirms keeping
  implementations and profiles separate.
- Caveats: the bottleneck is `basis: inferred` from counter-free evidence (rule in
  `swdb/profile.py _bottleneck`); the host is shared (load 1-3 during the runs, recorded per
  profile). Gauss-Seidel needs fewer sweeps than Jacobi except on kron-g16-k16 (10 vs 8 at
  1 thread).
- Records committed and pushed (ead5172, 10e4b76).
