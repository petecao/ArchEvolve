# 58 — "Is the specification enough?" experiment

Created: 2026-10-03
Updated: 2026-10-04 ET (resolved after attempt a3); 2026-10-04 ET (login write-back fix; attempt a1 blocked on the Codex login); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D7, D10)
**Type:** slice
**Status:** resolved
**Blocked by:** — (48, 07, 08, 20, 62 resolved)
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
  - 2026-10-04 00:45 ET: likely root cause of a1's 401s found and fixed (local only, not yet on mbit10). Every
    guarded session copied `auth.json` from CODEX_HOME into a private provider home and deleted the
    copy afterward. Codex refreshes its OAuth tokens inside a session and saves them only to the
    `auth.json` in its own home, and the refresh token is single use. So any session that refreshed
    (for example the ticket 07/20 sessions) left the source holding a consumed refresh token, and the
    next session got `token_invalidated` / `refresh_token_reused`. Fix: new
    `swdb/provider_login.py`, used by `provider_workspace`, `provider_roles` and
    `provider_guard.prompt_context`. When a session ends, a changed copy that is still a well-formed
    login is written back atomically (temp file, `os.replace`, mode 0600) under a lock file
    (`auth.json.swdb-lock`), only if the source still holds the snapshot the session started from.
    Receipts record only short hashes and changed/written flags (`workspace_manifest.login_writeback`).
    The copy is still deleted and audited. The driver now runs an offline login preflight before each
    session: a missing or malformed login, or a login whose hash a session already saw refused,
    pauses the run as an uncounted D7 login failure (`ledger.preflights`). Tests:
    `tests/test_provider_login.py`. Yan-Ru still has to run `codex login` on mbit10 once, because
    the current source token is already consumed.

## Answer

Resolved 2026-10-04 08:03 ET by the agent under Yan-Ru's 2026-10-04 delegation (agent-decided;
revisable). A3 used 9 more counted calls than the original 9-call budget, because the
experiment needs 3 samples per input.

**Attempt a2** (node 1, generation 509, 01:40–02:22 ET, commit `0775f7d`): 0 samples scored.
Five sessions were counted and failed the strict audit: heredocs, awk, non-literal sed and
`git apply`/`git diff`. A sixth session crashed the driver: the audit raised ENAMETOOLONG on
an awk program. That crash is fixed in `db49d5d`. Three sessions never opened. Compact record:
[evaluation/spec-enough-a2-summary.json](../evaluation/spec-enough-a2-summary.json).

**Attempt a3** (node 1, generation 512, 06:59–07:51 ET, sessions at `d56d972`; rescore at
generation 513 on `3965ca1`; 0.91 lane-hours; load1 1.3–1.4).

- Prompt: plain reads only, the diff written by hand, and no heredocs, awk, git, patch or
  file writes. The audit stayed strict.
- Certifier: ticket 62.
- Sessions ran strictly sequentially under `swdb-session.lock`. All 9 completed and passed
  the audit.
- Positive control: ticket 20's patch certified through the same path
  (`certification.bc0341d701f441d4b8396116230eddd4`, 10/10 cells, 16/16 controls).
- Recount fix: in the first scoring pass, hand-written hunk counts were wrong, so `git apply`
  refused 6 patches. Hunk counts are now recounted before scoring (`d8aaa64`, equivalent to
  `git apply --recount`, as the campaign adapters already do). The 6 samples were rescored;
  their earlier scores are kept as `score.before-recount`.

| Input | s1 | s2 | s3 | Certified | Controls rejected |
|---|---|---|---|---:|---:|
| spec | no apply | failed, matrix 0/10 | failed, 0/10 | 0/3 | 0/48 |
| spec + draft | failed, 0/10 | failed, 0/10 | failed, 0/10 (1 control) | 0/3 | 1/48 |
| spec + draft + contract | no apply | no apply | failed, 0/10 | 0/3 | 0/48 |

"No apply": the hand-written context dropped a blank line at bfs.cc line 97. "Failed": the
strict layer reported `register_handle` / `thread_ownership_register` in every cell.

**Finding.** All 9 samples pass plain values where DX100 takes register handles
(`__dxc_stream_load(queue.shared, chunk_begin, chunk_end, 1, tile)` and the `stride` of
`__dxc_range_loop`). They follow Peter v1.1 §3.1/§3.3 and the §5 template, which give these
operands `int32_t` value types. The lowering header's `int` parameters do not disambiguate.
The contract's label "E2 register handles" did not help either. The specification is
therefore not enough: it must type scalar operands as per-thread registers set by a
constant-load. Compact record:
[evaluation/spec-enough-a3-summary.json](../evaluation/spec-enough-a3-summary.json). Draft for
Peter: [drafts/outgoing-2026-10-03/60-peter-spec-enough.md](../drafts/outgoing-2026-10-03/60-peter-spec-enough.md)
(ticket 60; never sent by the agent).
