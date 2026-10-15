# Source recovery before closeout pruning

Created: 2026-10-15 ET. Prepared commands only; no snapshot, tag, bundle or deletion
has been performed by this helper's preparation.

Root first stops every agent/evaluation, commits the final reviewed SWDB union,
releases the five still-open claimed tickets to ready-for-agent without marking
them resolved, merges/pushes `yanrujhou_main`, and verifies its exact remote tip.
The final handoff must retain all 63 tickets, the 32 resolved/31 open count,
07/24/27 ready frontier and blocked 25/36 acceptance gaps. The archive is a source
recovery operation, not completion or a production method freeze.

The helper defaults to read-only inventory. Substitute the verified final main
commit, never a moving branch name:

```sh
python3 swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/closeout/source_recovery.py \
  --repo /Users/yanrujhou/CLionProjects/ArchEvolve --final-main FINAL_COMMIT
```

After reviewing that manifest and confirming all workers stopped:

```sh
python3 swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/closeout/source_recovery.py \
  --repo /Users/yanrujhou/CLionProjects/ArchEvolve --final-main FINAL_COMMIT \
  --execute --workers-stopped
```

Execution archives only; **the helper implements no deletions**. It verifies main
is already pushed and checked out clean. Only known dirty source worktrees
`/private/tmp/probata-standard-at-view` and `/private/tmp/probata-vector-ownership`
may be stashed, using `stash push --include-untracked -- swdb-project`. All other
dirty worktrees stop the process for root's explicit recovery disposition. It
refuses outside-SWDB changes. Every stash is kept and its original index tree,
staged/unstaged binary patches, untracked file modes and blobs are checked.
Ignored build/raw outputs are outside this source-only snapshot.

One synthetic archive commit has exactly the final main tree and parents covering
all current local/remote `codex/probata-*` tips plus new stash commits. Historical
branches are archived, **not merged into main**. An annotated recovery tag retains
the complete branch-to-tip map and stash restore metadata. The tag is pushed and
its peeled remote commit is verified before creating a local bundle. The ignored
`recovery/` folder holds the bundle and manifest, with an approximately 83 MiB
estimate, 256 MiB budget and 1 GiB free-disk gate. Readers are root and future
source-recovery users; retain the bundle and stashes through final cleanup.

The local manifest emits review-only commands. Before root uses them, recheck each
exact tip, tag ancestry and current use. Remote ref deletion uses
`--force-with-lease=REF:EXPECTED_TIP`; local worktree removal has no `--force` and
must find a clean idle checkout. Local `branch -D` is allowed only after verified
archive/tag/bundle retention; it does not assert historical main ancestry.
Preserve both LANL and both `.claude` worktrees and all unrelated refs. Do not
remove remote original/baseline/evaluation checkouts; frozen evaluation source
and raw artifact readers remain root-owned.

Recovery is `git fetch BUNDLE refs/tags/TAG:refs/tags/TAG` when needed, followed by
`git switch -c codex/probata-recovered-NAME ORIGINAL_TIP`. For dirty source, run
`git stash apply --index STASH_OID` from a checkout of its recorded original HEAD.
The annotated tag includes these snapshot HEADs and original index/untracked
checksums even if the local ignored manifest is unavailable.
