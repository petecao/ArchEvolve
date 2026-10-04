# 61 — Native protocol for the scale-22 Extensa classes

Created: 2026-10-04 ET (by ticket 56)
Updated: 2026-10-04 06:30 ET (resolved as a decision)
**Type:** decision
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D3, D4

**What to decide:** how a native Extensa campaign can time BFS on the scale-22 graphs D4 chose.
No threshold changes; this ticket only proposes options.

## Finding (ticket 56, 2026-10-04)

D3/D4 cannot run on the current native evaluator. The scale-22 graphs exceed its fixed
materialization limits, so the A/A pilot could not start:

- `swdb/bfs_native.py:39-41`: `MAX_VERTICES = 2_000_000`, `MAX_DIRECTED_EDGES = 32_000_000`,
  `MAX_GRAPH_BYTES = 512 MiB`.
- `bfs-20261004-kronecker22.3dc69be403db57e9` has 4,194,302 vertices and 128,311,450 directed edges
  (1,798,070 isolated vertices); `bfs-20261004-uniform22.facb16e6260c3a82` has 4,194,304 vertices and
  134,217,158 directed edges. `swdb/bfs_protocol.py` `_representation(..., allow_streaming=False)` refuses them
  ("registered graph exceeds native materialization limits").
- Even with the limits raised, the evaluator builds a Python adjacency (several GB per evaluation),
  writes a text `graph.swdb` copy (about 2 GB per evaluation) and verifies every timed trial in pure
  Python (two O(V+E) passes over 134 M edges). A paired block runs 60 trials, so one block would take
  hours and one campaign iteration (4 blocks) far more than its share of the 24 lane-hour cap.

A second D3/D4 conflict: `bfs-20260925-uniform22.f23b09bb0c0601b5` registers source `[2796003]`,
not D3's `[0, 1234, 7777]`. Ticket 56 registered `bfs-20261004-uniform22` (same graph files, D3's
sources) and the new `bfs-20261004-kronecker22`.

The native acceptance campaign `extensa-native-bfs-20261004-a1` therefore stopped at setup with
`infrastructure_failure`, with no pilot block and no provider call.

## Options (agent proposal; Yan-Ru decides)

1. **Scalable native verifier.** A compiled, trusted structural verifier over the registered SG
   files (mmap CSR, same criterion as `verify_parents`), with new verifier and evaluator versions,
   and limits sized for scale 22. Keeps D3/D4 unchanged. About 6-8 h of work plus a short A/A pilot.
2. **Largest graphs the current evaluator admits.** Scale 20 with edge factor 8 (about 1 M vertices,
   16 M directed edges) for both classes. Keeps the evaluator; spread at scale 20 is unknown, so the
   A/A pilot decides.
3. **Keep scale 18 and change the protocol's repetition design** (for example more sources per
   class). D3 notes spread does not fall with repetitions, so this needs Yan-Ru's view.

Agent recommendation: option 1, because D3's reason for scale 22 (spread 0.13-0.14 at scale 18)
remains, and the evaluator's limits are input bounds, not a correctness rule.

## Answer

Resolved 2026-10-04 06:30 ET as a decision: **option 1, a scalable native verifier.** Agent-decided under
Yan-Ru's 2026-10-04 delegation; revisable by Yan-Ru.

- D3 and D4 stay unchanged: Kronecker and uniform scale 22 (edge factor 16), sources `[0, 1234, 7777]`,
  10 paired repetitions, 1 thread, `bfs.complete_call.v1`, `-O3`, and the A/A pilot gate at spread 0.1.
- The evaluator gets new version identifiers instead of raised v1 limits: native evaluator
  `swdb.native.evaluator.scalable.v2` with verifier `swdb.bfs.structural.compiled.v2`. Native evaluator v1
  (`swdb.bfs.structural.v1`) and every protocol and record frozen under it keep their meaning. New
  protocols pin v2 explicitly (`settings.evaluator`).
- The verifier criterion is unchanged (ADR 0001): exactly `verify_parents`, compiled.
- Implementation slice: ticket [63](63-scalable-native-verifier.md). The campaign file
  `campaigns/extensa/extensa-native-bfs-20261004-a2.yaml` pins v2; ticket 56's acceptance run uses it.
