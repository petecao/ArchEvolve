# Two modes, same evaluator

Date: 2026-10-03 ET
Status: proposed

Extends ADR 0006 from rewrite providers to every agent role.

ArchEvolve and Extensa modes share the evaluator, records, typed library and provider launcher. Each role has its own workspace input and output schema, with shared model/effort pins and audit. Real roles run only inside an mbit10 socket lane. Workspaces hide evaluator inputs, workload data, other candidate artifacts and the authors’ accelerated code. Calibration stays outside all provider workspaces. Extensa is a new SWDB system seeded from frozen MemAcc source; this decision does not implement the later campaign tickets.

## Scope and authority

Implementation follows the authorized tickets [01–37](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md). This proposed record does not assert Yan-Ru accepted the ADR or sent the team note. Human review and communication receipts remain separate.
