# A2 Linux fixture route

Created 2026-09-26 ET. Preparation only. No fixture or guest dispatch is authorized
by this document. The sole active native pilot remains unchanged until its whole
terminal outcome and independent cleanup audit.

The new `scripts/bfs_a2_linux_fixture.py` supervisor runs from a separately
reviewed code checkout. It tests exactly
`67313d9b2a45d9f0fb23d935b56e755a3a19fa7f` in a distinct clean checkout under
`/data1/yanruj`. It does not import that historical runtime into its own process,
change its files or plans, or substitute the newer simulator runtime. Before
any historical child import, immediate checkout entries must be Git-tracked
(except `.git`), including ignored files and packages; an untracked `pytest.py`
or `pytest/` cannot replace the selected test module. There are
only two allowed selections:

| Kind | Fixed pytest selector | Exact cases | New raw directory under `/data/yanruj/EvolveSWDB_runs/` |
|---|---|---|---|
| `owned_cleanup` | `tests/test_bfs_dx100_coverage_a2.py::test_linux_a2_reaps_detached_child` | `[False]`, `[True]` | `bfs-a2-owned-linux-20260926-a1` |
| `dx100_interruption` | `tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem` | `[raises]`, `[stalls]` | `bfs-a2-interruption-linux-20260926-a1` |

Each selection has its own original 90-second outer clock, captured in the owned
tmux pane before the normal socket helper. TERM at 60 seconds and KILL 30 seconds
later preserve that same deadline. Setup and three owned subprocess stages share
60 seconds: a fixed read-only `runtime_identity(673...)` command in the tested
checkout, the exact pytest selection, and the same runtime command afterward.
Each metadata command is capped at ten seconds and the remaining work budget.
Pytest receives only the remaining work budget. There is no retry, provider call,
empirical workload, protocol publication, or changed test selector.

`SharedCleanup`, `Owned`, `Monitor`, and `run_stage` from the separately pinned
supervisor runtime handle all three children and their observed/adopted
descendants. They share one cumulative 30-second cleanup and finalization budget.
The monitor stays active through teardown with finalization signals disabled;
its stop uses the actual remaining reservation. Limits are 512 MiB sampled whole
tree RSS and 512 MiB new output, nominal five-second samples, a maximum 30-second
telemetry gap, and 10 GiB build / 30 GiB raw free-space reserves. RSS is sampled,
not a kernel memory quota. Each runtime JSON is limited to 4 MiB. Final evidence
and pending-proof writes must finish before the original deadline.

The child environment removes Python startup/path/userbase/optimization inputs,
`PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, loader overrides and compiler search overrides.
It sets `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, with `PATH=/usr/bin:/bin`. The supervisor rejects Python optimization
before project imports; assertions must remain enabled. Use the already available
venv Python, freshly pinning its resolved executable and pytest version/module.
Disable pytest cache and place TMPDIR, basetemp, JUnit and logs under the new raw
root. Neither a historical checkout nor HOME receives output.

The retained driver distinguishes `supervisor_commit` / `supervisor_runtime`
from the tested `code_commit` / full A2 `runtime`. Both historical runtime JSON
files, all command lines, exits and log hashes are retained. Their parsed full
identities must match exactly. Supervisor bytes and pytest identity must also
remain unchanged. The pending proof uses the full tested A2 runtime, including
its root, Python, files, plan, project config and test files; a simulator runtime
hash subset is insufficient.

The supervisor only writes `proof.pending.json` with state
`tests_passed_cleanup_unverified`. It cannot attest its own process absence. After
the outer wrapper exits, an independent audit reopens driver, logs, JUnit,
snapshots, samples and the final shared ledger; checks all exits are zero; unions
actual pane/helper/timeout/supervisor, all three direct children and every
sampled/adopted identity; and checks PID plus start time. The exact released lease
generation and empty kernel lock must match. Only the precisely retained pane may
remain as an explicitly recorded zero-RSS zombie. Unknown/live descendants or an
unsettled/exceeded ledger leave the pending proof unaccepted.

After successful independent closure, seal a new immutable `proof.json` with
state `passed`, binding the pending file and terminal audit by path/hash. Preserve
the original fixture `started`/`finished` interval within 90 seconds; record the
later audit timestamp separately. Never overwrite the pending proof. Both admitted
proofs then enter A2's existing `linux_proofs` map; they remain contract fixtures,
not accelerator coverage or timing evidence.

The fixed CLI takes `KIND`, `--expected-supervisor-commit`, `--tested-checkout`,
`--python-sha256`, `--pytest-version`, `--pytest-sha256`, `--outer-started`,
`--outer-deadline`, `--pane-pid`, `--pane-start-ticks`, and `--lane`. Place normal
helper and outer-exit receipts in a new sibling `.dispatch` directory so the raw
selection root is absent on admission. The actual expanded argv, two runtime pins,
current helper identity, both socket/legacy locks, capacity and native terminal
reference must be recorded before launch. Future code hashes are deliberately not
guessed here. Neither this route nor its fixtures extend A2's existing window.
