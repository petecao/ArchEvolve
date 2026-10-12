# 01 — Team-safe check, t75 OpenMP projections and the trial bind

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** ready-for-agent
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

- [ ] Team-safe output saved in `evidence/01-trial-bind/`.
- [ ] Two t75 OpenMP projection records committed and `swdb validate` accepts them (targeted check).
- [ ] Trial unknowns summary saved: the real list of call, bin, projection and memory gaps once the allowlist admits the counts.
- [ ] `## Answer` lists which planned calibration items (tickets 04–07) are still needed and any new gap not in the spec.
