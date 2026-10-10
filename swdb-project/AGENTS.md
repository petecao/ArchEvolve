# Agent Rules — EvolveSWDB

Updated: 2026-09-29. EvolveSWDB is the `swdb-project/` folder of the ArchEvolve monorepo;
the ArchEvolve root `AGENTS.md` sets branch and scope rules.

## Language and documents

- Use the terms in `GLOSSARY.md`. Respect the decisions in `docs/adr/`.
- US spelling. Dates are `YYYY-MM-DD`, Eastern Time. Date every document you create or edit.

## Tracker

- Specs and tickets are local Markdown under `.scratch/<feature-slug>-YYYY-MM-DD/`:
  `spec.md`, `map.md`, and `issues/<NN>-<slug>.md`.
- Each ticket has `Type:`, `Status:`, and `Blocked by:`. Status strings: `needs-triage`,
  `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, plus `claimed` and `resolved`.
- Claim a ticket by setting `Status: claimed` before work. Resolve it by appending
  `## Answer`, setting `Status: resolved`, and adding a context pointer to `map.md`.

## Agent skills

### Issue tracker

Local Markdown under `.scratch/<feature-slug>-YYYY-MM-DD/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default role strings, used as the `Status:` value. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the `swdb-project/` root (not the ArchEvolve
root). See `docs/agents/domain.md`.
