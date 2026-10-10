# Independent fresh-a5 derivative source review — 2026-10-08

Conclusion: PASS for the authorized fresh-route/published-input substitutions. No material defect found in these source deltas. The sources are consistent with the supplied a5 routes and hook2/request2 pins. Remote publication, route absence, native state, successful prepare, and scientific admission are not established by this review.

Source identities verified from local bytes:
- Capture a4: 29451 bytes, SHA-256 `bd75569d45a6442c2edef72a721f51b5093faf9ab7c8a34347df30a624b2691d`; baseline a3: `af41955121ea6db8d5064ee543130b5e5b38a0c057011a2b748be7b6f6b4c93c`.
- Hostquery a2: 13955 bytes, SHA-256 `4f60a393c1747dd4c1ff60c1c780647dfa979a6990f50906c9e9ced5c11700ff`; baseline a1: `c90694d232532fd4aab6b34effb98cd0a7098df982c5a7184075015e586411b0`.
- Derivation manifest: `/private/tmp/lanl17-fresh-a5-derivative-source-preparation-20261008.json`, SHA-256 `19d1caa0972913d4bf8ad4e7a815842e1cf8f66009c89c9567222e74b6292408`.

Independent checks:
- Every manifest substitution count matches the actual baseline bytes. Applying exactly its declared substitutions reproduces each candidate byte-for-byte; reversing them restores the complete baseline bytes. Both recorded diff lengths and SHA-256 pins match their local diff files.
- Capture changes only PREP (line 16), PUBLISHED_OVERRIDES (22), decoded BOOT (75), PRESTARTUP (76), and direct_argv (85). All other source bytes/AST nodes are preserved. Source/raw/prepare/freeze-evidence routes and the evidence branch/tag consistently use 20261007-a5. BOOT and direct_argv agree on fresh source/raw/prepare and tag.
- The decoded BOOT parses. Its two before/after exact checks consistently use hook2 `/data1/yanruj/lanl17-dx100-hooks-20261008-a2/post-checkout`, 20078 bytes, `f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a`, mode 0700; request2 `/data1/yanruj/lanl17-dx100-deployment-20261008-a2/request.json`, 19596 bytes, `a7f34492e2db1b21849da0e467bd546dc5bb6bc53b4ac443da5f43922f34bd8c`, mode 0600. PRESTARTUP, PUBLISHED_OVERRIDES, and BOOT overrides agree on the new public routes/request digest.
- Hostquery changes only ABSENT (28) and PUBLISHED (44): all six reserved source/freeze/report/raw/prepare/finalize routes use a5; the hook/request paths, lengths, digests and modes match the capture.
- The selected 9c/28/fa source names, paths, sizes and digests, original proof routes/pins, R/C/185/F6 checks, native pins and capacity/timeout/cleanup contracts remain unchanged. The honest a3 marker start-metadata dictionary is AST-identical. The CODEX_HOME validation/task-marker restoration statements are unchanged.

Method: local byte/hash/diff comparisons, Python AST parsing and literal extraction, decoded BOOT AST parsing, and static shell reasoning only. Neither selected module was imported or executed; no selected shell snippets, tests, SSH, or remote operations ran. Baselines and prior reviews were preserved. This review creates only the requested new exclusive private artifact.
