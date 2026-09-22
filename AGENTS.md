# Agent Rules — EvolveSWDB

Updated: 2026-09-22

## Language and documents

- Use the terms in `CONTEXT.md`. Respect the decisions in `docs/adr/`.
- US spelling. Dates are `YYYY-MM-DD`, Eastern Time. Date every document you create or edit.

## Tracker

- Specs and tickets are local Markdown under `.scratch/<feature-slug>-YYYY-MM-DD/`:
  `spec.md`, `map.md`, and `issues/<NN>-<slug>.md`.
- Each ticket has `Type:`, `Status:`, and `Blocked by:`. Status strings: `needs-triage`,
  `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, plus `claimed` and `resolved`.
- Claim a ticket by setting `Status: claimed` before work. Resolve it by appending
  `## Answer`, setting `Status: resolved`, and adding a context pointer to `map.md`.

## Code

- Dependencies stay at Python 3.12, PyYAML, and jsonschema. Use only jsonschema features
  that version 4.10 supports (mbit10's system Python); in particular, no cross-file `$ref`.
- Test through the command line only: run `swdb` as a separate process against a
  temporary records folder. Every validation rule gets one passing and one failing fixture.
- Records in `records/` are the master copy. Never commit generated files (SQLite, raw run output).
- Never edit `archevolve/hw_ensemble/`: it is a copy of someone else's drafts, checked by `SHA256SUMS`.

## Hosts

- Code reaches the lab host mbit10 through git only. On mbit10, work under
  `/data1/yanruj/`, never `$HOME`; multi-threaded runs go through the host's socket-lane
  procedure; raw run output stays outside the repo.
