# 20 — Peter's §5 patch with fixes E1–E5, certified

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 13, 14, 18, 19, 17
**Spec:** `../spec.md`

**What to build:** Peter's §5 rewrite, with fixes E1–E5, certifies on the Mac as a patch against the scalar-only snapshot.

## Acceptance

- [ ] The patch edits the BFS source and adds a byte-identical copy of the lowering header; runtime guards run once per BFS call; knobs use the spec defaults (threshold 64, chunk size equal to the build's tile size, dynamic schedule with granularity 1).
- [ ] The patch calls the accelerated-chunk hook and the compare-and-swap probe, so the gem5 primary and diagnostic builds use exactly the certified tree.
- [ ] `swdb certify` with the BFS contract, `--snapshot bfs-dx100-scalar-only-20260929-a1.source` and the patch certifies it on the whole matrix.
- [ ] All eight rewrite negative controls are rejected.
- [ ] The certification record holds the patched tree's sha256.

## Comments
