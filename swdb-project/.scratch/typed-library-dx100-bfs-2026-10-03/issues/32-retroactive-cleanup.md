# 32 — Clean up existing run output on mbit10

Created: 2026-10-03
**Type:** task
**Status:** ready-for-human
**Blocked by:** 25
**Spec:** `../spec.md`
**Needs go-ahead:** Yes: Yan-Ru approves the mbit10 dispatch before it starts (Q62).

**What to build:** The existing run output on mbit10 shrinks without losing any input or claim evidence.

## Acceptance

- [ ] A dry-run listing is produced on mbit10.
- [ ] Yan-Ru reviews it and records her approval with `swdb prune --approve`.
- [ ] Apply deletes only the approved files; retention records are committed; free space before and after is recorded.

## Comments
