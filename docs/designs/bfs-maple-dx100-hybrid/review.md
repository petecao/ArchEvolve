# Sketch review notes

This review concerns the design document and pseudocode. It does not certify a hardware mapping, generated implementation or performance.

## Checks performed

- Compared the seven statement IDs and source lines with the pinned `TDStep` and existing source observations. All seven are represented in `partition.yaml`; row-bounds fetching and range enumeration deliberately split responsibilities within line 241.
- Checked that each partition region has a corresponding annotated code marker, that region IDs are unique, and that the pseudocode has an explicit compile guard.
- Independently enumerated the small CSR example as scalar `(u,j,v)` tuples and applied its CPU discovery rule. It produces the five tuples listed in the guide and next frontier `[3,4]` for that one-worker order. The hybrid pseudocode and hardware were not executed.
- Rendered both Mermaid diagrams and visually inspected the resulting PNGs. Dataflow edges refer to the same batch; the separate schedule shows the intended n/n+1 overlap.
- Checked local document links, catalog operation references, source hashes and artifact hashes. No established handoff, typed-library entry, catalog capability or production code was modified.

## Edge-case reasoning

| Case | Required behavior in the sketch |
|---|---|
| Empty frontier | Return before setup or device requests. |
| Worker with empty span | No metadata requests; still participate in final worker/step synchronization. |
| One batch or last batch | No extra lookahead submission; finish all current effects and drain. |
| Tail smaller than B | Submit/consume its actual n bounds per queue; packing support must be admitted in advance. |
| Zero-degree rows | Consume both metadata values; produce no neighbor for that row; confirm completed range exhaustion. |
| Degree greater than T | Retain continuation across chunks and confirm terminal exhaustion after all edges. |
| Repeated neighbor destination | Preserve every logical access; only successful CPU CAS appends a new discovery. |
| Out-of-order memory replies | Preserve queue ordinal and DX result-slot association; do not cross-pair vertex and neighbor identities. |
| Future metadata fills before current work ends | Its full bounded result fits in the owned queue pair; no background consumer is required. |
| No admissible queues/tiles/types/publication protocol | Whole-step scalar fallback before parent/output effects. |
| Device error after effects begin | Candidate run is incomplete; no automatic full-step replay over changed state. |

The resource-progress argument is conditional: queue capacity/count decoding, device progress, MMIO/platform binding, producer exhaustion, initialization visibility and safe tile reuse still require real implementation contracts. The sketch intentionally does not resolve these by assuming a universal fence or treating `CLOSE` as drain.

## Scope

No unit-test suite, benchmark, functional hybrid, Gem5 simulation or hardware run was used to claim execution correctness. The contribution is a source-anchored thought experiment and reviewable work partition, as requested in the October 8 meeting. The two other assigned tasks—Peter feature audit and evolutionary/prompt-loop design—remain separate follow-ups.
