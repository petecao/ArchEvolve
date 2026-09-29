# Integrate SWDB BFS workflows and the annotated DX100 handoff into ArchEvolve

Updated: 2026-09-29 ET

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

T17 imports retained metadata with digest-checked dependency closure and uses the
existing frozen v2 protocol through public `compare-evaluations`. Public qualification
is **pending the raw-trace recheck**. Its claim scope is simulated source vertex 0,
one repetition under declared determinism, and strategy
`existing-dx100-top-down-offload`, which reuses the DX100 authors' `TDStepMAA` path
with a `wait_ready(tile5)` fix. Hardware/software attribution is joint. The retained
closure's timings alone are insufficient to claim a qualified performance result.

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
  records. Provider workspace fixtures also lacked real-provider launch evidence.
  **After:** Metadata-import and comparison helpers are implemented. T17's raw
  recheck, the real-provider feasibility/smoke receipts, and the final combined
  regression/code review are still pending; update this paragraph with their actual
  outcomes before Yan-Ru opens the PR.

## Merge Danger

**Door:** two-way. YAML metadata and CLI code can be reverted; existing raw artifacts
remain on mbit10 outside Git. The integration adds a large source/record tree to `main`.

**Blast Radius:** repository.

The statement extension is provisional until Peter confirms the report/source binding
and intrinsic request format. The received report's 64-bit offsets differ from pinned
DX100's 32-bit `SGOffset`; tickets 05/06 remain `needs-info`. Team-chat delivery and
opening this PR remain Yan-Ru's tasks (01/07). Merging into `main` requires his approval.
