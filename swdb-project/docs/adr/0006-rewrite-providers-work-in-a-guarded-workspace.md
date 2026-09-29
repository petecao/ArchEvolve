# Rewrite providers work as tool-using agents in a guarded workspace

Date: 2026-09-29
Status: accepted; implementation pending (`.scratch/rewrite-provider-codex-2026-09-29/`)

A rewrite provider no longer receives everything in one prompt with no tools. It works as
a coding agent inside a provider workspace that holds only what its rewrite proposal
needs, where it may read, edit, build, and run code. SWDB derives that workspace from the
proposal, confines the provider with its own Landlock launcher, audits the provider's
event log, and takes the edit as the diff of the workspace. We chose this because real
applications do not fit in one prompt, and an agent that can explore the code writes
better rewrites; the guard and audit keep it from reading the evaluator, workload inputs,
other candidates, or the DX100 authors' optimized code. Codex (`gpt-5.6-sol`, `xhigh`) is
the default kind and Claude (`claude-sonnet-5-5`, `high`) the alternative, both pinned in
code and recorded in every receipt.

## Considered options

- **Prompt-only, no tools (the previous design).** Simple to contain, but it cannot scale
  to large code bases. Kept as an opt-in (`workspace: false`) so recorded configurations can
  be re-run exactly.
- **The CLIs' own sandboxes.** Codex can restrict reads through a custom permissions
  profile, but on Linux both Codex and Claude rely on bubblewrap, which AppArmor blocks for
  unprivileged users on mbit10. Landlock works there without sudo.
- **Running providers on the Mac**, where Codex's sandbox works. Rejected: builds would be
  aarch64, x86-only code could not run, and artifacts would be split across machines.

## Consequences

- Supersedes the provider boundary in
  [bfs-rewrite-worker.md](../reference/bfs-rewrite-worker.md), which says the provider runs
  without command or editing tools.
- Real provider runs happen only on mbit10, inside a socket lane.
- An application whose source mixes the baseline with the authors' optimized version needs
  a baseline-only source snapshot for proposals that must not see the optimized code. For
  DX100 BFS this is a scalar-only snapshot without the `*MAA` functions.
