# 09 — Rerun ticket 03: estimate the t75 pair with services.v2

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** resolved
**Blocked by:** 08
**Spec:** `../spec.md` (C13 (estimate half); user stories 1, 24, 25, 27, 28)
**Code map:** `../notes/ops.md`

**Time estimate:** about 2.5 hours (two freezes + two estimates).

## What to do

Reuse the saved `fga03.t75-{baseline,candidate}.uniform22.t1.request.a1.yaml` and the a2
characterizations (no recount). Freeze `.a3` protocols that pin `services.v2`, both at the same
commit (F47), estimate both sides (`.a3`), run `swdb attribute` (unchecked report). Log the order
(estimates before any timing).

## Acceptance

- [x] Both estimates have non-null seconds, or `## Answer` closes negative with every remaining gap named (parameterized unknowns summary).
- [x] Attribution report with numeric rewritten/untouched/unattributed shares saved as a record.
- [x] Records committed and pushed; order log saved in `evidence/09-rerun-03/`.

## Answer

Resolved: 2026-10-12 21:55 ET. Branch `cpud/08-09-bind-estimate`. Runbook and evidence:
[`evidence/09-rerun-03/`](../evidence/09-rerun-03/README.md).

**Short version.** Both t75 estimates are numeric, with 0 unknown regions. The attribution report
has numeric shares and a numeric resource floor in every region. Positive close.

### Estimates (`services.v2`, frozen and estimated at `c9f9df67`)

| Side | Estimate | Seconds | Regions (unknown) | Created (ET) |
|---|---|---|---|---|
| Baseline | `fga03.t75-baseline.uniform22.t1.estimate.a3` | **26.643** | 286 (0) | 2026-10-12, ended 20:13 |
| Candidate | `fga03.t75-candidate.uniform22.t1.estimate.a3` | **20.770** | 289 (0) | 2026-10-12, ended **20:40:38** |

- Protocols: `…protocol.a3.badeda2d2d43b04b` (baseline), `…protocol.a3.40eae3eb40b5a110` (candidate),
  both frozen in one lane job at `c9f9df67` (F47). Shared `estimator_sha256` `fcc40da1…`; shared
  `target_description_sha256` `edd7913d…`.
- Unknowns summary (`unknowns-summary-a3.json`): 0 unknown regions per side; it agrees with each
  estimate's `parameter_report` and across trials.
- **Ticket 10:** time on **2026-10-13 ET or later** (F43 compares ET dates).

### Attribution (`records/attributions/fga03.t75.uniform22.t1.attribution.a3.yaml`, unchecked)

| Origin | Baseline s (share) | Candidate s (share) | Realized speedup |
|---|---|---|---|
| Agent-rewritten | 24.912 (**93.50%**) | 19.040 (**91.67%**) | 1.308x |
| Untouched | 1.730 (**6.49%**) | 1.730 (**8.33%**) | 1.000x (drift 1.000) |
| Unattributed | 0.00039 (**0.0015%**) | 0.00039 (**0.0019%**) | — |

- Whole program: total speedup **1.283x**; Amdahl ceiling 15.4x (the rewritten share driven to 0);
  unattributed below the 10% flag.
- Nearly all rewritten time is one region per side: `TDStep` (24.37 s baseline, 18.20 s candidate).

### Resource floor

- Numeric in all 286 + 289 regions. Sum of region floors: **0.197 s** (baseline), **0.206 s**
  (candidate). Every region is compute-throughput-limited.
- The bandwidth term (15 071 467 834 B/s, floor-only) sums to 0.010 s / 0.018 s, below compute.
- Hot `TDStep` floor: 0.176 s against 24.37 s / 18.20 s estimated, so the floor is far below the
  estimate (memory-latency time is not in a floor term by design, F6).

### Two attribute runs (assumption, stated)

- The first run at `c9f9df67` had the same shares, but an **unknown floor in 9 regions per side**
  (including both `TDStep`s): `access.N.streaming_classification`, because `services.v2` has no
  `cache_fit`/latency model to cover indirect accesses.
- Review fix F1 (`bf21f94d`, in `cpud/integration` `4324b546`) lets `memory_service_scenario`
  cover them for floor-only rates. I reran `attribute` with that code on the **same saved
  estimates** (estimates and protocols untouched). That report is the record; the first one is kept
  as evidence in `first-attribute-c9f9df67/`.

### Remaining gaps and caveats (none block the numbers)

1. **No error band for `services.v2`** (C14): the estimates have no validated band.
2. **No catalog bound:** no site finder was passed, so the ranking has only the floor-headroom tier.
3. **Inferred transfers:** allocator regime (`malloc` 6 144 B at 1.32 µs), memmove 30 164 B
   (702 ns, noisy disjoint profile) and OpenMP class 22 (32% spread) carry ticket 07's caveats.
   Each is one or a few executions per side; none moves the totals visibly.
4. Ticket 10 (timing, checked report, split check) is still to run.
