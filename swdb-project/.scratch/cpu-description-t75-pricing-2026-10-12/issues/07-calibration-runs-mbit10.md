# 07 — Calibration runs on mbit10

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** resolved
**Blocked by:** 01, 02, 04, 05, 06
**Spec:** `../spec.md` (C5–C8, C10, C12; user stories 20, 22)
**Code map:** `../notes/ops.md`, `../notes/bulk.md`

**Time estimate:** about 2–3 hours of lane time.

## What to do

From a clean, pushed commit, in a free lane, raw output under `/data/yanruj/EvolveSWDB_runs/`
(`/data1` is near 20 GB), measure only the gaps that ticket 01 confirmed:

- `memory_v2` cells (write 1, write 2);
- allocator v2 cells (malloc sizes, 16 MiB `new[]`/`delete[]` bins);
- OpenMP a2 (`_8u`);
- library-call family and `indirect-call`;
- one new bulk-total batch for the six `llvm.memmove` sizes (no code change, `../notes/bulk.md`).

Microbenchmarks only: never run a t75 binary (C12). Export compact receipts as records with their
machine record and load; raw output never enters git. Write a runbook like the `services.v1` runbook.

## Acceptance

- [x] Every new receipt is a committed record with its lane record and load.
- [x] Targeted `swdb validate` of the new records passes; the whole-store check runs once on mbit10.
- [x] Runbook saved in `evidence/07-calibrations/`.

## Answer

Updated: 2026-10-12 15:50 ET. Branch `cpud/07-calibrations`. Runbook and compact evidence:
[`evidence/07-calibrations/`](../evidence/07-calibrations/README.md).

**Short version.** All five gaps are measured on mbit10 and imported as 8 committed records.
Targeted validation passes, and the whole store passes on mbit10 (`OK: 722 record(s) valid`).
One runner bug was found and fixed (library-call pilot headroom). Ticket 08 binds the 5 IDs below.

### Records for ticket 08 (`--calibration`)

| Bind this | Source record | File sha256 (bind / source) |
|---|---|---|
| `mbit10.cpu.lanl20261006.resource.memory-v2.a1` | `…service.memory-v2.a1` | `2b6a8693…` / `a068b637…` |
| `mbit10.cpu.lanl20261006.resource.allocator-v2.a1` | `…service.allocator-v2.a1` | `88e09c2b…` / `5130dec1…` |
| `mbit10.cpu.lanl20261006.service.openmp.a2` | (itself; class 22 only) | `10d895c7…` |
| `mbit10.cpu.lanl20261006.service.library-call.a1` | (itself; 7 services) | `add24743…` |
| `mbit10.cpu.lanl20261006.resource.bulk-total.a3` | `…service.bulk-total.a3` | `1d2b525c…` / `7c370ce2…` |

- Keep `service.openmp.a1` (classes 0–21) and `--bulk-copy-calibration …resource.bulk-total.a1`
  (batch a3 also measures the memcpy8 cell).
- Full hashes: [`targeted-validate.json`](../evidence/07-calibrations/targeted-validate.json).
  Raw receipt and count-proof hashes: [`raw-hashes.txt`](../evidence/07-calibrations/raw-hashes.txt).

### Measured values (median per event, 7 trials)

| Cell | Value | Spread (max−min)/median |
|---|---|---|
| write 1 B @ 8 MiB (gross resource) | 0.694 ns | 0.3% |
| write 2 B @ 8 MiB (gross resource) | 0.575 ns | 1.3% |
| `malloc` 64 / 128 / 6 144 / 2 097 152 B | 7.7 ns / 48.1 ns / 1.32 µs / 1.67 µs | ≤ 3.6% |
| `new[]` 16 777 216 / 16 777 220 B | 1.63 / 1.69 µs | 2.9% / 6.5% |
| `delete[]` 16 777 216 / 16 777 220 B | 1.45 / 1.60 µs | ≤ 3% |
| OpenMP class 22 `__kmpc_for_static_init_8u` | 6.37 ns | **32%** (one 8.3 ns trial) |
| `strlen` / `put` / `flush` | 1.62 ns / 8.37 ns / 1.43 µs | ≤ 4% |
| `__ostream_insert` / `_M_insert<unsigned long>` / `_M_widen_init` | 23.2 / 32.4 / 49.2 ns | ≤ 3% |
| `indirect-call` | 0.58 ns | 2% |
| memmove envelope 140 / 4 388 / 7 300 / 9 044 / 14 496 / 30 164 B | 9.2 / 46.3 / 69.1 / 86.6 / 136.8 / **701.9** ns | see below |

### Lanes, load and timing

- Every measurement ran in the **node1** lane (lease generations 558, 559, 561), one job at a time.
  Node0 was held all day by other sessions' test suites, so the planned two-lane split was not possible.
- Host load1 was 5.8–9.0 during measurements: the other socket ran a `pytest -n 6` suite. Each
  receipt records its own start and end load; lane records are `lane-{a,b,l}.json`.
- Lane time: about 2.5 h. Each calibrator step took 11–15 min, of which about 5–10 min is loading
  the 1.1 GB store (3.8 GB RSS). Each import took about 21 min (whole-store check inside, 7.1 GB
  RSS). Targeted check 6 min; whole-store check 14.5 min, 3.9 GB. Details: `step-times.tsv`, `order.log`.
- Sources: memory, allocator, OpenMP and bulk at `598232ca`; library-call at `f2d41156` (the fix
  below). All from clean detached worktrees; every receipt says `dirty: false`.
- No t75 binary ran, and `bfs-20261004-uniform22` was not timed (C12).

### Surprises and noisy cells

1. **Runner bug (fixed, `f2d41156`).** Library-call attempt 1 failed validation: the strlen pilot
   driver took 0.052 s, then every warm trial took 0.042–0.046 s, below `min_trial_s`. The pilot now
   needs 1.25x headroom, like the OpenMP and allocator runners. New test:
   `test_pilot_keeps_headroom_so_warm_trials_still_resolve_min_trial`. Library-call tests: 5 passed (Mac).
2. **memmove 30 164 B, disjoint profile: 701 ns with 19% spread.** The forward and backward
   profiles at the same size take 281–283 ns, with spread ≤ 1%. The envelope is the max of the three
   profiles, so the 30 164 B bin is priced at 702 ns. Plausibly a copy-path change (e.g. `rep movsb`
   or 4K aliasing) for that size and alignment. It is one execution per side in t75, so the effect
   on the estimate is ≤ 0.5 µs.
3. **OpenMP class 22 has a 32% spread** (6.28–8.34 ns): one outlier trial; the median is stable.
4. **`malloc` 6 144 B costs 1.32 µs**, about 170x the 64 B cell. Most likely each batch frees
   enough to trim the heap top, so the next batch's allocations fault in fresh pages. This is the
   allocator-regime caveat from ticket 04 (`transfer_basis: inferred`); t75 calls it once.
5. **1-byte stores are 21% slower than 2-byte stores** (0.694 vs 0.575 ns). The 2-byte value equals
   the v1 4- and 8-byte cells (0.581 and 0.575 ns).
6. The memory and bulk *service* records keep their paired values null (gross minus driver is about
   0); the gross *resource* records carry the prices, as in `services.v1`.

### Native OpenMP tests (ticket 05)

**Both tests still fail on mbit10, and not because of the host.** The real count-only proof passed.

- **The real proof passed.** The ticket-07 count-only run (`openmp-a2-count`) gave format
  `swdb.cpu-openmp-count-only.v1`, `timings_collected: false`, 23 classes, 4 points and 23
  projected sites. These are the first test's main assertions. The receipt validator and the import
  then admitted the a2 receipt.
- **Attempt 1** (node1 lane) failed in 2 s with `'cstddef' file not found`. The tests pass no
  toolchain flag, and clang 22 on mbit10 picks GCC 14, which has no libstdc++ headers.
- **Attempt 2** used a wrapper bin folder that adds the `--gcc-install-dir` flag every real run uses.
  - It ran pinned to socket 0 with `numactl`, without a lease. Both leases were held for hours by
    other sessions' test suites (not measurements). Assumption: a 2-test pytest is not a measurement.
  - Both tests then hit the helper's 240 s subprocess timeout
    ([`openmp-native-tests-attempt2.txt`](../evidence/07-calibrations/openmp-native-tests-attempt2.txt)).
  - **Cause:** each test copies the full 1.1 GB repo store (`records.copy_repo()`). On mbit10, loading
    that store takes 5–10 min (the real count run took 11.5 min). The Mac hits the same limit.
- **Follow-up (not done here):** give these tests a minimal store, or a larger budget, plus a toolchain-flag
  input (for example an env var) for Linux hosts.

### Cleanup (LR-06)

After the records were committed and their hashes recorded, everything this ticket made on mbit10 was deleted:
- the raw root `/data/yanruj/EvolveSWDB_runs/cpud07-20261012-a1/` (receipts, count proofs, 3 store copies, pytest temp);
- both worktrees (`/data/yanruj/ArchEvolve-cpud07-{598232ca,f2d41156}`).

No other session's folder was touched. Free space at the end: `/data1` 22 GB, `/data` 61 GB.
Other sessions' test runs are filling `/data`; it had 94 GB at 10:47 ET.
