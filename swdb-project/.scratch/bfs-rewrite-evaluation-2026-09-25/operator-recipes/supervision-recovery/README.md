# Supervision recovery proof group

Created 2026-09-27 ET. Prospective preparation; no proof, evaluation, lane lease,
provider call or compiler invocation has started from this operator.

The fixed group is `bfs-supervision-recovery-linux-20260926-a1`. The original
600-second/2-GiB reservation covers supplement (90 seconds plus 60-second audit),
owned a5 (90 plus 60), interruption a5 (90 plus 60), and the remaining allowance
for closure and final storage readback. Each stage runs once. No failure is
retried, no old ID is resumed, and no new standard proof kind is introduced.
The 42 supplemental cases include injected fault controls; they are not empirical
BFS execution evidence. Standard proof cardinalities remain five and two.

`operator.py` orchestrates existing runtime scripts. It does not replace their
ownership/cleanup implementation. Each stage has a separate fixed named tmux
session; its Bash pane identity is captured before launching the fixture helper.
The session must exit before its independent audit starts. The enclosing operator
also runs inside a named tmux session, with `launch.sh` enforcing an outer maximum
of 600 seconds including its final kill interval. The shell captures this original clock before any runtime
manifest guard and passes the same timestamps into the group preflight. All per-stage/audit clocks are
inside the original group clock. Audit invocations use a 59-second TERM bound and
one-second final kill reserve within the unchanged 60-second allowance.

The runtime is pinned to `8cbfee600f23416a8e9578fa8d3ce3f0e19fced8` at
`/data1/yanruj/EvolveSWDB_supervision_recovery_runtime_20260927_a1`.
`runtime-manifest.json` was derived from all 802 Git blobs (14,058,689 bytes) in
that exact commit. Before importing any runtime code the stdlib guard rejects
changed, missing, untracked or ignored files and symlinks across the complete
checkout, then checks HEAD and the actual Python binary. Code lives separately
from the operator/configuration and output roots. Python uses explicit `-I -B`;
the controlled child environment disables pytest plugin autoload and bytecode.

Fresh read-only observation at 2026-09-27 00:21 ET verified the existing test
venv `/data1/yanruj/venvs/evolveswdb-test/bin/python3` and pytest 9.1.1; their
actual file hashes are in `config-template.json`. The initial system-Python
identity query could not import pytest and ran no tests. No installation was
performed. Node 1 is the prospective choice; it must still be free at dispatch.
The helper must pass a fresh full upstream host-subtree comparison before the
configuration's currently null `helper_upstream_comparison` field is filled.
The operator checks the pinned helper/hostlock bytes, both socket and legacy
metadata against kernel locks, current free lane, storage reserves and available
memory before each stage. A concurrent acquisition can make the helper refuse;
that is a retained failed attempt, never an automatic retry.

Before dispatch, root must seal a separate Git-carried configuration with the
verified helper comparison and update its hash. The manifest path is relative to
the configuration file. Export this operator directory by Git, separately from
the runtime, and verify its exact files before running it. Use the reviewed
operator/configuration SHA-256 values as environment variables:

```sh
OPERATOR=/absolute/git/operator.py OPERATOR_SHA=exact_reviewed_sha \
CONFIG=/absolute/git/sealed-config.json CONFIG_SHA=exact_reviewed_sha \
bash /absolute/git/launch.sh
```

The launch must be in the named tmux caller. Keep coordinator stdout/stderr in
the tmux buffer for bounded typed observation, rather than an uncounted sixth
raw-output root. After the group exists, ordinary coordinator exceptions are
retained in its fixed `operator-failure.json` and re-raised only when this exact
invocation exclusively created the group directory; refused retries never write
into an earlier root; pre-group failures
remain typed operator observations with no experiment output root. Do not precreate any of the
five reserved roots: two standard raw/dispatch pairs plus the group dispatch
folder. The operator creates them exclusively. Stage pane stdout/stderr and
helper/auditor logs remain inside those roots, including on failure. No raw output
or binaries are copied to the Mac.

After all audits pass, the operator reopens the complete retained identity sets,
checks current terminal process states, writes its last group closure artifact,
and runs the existing `validate_preparation_reservation` against the exact
consumer-shaped admission fragment. The final read-only allocated-byte count
covers all five roots. Its typed receipt is written outside those roots at
`/data/yanruj/EvolveSWDB_runs/bfs-supervision-recovery-linux-20260926-a1.final.json`,
following the existing external final-observation convention. This fixed closure
metadata is excluded from the five charged artifact roots by design; no test
output, runtime source, binary, or resource stream may be written there. The receipt is not
itself an admission to either scientific batch: their later fresh host/proof,
cost, deadline and runtime checks remain mandatory. No write to the five roots
may follow this final count.

Validation: fourteen bounded local operator controls and two independent lease
controls passed (16 total); shell syntax passed.
They exercise the deadline calculation, unresolved-pin rejection, fixed paths,
isolated arguments/environment, untracked import and symlink rejection, launch
preconditions and exact Git manifest. No local control substitutes for actual
Linux proof execution or independent post-exit closure.
