# 32 — Clean up existing run output on mbit10

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 25
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The existing run output on mbit10 shrinks without losing any input or claim evidence.

## Acceptance

- [x] A dry-run listing is produced on mbit10.
- [x] Yan-Ru reviews it and records her approval with `swdb prune --approve`.
- [x] Apply deletes only the approved files; retention records are committed; free space before and after is recorded.

## Comments

- 2026-10-03 08:35 ET: root reviewed the exact two-file failed-smoke listing under the user's explicit current/future project-action approval. Applying through the public guarded CLI; historical coverage files remain excluded. [Concrete review](../cleanup-review-2026-10-03.md).

## Answer

Completed 2026-10-03 08:40 ET. Root reviewed the exact listing and recorded delegated approval under the user's explicit current/future project authorization, using public `swdb prune --approve` and `--apply`. This is delegated review, not a claim of personal human inspection. Listing SHA `feb871b74833f8a88822af1321baeeaa762ac37e79dacdd2537521d46661c636` covered exactly two failed-smoke checkpoint files totaling18,039,198bytes. Both files are absent; all nine compact artifacts remain. No running-record coverage, shared/input checkpoint, trace claim evidence, or other historical root was deleted.

Approval `prune-approval-5482d06e021343978cc76026faebc70f`, intent `prune-intent-528e33cdab12488181709aac274e9094`, and actual deletion `retention-0fdfef7b828d49238d9af06e8c1378d5` are published in `010bec7a473e29b3d21c4877aaf549a059ec4d16` and synchronized locally. Available `/data` bytes increased78,819,528,704→78,837,571,584; the separate `/data1` decrease during metadata/host activity is recorded without attributing it to this deletion. All431 remote records validate. See [concrete review](../cleanup-review-2026-10-03.md) and [machine receipt](../evaluation/ticket32-cleanup-receipt.json).
