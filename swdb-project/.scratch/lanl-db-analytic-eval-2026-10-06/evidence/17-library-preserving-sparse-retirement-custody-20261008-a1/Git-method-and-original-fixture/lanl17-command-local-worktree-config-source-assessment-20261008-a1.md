# Command-local worktreeConfig assessment — 2026-10-08 ET

The proposed `git -c extensions.worktreeConfig=true -C WT sparse-checkout set --no-cone --no-sparse-index /swdb-project/library/` cannot preserve the common config on the observed repository. This is an exact Git 2.48.1 source finding, not a new fixture or remote observation. The parent required a fresh variant only if source confirmed the route feasible; consequently that variant was **NOT RUN**. The earlier ordinary sparse fixture remains separate synthetic evidence.

The actual parent-run configuration original is `/private/tmp/lanl17-git-common-sparse-configuration-query-original-actual-20261008-a1.json` (14,661 B; SHA256 `1891bebe4f3a8fbbf8c1ee9c5813b8ac2e6617cdabe0b11e76da5cb837bdc83a`). Its reported native Git is 2.48.1; selected repository configuration has only `core.bare=false`, no extension/sparse keys, zero includes, and all registered `config.worktree` files absent. This does not establish a future mutation's acceptance or allocation.

## Exact upstream source chain

Read directly from the upstream Git repository's `v2.48.1` tag, using bounded read-only HTTPS fetches:

- [setup.c](https://github.com/git/git/blob/v2.48.1/setup.c#L835), 73,832 B, SHA256 `f910e98a7e4bffe6e5c9ce231da16993cc4351d5dab64d5470a3ef2b40682b58`: lines 835–841 read repository format using the specified physical config file; lines 1957–1958 assign its worktree-config format flag. The command-line option does not replace that file read.
- [config.c](https://github.com/git/git/blob/v2.48.1/config.c#L2079), 96,180 B, SHA256 `19da79c19b956bb577b2e5282704b163ba93669ad1e4ab9a2886970da636d4b1`: lines 2079–2088 consult the existing format flag before loading `config.worktree`, and process command-line parameters afterward. Lines 3081–3091 select a worktree config write only when that format flag is enabled.
- [builtin/sparse-checkout.c](https://github.com/git/git/blob/v2.48.1/builtin/sparse-checkout.c#L374), 29,392 B, SHA256 `2aad170bdd206ffd516bb4f6ee5d082ced9e5cad258b49761da5dba36426670f`: lines 374–380 call `init_worktree_config` before writing sparse options.
- [worktree.c](https://github.com/git/git/blob/v2.48.1/worktree.c#L956), 28,761 B, SHA256 `f499b2d4f13567842d64718da4f8e805aa25914c2df35a6dbc45a9d2deba5e9c`: lines 956–1015 skip migration only when the repository-format flag is already true. Otherwise line 971 writes the common extension. `core.bare=true` and `core.worktree` migration follow; the observed false/absent values require neither move.

The source therefore contradicts the desired common-config byte invariance. A displayed command-scope value from `git config` would not demonstrate format initialization. This rules out claiming command-local isolation; it does not rule out an explicitly reviewed ordinary Git migration.

## Practical boundary for a distinct sparse action

If parent selects ordinary `sparse-checkout set --no-cone --no-sparse-index /swdb-project/library/`, the first selected row enables the common extension; it is a real common-repository administrative change. Later selected rows write their own `config.worktree`, pattern file and index. Other absent worktree configurations remain absent; `core.bare=false` retains its value. Exact common postbytes/stat and all unselected behavior must be verified rather than labeled unchanged. `disable` restores excluded tracked bytes but does not undo the common extension or restore removed file inodes; the earlier fixture already documents that limitation.

The currently measured actual library/root/pointer blocks in agent03's O5 worksheet supersede this agent's illustrative 4 KiB Git-tree rounding. No shared-Git/index allocation may be counted as checkout-space recovery. This note makes no source-pool action, subset choice, capacity admission, physical consumer clearance or scientific claim.
