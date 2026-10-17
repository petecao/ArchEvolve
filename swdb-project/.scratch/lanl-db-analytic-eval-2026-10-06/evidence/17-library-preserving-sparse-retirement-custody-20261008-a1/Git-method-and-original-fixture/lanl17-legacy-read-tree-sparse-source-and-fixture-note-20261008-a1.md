# Legacy read-tree library retirement — 2026-10-08 ET

The legacy plumbing route is feasible without enabling `extensions.worktreeConfig` or modifying the common config. ONE newly authorized synthetic temporary Git fixture completed with exit 0 and 26 checks. No managed checkout, remote source pool, selected guard, library source, campaign or scientific command changed. This is prospective source/behavior evidence, not actual capacity or consumer admission.

## Native action and restoration

For a clean full linked worktree, resolve its absolute private Git admin directory and require a fresh absent `info/sparse-checkout`; if `info` already exists, preserve it and its unrelated contents. Create the exact owned pattern bytes `/swdb-project/library/\n` (fixture: new `info` 0700, pattern 0600), then run:

```sh
git -c core.sparseCheckout=true -c core.sparseCheckoutCone=false -c index.sparse=false -C WT read-tree -m -u HEAD
```

No `--reset`, force, common config write or `sparse-checkout set` is used. Both the file/pattern creation and native checkout mutation require the distinct parent's selected action; this note grants neither. The sparse flags are supplied again for commands that depend on sparse behavior; ordinary status was also verified clean. Ordinary later checkout/merge behavior is not a recovery guarantee and must stay under the action's custody.

Restoration changes only the owned new pattern to `/*\n`, runs the same native command, verifies all original tracked bytes and cleared skip-worktree bits, then removes only the newly created pattern and (only if created and empty) `info` directory. The restored excluded files get new inodes; selected index administrative bytes may differ. Library files/directories and RAW link full stats remain exact through restoration. No claim of byte-exact index/admin rollback is made.

## Exact Git 2.48.1 source basis

The remote native query independently reported Git 2.48.1. These are bounded read-only upstream tag reads:

- [read-tree source](https://github.com/git/git/blob/v2.48.1/builtin/read-tree.c#L166): `git_config` at line 166 loads general command-line config before `unpack_trees` at 269. Its configuration callback delegates ordinary core settings to `git_default_config`. This command never calls `init_worktree_config`. Source: 8,562 B / SHA256 `68c35be51b0eebbcf8be51950aa9ff6d5bbbb80c5df95542aab6b3fd4d3732a8`.
- [core config](https://github.com/git/git/blob/v2.48.1/config.c#L1624): lines 1624–1631 assign the sparse settings; the command-line config processing is at 2087–2088. Source: 96,180 B / `19da79c19b956bb577b2e5282704b163ba93669ad1e4ab9a2886970da636d4b1`.
- [unpack-trees](https://github.com/git/git/blob/v2.48.1/unpack-trees.c#L1925): lines 1925–1930 require sparse-enabled plus working-tree update and load existing patterns. Source: 86,569 B / `229fdebfa224e4f33fcc9a46b1078314e66c49e7719f074e6267b00526cbd6f5`.
- [pattern routing](https://github.com/git/git/blob/v2.48.1/dir.c#L3456): lines 3456–3470 read the Git-dir `info/sparse-checkout` path with non-cone mode. Source: 113,576 B / `a5dba4ab186855dcef4ee187aa59b930e8f012bb8b242d7bba27bd8b5f67934c`.
- [official read-tree documentation](https://github.com/git/git/blob/v2.48.1/Documentation/git-read-tree.txt#L375): lines 375–427 document this older plumbing, skip-worktree transitions and all-inclusive restoration. Git recommends porcelain for general use; the explicit plumbing route here avoids that porcelain command's common-config migration. Documentation source: 16,897 B / `113e01e50b3bf4d0cb41d21f55c7c5e522dbb1acd71fe7efd6f215304f9ec0fc`.

## Original synthetic custody

- `/private/tmp/lanl17-legacy-read-tree-sparse-roundtrip-fixture-20261008-a1.py`: 9173 B / SHA256 `d53222fef3e2f34c2f590af30f1642f7573acae871068b8afed165ec6ee2d786`.
- `/private/tmp/lanl17-legacy-read-tree-sparse-roundtrip-fixture-result-20261008-a1.json`: 26335 B / SHA256 `3e8253969e9a2762e3c6c4edf20896101d64629012e5231b2192975e3a375a15`.

Fixture root: `/private/tmp/lanl17-legacy-read-tree-fixture-8ox0vnco`. Native local Git: `git version 2.54.0 (Apple Git-157)`. The local native version differs from the actual remote 2.48.1; the exact older source establishes why the command is supported, while actual guard postconditions remain required. Original fixture files and result are retained, with no repeat run.

The 26 checks establish: linked-only pattern routing; absent initial pattern/info/worktree configs; exact library-only retained tracked files (including hidden library data, excluding root/parent/siblings); all library file and directory device/inode/mode/UID/GID/link count/size/mtime/ctime and SHA invariance; all 22 RAW symlink literal/full-stat invariance and target readability; common-config byte/full-stat invariance; no worktree configs created; exact HEAD/refs/staged entries/index tree; clean status with and without command-line flags; unchanged primary and other-worktree tracked bytes and physical indexes; correct skip-worktree bits and no sparse-directory index entries; full byte restoration and cleared bits; owned-new-pattern cleanup; linked `.git` pointer byte/full-stat invariance. Full fixture source and command hashes in the result show the assertions rather than substituting check names for remote evidence.

## Guard/action consequences

This route removes the common-config migration issue and needs a distinct exact pattern/index action journal instead of a worktree-config migration policy. Existing guards that require every tracked checkout file physically present remain incompatible after retirement; their checks must distinguish this recoverable sparse state and preserved library closure explicitly. Existing source/RAW references outside the library still need the parent's actual classification. Preconditions remain tracked clean, untracked/ignored absent, exact library/RAW preservation, HEAD/refs retained and no active consumer; the native operation's success is not those attestations.

Actual O5 library/root/pointer allocated blocks and fresh free space supersede illustrative Git-tree rounding. Common/shared Git objects and pre-existing index/admin allocation are not reclaimed checkout bytes; sparse pattern/index deltas are administration, not an observed benefit. No subset, cleanup or capacity clearance is asserted here.
