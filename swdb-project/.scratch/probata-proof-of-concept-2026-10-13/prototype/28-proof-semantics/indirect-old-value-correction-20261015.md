# Indirect duplicate old-value source correction

Created: 2026-10-15 ET. Read-only source inspection; no compiler, verifier or simulation.

The retained interface/history exploration notes incorrectly describe the optional
old-value result as reading the untouched original response payload. At immutable
DX100 e4fc4afdf894f295442cef3604667a469fab8e62,
`src/mem/MAA/IndirectAccess.cc:898–901` declares `new_data[block_size]`, binds both
`dataptr_u32_typed` and `dataptr_u64_typed` to `new_data`, then copies `dataptr` into
`new_data`. The result reads at911/914 therefore alias the progressively updated
copy. Later store/RMW entries in the same iteration can observe earlier updates
in that entries order. RMW arithmetic also uses `new_data` directly.

Physical source: `/private/tmp/probata-ticket28-interface-upstream-20261015/IndirectAccess.cc`,
SHA-256 `7e238a370f25ff5a7a1211548630a291d6358c32d8a199fc58bfacd37d1d35db`.
The exact `for (auto entry : entries)` order is source-backed within this response;
this does not establish a global lane/request/packet ordering. No new contract or
duplicate-index theorem is claimed. Future models must preserve the alias fact
and either establish the entries order or conservatively admit its possibilities.
