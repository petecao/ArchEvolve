# Integrate SWDB BFS workflows and the annotated DX100 handoff into ArchEvolve

Updated: 2026-09-29 23:20 ET

## Summary

```text
Yan-Ru: source, profiling, statement IDs
  → Peter: per-statement features
  → Josh/Eric: hardware candidate
  → Peter: intrinsic spec
  → Yan-Ru: guarded rewrite and evaluation
```

This branch adds `swdb-project/` to ArchEvolve: the YAML record catalog, public CLI,
source/profile/rewrite/evaluation workflows, BFS source and protocol records, tests,
and documentation. The current diff against `main` also contains the existing root
agent/scope instructions, remote-host/time-zone rules, mbit10 skill, README integration,
and `.idea/.gitignore`; review those as part of the full integration.

The new handoff work binds Josh's seven `bfs-td-*` statement IDs to the unchanged
DX100 `e4fc4af` TDStep, with complete access-pattern chains and separate row-start/
row-end expressions. It marks the retired SPARTA Workload view as historical and
aligns the older BFS plan with the 2026-09-24 pipeline. Peter retains ownership of
per-statement feature extraction.

Rewrite providers now have pinned Codex/Claude adapters, repairs that retain provider
identity, projected provider workspaces with a protected verifier, event-log audits,
and a Linux Landlock ABI 4 launcher with external strace/resource observation. A registered
25-file scalar-only DX100 source
snapshot removes the authors' accelerator functions from proposals that start from
scalar code. Its derivation and native correctness receipt are recorded; the full
DX100 source snapshot remains available for strategies that explicitly reuse it.

T17's public retained-evidence recheck completed under the unchanged frozen v2
protocol `bfs-t17-controlled-simulator-20260928.952dead4468b86d7`. Both comparisons
accepted gain claims against scalar TDStep:

| Comparison | Primary BFS ROI speedup | Decision |
|---|---:|---|
| `bfs-t17-handoff-20260929-a1.uniform18` | 3.0805868937958523× | gain |
| `bfs-t17-handoff-20260929-a1.kronecker18` | 2.7989783693430432× | gain |

The scope is simulated source vertex 0/source position 0/repetition 0, with one
repetition per family under declared deterministic replay. Strategy
`existing-dx100-top-down-offload` reuses the authors' `TDStepMAA` plus
`wait_ready(tile5)`. Attribution is joint hardware/software because MAA is enabled
only for the candidate. These results establish neither a provider-discovered
accelerator algorithm nor general-source coverage. Diagnostic per-thread elapsed
ratios remain separate from primary ROI timing; the uninvoked scalar MAA region
has no regional ratio. The singleton bootstrap interval does not establish
independent repeated-run uncertainty.

## Evidence

- **Before:** The TDStep implementation record had no team-wide statement binding;
  the old role description still assigned profile consumption to SW/HW ensembles.
  **After:** Seven source-bound statement IDs and eight terminal access expressions
  validate, with parent CAS/store/queue semantics retained. Focused public add tests
  passed (8); repository/view tests passed (13, with 1 skip). All 51 vendored DX100
  manifest entries retain their original hashes.
- **Before:** A from-scratch DX100 proposal could receive the authors' accelerator
  implementation in the full source snapshot.
  **After:** `bfs-dx100-scalar-only-20260929-a1.source` records a 25-file artifact,
  SHA-256 `2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af`.
  GCC 13 on mbit10 node 0 built it with the DX100 `-DFUNC` flags; four-thread
  scale-10 Kronecker and uniform runs both printed `Verification: PASS` for source 0.
  The receipt is retained under `EvolveSWDB_runs/provider-scalar-20260929-a1/`;
  this finite correctness smoke establishes no performance claim.
- **Before:** T17's positive a3 closure lacked locally retained public comparison
  records. **After:** Both public comparisons rechecked the retained raw evidence
  and accepted the bounded gain claims above. The node1 retry used evaluation
  checkout `c55614e1c8c64b2a04d812789e9e59805f4c8033`, lease generation 489, and
  exited 0 at 2026-09-29 21:41 ET. The two records were synced in
  `cadf16b2fe9a945ebfc066eeccd78357a9ad05a8`; public validation passed with 352
  records. Candidate source artifact SHA-256
  `ca09d2f439a56f295c5ccdc5e18a5fd5a4c2c9726005365f8125cc1d8979740a`
  and timed binary SHA-256
  `852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527`
  remain pinned. The exact-binary companion passed and observed 14,546 competing
  parent updates. Raw requests, stdout, stderr, and final summary remain under
  `/data1/yanruj/EvolveSWDB_runs/t17-handoff-20260929-a1/`; [ticket03](issues/03-record-t17-comparison.md#answer)
  links the actual records and receipt bindings.
- Provider implementation acceptance is complete: Linux A10 passed 443 workspace
  cases at `a7cca27`; final A11 passed 216 selected cases at `3a73c6c`, with all six
  retained-log audit decisions matching expectations. Local final audit checks
  passed 154 cases, and independent checks passed 114. Actual Codex DX100 A2 passed
  source0/3/8 native structural checks on a tiny graph; Claude's OAuth-expired
  failure is recorded, as permitted by ticket10, with no candidate. These native
  checks claim no performance gain.
- The independent session review of `65c84fd...40c5011` found no Spec issue and
  one P3 possible code-duplication judgement. The shared first-candidate helper
  repair at `8889e175` passed both reviewers' rechecks with no remaining finding.
  This review covers the ticket changes since the session base, rather than the
  complete existing integration diff against `main`. The final public workflow
  regression passed 45 cases in 673.40 s at `8889e175`, with no failures/skips.
  All agent-owned tickets are complete; this draft is ready for human delivery.
  [Review report](../rewrite-provider-codex-2026-09-29/validation/code-review.md).

## Merge Danger

**Door:** two-way. YAML metadata and CLI code can be reverted; existing raw artifacts
remain on mbit10 outside Git. The integration adds a large source/record tree to `main`.

**Blast Radius:** repository.

The statement extension is provisional until Peter confirms the report/source binding
and intrinsic request format. The received report's 64-bit offsets differ from pinned
DX100's 32-bit `SGOffset`; tickets 05/06 remain `needs-info`. Team-chat delivery and
opening this PR remain Yan-Ru's tasks (01/07). Merging into `main` requires his approval.
