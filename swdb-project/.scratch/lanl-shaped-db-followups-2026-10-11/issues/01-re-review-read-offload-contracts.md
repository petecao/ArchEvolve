# 01 — Restore the reviewed tier of the re-pinned DX100 read-offload contracts

Created: 2026-10-11
**Type:** task
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../../lanl-shaped-db-2026-10-09/map.md` (follow-up 1)

**What to do:** commit 87e8646e (2026-10-10) re-pinned `library/contract.bc_read_offload` and
`contract.bfs_read_offload` to the merged hardware catalog. Their content hashes changed, so the
existing reviews (which pin the old hashes) no longer apply and both tiers fell to `experimental`.
ADR 0007: an entry becomes shared only through Yan-Ru's recorded review of certified content.
Prepare a review packet (what changed, which certification covers the current hash, the exact
`swdb promote` command), get Yan-Ru's review, record it, and confirm the two failing tests pass.

- [ ] Packet lists the content diff between the reviewed and current hashes, for both contracts
- [ ] Certification evidence exists for each current hash (or the missing certification is named)
- [ ] Yan-Ru's review is recorded through `swdb promote` (never authored on Yan-Ru's behalf)
- [ ] `test_library_index::test_library_entries_clauses_and_dependencies_are_indexed` and
      `test_bc_certification::test_derived_contract_cites_bfs_adds_bc_l1_and_is_shared` pass

## Answer

Resolved 2026-10-12 00:20 ET.
- 87e8646e changed only hash pins (the 5 cited catalog claims are byte-identical); packet:
  [review-packet.md](../review-packet.md).
- `contract.bc_read_offload` re-certified for its current content (7d2edf75…):
  `certification.13d27de288c14557a833fd8aeec7a124`, procedure 1.7, strict functional model on the
  Mac, 10/10 cells, 28 negative controls (276e62b1).
- Both contracts promoted by an agent under Yan-Ru's explicit delegation (2026-10-11 23:45 ET for
  BFS, 2026-10-12 00:00 ET for BC): `review.contract.bfs_read_offload.13ca61af425c`,
  `review.contract.bc_read_offload.33b76c964447`. Tier is `shared` again.
- Yan-Ru chose option B: the two tests accept a parent status of `certified` or
  `evaluated_on_target` (557f3454); no new gem5 run. Both tests pass.
