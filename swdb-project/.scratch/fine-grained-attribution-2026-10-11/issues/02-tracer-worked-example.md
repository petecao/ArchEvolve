# 02: First working version: the worked example end to end

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** claimed
**Blocked by:** 01 — Review and commit design
**Spec:** `../spec.md` (F1, F3–F5, F8, F17, F18, F22; seam 1)
**Time estimate:** about half a day

**What to build:** A public `swdb attribute` command takes a baseline estimate, a candidate estimate and their two source snapshots, computes the diff itself, finds rewrite sites, labels each region untouched, agent_rewritten or unattributed by file and line, and writes one validated `swdb.attribution.v1` record that is indexed into `swdb_`-prefixed SQLite tables. The record holds per-group baseline and candidate seconds, shares, realized speedup, untouched drift, total speedup and the Amdahl ceiling, composed per trial and then medianed. This is the narrowest complete path; later tickets widen it.

## Acceptance

- [ ] The 100 s / 60% / 40% fixture gives hand-computed shares, speedups, drift and Amdahl ceiling 2.5×.
- [ ] A loop without a catalog loop ID but with a source line gets a real label, not unattributed.
- [ ] One unknown region makes its group and dependent whole-program fields unknown, with reasons.
- [ ] Group medians are not rescaled to sum to the total.
- [ ] Mismatched inputs are refused; identical inputs give a byte-identical record.
- [ ] The record pins the hashes of both estimates, both snapshots and the target description.
- [ ] `swdb validate` passes and the SQLite tables hold the groups.
- [ ] Tests go only through the command.
