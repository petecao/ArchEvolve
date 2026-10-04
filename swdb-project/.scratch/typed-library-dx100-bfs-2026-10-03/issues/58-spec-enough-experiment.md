# 58 — "Is the specification enough?" experiment

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D7, D10)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 48 (07, 08, 20 resolved)
**Spec:** `../spec.md`
**Needs go-ahead:** Granted. Yan-Ru approved mbit10 dispatch on 2026-10-03. The experiment is one dispatch (Q62), and actual lane admission and receipts are still required.

**What to build:** Peter learns what an intrinsic specification must contain for a rewrite provider to rebuild the rewrite.

## Acceptance

- [ ] There are three inputs, with exact sha256 pins:
  1. Peter's v1.1 specification only (`docs/bfs-intrinsics-spec-yanru.md` at `0b56895`);
  2. the specification plus Josh's draft (`intrinsic-draft.yaml`, sha256 `01f05bdc517922a082a10c9e28d8f1501c92892ba06a1e5298a60e7cc5d0bf30`);
  3. both plus our contract (`library/rewrite_contracts/bfs_read_offload.yaml`).
- [ ] Each input gets 3 rewrite-role samples (9 provider sessions) on one mbit10 lane with the default pin. The working rewrite (ticket 20's patch) and the authors' accelerated code are hidden, as checked by the role's workspace audit.
- [ ] Records carry `mode: extensa` and the campaign ID `extensa-gem5-bfs-<date>-s1`. They are kept in the campaign record store, and the run stays within about 3 lane-hours.
- [ ] Each sample is scored by `swdb certify` against the BFS candidate profile: certified or not, and controls rejected out of total. A table compares the three inputs.
- [ ] Results stay local. The finding is drafted at `drafts/outgoing-2026-10-03/60-peter-spec-enough.md`, and ticket 60 (ready-for-human) delivers it. The agent never sends it.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
