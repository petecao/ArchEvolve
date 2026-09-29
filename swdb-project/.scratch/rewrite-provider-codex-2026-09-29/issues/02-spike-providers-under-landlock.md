# 02 — Spike: both providers under a Landlock launcher on mbit10

Created: 2026-09-29
**Type:** prototype
**Status:** claimed
**Blocked by:** None — can start immediately (needs a free socket lane)
**Spec:** `../spec.md`

**What to build:** Answer, on mbit10 and inside a socket lane, what tickets 07 and 08 need to know:

1. Can a small Landlock launcher (ABI 4) start `codex exec` (own sandbox off) and `claude -p`,
   let both reach their model API on port 443, and complete a turn?
2. Does a read outside the allowed set fail, a read inside succeed, and a write outside the
   workspace fail?
3. Can each CLI's tool commands be wrapped with an inner no-TCP layer? Claude: its shell-prefix
   setting. Codex: find out whether any shell override exists. If none, say so; the spec's
   fallback then applies.
4. Which Codex flag combination disables web search, MCP, plugins, apps, memories, hooks,
   image tools, multi-agent tools, and project instruction files, and which tools remain?
5. Which event types does each CLI emit for commands, file reads, and file edits?
6. Wall time and token use of one real DX100 proposal at the pinned model and effort.

## Acceptance

- [ ] Each question has a recorded answer under `## Answer`, with the commands used.
- [ ] Raw output stays on mbit10 under the EvolveSWDB runs folder; nothing is written under `$HOME`.
- [ ] The run's lane, load, and checkout commit are recorded.
