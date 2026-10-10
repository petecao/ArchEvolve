# CPU independent-chain extension preregistration

Created:2026-10-06 ET, before second-run dispatch. Owner: parent remote coordinator.

Primary source97f5f19; compact evidence commitb7b01ed, primary receipt
edde78d5210d8c55ebea529781c2707e2a18dfe44908603ce18a888019feb286.
A bounded repeat tests whether the apparent late plateau persists. It does not fit
application timings and cannot force a known parameter. The primary is immutable.

| T | C8 M_eff | C16 M_eff | C32 M_eff | C16→32 gain | Final3 relative range |
|---|---:|---:|---:|---:|---:|
|1|7.3543|10.6021|10.5897|−0.12%|30.67%|
|2|7.1291|10.4873|10.7624|+2.62%|34.64%|
|4|6.8641|10.3076|11.2704|+9.34%|42.75%|
|8|5.9160|7.4902|7.8286|+4.52%|25.53%|
|16|3.9931|4.2040|4.2188|+0.35%|5.37%|

All cells had balanced workers and equal footprint; dependent/late-cell elapsed
spread was below25%. T1/2/4/8 failed the15% three-point range, rather than the
noise or footprint premise. T16 already admitted a constructed-work plateau.
Increasing C tests persistence beyond the currently clipped sweep; CPU-side
loop/head-state costs may also cause a plateau, so it never proves physical MSHRs.

Repeat: all T=1,2,4,8,16; C=1,16,32,64,128;10other existing groups, total75cells.
Seven trials/cell;256MiB large active footprint;8MiB cache footprint; minimum0.2s
except single cold pass; seed20261006; LLVM22.1.8 `-O3 -std=c++17 -pthread` with
GCC13 header selection. Native timing kernels are unchanged. Increasing heads to
128 costs1KiB/worker, while disjoint rings partition the same total nodes; total
constructed resident storage stays below1.5GiB. Raw cap50MiB; wall cap900s; no
address streams. Physical-core pinning, NUMA first-touch and verified lane required.
Parent rechecks both socket leases, legacy lease, load, memory, source cleanliness
and ≥20GiB free; picks a free lane and retains separate context/lease metadata.

Admission criterion is unchanged: last3distinct-C median M_eff values span≤15%
relative to their median; each dependent/last3cell elapsed spread≤25%; equal
footprints and balanced complete workers. Admit their median only when every
premise holds; otherwise value stays null/unknown and all points remain available.
Use the repeat's own C1 reference latency; do not combine primary/repeat trial rates.
Import a fresh target-description ID/version for every T. Keep primary descriptions
and their hashes. Any later source-normalized-v2 numerator equivalence/correction
gets an explicit pipeline/lineage receipt and does not alter measured wall times.
