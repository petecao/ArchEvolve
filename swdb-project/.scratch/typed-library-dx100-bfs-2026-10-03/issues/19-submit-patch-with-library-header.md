# 19 — Submit a patch that ships the lowering header

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 15
**Spec:** `../spec.md`

**What to build:** A rewrite proposal can carry a patch that adds the lowering header, and submit proves it uses certified, shared library entries and the library's exact header bytes.

## Acceptance

- [ ] The rewrite-proposal message (new message version) gains an optional library section: the contract, every cited intrinsic, lowering and library-operation entry with its content sha256, and every shipped file with its lowering entry IDs.
- [ ] ArchEvolve-mode submit refuses the proposal unless every cited entry is shared and certified or later for that sha256.
- [ ] Submit rejects a header whose sha256 differs from its lowering entries' code-file sha256, and any other new file; the BFS source and the header are the editable files.
- [ ] No rewrite provider runs for a patch payload; the producer names the authoring session (provenance kind agent_run).
- [ ] Tests go through submit with contract fixtures (prior art: the proposal-submission tests).

## Comments
