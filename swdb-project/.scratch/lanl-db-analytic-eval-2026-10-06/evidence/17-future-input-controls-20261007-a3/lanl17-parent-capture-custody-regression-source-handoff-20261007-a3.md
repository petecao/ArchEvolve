# Isolated custody regression: source-only, NOT RUN

Prepared 2026-10-07 ET at the parent's request. The full test source is `/private/tmp/lanl17_parent_capture_custody_isolated_regression_a3_20261007.py`, 14,003 bytes, SHA `e1fbd54de38492f1706002f6755b8d5d09c5ad5fb21a7f2a3b3ca3ca132048f7`. Preparation proof: `/private/tmp/lanl17-parent-capture-custody-regression-source-proof-20261007-a3.json`, seal `7ac9e87f563311422760d91439ad3731a8eb5ac1a5858aa7da93a9be28a830c5`. The test source was syntax-compiled and statically inventoried only. Its source loader, AST lift, fixtures, tests and main have NOT RUN. Parent review and separate execution authorization remain required.

It binds the exact new producer source `/private/tmp/lanl17_parent_capture_projection_producer_a3_20261007.py`, 46,165 bytes, SHA `32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6`. It reads that source as bytes only, then will lift exactly `Refused`, `require`, `need`, `sha`, `hex64`, `regular`, `hash_file`, `returned_bytes`, `manifest_output_roots`, the three exact output/publication/success guard expressions, and the final diagnostic except type/body. Every fragment's AST hash is inventoried in the preparation proof. The producer module, original main/try body, eight scientific role builders, auditor, collector, SWDB, Store and controls are never imported or invoked. Only standard-library modules and PyYAML are imported by the test source.

The future batch has twelve tests:

| Case | Narrow purpose |
| --- | --- |
| 01 | Exact returned original bytes succeed |
| 02 | Equal-size different returned bytes refuse by SHA |
| 03 | Same-byte inode replacement at the after-fstat window refuses by metadata |
| 04 | Exact M2-derived source/raw/four campaign roots each refuse output containment |
| 05 | A fresh output outside those exact roots passes the lifted containment expression |
| 06 | Missing original M2 refuses |
| 07 | Wrong M2 helper writer or helper body refuses (two bounded subcases) |
| 08 | Wrong M2 source commit refuses |
| 09 | Wrong M2 policy refuses |
| 10 | Both own-source guards pass exact synthetic source and refuse subsequent mutation |
| 11 | Synthetic malformed YAML parser context is hashed, with bounded JSON and no raw marker |
| 12 | An existing ValueError message is hashed, with bounded JSON and no raw marker |

Fixtures use a new owned nonsymlink temporary directory and tiny synthetic files only. No `/data`, actual campaign/source directory, scientific original, real M2 or study input is opened. A transparent logical `/data/yanruj/isolated-custody-fixture` Path facade maps all filesystem checks into that temporary directory, preserving the lifted helper/guard AST and exercising its original logical prefix/routing. Its parent paths also map to the same owned sandbox. The synthetic compact loader supplies only the previously validated M2 interface; it is deliberately not a seal loader test or an actual original admission. Inode-window injection wraps only `os.fstat` and replaces two sandbox files with identical bytes, proving that returned-byte SHA alone cannot satisfy the lifted fd/path metadata guard.

The diagnostic wrapper raises a supplied synthetic exception and lifts only the exact source except handler; it never calls producer main. No raw diagnostic is published outside the test's in-memory buffer. Assertions require exit2, a single bounded JSON line, exact class/message hash and absence of the synthetic private marker. The batch adds no broader parser, scientific, trajectory, statistical, integration, catalog or repeat tests; none of the prior 47/18 tests is rerun.

The only future test invocation, after explicit parent review, is the approved Python interpreter with this exact pinned test source. That is not authorized or executed by this preparation. Original a1/a2/a3 producers/proofs, 6a91 auditor, b08 collector, C/F6, actual inputs, owned worktree and approved ticket14 reader remain unchanged. Ticket14 reader3a0 remains NOT RUN pending actual E and parent admission.
