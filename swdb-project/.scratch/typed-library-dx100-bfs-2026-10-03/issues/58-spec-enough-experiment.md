# 58 — "Is the specification enough?" experiment

Created: 2026-10-03
Updated: 2026-10-04 ET (attempt a1 blocked on the Codex login); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D7, D10)
**Type:** slice
**Status:** needs-info
**Blocked by:** Codex login on mbit10 (Yan-Ru); 48, 07, 08, 20 resolved
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

- 2026-10-04 00:29 ET: claimed by agent. Approvals: Yan-Ru approved the mbit10 dispatch (Q62) and
  the use of Codex CLI / Claude Code on 2026-10-03.
- 2026-10-04 00:50 ET: **attempt a1 ran but produced no sample: the Codex login on mbit10 is
  invalid.** Needs Yan-Ru (below). Details in
  [evaluation/spec-enough-a1-failure-summary.json](../evaluation/spec-enough-a1-failure-summary.json).
  - Driver: `swdb-project/tools/spec_enough_driver.py` (commit `fc42fde` for a1; login fix after).
    Stages `reference`, `provider`, `score`, `summary`. Arms `spec`, `spec_draft`,
    `spec_draft_contract`, 3 samples each, interleaved; at most 9 counted calls, about 3 lane-hours.
  - Ran on mbit10 node 1 (lease generation 508, 00:35-00:37 ET, load1 2.3) from a separate clone
    `/data1/yanruj/ArchEvolve-spec58` at `fc42fde`, delivered by git bundle (not pushed).
    `/data1/yanruj/ArchEvolve` was not touched because ticket 45 ran from it on node 0.
  - Harness check passed: ticket 20's patch, scored through the same path, certified
    (`certification.c633af01c4a54f418b2fc444d750b46b`, matrix 10/10, controls 16/16, tagged
    `mode: extensa`, `campaign: extensa-gem5-bfs-20261004-s1`).
  - All 9 provider sessions failed in 2-3 s with `401 Unauthorized` (`token_invalidated`, then
    `refresh_token_reused`). Guard and audit passed, and the private login copy was deleted. Zero real
    provider calls were spent. Under D7 these are uncounted login failures. a1 logged them as counted
    `failed` because the driver read only the exit message. Fixed: the driver now reads stderr, stops
    at the first login or usage-limit failure, and moves the paused sample aside for retry.
  - Likely cause: `/data1/yanruj/.codex/auth.json` has not changed since 2026-09-29 16:54 ET. The guard
    copies it privately and deletes the copy, so a token refresh inside a session (ticket 36 saw the
    401 signal) uses up the single-use refresh token and never writes the new one back. The original
    file is now stale. This will happen again after each refresh. It needs a follow-up on the provider
    launcher, which is outside this ticket.
  - **Yan-Ru, to unblock:** on mbit10, run `CODEX_HOME=/data1/yanruj/.codex codex login` (the agent
    never handles credentials), then say "resume 58". To resume: bring `/data1/yanruj/ArchEvolve-spec58`
    to the commit with the login fix (git bundle or push), then on a free lane run
    `ATTEMPT=a2 bash /data1/yanruj/EvolveSWDB_runs/extensa/extensa-gem5-bfs-20261004-s1/run.sh` through
    `socket_lane.sh` (`run.sh` is attempt-aware; a1's copy is kept as `run-a1.sh`).
  - Design choices (agent-decided, revisable): (1) Every arm also gets the base snapshot, the canonical
    lowering header and HARNESS.md: the build, the protected logging line and the witness hooks.
    Without these no rewrite can build or be scored. The header's API partly encodes E1/E3, so arm A
    means "specification + executable intrinsic interface". (2) The pinned draft names `TDStepMAA`
    once in a note (line 198). The role's input check refuses that name, so the workspace copy changes
    that one name. Both sha256s are recorded. (3) The harness adds the canonical header to the scoring
    patch, so providers patch only `bfs.cc`. (4) No `campaign_summary` record: its schema needs a
    campaign file and per-class speed verdicts that this experiment does not have. The compact
    summary JSON stands in for it.
  - Open scoring caveat found in the local fixture smoke test: `swdb certify`'s BFS negative controls
    are exact-text mutations of the ticket 20 spelling (`swdb/certification.py` `_rewrite_control`).
    A rewrite with the same meaning but different spelling (for example spaces in
    `if(claimed){...}`) aborts certification with "candidate source lacks a unique negative-control
    mutation site". Independently written samples will probably score "not certified" for that reason
    alone. The driver keeps the official verdict and adds a labeled diagnostic, never a
    certification: the functional matrix, which control sites exist, and the controls run where a
    site exists.
