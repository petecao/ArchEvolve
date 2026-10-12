# 01 — Team-safe check, t75 OpenMP projections and the trial bind

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` (C3, C4, C7 projections)
**Code map:** `../notes/binder.md`, `../notes/openmp.md`, `../notes/ops.md`

**Time estimate:** about 3–4 hours (two protocol freezes at ~50 min each dominate).

## What to do

1. **C3.** Record that `require_team_safe` passes for both t75 characterizations, the base
   calibration and `services.v1` (the code map already checked this on the Mac; keep the output as evidence).
   If it fails, stop and report; do not weaken the gate.
2. **C7 projections.** Produce sealed OpenMP call projections for
   `fga03.t75-{baseline,candidate}.uniform22.t1.characterization.a2` with the existing projection
   script. They are counted-scope records (no timing), so they are committed as real records: the
   binder needs one per allowlisted characterization (`cpu_openmp_binding.py:19`), including for the trial.
3. **Parameterize the summary.** Copy `unknowns_summary.py` into this effort's `evidence/01-trial-bind/`
   with arguments for the estimate IDs, records root and output path. Do not touch the committed fga03 copy or its JSON.
4. **C4 trial.** On mbit10 (a free lane, scratch store under `/data/yanruj/EvolveSWDB_runs/`), bind a trial
   description = `services.v1` inputs + the two t75 characterizations in the allowlist (C2), nothing else.
   Freeze trial protocols and estimate both sides in the scratch store. Run the parameterized summary.
   The trial description, protocols and estimates are **not** committed (keep only compact evidence: summary JSON, order log, lane record).
5. No timing of workload `bfs-20261004-uniform22.2f83a134a6bef789` with either t75 binary (C12).

## Acceptance

- [x] Team-safe output saved in `evidence/01-trial-bind/`.
- [x] Two t75 OpenMP projection records committed and `swdb validate` accepts them (targeted check).
- [x] Trial unknowns summary saved: the real list of call, bin, projection and memory gaps once the allowlist admits the counts.
- [x] `## Answer` lists which planned calibration items (tickets 04–07) are still needed and any new gap not in the spec.

## Answer

Updated: 2026-10-12 05:40 ET. Branch `cpud/01-trial-bind`. Evidence: [`evidence/01-trial-bind/`](../evidence/01-trial-bind/).

**Short version.** Team-safe passes. Both t75 projections exist and pass the binder. With the
allowlist fixed, unknown regions drop from 16 → **6** (baseline) and 19 → **6** (candidate).
Every remaining gap is already planned in tickets 02 and 04–07. Nothing on that list can be dropped.
One new gap, already fixed: the OpenMP projector could not read the t75 counts.

### 1. C3 team-safe: pass

`require_team_safe` passes for both t75 counts, the base and `services.v1`, and for all 16
trial-bind inputs together (mbit10, commit `cce7be7b`):
[`team-safe-mbit10-20261012-a1.json`](../evidence/01-trial-bind/team-safe-mbit10-20261012-a1.json).
The trial bind ran the same gate again and passed.

### 2. C7 projections: committed

- Files: [`openmp-t75-baseline-projection-mbit10-20261012-a1.json`](../evidence/01-trial-bind/openmp-t75-baseline-projection-mbit10-20261012-a1.json)
  and [`openmp-t75-candidate-projection-mbit10-20261012-a1.json`](../evidence/01-trial-bind/openmp-t75-candidate-projection-mbit10-20261012-a1.json).
  Each has 9 executed `__kmpc_*` sites and 1 530 call sites, all cross-checked.
- Targeted check: [`projection-check.json`](../evidence/01-trial-bind/projection-check.json)
  (script `check_projections.py`) applies the binder's per-document rules. Both pass:
  identity, characterization `{id, sha256}`, source IR, executed-site union, compiler hash, no execution.
- The binder accepted both (trial bind, 0 of 216 compatibility rows with a missing item).
  The scratch store with the trial description passed the whole-store check inside both
  `freeze-protocol` runs.
- Projections are JSON evidence, not `records/` entries, like the four g16/g17 ones. Ticket 08 passes
  them with `--openmp-projection`.
- Profile match: 8 of 9 sites map to existing classes. Site 84 (`__kmpc_for_static_init_8u`, in
  `TDStep….omp_outlined`) maps to none. Its literals are ident 514, schedtype 34, and 64-bit incr/chunk 1.
  That is exactly the `_8` profile shape, so ticket 05's "mirror `_8`" guess holds.

### 3. New gap (not in the spec), fixed here

- **What happened:** the projector refused both t75 counts with "call map mismatch at 1119".
- **Cause:** since `ba29ceec` (2026-10-10), `Characterize.cpp` counts pure intrinsics
  (`llvm.ctlz`, `ctpop`, `fabs`, `umax`, …) as operations, not call sites. `OpenMPCallProjection.cpp`
  still enumerated them as calls, so its site numbers drifted. The t75 count has `llvm.ctlz.i64` in `MakeCSRInPlace`.
- **Fix (commit `cce7be7b`):** the projector now skips the same intrinsic list.
- **Tests:** a fixture test (`tests/fixtures/analytic/openmp_abi_pure.cpp`) and a guard test that
  both C++ lists stay equal (`tests/test_openmp_call_projection.py`, 12 passed on the Mac).
- **Effect on old projections:** none. The four g16/g17 projections predate `ba29ceec`, and
  nothing pins `projector_source_sha256`.

### 4. C4 trial: the real gap list

- **Trial description:** `mbit10.cpu.lanl20261006.t1.services.cpud01-trial.a1` (sha256 `ec326628…`).
  It equals the `services.v1` inputs plus the two t75 counts and their projections.
  Pinned in [`trial-description-receipt.json`](../evidence/01-trial-bind/trial-description-receipt.json).
- **Protocols:** frozen in a scratch store (`…trial-a1.4994e86b6d3d6ef6`, `…trial-a1.620dd3e002a2d764`).
  Neither the description nor the protocols are committed.
- **Summary:** [`unknowns-summary-trial.json`](../evidence/01-trial-bind/unknowns-summary-trial.json).
  Per-region terms: [`unknown-regions-trial.json`](../evidence/01-trial-bind/unknown-regions-trial.json).
  Both sides share `estimator_sha256` `617197bb…`.

| Region (both sides) | Real gap | Ticket |
|---|---|---|
| `serial.16002…` | `malloc` at 64 (×2), 128, 6 144, 2 097 152 B: no rate | 04 |
| `alloc_MAA.39.0` | 1-byte store: `cell.write.1`, primitive 113 | 02, 07 |
| `alloc_MAA.33.1` | 2-byte store: `cell.write.2`, primitives 107, 109 | 02, 07 |
| `serial.12991…` | `__kmpc_for_static_init_8u` (`openmp.unsupported_abi_class`); `llvm.memmove` bins 140, 4 388, 7 300, 9 044, 14 496, 30 164 | 05; 07 (bulk batch) |
| `serial.99548…` | `_Znam`/`_ZdaPv` at 16 777 216 and 16 777 220; `strlen`, `__ostream_insert`, `ctype::_M_widen_init`, `put`, `flush`, `indirect-call` | 04; 06 |
| `DOBFS.180.0` / `DOBFS.207.0` | `strlen`, `__ostream_insert`, `ostream::_M_insert<unsigned long>`, `put`, `flush` | 06 |

**Cascades, not real gaps.** A region's whole `native_service_costs` term goes unknown if any one
call in it is missing (`analytic_cpu_service.py:105`). So `call_cost.__kmpc_for_static_fini`,
`call_cost.llvm.memmove…`, `call_cost._Znam` and `call_cost._ZdaPv` clear once the items above are priced.
`fini` has profile 10 and is priced in every other region.

**Already priced now:** clock, `memcpy`, small allocator bins (incl. `_Znam` 524 288 B), and the other
OpenMP sites (`fork_call` n=2/4/7, `static_init_4`, `fini`). Every other region is numeric:
280 of 286 on the baseline and 283 of 289 on the candidate.

### 5. What tickets 04–07 still need (nothing can be dropped)

- **02 / 07:** write widths 1 and 2 are both needed.
- **04:**
  - `malloc` at exactly 64, 128, 6 144 and 2 097 152 B.
  - `_Znam`/`_ZdaPv` at 16 777 216 and 16 777 220 B.
  - `free` is not executed in the ROI, so do not add it.
- **05:** `_8u` is needed. Exactly one site (84) per side. Mirror the `_8` profile literals.
- **06:**
  - The call list is 6 library ABIs: `strlen`, `_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l`,
    **`_ZNSo9_M_insertImEERSoT_`** (`ostream::_M_insert<unsigned long>`), `_ZNSo3putEc`, `_ZNSo5flushEv`,
    `_ZNKSt5ctypeIcE13_M_widen_initEv`.
  - Plus `indirect-call` (1 site, 1 execution).
  - Ticket 06's "ostream put/flush/insert" must name **both** insert symbols.
- **07:** the bulk batch for the six memmove sizes is needed.
- **Ticket 08 bind:** add the two projections from this folder.

### 6. Run notes and assumptions

- **Where:** node1 lane (leases 553–556) via `Memacc-evolveswdb-lane` `socket_lane.sh` (same hash as
  `origin/yanrujhou_main`). The `/data1/yanruj/Memacc` checkout has no `socket_lane.sh`.
  Order log: [`order.log`](../evidence/01-trial-bind/order.log).
- **Timings:** bind 20 min; each freeze about 55 min.
- **Disk failure:** the candidate freeze wrote and validated its protocol (03:32 ET), then exited 120 at
  03:38 ET. **/data had reached 0 bytes free.** The cause is another session's full-suite pytest
  basetemp (`/data/yanruj/EvolveSWDB_runs/swdb-full-suite-20261011-a1/bt`, 90 GB, still running
  at 05:12 ET). I did not touch it.
- **Assumption (estimates in memory):** committing two 65 MB estimates plus the sqlite rebuild fit on
  neither disk (/data full; /data1 at 21 GB vs. the 20 GB floor). So both trial estimates ran in
  memory: the exact `swdb.analytic.estimate` path, with only `writer.commit` replaced by a capture
  (`dry_estimate_summary.py`, `run-trial-dry.sh`). This is allowed because the trial estimates are not
  committed anyway. Two runs gave identical results; 6 min per side.
- **No application timing:** workload `bfs-20261004-uniform22` was not timed with any binary (C12).
- **Cleanup:** the scratch worktree and raw output (2.2 GB on /data, 212 KB on /data1) were deleted.
  The trial `bind.json` sha256 before deletion: `a7bc2f8d…`.
