# 41 — BC native evaluation on mbit10

Created: 2026-10-03
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 08, 40
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** A real native BC evaluation passes BCVerifier on mbit10.

## Acceptance

- [ ] The go-ahead and the run environment are recorded.
- [ ] The BC workloads are registered and one native evaluation passes BCVerifier.
- [ ] Records are committed after Yan-Ru approves.

## Comments

- 2026-10-03 ET (BC-track agent, ticket 40): code is ready. On mbit10 inside an owned lane:
  `scripts/prepare_dx100_bc_scalar_snapshot.py --runs-dir <runs> --register --check --lane <lane>`
  registers `bc-dx100-scalar-only-20261003-a1.source` (not yet in repository records; ticket 42's
  certification cites this ID and its deterministic tree sha256), then
  `scripts/register_bc_workloads.py --from-workload <registered BFS kronecker/uniform workload> --id <bc id> --work-dir <dir> --request-out <file>`
  registers BC workloads on the same graph files (sources need an outgoing edge; pass `--sources` if a BFS source has none).
