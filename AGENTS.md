# Agent Rules — ArchEvolve

Updated: 2026-09-29.

## When the user is Yan-Ru Jhou (`yanrujhou`)

These rules apply when `git config user.name` is `Yan-Ru Jhou` or `$USER` is `yanrujhou`.

- **Branch:** `yanrujhou_main` is the default main branch. Use it as the base for work,
  diffs, reviews, and PRs, not `main`. If the checkout is on another branch, ask before
  working.
- **Scope:** work only inside `swdb-project/`. Its own `AGENTS.md` applies there.
- **Outside `swdb-project/`:** read freely, but do not create, edit, move, or delete any
  file without Yan-Ru's explicit approval for that change. This includes the root
  `.claude/`, `README.md`, and this file.
- **Other members' work:** never revert, reformat, or clean up files outside
  `swdb-project/`, even when they are uncommitted or look broken. Report them instead.
- **`main`:** merging into or from `main`, pushing to it, or opening a PR against it needs
  approval each time.

## General

- Criticism is welcome.
  - Please tell me when I am wrong or mistaken, or even when you think I might be wrong or mistaken.
  - Please tell me if there is a better approach than the one I am taking.
  - Please tell me if there is a relevant standard or convention that I appear to be unaware of.