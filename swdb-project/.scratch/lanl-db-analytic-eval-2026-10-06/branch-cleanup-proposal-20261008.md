# Proposed remote development branch cleanup

Updated: 2026-10-08 10:29 ET

**Discussion only: no branches deleted.** Yan-Ru requested a deletion plan before any removal.

The current audit finds **41 candidates** among 55 remote `codex/` branches. Every candidate tip is an ancestor of observed GitHub `yanrujhou_main` (`5e12a9796432654d88def24ecea617d16ca605b2`). The upcoming pause checkpoint retains that full history.

Delete only the exact candidates below after user approval. Recheck remote tips, ancestry, open PRs and active local/remote worktree or worker references immediately before deletion. If a tip has moved or acquired an active use, skip it. Use an explicit expected-tip lease on each deletion; never delete by wildcard. Preserve local branches/worktrees and all main branches. `peter/work` is outside this proposal.

The [machine-readable audit](branch-cleanup-proposal-20261008.json) retains every original 40-character tip for recovery. A deleted branch can be recreated from its recorded SHA. Removing remote refs does not remove those merged commits from `yanrujhou_main`. This audit makes no mbit10 connection; remote active-use checking remains a prerequisite before deletion.

| Proposed remote branch | Recovery tip |
|---|---|
| `codex/lanl-allocator-count-evidence` | `40ed8e8e3d81df4435c6d073398d2fcc206c8ccc` |
| `codex/lanl-allocator-extra-count-evidence-a1` | `11f5d41ebc4fcfc6aeb2146687b9eac45bdc5685` |
| `codex/lanl-allocator-extra-elapsed-evidence-a1` | `2cbd99dddda2f468c1b241efd86b327ef885acf3` |
| `codex/lanl-allocator-service-evidence` | `2aa3c92c54534fe7c75c23152e46378b68154297` |
| `codex/lanl-bound-estimate-evidence` | `68df1ddbab971ca6cb51f66ae74ae2f4cb62acca` |
| `codex/lanl-bulk-count-evidence-a2` | `109b7b63c8b4147696e01ce62256fc39d8c8b437` |
| `codex/lanl-bulk-total-count-evidence-a1` | `5e8b9ca5d121e598762bd9d6c169a7d3e0e42d1d` |
| `codex/lanl-bulk-total-elapsed-evidence-a1` | `045990a3bf40240c130fac86274f376521d2edb4` |
| `codex/lanl-byte-read-service-evidence` | `294c2d340bdc38c52c5234e0b3689a3a8b60ad2a` |
| `codex/lanl-corrected-count-evidence-a2` | `eaa56d057bb0bbcfb42e64fdb4266d2d04c3f0d4` |
| `codex/lanl-cpu-band-report-evidence-a3` | `8969d567599cb9f0d071f77936ab283fcb97c137` |
| `codex/lanl-cpu-calibration-evidence` | `b7b01edee605b0d83e55c2b7d0a0ef4a2f6057c2` |
| `codex/lanl-cpu-calibration-evidence-a2` | `9e224c6c3c12a97a1d48cc378f58c9f553f155b4` |
| `codex/lanl-cpu-count-equivalence-evidence` | `c1cd9077c58db5d093e1bc4c7545ab1899ec502b` |
| `codex/lanl-cpu-count-equivalence-source` | `695e900d4f46d18fa50a0f66c11852c52aaffbcf` |
| `codex/lanl-cpu-development-evidence-a3` | `791824ff8b9332da51eb97bdaaa74b4537ed4751` |
| `codex/lanl-cpu-holdout-evidence-a3` | `8ef759fc126074c38e013df9bee5fbde1cbeb709` |
| `codex/lanl-cpu-model-evidence-a3` | `887d9bfd319a08df20d6f6cf3571bde8db71406c` |
| `codex/lanl-cpu-t1-count-evidence` | `a15d9eade7d90e210fd4a37f30bbab9ab6612d72` |
| `codex/lanl-estimation-role-postfill-evidence-a2` | `f9c6908f254673cd684992c86949bfaa8f16601c` |
| `codex/lanl-float-memory-count-evidence-a1` | `24992e1c95b5b0e423fe671db7fb8e4a9286427c` |
| `codex/lanl-float-memory-elapsed-evidence-a1` | `310dcc1e7e6416b4f8109c47e549575ec86aae5b` |
| `codex/lanl-functional-bfs-evidence` | `31b4de8a81fe4ade8e497565903bce14b2c475b8` |
| `codex/lanl-functional-evaluation-evidence-a1` | `6f6ab0092da57dbfdfa2e318a9a218bd73e6223f` |
| `codex/lanl-functional-object-count-evidence-a2` | `c01c0e5645f87718128b4605261d0cb4dabcd84a` |
| `codex/lanl-generality-count-evidence-20261006-a1` | `84b53a4372d2fdbd70d7e18127530e09cbe4ca07` |
| `codex/lanl-generality-estimate-evidence-20261007-a1` | `43256ee0300a59a03919833075fbb13fb3ba9ab3` |
| `codex/lanl-memory-service-evidence` | `4f70136e4dd8a6862597d67ec5244fde807bc374` |
| `codex/lanl-native-object-count-source-a1` | `502fea76159cb7b4c692291ee779dd0235b20c8b` |
| `codex/lanl-object-count-evidence` | `e361e83b64578890003ac001e7d6e344556a1876` |
| `codex/lanl-openmp-count-evidence-a1` | `1698975705d66eaf7d47ab508afab18f9ab61231` |
| `codex/lanl-openmp-elapsed-evidence-a1` | `3c968303eadb2a08c539ef823708c4f188f778c8` |
| `codex/lanl-openmp-projection-evidence-a1` | `538adc376f945eee9741da1dc1806cb5e22f37b5` |
| `codex/lanl-openmp-projection-source-a1` | `8949e10fc228bc1009de19fa9df6c9e1a61808ef` |
| `codex/lanl-prospective-input-evidence-a2` | `490abaf96eb564b8f5b58ecf2beb1f615e523a27` |
| `codex/lanl-prospective-input-source-a1` | `b80b2b0407afb7caeeec43fa3ebc00bd9895defb` |
| `codex/lanl-registered-count-evidence` | `5d0fbdb77133ed0520cdbcbcf959d24acad1a6fb` |
| `codex/lanl-root-projection-evidence` | `a5d983ac09fbc5b36babc4989d83ca4b87fe7e6a` |
| `codex/lanl-service-clock-evidence` | `00f96d92499ae2bbec7225351c8e8a2de0b7a512` |
| `codex/lanl-service-clock-evidence-a2` | `88fcdf6992f86ec0a29a1b5f4626d02ec1a625a5` |
| `codex/lanl-service-count-evidence` | `48e03ab1bc37357ef27057fe14434a42de4deda4` |

Retain the integration branch `codex/lanl-analytic-eval`, pending storage branch `codex/lanl17-storage-guard-cost`, original ticket-17 branch, and every remote branch checked out in a retained worktree or sharing its current tip. No candidate is an open PR head in the current connector observation. The existing PR from `yanrujhou_main` to `main` is unchanged.

This proposal does not authorize deletion. Confirm this list with Yan-Ru, then refresh and apply the checks above.
