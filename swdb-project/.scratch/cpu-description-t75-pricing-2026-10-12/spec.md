# Spec: CPU target description that can price the t75 BFS pair

Created: 2026-10-12 00:42 ET
Updated: 2026-10-12 00:55 ET (aligned with the fine-grained final fixes F40–F47 at `1aa8feeb`:
memmove bins, OpenMP projection group, source-0 later-date timing, split rule v2)
**Type:** spec
**Status:** claimed
**Blocked by:** None
Owner: Yan-Ru Jhou
Builds on: the fine-grained attribution effort (`.scratch/fine-grained-attribution-2026-10-11/`,
tickets 03 and 09 closed negative) and the analytic-eval effort
(`.scratch/lanl-db-analytic-eval-2026-10-06/`, ticket 11 built `services.v1`).
Test seams: confirmed by Yan-Ru 2026-10-12 (bind → estimate main seam).
Map: [map.md](map.md)

## Summary (read this first)

1. **Problem:** `swdb attribute` works, but the real t75 BFS pair has no numbers. Both estimates
   are unknown because the CPU target description `mbit10.cpu.lanl20261006.t1.services.v1`
   cannot price them. So the split (rewritten / untouched / unattributed) is unknown, and the
   split check is `split_unverified`.
2. **Fix:** bind a new description, `services.v2`, that closes four gaps:
   1. **Allowlist:** add the two t75 characterizations.
   2. **Calls with no rate:** add calibrations for them.
   3. **1- and 2-byte stores:** add memory cells.
   4. **Bandwidth rate:** add one for the resource floor.
3. **Order:** freeze `services.v2` before any timing of the t75 uniform22 workload. Then rerun
   ticket 03 (estimate + attribute) and ticket 09 (time + split check).
4. **Done when:** both t75 estimates have non-null seconds and the attribution report has numeric
   shares. A negative result is allowed if it names what is still missing (LR-01).

## Problem Statement

The advisor (Scott) wants to know two things about the t75 native BFS candidate:

- How much did the agent-rewritten code gain?
- How much could the untouched code still gain?

The paper needs that breakdown as a figure. The `swdb attribute` tool answers both, but only when
the estimate has seconds.

Ticket 03 of the fine-grained effort estimated the real t75 pair on mbit10 and got
`seconds: null` on both sides:

- **Baseline:** 16 of 286 regions unknown.
- **Candidate:** 19 of 289 regions unknown.
- **All other regions:** 0 s.

The unknown reasons fall into these groups. The full, script-generated list is
`../fine-grained-attribution-2026-10-11/evidence/03-first-real-pair/unknowns-summary.json`
(made by `unknowns_summary.py` beside it, F41).

| Group | Reasons seen | Kind |
|---|---|---|
| Allowlist | `service_scope.characterization_allowlist`, `memory_scenario.characterization_allowlist` (every unknown region) | Policy: the description admits only the four gapbs g16/g17 counts |
| Calls | `call_cost.*` for OpenMP, allocator, memcpy/memmove, clock, iostream, `strlen`, `indirect-call` | Mostly a cascade of the allowlist failure; some genuinely missing |
| OpenMP projection | `openmp.exact_characterization_projection` | Missing: no sealed projection for the t75 counts |
| Size bins | `call_shape.cost` for `_Znam`/`_ZdaPv` at 16 777 216 / 16 777 220 bytes; `llvm.memmove` at 140, 4 388, 7 300, 9 044, 14 496, 30 164 bytes | Missing: no exact bin at these sizes |
| Memory cells | `memory_scenario.cell.write.1`, `write.2`; primitives `access.107`, `109`, `113` | Missing: no 1- or 2-byte store cells |
| Bandwidth | No `bytes_per_s` in the description | Missing: the resource floor stays unknown |

The allowlist failure hides the real gaps. It nulls the whole `native_service_costs` mechanism,
so calls that *do* have rates (clock, `_Znam`/`_ZdaPv` small bins, memcpy/memmove, most
OpenMP calls) also show as unpriced.

## Solution

A new CPU target description, `mbit10.cpu.lanl20261006.t1.services.v2`, built the same way as
`services.v1`, with four additions:

1. **Allowlist.** The two t75 characterizations from ticket 03
   (`fga03.t75-{baseline,candidate}.uniform22.t1.characterization.a2`) join the allowlist next to
   the four gapbs counts.
2. **Calls.** New calibration receipts for each call that has no rate today. The binder admits
   them like the existing ones.
3. **Memory cells.** New calibration cells for 1-byte and 2-byte stores, so the `alloc_MAA`
   stores get a rate.
4. **Bandwidth.** The measured `bytes_per_s` from the base calibration is carried into the
   description, for the resource floor only.

Everything is bound and committed before any timing of the t75 uniform22 workload, so the
estimates stay prospective. Then the fine-grained tickets 03 and 09 are rerun with
`services.v2`:

1. Freeze new protocols.
2. Estimate both sides.
3. Run `swdb attribute`.
4. Time the workload.
5. Run the split check.

## User Stories

### Getting a number

1. As Yan-Ru, I want both t75 estimates to have non-null seconds, so that the attribution report
   has numeric rewritten, untouched and unattributed shares.
2. As Yan-Ru, I want the new description to admit the two t75 characterizations by exact ID and
   SHA-256, so that no other count is silently admitted.
3. As Yan-Ru, I want the four gapbs g16/g17 characterizations to stay in the allowlist, so that
   `services.v2` still prices the workloads `services.v1` priced.
4. As Yan-Ru, I want `services.v1` left unchanged, so that its error bands and past estimates stay
   valid.
5. As Yan-Ru, I want the binder to compatibility-check every service against every allowlist
   member, so that a calibration that does not fit a t75 count is refused at bind time, not at
   estimate time.

### Calls

6. As Yan-Ru, I want calls that already have a rate (clock, small allocator bins, memcpy/memmove,
   the listed OpenMP calls) to be priced once the allowlist admits the count, so that no new
   measurement is spent on them.
7. As Yan-Ru, I want `malloc` priced by the allocator calibration, so that C allocations are
   costed like `new[]`.
8. As Yan-Ru, I want exact-size allocator bins at 16 777 216 and 16 777 220 bytes, so that the
   two large BFS arrays are priced from a measurement, not interpolated.
9. As Yan-Ru, I want exact `llvm.memmove` bins at the six sizes the t75 counts use, so that those
   copies are priced from a measurement, not interpolated.
10. As Yan-Ru, I want `__kmpc_for_static_init_8u` priced as an OpenMP call, so that 64-bit
   unsigned loops cost the same way as 32-bit ones.
11. As Yan-Ru, I want OpenMP projections for the two t75 characterizations, so that OpenMP sites
    in those counts are priced.
12. As Yan-Ru, I want `strlen`, the iostream calls (`ostream` put/flush/insert,
    `ctype::_M_widen_init`) and `indirect-call` priced from their own calibrations, so that
    every call in the ROI has a measured cost.
13. As Yan-Ru, I want a call that still has no rate to stay unknown with its reason named, so that
    a gap is never priced as 0 s.

### Memory

14. As Yan-Ru, I want 2-byte store cells calibrated, so that the 16-bit volatile stores in
    `alloc_MAA` (primitives 107 and 109) are priced.
15. As Yan-Ru, I want 1-byte store cells calibrated, so that the 8-bit store (primitive 113) is
    priced.
16. As Yan-Ru, I want the new store cells built with the same calibrator and footprint as the
    existing read/write cells, so that they are comparable.

### Bandwidth and the floor

17. As Yan-Ru, I want the description to carry a measured `bytes_per_s`, so that the resource
    floor in the attribution report is numeric.
18. As Yan-Ru, I want that rate to feed only the resource floor, not the estimate, so that adding
    it does not change any estimate's seconds.

### Prospective order and records

19. As Yan-Ru, I want `services.v2` bound, validated and committed before any timing of the t75
    uniform22 workload, so that the estimates are prospective (D26, D35, LR-02).
20. As Yan-Ru, I want new calibration runs to time only microbenchmarks, never the t75
    application, so that no application outcome leaks into the description.
21. As Yan-Ru, I want the bind command recorded as a runbook, like the `services.v1` runbook, so
    that the description can be rebuilt.
22. As Yan-Ru, I want every new calibration receipt kept as a record with its machine record and
    load, so that each rate can be traced to a run.
23. As Yan-Ru, I want the whole record store to validate after the new records are added, so that
    nothing downstream breaks.

### Rerun

24. As Yan-Ru, I want ticket 03 rerun with new protocols that pin `services.v2`, reusing the saved
    prospective requests and counts, so that no recount is needed.
25. As Yan-Ru, I want the estimate order recorded (estimate both sides, then time), so that the
    estimates are provably prospective.
26. As Yan-Ru, I want ticket 09's split check run on the same workload ID, source 0 only, on a
    later date than both estimates, under rule `swdb.split_check.v2`, so that the real split gets
    a `passed` or `failed` verdict that `swdb validate` accepts.
27. As Yan-Ru, I want the real attribution report saved, so that it can feed the paper figure and
    the site-finder ordering.
28. As Yan-Ru, I want a negative close that names every remaining gap if an estimate is still
    unknown, so that the next effort starts from a precise list.

## Implementation Decisions

Decisions are numbered C1–C14 so tickets can cite them.

### The description

- **C1 — New record, same binder.** `services.v2` is a new target description built by the
  existing CPU service binder from the same base calibration (`mbit10.cpu.lanl20261006a2.v2.t1`),
  the same nine calibrations and policies as `services.v1`, plus the additions below.
  `services.v1` is not edited.
- **C2 — Allowlist.** The scope characterizations are the four gapbs counts plus
  `fga03.t75-baseline.uniform22.t1.characterization.a2` and
  `fga03.t75-candidate.uniform22.t1.characterization.a2`, pinned by `{id, sha256}`. The primary
  characterization stays the BFS kron g16 count. The binder checks every service against all six.
- **C3 — Team-safe gate.** The binder runs `require_team_safe` over its inputs. The t75
  candidate is an Extensa-mode candidate. The first ticket checks that its characterization's
  whole lineage passes. If it does not, stop and report before any calibration work; do not
  weaken the gate.

### Calls

- **C4 — Cascade first.** Before any new calibration, bind a trial description with only the
  allowlist change (C2) and estimate both t75 sides. Run `unknowns_summary.py` on the trial
  estimates; its output is the real list of call and bin gaps. Only those get new calibration work. The trial description is a
  scratch record and is not committed.
- **C5 — `malloc`/`free`.** Extend the allocator calibrator's ABI list and the binder's allocator
  fields to include the C allocator calls that the t75 counts use.
- **C6 — Large allocator bins.** The allocator calibrator caps sizes at 1 MiB. Add exact bins at
  16 777 216 and 16 777 220 bytes, measured independently before the freeze. No interpolation
  from smaller bins (calibration doc: "New or unmatched allocator length/lifetime bins stay
  unknown"). Same rule for the six `llvm.memmove` sizes (140, 4 388, 7 300, 9 044, 14 496 and
  30 164 bytes): exact bulk bins, measured before the freeze.
- **C7 — OpenMP.**
  - Add `__kmpc_for_static_init_8u` to the OpenMP profiles with its own ABI class.
  - Produce sealed OpenMP call projections for the two t75 characterizations with the existing
    projection script.
- **C8 — Library and indirect calls.** Add one calibration family, "library call service", for
  `strlen`, the iostream calls and `ctype::_M_widen_init`. It is measured per call with paired
  receipts, like the clock service. `indirect-call` gets a receipt for the call overhead only;
  the callee's work is counted where it is defined.
- **C9 — Still-missing stays unknown.** Any call left without a rate after C5–C8 stays
  `call_cost.<name>` unknown. Nothing is priced as 0 s.

### Memory

- **C10 — 1- and 2-byte stores.**
  - Extend the memory calibrator to widths {1, 2, 4, 8} for both reads and writes.
  - Extend the evaluator's memory construction to accept the 1-byte and 2-byte write regimes.
  - Use the same footprint (8 388 608 bytes) and the same calibration procedure as the existing
    cells.

### Bandwidth

- **C11 — Floor-only rate.** Carry the base calibration's measured `bytes_per_s` into
  `services.v2` as a resource rate that the attribution resource floor reads. Do not add
  `streaming_bandwidth` back as an estimate mechanism; `services.v1` superseded it with the
  memory scenario. Adding a bandwidth rate must leave every estimate's seconds unchanged.

### Order and records

- **C12 — Freeze order.** All calibration runs, then the bind, then `swdb validate`, then commit
  and push `services.v2`. All of this happens before any timing of workload
  `bfs-20261004-uniform22.2f83a134a6bef789` with either t75 binary.
- **C13 — Rerun.**
  - Reuse the saved requests `fga03.t75-{baseline,candidate}.uniform22.t1.request.a1.yaml`.
    They do not pin a description.
  - Freeze new protocols (`.a3`) that pin `services.v2`, and estimate both sides.
  - Both estimates use the same estimator commit, so they share `estimator_sha256` (F47).
  - Then run ticket 09's timing recipe on a later date than both estimates (F43):
    - LLVM 22 `clang++`, evaluator v3, 20 repetitions.
    - Source 0 only. F44 requires the profile's machine, sources and seed to match the counted
      characterization.
    - Use the kept counted binaries on mbit10
      (`/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/`, 65.7 MB).
  - The split check uses rule `swdb.split_check.v2`: each region keeps its full seconds, call
    time included (F40).
- **C14 — Error band.** `services.v2` has no error band; the existing four bands pin
  `services.v1`. Per D25, an unvalidated band gives `within_error`. This effort does not build a
  band. The split check (F19) and the attribution report do not need one.

## Testing Decisions

A good test checks behavior at the seam: given records in, which estimate or report comes out.
Do not test private helpers or record layout beyond what the seam returns.

**Seam 1 (main): bind, then estimate.** Bind a description from calibration receipts and scope
characterizations, then estimate a fixture characterization that contains the new calls and
stores. Check:

1. Seconds are non-null when every service is covered.
2. Each new service (malloc, 16 MiB bins, memmove bins, `_8u`, library calls, 1- and 2-byte stores) contributes
   priced seconds.
3. A characterization outside the allowlist is still refused.
4. A call with no receipt stays unknown with `call_cost.<name>`.
5. Adding the floor-only bandwidth rate leaves the estimate's seconds unchanged.

Prior art: `tests/test_cpu_service_binding.py`
(`test_binding_freezes_exact_outcome_free_characterization_allowlist_and_checks_every_member`),
`tests/test_analytic_cpu_service.py`
(`test_exact_characterization_allowlist_admits_only_named_counted_scope`,
`test_exact_size_service_bins_require_full_site_coverage`),
`tests/test_cpu_memory_service_binding.py`, `tests/test_cpu_openmp_binding.py`,
`tests/test_analytic_cpu_openmp.py`.

**Seam 2: calibrator runners → receipt records.** Each extended runner (allocator with C calls and
16 MiB bins, memory with widths 1 and 2 for writes, the new library-call family) writes a receipt
that validates against its schema and that the binder admits. Use the existing calibrator tests as
prior art.

**Seam 3 (existing): attribution floor.** With a description that carries `bytes_per_s`, the
resource floor is numeric and below the estimate. Prior art: `tests/test_attribution.py`
(`test_a_missing_bandwidth_rate_gives_an_unknown_floor_with_a_reason_not_zero`,
`test_resource_floor_is_below_the_estimate…`).

**Real check (acceptance, not a unit test).** The rerun of tickets 03 and 09 on mbit10 with the
real records. Follow the Mac memory rules for the full suite and the whole-store check (about
7 GB RAM, about 50 min).

## Out of Scope

- Editing `services.v1` or its four error bands.
- Building an error band for `services.v2`.
- Recounting the t75 binaries. The ticket-03 characterizations are reused.
- Workloads other than the t75 pair on uniform22.
- Thread counts other than T1.
- Hardware counters (unavailable to `yanruj` on mbit10).
- Using any gem5 or Extensa simulator number in the description (ADR 0013).

## Further Notes

- **Risk labels B1/B3.** The fine-grained tickets say "risk B1" (allowlist) and "risk B3"
  (bandwidth rate) but never define them. This spec uses the plain names instead.
- **Cost of the trial bind (C4).** It is the cheapest step and may shrink the call work a lot:
  the allowlist failure alone explains most `call_cost.*` reasons.
- **Disk.** Calibration output goes under `/data1/yanruj/EvolveSWDB_runs/` (or `/data` if
  `/data1` has under 20 GB free). Raw output never enters git. The kept ticket-03 binaries stay
  on mbit10 until ticket 09's rerun finishes, then follow LR-06.
- **Lanes.** Calibration and timing runs go through the socket-lane procedure (`mbit10-runs`
  skill).
- **Time estimate:**
  - Trial bind and cascade check: about 2 hours.
  - Calibrator extensions and runs: about 1–2 days of agent work.
  - Bind, freeze and rerun: about half a day (each protocol freeze takes about 50 min).
