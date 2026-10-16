# Ticket 36 profile cwd correction

2026-10-15 ET. Read-only diagnosis of root-admitted exact source `2033c1746eeab02b1d59d4d910a4e31b3e726da8`. The initial command JSONs remain immutable at their original paths. No dispatch or source/toolchain mutation was performed for this correction.

The inherited `run.sh` changes into `/data1/yanruj/probata-reviewed-2033c174`, sets `PYTHONPATH=/data1/yanruj/probata-reviewed-2033c174/swdb-project`, disables bytecode writes, sets external raw `TMPDIR`/cache and verifier lock, and invokes the guarded execute/watch chain. `execute.py` calls the selected command with `cwd=source`, the monorepo root. My initial `tests/...` nodes assumed the project subdirectory; root's command review missed that assumption too.

The setup profile naturally released node0 generation581 at 2026-10-15 21:46:51 ET with exit4,0.275289s,peak31,981,568bytes,noOOM/timeout. Facts naturally released node1 generation607 at21:48:09ET with exit4,0.279680s,samepeak,noOOM/timeout. Both say file/directory not found and no tests ran. Setup's source-after receipt remains exact2033, unchanged and tracked-clean. This is a pre-test dispatch error, not a proof failure or scientific outcome. Original raw folders, commands, runtime, reports and receipts remain retained under `/data/yanruj/EvolveSWDB_runs/probata-reviewed-2033c174-t36-{setup,facts}`.

New command files use absolute `{SOURCE}/swdb-project/tests/...` nodes and explicitly change into `{SOURCE}/swdb-project` before executing pytest. The shell receives source and command as separately quoted positional arguments; no path is interpolated into executable shell text. This also aligns fixture method identity creation with `run_swdb` child cwd, which is the project directory. Full cc1 runtime identities retain cwd-sensitive metadata, so absolute test paths alone would leave a method-context mismatch.

| New command | SHA-256 | Expected selected cases |
|---|---|---|
| `/private/tmp/probata-t36-setup-cwd-v2-command-20261015.json` | `508775ec672906a22713535777000e28f5674fc3f9f6f4ef4861e672a719d349` |128; prior126 plus2 added context controls, root collection confirmation required |
| `/private/tmp/probata-t36-facts-cwd-v2-command-20261015.json` | `b71dcaa224c7c32f0393f027ed386bcc9dd7a481774adbdefddf3b0fbb320b30` |13 parameter cases |
| `/private/tmp/probata-t36-production-cwd-v2-command-20261015.json` | `a9dcf0ebd27755f50423d74c10f6ce793c19cf84708a7113db3b2bba45393572` |5 pytest cases:3WP and2bounded cases; bounded cases produce multiple proof records |

No collection was performed here; collection can itself invoke real Frama-C version discovery and remains root-admitted. Root will confirm exact counts before redispatch to fresh `*-v2` raw folders. The inherited bootstrap runtime snapshot is collected from monorepo cwd; actual project-cwd runtime identities may differ in cwd-sensitive frontend metadata. Preserve both observations and their exact contexts, or collect a separately admitted matching-context snapshot. Do not silently label them byte-identical.
