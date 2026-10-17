# Full swdb suite on mbit10: `cpud/integration` vs base

Created: 2026-10-13 15:21 ET.

## Verdict

**No test fails because of this effort.** No test fails at head and passes at base.

| | Head `07b63e3e` | Base `e954e938` |
|---|---|---|
| Collected | 5,389 | 5,345 |
| Passed | 4,322 | 4,264 |
| Failed | 408 | 407 |
| Errors | 515 | 517 |
| Skipped | 144 | 139 |
| Not run | 0 | 18 (not needed: they pass or skip at head) |

- Head failures and errors: 923. All 922 that exist at base also fail there.
- The one head failure that has no base twin is a **new test**, and it fails for a known
  mbit10 environment reason (below). It passes on the Mac.

## The one new test that fails on mbit10

`tests/test_bfs_profiling.py::test_public_profile_of_a_scalable_v3_evaluation_times_regions_on_the_sg_input`

- mbit10 reason: `mbit10 evaluations cannot disable socket-lane policy` (the hostname guard).
- Its older sibling `test_public_compiled_toy_profile_and_fresh_rankings` fails at base for
  the same reason.
- On the Mac at head, this test and its two siblings pass (3 passed, 31.7 s, 2026-10-13).
- Not fixed here: the host-detection fix is another agent's ticket.

## Head failures by cause

All are pre-existing. Counts are head failures plus errors.

| Cause | Count |
|---|---|
| `swdb source-snapshot` hits the test's 600 s limit | 274 |
| mbit10 hostname guard (socket-lane policy, `/data1` build path, lane preflight) | ~330 |
| `swdb validate` on the whole store hits 600 s | 108 |
| Other whole-store commands hit 600 s (`register-workload`, `compare`, `view`, `bfs-coverage`, ...) | ~70 |
| Mac-only compiler path `/opt/homebrew/opt/llvm/bin/clang++` | 15 |
| Other, same failure at base | rest |

Only 2 shared failures have a different message at head and base. Both are environment
effects: one profiling test (head: host guard; base: source-snapshot timeout) and one
provider-workspace test (head: `/data1` build-path rule; base: node-1 memory admission).

## How it ran

- Host mbit10, one socket lane per side (head node 0 then node 1; base node 1), `-n 8`,
  `SWDB_TOOLCHAIN_FLAGS=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`, venv
  `/data1/yanruj/venvs/swdb-test`, temp under `/data/yanruj/EvolveSWDB_runs/`.
- Head and base ran at the same time, one per lane, instead of a base rerun afterwards:
  rerunning ~900 failing ids (most of them 600 s timeouts) would have cost about as much as a
  full base run.
- Wall time: 2026-10-13 04:55 ET to 15:20 ET (10 h 25 min). Lane time: head 10.2 h,
  base 9.9 h.
- `--report-log` per round; each result is the latest round that ran the id
  (`scripts/status.py`, `scripts/finalize.py`).

### Four rounds, and why

| Round | Ids | Why it stopped |
|---|---|---|
| 1 | all | Manual stop at 2 h 21 min: `/data` fell from 89 to 40 GB free |
| 2 | not finished in 1 | Manual stop: snapshot-namespace collisions (harness bug, below) |
| 3 | not finished + collided | Manual stop: xdist `load` left the last ~35 ids on one worker |
| 4 | the rest | Finished (`--dist worksteal`) |

**Harness lessons (for the next mbit10 suite):**

1. `-o tmp_path_retention_policy=none` does **not** remove per-test folders during the run.
   pytest 9 deletes them only at session end. A run-local plugin
   (`scripts/swdb_tmp_reaper.py`) empties each test's `tmp_path` after teardown.
2. Track `tmp_path` from `pytest_fixture_setup`. `item.funcargs` misses it when another
   fixture fails in setup, and those folders leaked (1.3 GB each).
3. Empty the folder, but keep it. Deleting it lets pytest reuse the same numbered path. On
   mbit10, `workflow._source_destination` hashes that path into
   `/data1/yanruj/EvolveSWDB_sources/<hash>`, so the next test collided (`FileExistsError`).
   Every collided id was rerun in round 3; none remains.
4. Use `--dist worksteal`. With the default `load`, the slow tail sits on one worker.

## Files

- `junit/<side>[-rN].junit.xml.gz`: JUnit XML per side and round (rounds 1–3 are partial,
  stopped with SIGINT).
- `classification.json.gz`: one merged outcome per test id per side, plus the
  classification lists.
- `lanes/`: `socket_lane.sh` records and `rc`/wall time per round.
- `env/`: host state at each round's start and end (load, users, disks, commit, memory).
- `scripts/`: run, lane, watchdog, reaper plugin, status and finalize scripts, plus the
  id lists for rounds 3 and 4. `run_suite.sh` shows its round-4 form (`--dist worksteal`).
- `watchdog.log`: why each round was stopped. The disk watchdog (`/data` < 25 GB or
  `/data1` < 12 GB) never fired.
- `head-collected.txt.gz`, `base-collected.txt.gz`: collected ids.
