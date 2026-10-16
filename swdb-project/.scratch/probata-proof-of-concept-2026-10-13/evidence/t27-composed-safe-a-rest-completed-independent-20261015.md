# Fresh Arest safe closure — 2026-10-15 ET

The four-case Arest profile at exact frozen
`0e7f232762e4555aa9435a3a3622923fad8ee928` completed naturally: **4/4 passed**,
exit 0. All four actual WP records are `proven`.

| Original unit | Ordinary Valid | Smoke passed | Init / RTE goals |
| --- | --- | --- | --- |
| store_source_wait | 90/90 | 29/29 | 17 / 15 |
| stall_condition | 111/111 | 35/35 | 21 / 16 |
| transitive | 72/72 | 21/21 | 12 / 16 |
| register_write | 43/43 | 15/15 | 8 / 8 |
| Total | **316/316** | **100/100** | **58 / 55** |

Independent read-only closure verified the exact four selected collector IDs,
all ordinary/smoke outcomes, actual launches/current passed setup, required
RTE/init/cache/solver/smoke flags, current semantics/method/lowerer identities,
explicit entry premises, unchanged exact source and natural lane/guard exits.
It rehashed **6,027 references / 925 files** without mismatch. The inner guard
took 2,704.695 seconds and peaked at 4,510,117,888 bytes; the outer guard took
2,706.671 seconds and peaked at 4,560,449,536 bytes. Neither had OOM or timeout.
Node1 generation 604 ended naturally at 00:14:49 UTC on October 16 (20:14:49 ET
on October 15). Raw outputs and physical producer source remain retained.

The long stall case was legitimate proof work: its final ordinary and smoke
goals all passed before the next case prepared source. The completed record,
not buffered log timing, establishes its acceptance. Exact record hashes, flags,
entry premises, reports, resources and script pin are in
[t27-composed-safe-a-rest-completed-independent-20261015.json](t27-composed-safe-a-rest-completed-independent-20261015.json).

Together with the separately completed CPU-only profile, this admits **5/11**
fresh safe units under their pinned original contract/semantics premises. The
six B1/B2 units remain pending; this receipt does not close Ticket 27 or broaden
CPU/device-overlap or source-language/ACSL agreement claims.
