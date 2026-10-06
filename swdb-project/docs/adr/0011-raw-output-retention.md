# Raw-output retention

Date: 2026-10-03 ET
Updated: 2026-10-05 ET (scope line)
Status: proposed

Extends the immutable evidence policy of ADR 0002 and the evaluator workflow.

Compact correctness, witness-chain, region-report and companion evidence stays. Only debug traces and checkpoint payloads are bulky. Successful execution can prune checkpoint payloads; trace pruning waits for re-reading records and a release from future team claims. Team-cited runs keep bulky output. Every deletion produces a retention record with path, content hash, reason and time; evaluation records remain immutable. Retroactive cleanup requires a reviewed listing and recorded approval. Every dispatch first checks runs-disk headroom and lane-local memory, with no automatic output-root switch.

## Scope and authority

Implementation follows the authorized tickets of the [typed-library map](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md): 01–37 at first, then 38–78 (updated 2026-10-05 ET; the map lists each ticket and its decision). This proposed record does not assert Yan-Ru accepted the ADR or sent the team note. Human review and communication receipts remain separate.
