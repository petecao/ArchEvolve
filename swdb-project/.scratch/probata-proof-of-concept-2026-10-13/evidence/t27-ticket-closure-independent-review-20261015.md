# Ticket27 scoped closure review — 2026-10-15 ET

**PASS: no blocker to merging the five-file closure packet at `2b4cc6e7fddb522437d4dc5f8de2fd5591a62264`.** This reviews ticket27 acceptance within the adopted CBMC/WP fixture scope, not whole-effort completion or production promotion.

Independent local receipt checks confirm 62 unique cases and 52 unique actual record identities: 25 proven, 12 bounded refutations with C++ replay, 15 not proven. Every profile receipt's record path/hash/verdict matches the final inventory. All seven strict-receipt hashes and their available local audit-script pins match; the committed inventory/B2 metadata agrees with the retained original local audit outputs. Seven profile resource/lane/source-after receipts show natural exit0, no timeout/OOM and unchanged frozen source.

| Acceptance item | Evidence supporting scoped closure |
| --- | --- |
| Coverage/citations | Bounded/native profile includes inventory, type-check, missing-verifier, citation/contract/owner controls; all35 cases pass. |
| Unready reads | Bounded read/size/CPU-write hazards refute with replay; safe CPU and size units prove under WP. |
| Every tile read | All three early-read variants refute at their individual bounded probes; corresponding WP hazards remain ordinary open obligations; safe three-read proves112ordinary/31smoke. |
| Wait rule | Store-source, tile transitivity, destination/condition stall and register-write safe cases prove; range/condition/unrelated waits retain the required failures. Adopted F6 excludes the original register-producer wait claim. |
| Values | Stream/gather/range safe WP units prove; bounded wrong-value controls replay; WP wrong-value ensures remain unproven. |
| Footprints | Safe WP membership proves57ordinary/18smoke; bounded outside membership refutes/replays. WP outside remains vacuous_pass with independent ensures timeout and failed smoke retained. |
| Capacity | Reviewed ordinary induction hint atb9 establishes32 under WP/CBMC;33 remains ghost_capacity without a source counterexample under both. |
| One ghost state/agreement | Declaration/control fixtures pass; adopted CBMC and WP outcomes agree across the admitted safe/negative scenarios. General source-language/C-stub/ACSL agreement remains ticket29. |
| Versioning | Safe records pin semantics/reduction; actual bounded/native profile includes older-semantics staleness control. |

All11 safe WP records have actual launches, passed setup and mandatory RTE/initializedness/smoke policy. Independently summed totals match **792/792 ordinary,252/252 smoke,143 initialization,141 RTE**. The13 WP negative records each retain ordinary open goals; their35 failed smoke checks are neither discarded nor called source refutations.

The capacity repair changes an ordinary checked hint, not a source premise, contract or runtime. `swdb/`, `library/` and original DX100 fixture bytes have an empty diff between `0e7f2327` and `b9a34bbb`. The configured runtime identities are consistently retained; native link/transitive-DSO closure is explicitly outside the audit boundary. Qualified typed windows, ordinary/ghost separation, trusted call contracts and reduction assumptions remain explicit. Tickets28/29/43/59 remain open separately. Historical failures are preserved as historical.

**Evidence boundary:** this review independently rehashed local receipts and exact commit blobs; it did not rerun remote physical-file checks or contact mbit10. Remote record/report/resource bytes are supported by the seven separately pinned strict audit receipts, not a fresh remote rehash by this reviewer. No compiler/verifier/test/provider job or repository mutation occurred.

Machine-readable checks/pins: `/private/tmp/probata-t27-ticket-closure-independent-review-20261015.json`, SHA256 `1f7a971d37fa95e5610e3a8b4a8bae67ac32d1d0a898222391f460972f2be073`.
