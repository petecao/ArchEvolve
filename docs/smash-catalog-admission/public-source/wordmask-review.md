# Public SMASH 64-bit bitmap masks

Three indexer clear-mask expressions in the bound public SMASH header use a
signed-int literal on an unsigned-long register that the source requires to be
64 bits. The new primitive fixture observes bit31 clearing discard a simultaneously
set high bit, and UBSan rejects shift32 on the narrow literal.

The minimal successor uses `UINT64_C(1)` in all three masks. It composes with the
previous exact-parent zero-CTZ guard. Publication review verified both source
hashes, the patch digest and that these three replacements are the complete
byte-level delta. The third-party header and patch remain private; only the
[identity/composition receipt](wordmask-binding.json) is published.

The completed integer fixture passes preservation at bit0/31/32/63 and rejects
its invalid fixture selectors. Those selector checks are not silently added to
the public indexer: the source correction is the typed literal only. Defined
64-bit CTZ on nonzero input supplies 0..63; zero/EOF progress and whole-indexer
bounds remain separate obligations. Returning zero under the existing CTZ guard
convention does not establish a present bit0.

The source/test handoff is owner commit `73403dbf`, lane
`smash_public_wordmask_2026_10_06`. Its Werror/UBSan fixture result is reused
without another application. No full indexer, kernel, numerical oracle or BMU
handler has run. Constructor/NZA extent and actual software consumer behavior
are the next implementation seams. Catalog assistance capabilities are unchanged.
