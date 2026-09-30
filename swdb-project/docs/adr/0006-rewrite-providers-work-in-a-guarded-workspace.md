# Rewrite providers work as tool-using agents in a guarded workspace

Date: 2026-09-29 (Eastern Time)
Updated: 2026-09-29 (Eastern Time)
Status: implemented

Implementation and acceptance are recorded in the
[provider ticket map](../../.scratch/rewrite-provider-codex-2026-09-29/map.md) and
[guarded provider evidence](../evidence/guarded-rewrite-providers-20260929-a1.yaml).
Linux A6 passed 222 guard/pins/workspace tests; A7 passed 42 status-parser cases.
Fresh public DX100 A2 at `c8a666f` passed both providers' original/current audits,
guards and cleanup. Codex created a candidate that passed small-input native
structural checks for sources 0/3/8; `gain_claim=false`. Claude retained an
OAuth-expired failure with no candidate, permitted by ticket 10. The older Codex
A1 log remains audit-refused and unchanged. Linux A10 passed all 443 workspace
cases and six retained-log expectations. The final network/Git/Python grammar repair
passed Linux A11: 216 selected cases in 695.71 s and six retained-log expectations
at `3a73c6c`. Independent whole-diff code review is pending; T17 is complete.

A rewrite provider no longer receives everything in one prompt with no tools. It works as
a coding agent inside a provider workspace that holds only what its rewrite proposal
needs, where it may read, edit, build, and run code. SWDB derives that workspace from the
proposal, confines the provider with its own Landlock launcher, audits the provider's
event log, and takes the edit as the diff of the workspace. We chose this because real
applications do not fit in one prompt, and a provider can inspect source files and test
local edits. The guard and audit restrict access to the evaluator, workload inputs,
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

- The implemented provider boundary is documented in
  [bfs-rewrite-worker.md](../reference/bfs-rewrite-worker.md); the previous
  no-tool route remains available through explicit prompt-only mode.
- Real provider runs happen only on mbit10, inside a socket lane.
- An application whose source mixes the baseline with the authors' optimized version needs
  a baseline-only source snapshot for proposals that must not see the optimized code. For
  DX100 BFS this is a scalar-only snapshot without the `*MAA` functions.
