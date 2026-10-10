# ONE early-exit7 dispatcher R1 — source-only correction

Prepared 2026-10-07 ET. NOT RUN. No dispatcher/fixture/helper import, main, SSH, test, staging, native probe, Store, science, Git mutation or worktree edit occurred. Only source-byte editing, AST parsing and exact literal reversal comparison ran.

Parent full review of original dc4c identified the primary's retained, untracked `swdb-project/records/.retention.lock` as a concrete false-refusal gate. This distinct R1 preserves the original source and complete original handoff/preparation byte-exact. It changes only decoded remote `source_state`:

1. Require empty unstaged and staged diff path lists.
2. Require porcelain status to be exactly `?? swdb-project/records/.retention.lock\n`; every other tracked/staged/untracked change still refuses.
3. Require the exact physical lock to be nonsymlink through every ancestor, regular, same owned UID114316761, stable during the read, exactly zero bytes and SHA E3.
4. Add original path/byte-SHA/UID/device/inode/mode to `source_state`'s projection. Existing pre-launch and post-run equality calls therefore require that same physical original and mode before and after. It is never opened for write, chmodded, moved or removed.

All other remote functions, constants, native/source pins, argv, environments, limits and local dispatcher ASTs are exact. The original→R1 complete diff has only these two nearby `source_state` hunks. Closed literal reversal restores the full original dc4c byte-for-byte. This proves source scope, not runtime usability or fixture success.

Selected R1 source: `/private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1-r1.py`, 28246 bytes, SHA `4eee5b64037081ef844c6f9efbb0d7d6ac923b5b533dec531f621fe9d228d86f`. Full argv/environment and unchanged future gates remain in the original handoff111868. Native and host facts remain original observations; no new actual readiness is inferred.

Future parent-selected invocation, after full R1/source/readiness review:

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 \
  /private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1-r1.py \
  --delivered-revision 673b39d75ec8ab2b7d1ca19cc6ec7e180444cb4e \
  --dispatcher-sha256 4eee5b64037081ef844c6f9efbb0d7d6ac923b5b533dec531f621fe9d228d86f \
  --output-directory /private/tmp/lanl14-reviewed-early-nonzero-dispatch-actual-20261007-a1
```

If the delivered checkpoint advances, the parent supplies its exact delivered revision; no future revision is invented by this packet. Output must remain fresh. Source preparation grants no extra run, retry or production/scientific admission.
