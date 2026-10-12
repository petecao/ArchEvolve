# 10 — Rerun ticket 09: time source 0 and run the split check

Created: 2026-10-12 01:10 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 09
**Spec:** `../spec.md` (C13 (timing half); user stories 26, 27)
**Code map:** `../notes/ops.md` (timing section, F43/F44)

**Time estimate:** about 3 hours of lane time.

## What to do

On a **later Eastern calendar day** than both `.a3` estimates (F43 compares the region profile's
`created` date to the estimates'), time workload `bfs-20261004-uniform22.2f83a134a6bef789` with the
kept counted binaries (`/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/`): LLVM 22
`clang++`, evaluator v3, 20 repetitions, `sources: [0]` (F44). Then `bfs-profile` per side, the checked
attribution report under `swdb.split_check.v2`, and `swdb validate`. Afterwards apply LR-06 to the
kept binaries (65.7 MB) and the raw run folders.

## Acceptance

- [ ] Split check verdict `passed` or `failed`, accepted by `swdb validate`.
- [ ] Checked attribution report committed; evidence in `evidence/10-rerun-09/`.
- [ ] Kept binaries removed per LR-06 (identity, size/hash and no-use evidence recorded).
