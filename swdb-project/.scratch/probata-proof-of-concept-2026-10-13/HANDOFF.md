# Resume Probata after the 2026-10-15 closeout

Updated: 2026-10-15 ET. User requested a controlled stop, review/fixes, integration
into `yanrujhou_main`, and recovery-safe cleanup. This is a partial implementation,
not completion of the 63-ticket spec. Final closeout metadata is linked below.

## Start in a new session

1. Read root `AGENTS.md`, `swdb-project/AGENTS.md`, `.claude/rules/`, this file,
   [resume.md](resume.md), [map.md](map.md), and [spec.md](spec.md).
2. Confirm a clean `yanrujhou_main` and its origin tip. Work only in `swdb-project/`.
   Inspect current ticket frontmatter and dependencies before claiming work.
3. Resume the unmet acceptance criteria in07,24,27 first. Ticket25 depends on24;
   ticket36 depends on27. Later tickets remain gated; never skip blockers merely
   because their status says `ready-for-agent`.

The user authorized this project's implementation/fixes/tests/reviews, commits and
pushes to `petecao/ArchEvolve` on `yanrujhou_main`, two free mbit10 evaluation lanes,
and scoped BFS workspace export through Codex CLI. Recheck the new session's actual
permissions. No new provider, evaluation or ready-frontier work is scheduled by this
handoff. The `probata-implementation-progress` heartbeat is PAUSED; re-enable a
30-minute progress heartbeat only when implementation resumes. In a new session,
attach the heartbeat to that new chat and leave this old chat paused.

## Remaining work and reliable evidence

| Ticket | Completed checkpoint | Remaining acceptance / first action |
|---|---|---|
|07|Method19 ended unproven,27/237 open, 52.04 counted minutes. [Negative audit](evidence/t07-method19-negative-20261015.json). Method20 is saved, unlaunched, with158 controls.|Read `prototype/07-wp-hints/METHOD20.md`; independently review/freeze the composed runner before any new counted run. Fresh provider must author its own hints; never seed historical concrete hints/counterstates. Focused probes are diagnostic only. Final fresh all-goal/smoke proof and covering-wait negative remain mandatory.|
|24|Original class safe: 146 ordinary + 11 smoke proves; seeded bug retains one invariant timeout. Pure-condition admission and public stand-in controls are separate compiler evidence.|Read [acceptance frontier](evidence/t24-acceptance-frontier-20261015.md). Templates need exact embedded-array origins; conditional-expression reads, original construct-group actual pairs and allocation-lifetime criteria remain incomplete. Do not claim group acceptance from model/dependency proofs.|
|25|Original bounded maximum, stale data/iterator and unchecked/checked `at` accepted under exact frozen pins; safe WP owner/pipeline slices have separate evidence.|Seven allocating/lifetime-bearing standalone bodies and three typed receiver arithmetic bodies remain incomplete. [Deferred index-only design](evidence/t25-vector-receiver-domain-plan-20261015.md) has no runtime implementation; its expected-feature control is plain text outside the active suite. An added typed representation is a supplementary assumption; generic callers must discharge it.|
|27|Original qualified stall now proves111ordinary+35smoke at frozen9940b155. Store, nested reads/assignments and footprint safe cases have separately pinned actuals.|Finish the complete current-policy acceptance matrix, including capacity and positive/negative agreement. The query outside case remains not_proven/vacuous_pass with an ensures timeout and failed generated-branch smoke. Keep that outcome. General native/ACSL agreement and CPU/device overlap belong29/28.|
|36|45 current scripted setup controls and separately pinned actual property/cache controls; later slices retain setup/source/report audits.|Depends on27 and final method/source freeze. Close the documented dedicated post-plan contract/summary mutation-control coverage gap if still absent; do not relabel historical exact-source evidence as current-source campaign acceptance.|

The exact ticket count/status and every dependency are in the tracker and the
[all-ticket status index](ticket-status-20261015.md). Unmet tickets stay open. Drafts 1/2 are immutable; draft 3 and
production method freeze have not happened. Held-out BC/PR/SSSP kernels stay gated.

## Evaluation and evidence rules

Mac: Apple Silicon/36GiB RAM. Use the selected Python3.12 environment, matching
LLVM22.1.8/Frama-C33 tools, the shared verifier lock and an8GiB guard. Two shared
slots were explicitly coordinated; inspect current memory/locks before reuse.
Do not start a third job. A passing stand-in or pytest exit code is not a theorem.
Retain ordinary properties, mandatory RTE/initializedness and every smoke result.

mbit10: load `.claude/skills/mbit10-runs/SKILL.md`, then recheck both socket leases,
the legacy lease, processes/load, memory/storage/GPU and the current wrapper.
Use Git-only source sync, remote rebuilds and `socket_lane.sh`; no ARM binaries.
Raw evaluations stay remote under `/data/yanruj/EvolveSWDB_runs/`; only compact
metadata comes to the Mac. The last accepted bounded controls used frozen `94769312`
at node0generation568/node1generation600. These are historical identifiers, not a
live lane claim; both were released at the13:56ET audit.

Raw Mac proof outputs under `/private/tmp/probata-*` and remote evidence folders
remain retained for future audit. Worktree cleanup removes redundant checkouts,
not those output folders. Absolute historical source paths may need reconstruction
from the exact recorded commit: use a detached worktree at the recorded path only
when an audit actually requires it. Never recreate it from the latest main tip.

## Recovery and closeout

[Code review](evidence/closeout-code-review-20261015.md),
[validation](evidence/closeout-validation-20261015.json),
[all-ticket index](ticket-status-20261015.md), and
[completion receipt](evidence/closeout-complete-20261015.json) are committed.
The implementation and handoff were pushed to `yanrujhou_main` at `8bae60b9`;
the enclosing receipt update changes documentation only. Final validation at
`53471f7f`: **313 passed / 42 deselected**, 747.43 s, no timeout/OOM. The reviewed
post-test translator docstring correction has identical executable AST; historical
actual proofs retain their original source pins. These are 313 passing controls,
not 313 proven subjects or complete ticket acceptance.

Cleanup removed **30 remote branches, 53 local branches and 33 idle worktrees**.
The primary checkout, two unrelated LANL checkouts and two `.claude` checkouts
remain. Their refs were not pruned. Both dirty source worktrees were stashed with
original index, tracked patch and untracked content/mode checks, and their stash
commits are retained as archive parents. Unmerged historical tips were archived,
not silently merged. Raw Mac/mbit10 output folders remain.

Recovery tag: `probata-source-recovery-20261015` (pushed and verified).
Archive commit: `7c42c55899b6c1dab7666c862014bce9a3801e1f`. The annotated tag stores the original
branch-to-tip map and snapshot recovery metadata. Its tree is exactly the
precleanup main checkpoint, and its parents preserve all archived source histories.
The local complete bundle is `83304432` bytes at
`recovery/source-recovery.bundle`; its SHA-256 is
`89fa3564e4f6adca9c9e62569490195a08e27ee428bddb26b01ccd155ccbd99f`. It is intentionally ignored, with a remote-tag fallback.

To recover a historical source checkout, fetch the tag and read its annotation:

```sh
git fetch origin tag probata-source-recovery-20261015
git show --no-patch probata-source-recovery-20261015
git worktree add --detach /original/historical/path ORIGINAL_COMMIT
```

For a dirty checkpoint, create its recorded original HEAD first, then apply its
recorded stash OID with `git stash apply --index STASH_OID`. Do not apply a stash
to the latest main tip. [Archive procedure](prototype/closeout/README.md) documents
the local bundle fallback. Reconstruct an old path only when an audit needs it.

At 2026-10-15 14:25 ET, mbit10 node 0 / node 1 / legacy were released, no owned evaluation
process remained, and the clean historical evaluation checkout stayed at `94769312`.
Origin main refs were synchronized; raw outputs were preserved. This observation
is historical: recheck all host state before resuming. The old heartbeat is paused.
