# 40 — BC on the native evaluator (code)

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 38
**Spec:** `../spec.md`

**What to build:** BC (kernel gapbs-bc) plugs into the native evaluator like BFS, tested with fixtures.

## Acceptance

- [x] A DX100 BC implementation record and a scalar-only BC snapshot derivation (the authors' accelerated BC code removed) exist.
- [x] Kronecker and uniform BC workloads can be registered; native evaluation uses BCVerifier; BC protocols freeze.
- [x] Fixture tests pass; BFS behavior is unchanged.

## Comments

## Answer

Resolved 2026-10-03 23:05 ET (agent, BC track). Regression in this state: 218 passed, 1 skipped (BC, kernel seam, BFS native, protocol, pair, profiling, region comparison, shared protocol, profile packages).

**Built.**
- BC plug-in `swdb/kernels/bc.py`, registered beside BFS (`gapbs-bc`: entry point `Brandes`,
  ROI `bc.complete_call.v1`, trial format `swdb.bc.native.trial.v1`, verifier
  `swdb.bc.brandes_scores.v1`, driver `tools/bc_native/driver.cc.in`, binary `bc-native`).
- The native verifier `swdb/bc_native.py` (its file hash is the retained `verifier_sha256`):
  BCVerifier reproduced with every operation rounded to the source's C++ types (`ScoreT`
  float; `CountT` float in DX100 `bc.cc`, double in upstream GAPBS; chosen per
  application). The native evaluator now passes the application into every result check
  (`bfs_native`, `bfs_native_pair`, `bfs_profiling`, `bfs_region_comparison`).
- DX100 BC implementation record `records/implementations/dx100-bc-scalar.yaml` and the
  scalar-only derivation `scripts/prepare_dx100_bc_scalar_snapshot.py` (removes `PBFSMAA`,
  `BrandesMaa`, their tile/register arrays and the MAA selection; keeps PBFS, Brandes and
  BCVerifier byte-identical).
- Workload registration asks the kernel plug-in about sources (out-degrees read from the
  adjacency, or from the SG offsets for streamed graphs); BC refuses sources without an
  outgoing edge. `scripts/register_bc_workloads.py` registers Kronecker/uniform BC workloads
  on the exact graph files of registered BFS workloads (same canonical adjacency).
- A native protocol freeze names its kernel's ROI; the verifier binding (ticket 39) covers BC.

**Tests.** `tests/test_bc_native.py`, 17 cases: fixture evaluation through the BC plug-in;
wrong, NaN and short scores, a BFS trial format, a vacuous source and the BFS ROI are
refused; reproduction rules; registration source rule; SG offset degrees; BC workloads on
BFS graph files; BC protocol freeze binds verifier, ROI and kernel; the real driver around
upstream `bc.cc` (clang, three random graphs) and around the DX100 scalar snapshot (OpenMP
clang, 4 threads) passes the reproduced BCVerifier; the snapshot derivation registers.

**Assumptions.**
- BCVerifier accepts any scores for a source without an outgoing edge (largest reference
  score 0, NaN comparisons are false), so such sources are refused, as GAPBS SourcePicker does.
- BCVerifier also accepts a NaN score at any vertex (`abs(NaN) > eps` is false). The
  evaluator is stricter: a score passes only when `abs(diff) <= eps`; a non-finite reference
  is refused as vacuous.
- No FMA contraction in evaluated builds (x86-64 without an FMA `-march`).
- The scalar BC snapshot is not registered in repository records here; ticket 41 registers it
  on mbit10 (`--register --check`), where its artifact path lives. Its identity is the
  deterministic sha256 of the derivation.
