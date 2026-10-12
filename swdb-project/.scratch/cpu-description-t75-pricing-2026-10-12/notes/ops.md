# Ops: running on mbit10, freeze/estimate, timing and the split check (C12, C13)

Written 2026-10-12 01:02 ET at `e2611242`. Paths are relative to `swdb-project/` unless absolute.
Load the `mbit10-runs` skill first (`/Users/yanrujhou/CLionProjects/ArchEvolve/.claude/skills/mbit10-runs/SKILL.md`).

## Lane dispatch (how prior runs did it)

- Check the leases: `grep -H '"state"' /data1/yanruj/lact-host-lease/mbit10-evaluation*.meta.json` (node0, node1, legacy).
- Dispatch from `/data1/yanruj/Memacc/AgenticRefiner/` after checking that `scripts/host/socket_lane.sh` is current:
  `bash scripts/host/socket_lane.sh <node> <job> --record <lane.json> -- bash -c 'cd <clean checkout>/swdb-project && timeout <s> <cmd>'`
  - Exit codes: 4 means the lease was refused; 5 means the load gate refused.
  - Prior lane records: `.scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair/lane-a2.json` (node1, gen 552), and every `11-*-mbit10-*.json` under `.scratch/lanl-db-analytic-eval-2026-10-06/evidence/` (`lane.socket_lane`).
- Calibrators take `--lane mbit10-evaluation-node<N>`. `swdb/cpu_service_native.py:13-41` `environment` checks:
  - the lane name is registered and verified live (`profile._verified_lane`);
  - the host is Linux x86_64 on mbit10;
  - LLVM 22 is used;
  - the output is under `/data1/yanruj` or `/data/yanruj`, with **≥ 20 GiB free** on that mount.

  `prepare` (lines 43–47) needs ≥ 7 reps and ≥ 0.05 s trials. The source checkout must be **clean and committed** (`dirty` check in each calibrator).
- **Disk:** at ticket-03 start, `/data1` had 21 G free and `/data` had 96 G (`env-start-a2.txt`). With `/data1` near 20 G, use `/data/yanruj/EvolveSWDB_runs/`.
- Pattern from prior runs: a `runner.py` or `run.sh` in the raw folder, run under the lane. Copy the canonical `records/` into `$RAW/records` and work only on that copy. Export compact records and receipts to git afterwards (see `11-bulk-total-runbook.md`).

## Measured durations (for planning)

| Step | Time | Source |
|---|---|---|
| clock service elapsed | ~4.5 min | `11-clock-service-mbit10-20261006-a2.json` |
| allocator elapsed | ~9 min | `11-allocator-service-…-a1.json` |
| memory elapsed | ~8.5 min; byte-read ~4 min | `11-memory-service…`, `11-byte-read-service…` |
| bulk-total, 2 batches / 48 sizes | ~21.5 min | `11-bulk-total-elapsed-…-a1.json` |
| OpenMP elapsed | ~10 min | `11-openmp-elapsed-…-a1.json` |
| `freeze-protocol` (whole-store check inside) | **~50–53 min each** | `order.log` (21:32 → 22:25) |
| `estimate` per side (t75, 286–289 regions) | ~25 min | `order.log` |
| whole-store `swdb validate` on mbit10 | ~14 min, 3.9 GB RSS | `validate-mbit10-head-528eadb6.txt` |
| whole-store check on the Mac | ~50 min, ~7 GB (Mac RAM rules: one at a time) | spec, MEMORY |
| `Store('records')` load + `require_team_safe` ×4 on the Mac | ~3 min | this session |

## Freeze and estimate (ticket-03 recipe)

Script: `.scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair/run-fga03-a2.sh`. For the rerun (C13), skip the `characterize` steps and reuse the counts.

1. **Protocol request per side.** The t75 sides have different argv, so there is one protocol per side. Ticket 03's frozen inputs: `freeze-baseline.yaml`, `freeze-candidate.yaml` (same folder). Build `.a3` requests:
   - `settings.target_description: mbit10.cpu.lanl20261006.t1.services.v2`
   - `estimator_version: swdb.analytic.v1`, `threads: 1`, `roi: bfs.complete_call.v1`
   - `sources: [<side's source id>]`, `inputs: [bfs-20261004-uniform22.2f83a134a6bef789]`
   - `input_run_arguments` copied from the characterization's `source.run_arguments`. These point at `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/swdb-protected-cpu-wrapper-*`, which is **kept, so do not delete it before the rerun**.
2. Freeze: `python3 -m swdb freeze-protocol <req.yaml> --records <store> --format json`. It returns a content-suffixed ID; use that ID.
3. Estimate:
   ```
   python3 -m swdb estimate --records <store> --characterization fga03.t75-<side>.uniform22.t1.characterization.a2 \
     --target-description mbit10.cpu.lanl20261006.t1.services.v2 --protocol <frozen id> \
     --id fga03.t75-<side>.uniform22.t1.estimate.a3 --format json
   ```
4. F47: freeze both protocols at the **same commit**, after every evaluator change. `estimator_sha256` comes from the protocol (`swdb/analytic.py:690`). `swdb attribute` requires equal `input`, `target_description_sha256`, `threads`, `evidence_kind` and `estimator_sha256` (`swdb/attribution.py:123`, `COMPARABLE`).
5. Order log: copy `log()` / `step()` from `run-fga03-a2.sh` (ET timestamps into `order.log`).

## C4 trial: `unknowns_summary.py` cannot be pointed at trial estimates

`.scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair/unknowns_summary.py`:
- hard-codes `ESTIMATES = {...estimate.a2}` (lines 25–26);
- reads `PROJECT/records/estimates/<id>.yaml` (line 84);
- writes `unknowns-summary.json` **beside itself**.

To use it on trial estimates kept in a scratch store, copy or parameterize it (estimate IDs, records root, output path). Running it unchanged reads the old a2 estimates and **overwrites the committed evidence file**.

## Timing (ticket 09 recipe, adjusted by F43/F44)

Source: `.scratch/fine-grained-attribution-2026-10-11/issues/09-split-check.md` (Progress, "What the mbit10 run must do").

0. Unchecked report first:
   ```
   python3 -m swdb attribute --records … --baseline-estimate … --candidate-estimate … \
     --baseline-source typed-library-bfs-scalar-profile-20261003-a1.baseline \
     --candidate-source extensa-native-bfs-20261005-a8.it1.kronecker.a0 --id <report id> --format json
   ```
   Optionally add `--site-finder …`. CLI at `swdb/attribution.py:127-150`.
1. `python3 -m swdb evaluate <request.yaml> --runs-dir <dir> --lane <lease>` per side (`swdb/cli.py:193-196`). Request: copy `fga03.t75-<side>.uniform22.t1.request.a1.yaml`, but with **`sources: [0]`** (the counted source; the a1 requests say `[0, 1234, 7777]`). Keep `evaluator: swdb.native.evaluator.scalable.v3`, `repetitions: 20`, and the LLVM 22 `clang++` build block.
2. `python3 -m swdb bfs-profile <profile request> --runs-dir <dir> --lane <same lease>` (`swdb/cli.py:207-210`; `swdb/bfs_profiling.py:197-`). The request has `message_version`, `id` and `evaluation: <evaluation id>`. The profile copies the evaluation's `context`, including `sources`, and must run on the evaluation's host and lane socket.
3. The checked report adds `--baseline-profile <rp id> --candidate-profile <rp id>`, then run `swdb validate`.

## Split-check rule and F43/F44 exact semantics (code)

- `swdb/attribution.py:1266-1277` `SPLIT_RULE`: id `swdb.split_check.v2`, `max_abs_share_gap 0.1`, tolerance 1e-9. Validation refuses any other rule (line 1236).
- `swdb/attribution.py:1307-1327` `_check_identity` (F44):
  - profile `machine` == characterization `host.machine`;
  - sorted set of `context.sources` == sorted union of `trials[*].sources` of the characterization (t75 counts: source 0);
  - generator seed equal.
- `swdb/attribution.py:1330-1360` `_Profile.__init__`:
  - outcome `partial`/`complete`;
  - `context.candidate_sha256` == source artifact sha;
  - workload == estimate input;
  - threads equal.
- **F43 at lines 1347–1353:** `str(profile['created']) > max(str(e['created']) for e in estimates)`.
  - This is a **lexicographic string compare of `YYYY-MM-DD`**. `created` comes from `writer.today()`, the ET calendar date (`swdb/writer.py:31-38`; falls back to UTC−4 without a tz database).
  - So it requires a **strictly later ET calendar day**, not a later timestamp.
  - It checks the **region_profile record's** `created` (`bfs_profiling.py:107`), not the evaluation's.
  - An evaluation timed on the same day as the estimates would pass if `bfs-profile` ran the next day. The spec's intent (C13: time on a later date) is stricter, so run the evaluation itself on a later ET day too.
- Estimates are dated by `created` only. Estimates made on day D mean evaluation and profile must run on day D+1 ET or later.

## Prospective order (C12) as a checklist

1. All calibration runs (microbenchmarks only; no t75 binary executes).
2. t75 OpenMP projections (static, no execution).
3. Bind `services.v2` into a store copy.
4. `swdb validate`.
5. Commit and push.
6. Freeze the `.a3` protocols (same commit).
7. Estimate both sides.
8. Next ET day or later: evaluate source 0, then `bfs-profile`, then checked `attribute`, then validate.

Kept binaries: `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/` (65.7 MB; manifest hashes in the ticket-03 Answer). Remove them after the last reader (LR-06).
