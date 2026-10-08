# Local worktree cleanup

Updated: 2026-10-08 11:11 ET

**Removed 17 completed local worktrees and their 17 merged local development branches; three checkouts remain.** Yan-Ru requested this cleanup after approving the final agent rules and committing the writing-preference edit (`cb6f75ae`).

| Retained checkout | Reason |
|---|---|
| `/Users/yanrujhou/CLionProjects/ArchEvolve` | Primary checkout on `yanrujhou_main` |
| `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve` | Paused integration work and next-session checkpoint |
| `/Users/yanrujhou/.codex/worktrees/lanl-ticket17/ArchEvolve` | Paused ticket 17 and exact source path used by its reviewed resume command |

Each removed checkout was clean, its exact tip was an ancestor of `yanrujhou_main`, and no open file handle or process working directory matched it. All implementers had completed their current tasks. No embedded Git repository or submodule was found. Codex archived each checkout before removing its directory and Git registration; all 17 recoverable snapshot refs were verified afterward. The associated local branch refs are absent. Git's ordinary deletion refused ticket 10 and ticket 11 because their upstream histories diverge; their exact tips were reverified in main and the saved snapshots before deleting those two local refs.

Seven ignored preparation originals (126,449 bytes, including two empty lock files) were copied byte-for-byte and hash-verified before removal. Python and pytest caches were disposable. The removed directories occupied 4,274,696 KiB in the pre-cleanup `du` inventory; this is their recorded footprint, not a measurement of recovered free space.

[Cleanup evidence](evidence/local-worktree-cleanup-20261008-a1/README.md) records every removed path, branch, original tip, snapshot ref, ignored original and app archive identity. Restore a saved attachment with Codex's worktree restore action; it restores a detached checkout. Each original tip also remains reachable from main.

This cleanup changed only local checkout state. Remote branches, mbit10 checkouts, raw output, private `/private/tmp` controls, frozen scientific source pins and evaluation state were preserved. Ticket 17 stays `claimed` / paused-by-user, substantive campaigns remain 0/4, and the progress heartbeat stays PAUSED. The next evaluation action is still the original retirement collection described in [resume.md](resume.md).
