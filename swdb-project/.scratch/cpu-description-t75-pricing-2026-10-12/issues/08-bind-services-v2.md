# 08 — Bind, validate and freeze services.v2

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** resolved
**Blocked by:** 03, 07
**Spec:** `../spec.md` (C1, C2, C9, C11, C12, C14; user stories 2–5, 19, 21, 23)
**Code map:** `../notes/binder.md`

**Time estimate:** about 2 hours.

## What to do

Bind `mbit10.cpu.lanl20261006.t1.services.v2` with the existing binder: same base calibration and
inputs as `services.v1` (runbook 11 command), plus the six-member allowlist (four gapbs + two t75
by `{id, sha256}`), the t75 OpenMP projections, every ticket-07 receipt and the floor-only bandwidth
field. `services.v1` stays unchanged. No error band (C14). Then whole-store `swdb validate`
(mbit10), commit and push — all before any t75 timing (C12).

## Acceptance

- [x] `services.v2` committed and pushed; `services.v1` byte-identical.
- [x] Whole-store validate passes (output saved).
- [x] Bind runbook saved in `evidence/08-bind/`.

## Answer

Resolved: 2026-10-12 17:55 ET. Branch `cpud/08-09-bind-estimate`. Runbook and evidence:
[`evidence/08-bind/`](../evidence/08-bind/README.md).

**Short version.** `services.v2` is bound, validated on mbit10 and committed. `services.v1` is
byte-identical. Every compatibility row passes, so the t75 counts are admitted with no
`calibration_admission` hold.

- **Record:** `records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v2.yaml`,
  file sha256 `70fc555390552fad5c150e53d9ff9ecc9d3262a1a8d3f9eb908aab7b10e4b66a`
  (`version` `c55908ad…`).
- **`services.v1`:** sha256 `cee03869…` before and after; `cmp` equal in the bind store.
- **Allowlist (C2):** six `{id, sha256}` members: the four gapbs g16/g17 counts, then
  `fga03.t75-{baseline,candidate}.uniform22.t1.characterization.a2`. Primary stays BFS kron g16.
- **Inputs (C1):** the `services.v1` runbook-11 arguments, plus the five ticket-07 records, the two
  t75 OpenMP projections from ticket 01, and the new ID. 14 calibrations in all.
- **Compatibility:** 252 rows (every service against all six members), **0 with a missing item**.
- **Floor-only bandwidth (C11):** `resource_floor_mechanisms[0]` = `streaming_bandwidth`,
  `bytes_per_s` 15 071 467 833.99 B/s (measured), carried from `mbit10.cpu.lanl20261006a2.v2.t1`
  and pinned to `mbit10.cpu.lanl20261006a2.v2.calibration.t1`. No `streaming_bandwidth` estimate
  mechanism.
- **No error band (C14).**
- **Whole-store validate (mbit10):** `OK: 723 record(s) valid` (13 min 46 s, 3.9 GB).
- **Lane:** node0, lease generation 519, through `socket_lane.sh`. Bind 20 min 20 s, 7.1 GB.
- **Order (C12):** bind → validate → commit → push, before any t75 timing. No application ran.

**Assumptions.**
- The bind ran from detached worktree `b8be5305` (this branch: the ticket-08 claim plus job scripts;
  code identical to `cpud/integration` `9c9b7a66`). Only the new file was added to the store copy.
- A Mac dry run (commit replaced by a capture) checked the arguments first, while both mbit10 lanes
  were held. It is a pre-check, not the bind of record.
