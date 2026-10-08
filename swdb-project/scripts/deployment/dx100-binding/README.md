# Checked DX100 source deployment

Updated: 2026-10-08 ET. Actual remote deployment remains parent-owned and unexecuted.

This hook provisions exactly `S/swdb-project/apps/dx100` during the original helper's
ordinary `git worktree add --detach S R`. It binds that alias to a protected source
artifact matching the original 53-file baseline and source-snapshot manifest. It does
nothing in EF, ER or any other cwd. The original baseline validator still runs afterward.

The tracked `/apps/dx100` rule ignores only the intentional runtime alias, including a
symlink; it has no trailing slash. Other app paths and all tracked modifications remain
visible. No shared Git config or info/exclude is changed. Git's documented
[post-checkout behavior](https://git-scm.com/docs/githooks) includes worktree creation;
[per-invocation config](https://git-scm.com/docs/git-config) can select hooksPath without
persisting it. Existing executable hooks must receive an explicit parent disposition
before overriding that setting.

A parent-reviewed request is an **unsealed original JSON**, not an admission. It contains:

| Field | Required original fact |
| --- | --- |
| `format`, `uid`, `creator_gid` | `swdb.dx100-source-deployment-request.v1`; actual account UID and identical real/effective primary creator GID |
| `source`, `expected_revision` | Exact absent S before launch, canonical direct child of private base; final 40-character R |
| `private_base`, `control_base` | `{path, identity}`; canonical nonsymlink 0700 owned roots |
| `control` | `{path, identity}`; already-created owned 0700 directory beneath control_base, disjoint from S and target |
| `target` | `{path, stat}`; original protected 53-file baseline/full-snapshot source, beneath private_base and outside all 18 consumed checkout paths |
| `target_stats` | Complete relative file **and directory** name → original full stat map, excluding only root (pinned separately) |
| `records` | Four `{path, bytes, sha256}` pins listed below, read from Git at R |
| `hook` | `{path, sha256}` of the exact executable private staged `post-checkout` bytes |
| `git`, `python` | `{path, sha256, stat}`; actual canonical executable paths and native byte/stat pins |

An `identity` is `{dev, ino, mode, uid, gid}`. A full `stat` also contains `nlink`, `size`,
`mtime_ns`, `ctime_ns`, all integers. `mode` includes file-type bits. Atime is excluded
because the reads themselves can change it. Private-base directory identity is stable
across creation of S; parent must not pin its mutable size/mtime as an identity field.
Targets and traversed directories are owned by the account and on the pinned private-base
device. Ordinary directories and target files may use only the private-base GID or the
explicit actual creator GID. SGID directories must use the private-base GID; SUID/sticky,
symlinks and special files are refused. Every target file retains its independent exact
stat and original manifest byte pin. Regular target files must be single-link. No modes
are changed by this hook. This handles the observed private BASE GID0 alongside C/fresh
source creator GID114316761, without accepting other supplementary groups.

The four record pins are exactly:

- `candidate`: `swdb-project/records/candidates/typed-library-bfs-gem5-20261003-a2.baseline.yaml`
- `snapshot`: `swdb-project/records/source_snapshots/bfs-dx100-compile-20260925-a1.source.yaml`
- `implementation`: `swdb-project/records/implementations/dx100-bfs-scalar.yaml`
- `application`: `swdb-project/records/applications/dx100-gapbs.yaml`

The selected real baseline/snapshot manifest has SHA
`d5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d`,
53 files and 641,928 logical bytes. Its BFS code SHA is
`6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465`.
The hook recomputes the original manifest digest and links candidate, snapshot,
implementation, application source commit and DOBFS; the physical target's complete
inventory and bytes must equal it. A whole simulator checkout is not that artifact.
Parent must independently bind the actual request's four record-byte pins to these
original records, target stat witnesses and protected route. No request builder here
claims that remote observation has happened.

Before prepare, parent selects an explicit descendant R containing this deployment
change, verifies C/185/F6 and unchanged original controls/cleanup proof, checks S absent,
publishes an exact owned private 0700 hooks directory and 0700 hook, and writes the request
exclusively 0600 in a separate already-created private deployment control directory.
Do not precreate the original guard’s fresh metadata-control directory; its own lifecycle
and argument contract remain unchanged. Physical inherited
Git modes are not assumed safe. Do not use the helper's raw root: it is created after
worktree creation. Pin native Python plus the installed PyYAML dependency; check startup
and PATH overrides before launching. Parent retains request, source/native facts,
original command/environment and streams. No auth or whole environment dump is needed.

With no preexisting `GIT_CONFIG_*` overrides (otherwise resolve them explicitly), the
reviewed prepare invocation receives these **task-specific** overrides:

```text
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=core.hooksPath
GIT_CONFIG_VALUE_0=<absolute private staged hooks directory>
SWDB_DX100_BINDING_REQUEST=<absolute exclusive request.json>
SWDB_DX100_BINDING_REQUEST_SHA256=<SHA of exact request bytes>
PYTHONDONTWRITEBYTECODE=1
```

PATH must resolve the original helper's `git` and this hook's `python3` to the pinned
native executables, with the original required commands still available. Use the original
public prepare/supervisor/guard argv and existing owned cleanup unchanged. Keep this
explicit deployment environment through nested calls; later EF/ER worktree creation
is a no-op. Original hook argv must be `(40 zeroes, R, 1)` and cwd exact S. An absent request
means unconfigured no-op, so parent preflight must require all deployment overrides.

The hook has a finite 90-second administrative deadline, each Git read at most 10 seconds,
2 MiB request/record reads, 32 MiB per original source file, 64 MiB native-file reads.
These are unmeasured deployment limits within the helper's unchanged 120-second Git-call
cap; they change no scientific, provider or cleanup budgets. Future failure is retained,
not a reason to silently widen limits or replay a partial attempt.

After successful binding, `control/dx100-binding-original.json` is an exclusive 0600
**unsealed** physical receipt, with original request/source/artifact/record/native pins,
exact alias and target facts, timestamps and `outcome: bound`. An existing alias or receipt
is refused, including broken links. Preflight failure creates no alias; once receipt
reservation/alias creation starts, failures retain partials and an error class/digest.
No overwrite, rollback or cleanup is performed. Parent accepts only original hook/Git
exit zero plus receipt and independent live binding checks; receipt content alone proves
no campaign acceptance or cleanup. Protected target/request/receipt/hook routes must be
carried as actual future preservation controls. The final baseline validator remains
independent and mandatory.

No original helper28d/supervisorfa/guard9c/auditor6a/collectorb08/cleanup receipt changes.
The original cleanup evidence describes that unchanged implementation, and does not
claim to exercise this new hook. Its deployment test evidence is separate. Tests in
`tests/test_dx100_deployment_hook.py` use real local temporary Git repositories with
synthetic 53-file source and catalog inputs; they never establish remote source, runtime,
capacity, campaign, provider or scientific success. Ticket 17 remains claimed.
