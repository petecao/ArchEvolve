# BFS branch consolidation

Updated: 2026-09-27 ET.

At the user’s request, main now consolidates the BFS implementation and the Git
histories of its runtime, operator and evidence delivery snapshots. Evaluation
work remains paused; merging does not complete any acceptance requirement.

The pre-merge inventory contained 37 local and 78 remote-tracking branch refs
(excluding origin/HEAD), representing 83 distinct commits. Of these, 78 distinct
BFS snapshot heads were outside the implementation branch ancestry; 52 independent
tips cover their entire history. The optimization-strategies branches were already
ancestors and require no additional merge.

Main first fast-forwarded to `9b852952a21a91caf23eb5a23682056a812ccc80`. Independent
review found every one of 94 differing functional blobs across 46 source/test paths
already present verbatim in that commit’s ancestry. Evidence review found no missing
records or other content; all three newly fetched a6 evidence changes already match
the current tree. Older snapshot variants are superseded or intentionally pinned
historical execution versions. The only branch-only files are two accidental Python
cache files from an earlier corrected export; they remain in history, not main’s tree.

Accordingly the remaining merge uses Git’s ours strategy only for these explicitly
inventoried BFS snapshot tips, retaining the already integrated implementation while
making the snapshot histories ancestors of main. This is not a claim that arbitrary
branch changes can be discarded. Original refs and exact commit hashes remain intact
for immutable execution provenance. No branch or worktree was deleted, no runtime was
changed on mbit10, and unrelated untracked weeklogs were not included.

Audit records:

- [All refs](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/branch-consolidation-refs-20260927.json)
- [Merge tips](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/branch-consolidation-merge-tips-20260927.json)
- [Functional history review](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/branch-consolidation-functional-review-20260927.json)
- [Evidence review](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/branch-consolidation-evidence-review-20260927.json)

Resume future work from main and the [resume checkpoint](../.scratch/bfs-rewrite-evaluation-2026-09-25/resume.md).
