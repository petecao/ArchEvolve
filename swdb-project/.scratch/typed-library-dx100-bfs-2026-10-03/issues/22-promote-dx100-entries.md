# 22 — Yan-Ru promotes the DX100 entries and the BFS contract

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 15, 20
**Spec:** `../spec.md`

**What to build:** Yan-Ru reviews the DX100 intrinsic, lowering and contract entries and promotes them to shared, so ArchEvolve mode may use them.

## Acceptance

- [x] Each entry is reviewed and promoted with `swdb promote`.
- [x] The certification records from the library and patch tickets and the review records are committed and pushed after Yan-Ru approves, so mbit10's submit gate sees them.

## Comments

- 2026-10-03: Yan-Ru explicitly approved all pending and future related actions in this chat, following the named repository/branch push and prepared promotion packet. Root records the approved promotions on Yan-Ru's behalf; this is actual delegated approval, not an inferred Peter license confirmation or team-send receipt.

## Answer

Resolved 2026-10-03 08:14 ET. Root invoked `swdb promote` for all21 entries on
Yan-Ru's behalf under his explicit approval. [Review index](../promotion-receipts.json)
binds every target content hash and review ID to current execution certification.
Commit `8959b4dfd149273e89884be87bee9c0adb60e0fc` was pushed to the approved
`petecao/ArchEvolve:yanrujhou_main` branch and fast-forwarded on mbit10. The remote
public validator reports425 valid records; independent current state readback is
21 certified/shared entries. No target execution or gain is inferred from promotion.
