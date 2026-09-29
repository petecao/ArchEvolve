# Independent Linux fixture proof closure

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).

`scripts/bfs_linux_fixture_audit.py` closes only the three selections in
`bfs_linux_fixture.py` and the two historical A2 selections in
`bfs_a2_linux_fixture.py`. It runs after the outer wrapper and helper exit. It
does not run a fixture, acquire a lease, signal a process, change an input, or
qualify empirical timing or simulator coverage.

Use the same controlled Python environment and exact supervisor checkout used
for the fixture. A2 retains its separate tested `67313d9` checkout and full
before/after runtime snapshots. The caller supplies the exact pending, lane,
outer-exit and final-ledger paths/SHA256, supervisor commit, node and lease
generation. Only the fixed raw selection root is admitted by the CLI.

The auditor reopens the pending and driver, exact commands, all child output
hashes, required unskipped JUnit names, runtime files and Python/pytest identity.
It requires the original 90-second outer interval, 60-second work admission and
30-second settled shared cleanup ledger. The whole-second helper timestamps are
treated as intervals; they do not replace the more precise driver clock. The
fixture outcome and every child/helper/outer exit must indicate success. Any
late failure, changed artifact, outstanding reservation or exceeded grant leaves
the pending proof unaccepted.

The process union includes driver, the exact captured pane and every intervening
ancestor, all three direct A2 children (or the single normal pytest child), all
sampled processes, retained owned identities, stage cleanup observations and final
cleanup observations. Each PID/start pair is checked twice. Reused PIDs are
recorded separately. The existing fixture protocol permits only the captured
pane as a zero-RSS zombie; another live or zombie process, or unavailable procfs
identity, fails closure. Both socket leases and the legacy lease are observed;
the fixture's exact generation and the legacy lease must be released with empty
kernel locks. The other socket may have an unrelated consistent held lease.

Periodic sampling cannot reconstruct unobserved short-lived processes. The
audit preserves that limit and does not infer absence from a terminated leader.

The audit has a separate 60-second metadata deadline and a 512-MiB cumulative
input-read bound. It changes none of the original fixture allowances. It writes
`terminal-audit.json` and a new `proof.json`, binding the original pending file
and audit by exact hash. Pending bytes and their original started/finished times
remain untouched; the later audit time is separate. Existing output names reject
another seal attempt. Failed preparation may leave an audit or staged proof;
neither is an admitted `proof.json`.

Example interface (replace every value with the retained exact identity):

```text
python scripts/bfs_linux_fixture_audit.py a2 owned_cleanup \
  --expected-supervisor-commit COMMIT \
  --pending PATH --pending-sha256 SHA \
  --lane PATH --lane-sha256 SHA \
  --outer-exit PATH --outer-exit-sha256 SHA \
  --ledger PATH --ledger-sha256 SHA --node 0 --generation GENERATION
```

Invoke under a bounded external 60-second read-only audit command after verified
outer exit. Preserve its actual exit and stdout/stderr before admitting the new
proof. Local synthetic tests verify rejection boundaries; no real Linux fixture
or independent host closure is claimed by those tests.
