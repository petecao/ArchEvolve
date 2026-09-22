# Local Resource Budget (Mac, 36 GB shared)

Copied 2026-09-22 from the owner's MemAcc rules.

> **Scope:** applies ONLY to commands executed on the local Mac. Ignore this file
> when working on mbit10.

- Never run out of RAM: ~30 GB total for agent work, shared across ALL sessions.
- No process >20 GB RSS; big-input benchmarks go to mbit10.
- Long runs: always `timeout`.
- Subagents/workflows are encouraged (they cost tokens, not local RAM) — just
  keep their local heavy processes within the budget above.
