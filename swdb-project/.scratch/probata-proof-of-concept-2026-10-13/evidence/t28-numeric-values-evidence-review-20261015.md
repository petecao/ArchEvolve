# Ticket 28 numeric contribution: independent evidence audit

Reviewed: 2026-10-15 23:16 ET. Read-only metadata/raw-file/Git-object inspection only. No tests, compiler, formal prover, provider, remote job, or repository edits were executed by this reviewer.

**Result: PASS; no actionable errors found in this packet.** This does not resolve whole ticket 28 or supply formal/refinement evidence.

Packet: `/private/tmp/probata-resume-t28-numeric/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t28-numeric-values-controls-20261015.json`. SHA-256 `286767768c218f8943d9f59f8d9f177aee5b8d147037cbbd1c744a6b220708db`. Source commit normalization is complete: `source_commit=c69d0296c9ce9eb2d8e501b98a665e60fb9612f6`. Exact audited composed checkout: `fd973e6902f04ad81e50223f27e3291d4ee72706`. A later integration merge/handoff commit is outside this frozen audit unless separately added and checked; the producer explicitly intends to preserve this exact already-audited composition.

All 345 path/hash references (336 distinct physical files) matched their SHA-256 and declared byte lengths, including all three reviewed source files, the copied independent source review, guards, retained raw logs/results/generated controls/binaries, and all 13 historical/final profile inventories. Each profile's retained physical file set exactly equals its listed inventory. Separately checked all 14 upstream file/hash entries. All three source files have identical hashes in source commit `c69d0296c9ce9eb2d8e501b98a665e60fb9612f6`, audited composition `fd973e6902f04ad81e50223f27e3291d4ee72706`, and the reviewed worktree:

| Source | SHA-256 |
|---|---|
| numeric_values.py | f49ebff7a85a88d93c20c78ad313b67a3459f0620254bba9b3cd91fcbd3ba018 |
| numeric-values-design.md | c7b57a4c61099557909375a77c433d6202957640b46ca5ea39493647efc57de0 |
| test_dx100_numeric_values.py | c06d61f35b417c2d1f2ee2192cb6a2dff1f000f3281ea554b442bf98ac671b15 |

Final profile `/private/tmp/probata-t28-numeric-reviewed-final` contains nine native compile-and-execution receipts. All nine compile statuses and native statuses are zero; nested native receipt contents agree exactly with the evidence JSON. Native binary hashes match surviving binaries. All nine retained compiler contexts match the surviving compiler hashes, have successful version receipts, and contain the stated sanitizer/no-fast-math command flags. No compiler/version command was re-executed during this audit.

JUnit records 9 tests, 0 errors, 0 failures, 0 skips. Reviewed test source supports the 128 integer opcode golden evaluations (4 dtypes × 16 opcodes × C11/C++17) and 486 signed ADD/SUB/MUL boundary evaluations (2 types × 9 lhs × 9 rhs × 3 operators). These counts describe finite native controls, not proof obligations. Metadata's resource object exactly matches the raw resource report: exit 0, wall 2.7942487919935957 seconds, peak RSS 117522432 bytes, no OOM and no timeout. The retained guard specifies 8589934592-byte RSS cap and 300-second timeout; both recorded measurements are within those limits. The compiler-worker wrapper serializes worker B and explicitly does not admit formal work.

The packet retains the correct limits: no ACSL parsing/proof execution; absent IEEE bit-level ACSL relation (`result_acsl=None`); runtime flags needing external source/runtime binding; Mac controls not establishing Linux/x86 simulator identity; object/address/cache-line duties beyond the offset helper; and no state/history/ownership/refinement/whole-ticket completion claim. Prior RED and failed-visibility artifacts remain identified; only the final successful profile supplies the reported final nine-pass result.
