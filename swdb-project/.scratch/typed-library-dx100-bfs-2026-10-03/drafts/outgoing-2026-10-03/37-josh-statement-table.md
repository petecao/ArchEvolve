Hi Josh,

Here is the audited seven-statement TDStep table from the scalar-only BFS profile. The real guarded annotation and scoring run completed on mbit10 on 2026-10-03 at 09:08 ET. Pattern classes and index provenance are agent claims from code reading for the first four statements and inference for parent CAS, parent store and queue append; every expected cost rank is inferred. The last-level misses and observed ranks below are Callgrind simulation.

Spearman rank correlation is **0.4925690038994379**. Top-3 overlap is **2 of 3** (`0.6666666666666666`; the published table rounds it to `0.667`).

| Statement | Scalar lines | Pattern class (agent) | Index provenance (agent) | Expected rank | Simulated LL misses | Callgrind rank | Contradicted |
|---|---|---|---|---:|---:|---:|---|
| bfs-td-frontier | 77–77 | stream: read | none | 4 | 6731 | 3 | no |
| bfs-td-row-bounds | 78–78 | stream → single_valued_indirect: read; stream → single_valued_indirect: read | bfs-td-frontier | 3 | 6809 | 2 | no |
| bfs-td-neighbor | 79–79 | stream → single_valued_indirect → ranged_indirect: read | bfs-td-frontier → bfs-td-row-bounds | 2 | 479207 | 1 | no |
| bfs-td-parent-read | 80–80 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: read | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 1 | 0 | 5.5 | yes |
| bfs-td-parent-cas | 84–84 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: compare_and_swap | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 6 | 0 | 5.5 | no |
| bfs-td-parent-store | 85–85 | stream → single_valued_indirect → ranged_indirect → single_valued_indirect: write | bfs-td-frontier → bfs-td-row-bounds → bfs-td-neighbor | 7 | 0 | 5.5 | yes |
| bfs-td-queue-append | 86–86 | stream: write | none | 5 | 0 | 5.5 | no |

Four statements have zero attributed misses and share the average rank 5.5. Queue append has **zero attributed debug-line rows**. Those zeros describe the retained line attribution; they do not establish that the operations have no cost. Optimized/coalesced code and work in inlined headers can be absent from a statement line. These results establish neither a native bottleneck nor a performance gain.

A cost-rank claim is marked contradicted when its distance from the simulated midrank exceeds one position. Top-3 boundary ties use fractional expected overlap. Pattern and index claims need a measured, simulated or person-reported access-pattern fact to contradict them. Callgrind collected continuously over the complete BFS call, with initially empty model caches at that call boundary and one final client dump; only TDStep and outlined-worker self costs were retained. Intervening BFS work contributes to cache history, so there is no cold reset per TDStep invocation.

The original DX100 file is `benchmarks/gapbs/src/bfs.cc` at revision `e4fc4afdf894f295442cef3604667a469fab8e62`, vendored at the repository path linked below. The table uses the derived scalar-only snapshot's line numbers. Original→scalar lines, in table order: 240→77, 241→78, 242→79, 243→80, 247→84, 248→85, 249→86. The mapping checks the exact statement text through the pinned source derivation.

The profiling model was Codex `gpt-5.6-sol`, effort `xhigh`, CLI `codex-cli 0.153.0`. Its three audited shell invocations only read the declared `statement-context.json` and `statement-source.cc` inputs. Per-line/statement ground truth and rank scores were withheld until independent scoring; the model ran no compiler, profiler or evaluator. Guard and audit passed, and the private login copy was removed.

Evidence pins:

- Scalar snapshot: `bfs-dx100-scalar-only-20260929-a1.source`; source-tree SHA256 `2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af`; scalar BFS file SHA256 `e2fd2653fd1adcfd9452d891d4ce2062659b4383c47b089b8dcf9489047278c3`; derivation SHA256 `08bb846f40cad690801e5e0ad8966271d15d11411eb13b3d7787b6a1cdc40991`.
- Region profile: `typed-library-bfs-scalar-profile-20261003-a2.profile`; record SHA256 `3df8599662e915ec66d6c326d1999103454ef4b49ca7125d06e33762c4d91883`.
- Prompt SHA256: `d383db6057c92d0e2761d49f4aff7ec6f211494f0ebe31183d2d4908ea8633e8`.
- Declared context input SHA256: `8d1b2787e6f5fdc0d6daf58097dbb56489f6544f61d3bfd6825de54a592d4214`; declared source input SHA256: `7ef7bdfd13f3b117665e7a4698a56d7a16368d46a32caa349eb9bf5c56b8955c`.
- Actual profile runtime commit: `f6972ebbf9c842c1a7091716505577d06c637231`; annotation/scoring runtime commit: `f642a94ba41e79f79b28a540cb8d758e15bec633`.

All repository pointers below use published commit `6c65bdfdcca83381ad09554fa1aabcb127768282` on `yanrujhou_main`:

- Original DX100 statements: [swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc, lines 240–249](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc#L240-L249).
- Published table: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/josh-statement-table.md, lines 7–24](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/josh-statement-table.md#L7-L24).
- Exact score and all source mappings: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/score.json, lines 1–407](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/score.json#L1-L407).
- Provider/model/effort/prompt: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/provider.json, lines 94–104](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/provider.json#L94-L104).
- Declared inputs and their pins: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/workspace.json, lines 6–21](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/workspace.json#L6-L21).
- Runtime and provider audit: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/annotation-a3.operator-audit.json, lines 62–91](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/annotation-a3.operator-audit.json#L62-L91).
- Actual input reads and withheld ground truth: [swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/annotation-a3.operator-audit.json, lines 178–272](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/annotation-a3/annotation-a3.operator-audit.json#L178-L272).
- Callgrind scope, cache history and source identity: [swdb-project/records/region_profiles/typed-library-bfs-scalar-profile-20261003-a2.profile.yaml, lines 1791–1837](https://github.com/petecao/ArchEvolve/blob/6c65bdfdcca83381ad09554fa1aabcb127768282/swdb-project/records/region_profiles/typed-library-bfs-scalar-profile-20261003-a2.profile.yaml#L1791-L1837).

Yan-Ru
