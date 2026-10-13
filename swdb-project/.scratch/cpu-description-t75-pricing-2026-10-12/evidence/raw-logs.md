# Raw lane and stdout/stderr logs, removed from git

Created: 2026-10-12 20:54 ET (code review housekeeping, branch `cpud/review-fixes`).

**Why:** these files were raw run output (lane wrapper stdout, command stderr, a pytest log).
Raw run output does not belong in the repo (`.claude/rules/remote_server.md`). Each is listed
below with its size and sha256, so a copy can still be checked. The files are in git history
up to commit `ddd50b27` (branch `cpud/review-fixes`); restore one with
`git show ddd50b27:swdb-project/.scratch/cpu-description-t75-pricing-2026-10-12/evidence/<file>`.

**Kept:** the compact lane records (`lane-*.json`), runbooks, scripts, hashes and summaries.
Evidence folders `09-*` and `10-*` belong to other agents and were not touched.

| File | Bytes | sha256 | Content |
|---|---|---|---|
| `01-trial-bind/phase-a/attempt1/projection-baseline.stderr` | 64 | `bbc57c725831351e2ebcb3cfe5cdd1bc02c64c6615fe1c2dab98a2ceb15b0629` | openmp-projector: call map mismatch at 1119 (fixed in ticket 01) |
| `01-trial-bind/phase-b/lane-b.out` | 1613 | `05d7f0ae713adf0a3c5f9cdaf2482ed70b94842666ae618484540464712436bd` | lane `mbit10-evaluation-node1` gen 555, job `cpud01-trial-b`, start 2026-10-12T05:29:03Z; the log holds only the start record; load1 at start 20.16 |
| `01-trial-bind/phase-d/lane-d.out` | 2328 | `8e7f8fc1fba74c4ac0cec716429763fdc3746a5870b940a86bc1f574454f9d6d` | lane `mbit10-evaluation-node1` gen 557, job `cpud01-trial-dry`, 2026-10-12T09:25:57Z to 09:38:19Z, exit 0, load1 at start 0.94 |
| `01-trial-bind/phase-d/dry.stderr` | 97 | `940b8df7264815d7a146ca5bab11256c1cea6df5721ea77cdc9e43f4d010b70f` | baseline: seconds=None, 6/286 regions unknown, 369.2 s; candidate: seconds=None, 6/289 unknown, 371.5 s |
| `07-calibrations/lane-a.out` | 1727 | `fe9da22fa97ffcc175ae3aa472f9dba5a367b2b82a98c7218b95785408d8bf8d` | lane `mbit10-evaluation-node1` gen 559, job `cpud07-calib-a`, 2026-10-12T15:39:43Z to 16:54:59Z, exit 0, load1 at start 7.97 |
| `07-calibrations/lane-b.out` | 1729 | `36cf30bd48e9f85478373447eea0dd63dd1cc6e16bea6c811e88e7acd0028eeb` | lane `mbit10-evaluation-node1` gen 558, job `cpud07-calib-b`, 2026-10-12T14:50:09Z to 15:39:31Z, exit 25 (library-call attempt 1), load1 at start 5.76 |
| `07-calibrations/lane-l.out` | 1727 | `950806ad3421389d30ebfa6992ef1e5075bce4b0e9c5df3ff32bf68bf471adc8` | lane `mbit10-evaluation-node1` gen 561, job `cpud07-calib-l`, 2026-10-12T16:55:07Z to 17:21:22Z, exit 0, load1 at start 8.19 |
| `07-calibrations/lane-t1.out` | 1727 | `1a9d4a4282fc3f3a37ff3080076475306caf78ed5c63a086054bda2bc1dd73ef` | lane `mbit10-evaluation-node1` gen 560, job `cpud07-calib-t`, 2026-10-12T16:54:59Z to 16:55:02Z, exit 1 (native OpenMP tests, attempt 1), load1 at start 8.12 |
| `07-calibrations/lane-t2-refused.out` | 224 | `c6301a8e271708f6dd0e2a3a1feea02e1905ae3c16ba7019124452a46fe60bad` | hostlock refused: lease timeout after 600 s on `mbit10-evaluation-node1` (holder generation 562); lane_rc=4 |
| `07-calibrations/libcall-attempt1.err` | 84 | `af9e5d0077ef28c9506d7361511e62c4ffc7afcb3f2c9c110091ce5ecc90f351` | native library call: paired ordering/resolution differs (pilot headroom bug, fixed `f2d41156`) |
| `07-calibrations/openmp-native-tests-attempt1.out` | 6644 | `d52f80a7589bcb6c63a3465f2ab326f25fd29748057c053602f82b9c0e439e5f` | pytest: 2 native OpenMP tests failed in 2.11 s (`'cstddef' file not found`, no toolchain flag) |
| `08-bind/lane-08.out` | 2741 | `c7c6fa05a47be1d9f299c1d8a1015934c91b4dc947726df9f4661b26fdc0aa88` | lane `mbit10-evaluation-node0` gen 519, job `cpud0809-job-08`, 2026-10-12T21:20:37Z to 21:54:45Z, exit 0, load1 at start 7.39; bind 20 min, services.v1 byte-identical, services.v2 sha256 `70fc5553…`, whole-store validate 14 min |
