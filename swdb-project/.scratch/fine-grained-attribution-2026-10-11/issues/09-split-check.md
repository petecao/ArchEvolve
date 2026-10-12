# 09: Split check on the real pair

Created: 2026-10-11 15:14 ET. Updated: 2026-10-12 00:41 ET (final review fixes: rule v2, profile checks,
boxes, full missing-piece list, Progress marked historical); 2026-10-11 23:32 ET (resolved: split_unverified, no timing, LR-01); 2026-10-11 21:28 ET (code half built; progress note added;
the real mbit10 run is still open); 2026-10-11 21:17 ET (claimed for the code half).
**Type:** task
**Status:** resolved
**Blocked by:** 03 — First real pair
**Spec:** `../spec.md` (F15, F19, F23; LR-02)
**Time estimate:** about half a day of agent work on mbit10

**What to build:** Time each group of the t75 pair natively on mbit10 with the existing BFS region thread-CPU counters, map the measured regions to groups by file and line, and apply the rule fixed before timing: pass when every group's measured and estimated shares differ by at most 10 percentage points. Write the verdict (`passed` or `split_unverified`) and the measured shares into the attribution report.

## Acceptance

- [x] The rule and the estimates are recorded before the timing starts. (No timing ran: the rule is
  in code since 21:31 ET, v2 since 2026-10-12; the estimates were saved at 22:50 and 23:16 ET.)
- [ ] Verdict and measured shares saved in the validated report. — not met: supported negative result (LR-01), see Answer
- [ ] Load on mbit10 recorded with the run. — not met: supported negative result (LR-01), see Answer
- [ ] Summary for Yan-Ru: verdict and the per-group share gaps. — not met: supported negative result (LR-01), see Answer

## Progress (historical, 2026-10-11 21:28 ET)

Kept as written then, except where marked. The ticket is resolved (see Answer); no rerun is
planned. 2026-10-11 21:28 ET — **code half done** (branch `fga/09-split-check-code`); the real run
on mbit10 was still open then.

**What exists now:**

- `swdb attribute` takes `--baseline-profile` and `--candidate-profile` (two saved
  `region_profile` records from `swdb bfs-profile`). Why flags on the same command: it reuses
  every input check and the byte-identical record path, and one record kind holds the split.
- The rule is the constant `SPLIT_RULE` (`swdb.split_check.v1`, max |gap| 0.1; **v2 since the
  final review**, F40) in `swdb/attribution.py`; it is written into every checked report and
  `swdb validate` refuses a report whose rule differs. It is recorded in code now, before any timing.
- Output: `split_check: {verdict, rule, reasons, profiles, measured_shares, gaps, regions}`.
  The profile pins carry `load_average` (host load recorded with each profile run).
- Refused: one flag alone, an unfinished profile, another tree, another input (F18) or thread
  count, a profile dated before an estimate (LR-02). Since the final review also another machine,
  other BFS sources or another input seed (F44), and a profile not dated a later day (F43).
- Format: `docs/reference/format-v0.4-attribution.md` § Split check. Tables:
  `swdb_attribution_split_checks`, `swdb_attribution_split_gaps` (`docs/reference/database.md`).
- Tests: 7 new cases in `tests/test_attribution.py`, all through `swdb attribute`.

**What the mbit10 run must do (historical; corrected by the final review, 2026-10-12):**

0. Make ticket 03's unchecked report first (`swdb attribute` without profiles, with the same
   flags as below). Ticket 03 made none: its estimates are unknown.
1. Fresh native `evaluation` of the baseline candidate and the t75 candidate on the ticket 03
   workload (`bfs-20261004-uniform22.2f83a134a6bef789`), **on a later day than both estimates**
   (F43), on the machine that counted them (F44), timing **source 0 only**: the counted source
   (F44), not the requests' `[0, 1234, 7777]`.
2. `swdb bfs-profile` of each evaluation, in a socket lane.
3. Each profile's `context.candidate_sha256` must equal the artifact hash of the source record
   ticket 03's report names for that side.
4. Run (the unchecked report's flags, plus the two profiles):

```sh
python3 -m swdb attribute --records records \
  --baseline-estimate <t03 baseline estimate> --candidate-estimate <t03 candidate estimate> \
  --baseline-source <t03 baseline source> --candidate-source <t03 candidate source> \
  [<t03 --site-finder flags>] \
  --baseline-profile <baseline region_profile> --candidate-profile <candidate region_profile> \
  --id <unchecked report id>.split-check --format json
```

5. `swdb validate`, then write `## Answer` with the verdict and the six gaps
   (`split_check.gaps`).

## Answer

2026-10-11 23:32 ET — **resolved on a supported negative result (LR-01): `split_unverified`, no timing run.**

- Ticket 03 ended negative: both t75 estimates (uniform22, T1) have `seconds: null`
  ([03 answer](03-first-real-pair.md#answer)). With no estimated group shares there is nothing to
  compare, so F19 cannot pass. Per F23 the verdict is `split_unverified`; no attribution ranking may
  steer the site finder (ticket 10 already ignores anything but `passed`).
- No native timing was started: timing without estimates would not be prospective (LR-02) and could
  not change the verdict.
- Missing pieces (same as ticket 03, corrected by the final review, F41): five groups, in
  [ticket 03's Answer](03-first-real-pair.md#answer) with every item in
  [`unknowns-summary.json`](../evidence/03-first-real-pair/unknowns-summary.json):
  1. the CPU description's characterization allowlist (risk B1; every unknown region);
  2. call costs with no service rate (OpenMP `__kmpc_*`, allocator, `llvm.memcpy/memmove`, clock,
     iostream, `strlen`, one indirect call);
  3. the OpenMP exact characterization projection (5 regions per side);
  4. call-shape size bins (`_Znam`/`_ZdaPv` 16 MB bins and six `llvm.memmove` bins);
  5. memory-scenario write cells and access primitives 107/109/113.
- **No attribution record exists** (`records/attributions/` has none): the `split_unverified`
  verdict is this Answer only. The site finder therefore sees no report, which also keeps
  today's order, so the outcome is the same as a saved `split_unverified` report (F23).
- The split-check code is in place and tested (see Progress). No rerun is planned: Yan-Ru
  declined the optional follow-up ticket on 2026-10-11.

**Final review fix (2026-10-12 00:41 ET, branch `fga/final-fixes`).**
- H1 (F40): the split check now compares like with like. Its estimated shares keep each region's
  call time in the region's own group, as measured exclusive time does; the report's groups keep
  F33. Rule `swdb.split_check.v2`; `swdb validate` still refuses any other rule.
- M2 (F43): a profile must be dated strictly after both estimates (estimates carry only a date).
- M3 (F44): a profile of another machine, other BFS sources or another input seed is refused; the
  rerun steps above say to time source 0 only.
- H2 (F41), M6, L6: the full missing-piece list, the boxes, the historical Progress section and
  the missing "unchecked report first" step.
