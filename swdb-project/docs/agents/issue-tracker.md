# Issue tracker: Local Markdown

Updated: 2026-09-22

Issues and specs for this repo live as Markdown files in `.scratch/`. The origin remote is
on GitHub, but GitHub Issues are not used.

## Conventions

- One feature per directory: `.scratch/<feature-slug>-YYYY-MM-DD/` (date the folder was created, Eastern Time)
- The spec is `.scratch/<feature-slug>-YYYY-MM-DD/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>-YYYY-MM-DD/issues/<NN>-<slug>.md`, numbered from `01` — never a single combined tickets file
- Each issue file starts with a `# NN — <title>` heading, then these lines:

  ```
  Created: YYYY-MM-DD
  **Type:** slice
  **Status:** ready-for-agent
  **Blocked by:** 02, 03        (or: None — can start immediately)
  **Spec:** `../spec.md`
  ```

- `Status:` holds the triage state (see `triage-labels.md` for the role strings) or `claimed` / `resolved`
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>-YYYY-MM-DD/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md`. Context pointers go under its `## Context pointers` heading (this repo's name for Decisions-so-far).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. The `**Type:**` line records the ticket type (`slice` for implementation work; `research`/`prototype`/`grilling`/`task` for wayfinding); the `**Status:**` line records `claimed`/`resolved`.
- **Blocking**: a `**Blocked by:** NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `**Status:** claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `**Status:** resolved`, then append a context pointer (gist + link) under `## Context pointers` in `map.md`.
