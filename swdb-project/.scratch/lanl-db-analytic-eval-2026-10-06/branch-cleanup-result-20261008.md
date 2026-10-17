# Remote branch cleanup result

Updated: 2026-10-08 10:53 ET

**37 merged remote development branches deleted; four retained because mbit10 worktrees still use their branches or tips.** Yan-Ru approved the proposed cleanup with “go ahead.”

Deletion used one atomic push with explicit expected-tip leases. Fresh GitHub reads verified all 37 refs absent, every other remote tip unchanged, all deleted tips still ancestors of `yanrujhou_main`, and all local branches/worktrees unchanged by deletion. There are 18 remaining remote `codex/` branches. Main, integration, storage-resume and contributor branches were preserved.

[Full result and recovery SHAs](evidence/branch-cleanup-20261008-a1/result.json), [byte custody](evidence/branch-cleanup-20261008-a1/manifest.json), and [original proposal](branch-cleanup-proposal-20261008.json) retain the audit.

| Retained candidate | Current mbit10 use |
|---|---|
| `codex/lanl-cpu-count-equivalence-evidence` | `/data1/yanruj/ArchEvolve-lanl-cpu-calibration-20261006` |
| `codex/lanl-native-object-count-source-a1` | `/data1/yanruj/ArchEvolve-lanl-native-object-counts-20261006-a1` |
| `codex/lanl-openmp-projection-source-a1` | `/data1/yanruj/ArchEvolve-lanl-openmp-projections-20261006-a1` |
| `codex/lanl-prospective-input-source-a1` | `/data1/yanruj/ArchEvolve-lanl-prospective-inputs-20261006-a1` |

The active-use check ran at **2026-10-08 10:48 ET**, after the preserved quiet boundary. It observed 29 registered remote worktrees, no matching owned processes, no unreadable owned process fields, and all three evaluation leases released. This is a bounded branch-use observation, not general consumer or scientific admission.

The existing retirement wrapper reported `guard_completed` and `guard_exit_code=0`. **The original retirement receipt was neither collected nor assessed.** Retirement count, recovery and capacity/scientific admission remain unassessed. [Resume](resume.md) still begins with one original collection for this existing attempt; the collector and decoder have not run for a4.

Implementation/evaluation and the 30-minute heartbeat stay PAUSED. No evaluation, worker control, host source sync, Git fetch/prune or checkout change occurred on mbit10. Primary remains the observed `5e12a979`. Do not prune its historical refs or advance primary before the existing original receipt and frozen-primary protocol are handled.

Recovery: choose the exact branch and SHA from `result.json`, verify that SHA in local main, then recreate that specific remote ref with `git push origin <recorded-tip40>:refs/heads/<recorded-branch>`. This restores a named deleted branch without changing main or local worktrees.
