# Library-only sparse retirement feasibility — 2026-10-08 ET

Recommendation: Git supports retaining the exact physical library subtree while removing other tracked checkout files, without changing HEAD/branches/objects. This is feasible administrative retirement, not deletion/reference/capacity admission. Parent owns actual subset, host checks and action;04 owns the distinct guard. No managed checkout or remote path changed here.

## Exact Git behavior and administrative boundary

Prospective per-linked-worktree command:

`git -C <exact completed checkout> sparse-checkout set --no-cone /swdb-project/library/`

Non-cone uses this anchored recursive pattern without cone mode's automatic top-level/parent sibling files. Hidden library files remain. Prefer explicit `--no-sparse-index` if that exact command is selected; otherwise prove the index remains expanded. [Official sparse-checkout manual](https://git-scm.com/docs/git-sparse-checkout).

`set` automatically enables common `extensions.worktreeConfig` if absent. Sparse options then live in linked `$GIT_DIR/config.worktree`; pattern lives in linked `$GIT_DIR/info/sparse-checkout`; the linked index changes skip-worktree bits. Thus first use is NOT common-config-byte-preserving. Existing `core.worktree` and `core.bare=true` need main-worktree qualification/migration; inspect actual original configuration before choosing exact permitted deltas. Old Git compatibility matters. [Official worktree configuration](https://git-scm.com/docs/git-worktree#_configuration_file), [config extension](https://git-scm.com/docs/git-config#Documentation/git-config.txt-worktreeConfig).

HEAD/ref/object content is retained; do not prune/remove/worktree-delete/GC. Only selected linked config/index/pattern and necessary common extension migration may change; journals need exact before/after scope. Do not treat every file under .git/worktrees as freely mutable. Library/RAW link content and complete retained physical identities require their own before/after proof. A normal status can be clean despite deliberately absent source files.

Recovery is `git -C <same checkout> sparse-checkout disable`: full tracked bytes return, but dropped files have new physical identities; common worktreeConfig and sparse configuration history remain. Do not claim a byte-identical administrative rollback. Restoring the original shared config is a separate coordinated concern, especially once other worktrees use the extension. No force/clean/reset is part of this proposal.

## Exact old18 library-tree sizes

Read-only native Git `ls-tree -r -l -z HEAD -- swdb-project/library/` for all18 exact ROWS heads in selected G6 (literal-only AST extraction; no guard import). All retained library files are regular100644, with two library trees:

| Tree | Rows | Files/row | LogicalB/row | File4KiBroundB/row | Illustrative incl parent4KiB/row |
|---|---:|---:|---:|---:|---:|
|7705d6f4182efdab6c817554daa233b885b065f0|8|127|487306|782336|897024|
|efd78f19dd19389f18a3cae36eb3c86d06459b55|10|147|520954|864256|987136|

Totals: logical9,107,988B; rounded regular files14,901,248B; illustrative retained files+all library/ancestor directories17,047,552B. Required11 subtotal10,498,048B versus historical whole-checkout2,278,719,488B; optional7 subtotal6,549,504B versus historical1,043,107,840B. Exact per-row heads/tree/file counts/pins are in `/private/tmp/lanl17-old18-library-git-size-observation-20261008-a1.json` (11103B/SHA e01e7f2272c61ffc02bba7f8d2d81224aa559df0565d803c8fa72930741de6f7).

These are Git logical sizes and an explicit 4KiB rounding illustration, NOT measured ext4 allocated/recovered bytes. .git pointer/root-directory allocation, retained full index/per-worktree administration, directory overhead and filesystem behavior remain additional facts. Shared Git objects remain retained; never subtract them twice. Use fresh actual block/statvfs deltas after any selected action, not historical ROWS sizes as current admission.

## Meaningful isolated round trip

A temporary synthetic repository under `/private/tmp` used native Git2.54.0 (Apple Git-157), detached linked checkout, nested/hidden library files and22 separate RAW/library symlinks. Corrected fixture passed11 checks: exact non-cone library-only files; retained library file AND directory full stat/inode/ctime/SHA;22 symlink full stat/literal and dereferenced bytes; stable HEAD/refs/index tree; untouched primary working files/index; expected common extension/local config; expanded index; disable restores every original byte; dirty excluded tracked file survives; untracked excluded file survives. No managed/research source or selected control was executed.

Original fixture7354B/c2f43a1877b7c606027714396b9fca8c22019f1b2f70bc077a4de7595d99db32 stopped on an incorrect test assumption that unset index.sparse must be explicit false; earlier retention assertions passed. Preserved original/failure directory. Distinct R1 fixture7732B/717d30a7ef13a73cb99106c556a682e3cbc9f6aefaf4a4935e5d1f850ca0b41b accepts unset/default-false and checks absence of040000 sparse-index entries. Its sole successful full run result is `/private/tmp/lanl17-sparse-library-roundtrip-fixture-result-20261008-a1-r1.json` (1752B/SHA398c3d0232c04e4b2b9cc4e508b389d955f9ac8a8383376f3511493531af3bad); both sources remain at corresponding `lanl17-sparse-library-roundtrip-fixture-20261008-a1[ -r1 ].py` paths (actual basename has no spaces).

Git version/filesystem-specific preservation must be re-established on actual selected Linux paths; the local fixture establishes feasibility, not host clearance.

## Practical constraints for the actual distinct guard

- Require original detached HEAD/tree, no staged/unstaged/ignored/untracked work, exact retained library blob/mode/byte/physical identities, complete22 RAW link preservation and ordinary consumer/source decisions. `set` does not resolve dirty or untracked data by itself.
- Current G6 `source` at989–1063 hashes/stats EVERY tracked physical path. It must reject a sparse checkout with absent source; do not silently reinterpret that full-source claim. Agent04's distinct action/format/poststate must qualify retirement explicitly. Historical original receipts stay byte-exact; proof by retained Git objects does not manufacture physical source availability.
- Skipped legacy app/source/record/control paths become absent. Parent must distinguish historical strings from still-dereferenced paths using genuine O5/reference evidence. Retaining library links alone does not clear every other consumer.
- No hidden credential routes, cap widening, source repair or statistical/policy change. Entire RAW namespace and original libraries/receipts remain preserved. Select minimum actual eligible subset using fresh allocation/process/reference facts, then preserve recovery refs and original administration custody.
