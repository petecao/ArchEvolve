# Worktree and branch cleanup

Updated: 2026-10-16 ET. Completed at the user's explicit request.

| Item | Before | After |
| --- | ---: | ---: |
| Local worktrees | 30 | 1 |
| Local branches | 51 | 4 |
| Remote branches | 24 | 23 |

Removed29 secondary local worktrees,47 merged local agent branches and the obsolete
remote `probata-poc/t25` branch. The remaining local branches are
`yanrujhou_main`, `main`, `codex/lanl-ticket11-source-c` and `codex/lanl-ticket17`.
LANL remains paused. Tickets25 and28 remain ready-for-agent and resume from the
primary `yanrujhou_main` checkout.

Every removed tip is an ancestor of published main148b2d06. Each worktree was
clean, unlocked and idle under a fresh own-user command-line/open-file/cwd check.
Ignored files were only34,092,672 bytes of Python bytecode and pytest caches.
No untracked source, reports or raw evidence were discarded. All other remote
branch tips, local stashes and remote evaluation checkouts were preserved.
The shared primary HEAD remained148b2d06 throughout the cleanup; no source merge,
compiler, tests, verifier or evaluation was performed by this cleanup.

Recovery tag **`worktree-cleanup-20261016-230442`** was published and independently
read back before removal. It points to148b2d06 and its annotation contains the
complete [recovery snapshot](recovery-snapshot.json): branch tips, worktree paths,
tree identities and original worktree configuration. The remote deletion used
an exact-tip lease. Local deletions used an atomic expected-tip transaction.
Exact outcomes are in [cleanup-result.json](cleanup-result.json) and
[remote verification](remote-deletion-verification.json).

## Restore only if a historical audit needs it

From the primary ArchEvolve checkout:

1. Preview a branch restore:
   `python3 swdb-project/.scratch/worktree-cleanup-2026-10-16/restore.py --branch codex/probata-resume-t25`
2. Add `--execute` to create that branch at its original tip without changing the
   primary checkout. The manifest lists every other original branch.
3. To reconstruct an old source coordinate, use
   `python3 swdb-project/.scratch/worktree-cleanup-2026-10-16/restore.py --worktree /private/tmp/probata-resume-20261016-c978393b --execute`.
   This recreates a full detached checkout at the exact original commit and path.
   The helper refuses an existing destination. Original sparse/configuration
   metadata is retained in the snapshot if an audit also needs that shape.

Cached bytecode is regenerated when needed. Historical proof receipts retain
their original path/hash identities; removing a reproducible checkout does not
upgrade any proof or make a historical command valid on current main. No remote
evaluation source or raw output was removed. The earlier1433 remote checkout
deletion refusal remains outside this local cleanup and was not retried.
