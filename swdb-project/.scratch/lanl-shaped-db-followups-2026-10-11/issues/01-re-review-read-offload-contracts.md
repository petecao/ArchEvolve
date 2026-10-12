# 01 — Restore the reviewed tier of the re-pinned DX100 read-offload contracts

Created: 2026-10-11
**Type:** task
**Status:** claimed
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
