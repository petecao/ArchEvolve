# Probata closeout: standards review

Created: 2026-10-15 ET.

Fixed comparison: `150930b4be39526e6eeefd881987dba1c6d6e4d3...53471f7f942d2c1ae7456d4fd08b776777006447`.
The separate commit inventory is `closeout-review-commits-20261015.txt`.
This review performs no formal-verifier run and makes no new proof claim.

## Documented standards

No confirmed must-fix violation of root/SWDB scope, Eastern dating, glossary,
immutable proof-record/method-version policy, or source-recovery retention was
found. All 286 changed paths are under `swdb-project/`; the new draft-2 file is
an added immutable checkpoint rather than an edit of an older method file.
Unfinished ticket acceptance remains explicitly unfinished.

The recovery helper implements no deletion. Before archive creation it requires
the exact pushed main tip, clean main checkout, stopped workers, disk headroom,
known dirty-worktree scope and absent archive tag. Its scoped stashes verify
original index, staged/unstaged patches and untracked modes/blobs. It pushes and
verifies a recovery tag before writing a verified local bundle; cleanup commands
are review-only and remote deletion uses exact expected-tip leases. Root still
must verify current use, retained ancestry and actual cleanup outcomes.

## Finding

**P3 — stale adapter-admission documentation.**
`swdb/cbmc_translator.py:1079-1080` says:

> source-origin or operation certificate; production adapters and runtime-check refuse these jobs.

The first half remains correct, but `swdb/cbmc_adapter.py:247-257` now accepts
entry-window jobs through `bounded_entry_windows.prepare`. Describe refusal of
unchecked routes/runtime-check and the independent certificates required by the
checked WP/CBMC routes. This is documentation accuracy, not a demonstrated
execution or proof-soundness defect.

## Heuristic review

Possible Duplicated Code appears in helper/nested view bookkeeping in
`wp_adapter.py` and repeated tiny AST accessors across policy modules. These
policies deliberately have separate accepted grammars, replay checks and content
hashes. No speculative extraction is requested during closeout: a generic shared
waiver or unreviewed identity change would be riskier than the small duplication.
No other actionable baseline-smell finding is reported.

Resume-state refresh, released ticket claims and heartbeat shutdown belong to the
coordinator's final closeout edits; the frozen review tip still predates them.
