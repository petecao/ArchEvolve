# T15 corrective Linux proof group — 2026-09-26 ET

State: prospective only. No fixture or auditor invocation is authorized by this file. The reviewed final Git commit and pristine new checkout replace `NEW_PIN` and `NEW_ROOT` before execution. Existing a1/a2 fixture roots and the active 8c39 campaign checkout stay unchanged.

The fixed group is `bfs-t15-correction-linux-20260926-a1`. Its original aware start is captured before the fresh on-host preparation checks; the deadline is exactly start + 600 seconds. The charged five roots are the two a3 fixture roots, their `.dispatch` siblings, and `/data/yanruj/EvolveSWDB_runs/bfs-t15-correction-linux-20260926-a1.dispatch`. The whole 600 seconds and 2,147,483,648 bytes are nonrefundable preparation charges. Any failure or deadline/storage overrun prevents corrective batch admission; neither fixture nor auditor is retried.

## Order and bounds

1. Confirm all five roots are absent, then create only the group dispatch directory and write `preflight.json` with `id`, `code_commit`, and the original `observed_at`. Preserve the initial helper identity, both socket/legacy metadata and kernel locks, node1/global capacity, disk reserves, original group deadline and controlled environment. Normal helper alignment is mandatory. A consistently held T16 node0 lease is recorded and preserved; node1 and the legacy lease must be released and unlocked.
2. Within the same group clock, run one read-only allocator parity check, at most 30 seconds overall, over each of the two closed T15 roots and two closed gzip-smoke roots. Compare the new process-free allocation function with a separate `du -sk ROOT` for each root. Require respective combined totals 11,014,971,392 and 200,704 bytes. Retain per-root values, exact closed references and actual elapsed time in `allocation-parity.json`; write nothing in those historical roots.
3. Run `owned_cleanup` once with ID `bfs-simulator-owned-linux-20260926-a3`, on node1 through the unchanged normal socket helper and named tmux. Capture the fixture outer timestamp and pane PID/start before helper entry. The existing standard runner executes four unskipped tests under its original 90 seconds (60 work + one shared 30 cleanup), 512 MiB sampled RSS/output. Original absolute end is never reset. Before starting, require at least 200 seconds remain in the group for fixture, independent audit and final readback/accounting.
4. After actual fixture/helper/timeout termination and outer exit0, run the existing standard post-exit auditor exactly once, under its separate original 60-second deadline. It verifies the complete retained PID/start union, two current observations, exact released generation/kernel lock, runtime, JUnit, settled cleanup ledger and immutable pending proof. Its receipt stays at `<fixture>.dispatch/audit-receipt.json`.
5. Wait for the auditor wrapper itself to exit, retaining the actual return code in `<group>.dispatch/owned_cleanup.audit-wrapper.exit`. Only on exact integer0, reopen/hash the immutable audit receipt, proof, pending and terminal audit and verify their bindings. Capture `finished` after these reads. Write `owned_cleanup.readback.json` once with the exact shape below. A post-write reread checks that file bytes are durable and still within the group clock; this is charged preparation.
6. Repeat steps3–5 once for `dx100_interruption`, ID `bfs-simulator-interruption-linux-20260926-a3`, two unskipped tests. Use the separate `.dispatch/dx100_interruption.audit-wrapper.exit` and `.dispatch/dx100_interruption.readback.json`. There is no overlap on node1.
7. After all helper, auditor, stdout/stderr and receipt writers have exited and every planned write has finished, perform the final read-only process-free count of all five canonical roots. Capture group `finished` after that count; require elapsed <=600 seconds and total allocated bytes <=2 GiB. Emit the final actual admission fragment outside all five roots. No later write in those five roots is permitted; any necessary later write requires a new final recount within the same original deadline and does not restore time.

## Literal public runner and auditor arguments

The fixture command uses the existing reviewed controlled environment map, no pytest entry-point/plugin autoload, no user-site injection and no optimization. The pinned venv executable resolves to the independently hashed system Python; pytest version/hash are reopened at admission.

```
timeout --signal=TERM --kill-after=30s <remaining-to-original-fixture-end-minus-30>s \
  bash /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh \
  1 FIXTURE_ID --record FIXTURE_DISPATCH/lane.json -- env CONTROLLED_ENV \
  /data1/yanruj/venvs/evolveswdb-test/bin/python3 -s NEW_ROOT/scripts/bfs_linux_fixture.py \
  KIND --expected-commit NEW_PIN --python-sha256 PYTHON_SHA \
  --pytest-version 9.1.1 --pytest-sha256 PYTEST_SHA \
  --outer-started ACTUAL_START --outer-deadline ACTUAL_START_PLUS_90 \
  --pane-pid ACTUAL_PANE_PID --pane-start-ticks ACTUAL_PANE_START --lane 1
```

```
timeout --signal=TERM --kill-after=1s <remaining-to-original-audit-end-minus-1>s \
  /data1/yanruj/venvs/evolveswdb-test/bin/python3 -s NEW_ROOT/scripts/bfs_linux_fixture_audit.py \
  standard KIND --expected-supervisor-commit NEW_PIN \
  --pending RAW/proof.pending.json --pending-sha256 ACTUAL_SHA \
  --lane DISPATCH/lane.json --lane-sha256 ACTUAL_SHA \
  --outer-exit DISPATCH/outer.exit --outer-exit-sha256 ACTUAL_SHA \
  --ledger RAW/cleanup-ledger.json --ledger-sha256 ACTUAL_SHA \
  --node 1 --generation ACTUAL_GENERATION
```

Auditing is a read-only post-lease operation, not a new lane claim. Therefore there is no invented second helper receipt for it: `lane.json` proves the fixture helper exit; the actual audit timeout return and final wrapper exit are separately retained.

## Receipt shapes

The existing audit receipt retains `id`, `audit_started`, `audit_finished`, `host_wall_s`, `outer_seconds:60`, integer `returncode:0`, `state:complete`, and hashed `invocation`, `stdout`, `stderr`, `exit`, `pending`, `proof`, `terminal_audit`. `audit_finished` is the time the bounded auditor subprocess returned; it is not misrepresented as the later wrapper readback endpoint.

Each group readback contains:

```json
{
  "id": "EXACT_FIXTURE_ID",
  "audit_receipt": {"path": "EXACT_FIXTURE_DISPATCH/audit-receipt.json", "sha256": "ACTUAL"},
  "proof": {"path": "EXACT_FIXTURE_RAW/proof.json", "sha256": "ACTUAL"},
  "pending": {"path": "EXACT_FIXTURE_RAW/proof.pending.json", "sha256": "ACTUAL"},
  "terminal_audit": {"path": "EXACT_FIXTURE_RAW/terminal-audit.json", "sha256": "ACTUAL"},
  "wrapper_exit": {"path": "GROUP_DISPATCH/KIND.audit-wrapper.exit", "sha256": "ACTUAL"},
  "wrapper_returncode": 0,
  "finished": "ACTUAL_AWARE_TIMESTAMP_AFTER_WRAPPER_EXIT_AND_ALL_REFERENCED_HASH_READS"
}
```

The final admission fragment is `preparation_reservation:{preflight, finished, raw_bytes, audits:{owned_cleanup,dx100_interruption}, auditor_readbacks:{owned_cleanup,dx100_interruption}}`, with each reference bound to its actual immutable file. `linux_cleanup_tests` contains the two sealed proof refs. Require proof.finished <= audit_started <= terminal.observed_at <= audit_finished <= readback.finished <= group.finished. The independent auditor clock is separate from each original fixture clock, while all costs fall inside the one group envelope.
