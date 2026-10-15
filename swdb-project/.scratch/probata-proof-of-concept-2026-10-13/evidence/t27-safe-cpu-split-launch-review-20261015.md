# Optional safe CPU split: prospective static review

2026-10-15 ET. **PASS for the optional selector partition; unchosen and unlaunched.** No SSH, pytest collection, compiler, verifier, measurement, dispatch or Git mutation occurred. Root awaits ticket24's continuation estimate and owns the scheduling decision.

| Command file under `/private/tmp` | SHA-256 | Static cases |
| --- | --- | ---: |
| `probata-t27-safe-cpu-command-0e7f.json` | `bd78793da8d34047dc698051b18513bf8ea76e5c228107e772523c0cd31533b0` | 1 |
| `probata-t27-safe-a-rest-command-0e7f.json` | `a07cb4f36406101d64fd8c503787a644ef007822d03669ebb5c9cc12c6e096e3` | 4 |
| `probata-t27-safe-b-command-0e7f.json` | `fd6ee9277df462cc8ca9d35994a03fbd2342476fed5a9cbe27f980f1d8fdb903` | 6 |

Independent static AST extraction from exact `0e7f232762e4555aa9435a3a3622923fad8ee928` confirms that existing `wp-safe` function selection followed by the staged `-k` expressions yields cpu_write alone; the other four original-A cases (store_source_wait, stall_condition, transitive, register_write); and the unchanged six original-B cases. Sets are pairwise disjoint, CPU+rest exactly equals reviewed original-A5, and their union with B6 is all eleven WP_SAFE IDs. These are expected static IDs, not observed collection or acceptance.

If this option is selected, **do not also launch original-A5**. Retain CPU1, A-rest4 and B6 once each, with distinct fresh output/kind/lease receipts. Expected actual report counts must remain1/4/6. There may be at most two active socket jobs at once; the three shards are not permission for three simultaneous lanes. Ticket24's priority and naturally free lane selection remain root-owned.

The v2 launcher hash is unchanged: `17996bd6e3c18419a9e48b7fdf06df043bbfdf87491ff3de225ef12a01fa413e`; auditor hash is unchanged: `faa1c32f04616e939cc2af74873e8908154b6e33b43a7540bb83e10debe94b34`. Exact0e7 existing composed-source reuse, detached/full-clean checks, integration ancestry, production equality, freshly verified socket wrapper, legacy/selected lease exclusion, pinned run/execute/watch, one worker, 8 GiB guards and unchanged proof acceptance remain as reviewed.

CPU whole-job budget2,400s/outer2,520s and A-rest/B whole-job7,200s/outer7,320s are external launcher arguments; confirm them in actual launch/dispatch receipts. Original maxfail=1 and separate JUnit/report outputs remain. The historical CPU call was330.695s; the suggested7–12minute lane interval includes unmeasured setup/bootstrap and is a planning estimate, not a finish guarantee. A-rest's historical call sum is2,645.910s, excluding fresh setup. Maxfail/deadline outcomes may leave a shard incomplete. No timing prediction or static selector result substitutes for full actual record/pin/ordinary/smoke/resource/source-after/ended-lease audit.
