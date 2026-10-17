# One early-exit7 fixture dispatcher — source preparation

Prepared 2026-10-07 ET. NOT RUN. Only stdlib AST parsing and source-byte hashing were performed. No SSH, selected fixture/supervisor import, main, synthetic test, source staging, Store, native tool probe, campaign or scientific action occurred. Existing source packets and worktrees remain unchanged.

The parent selects exactly one future invocation after full source review and live readiness. This source creates no stager or replacement supervisor: it invokes the direct primary-archive 388b fixture, which uses unchanged 503f exporter-mode `supervise(fixture=True)`. The selected 928 exporter is byte-checked and never imported or run by the fixture. No reader-mode runtime or actual exporter/reader admission follows from this case.

## Source and future invocation

- Dispatcher: `/private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1.py`, 27376 bytes, SHA `dc4c1f1111a7339414e83cd8faaa4f4922439ab502258e6baecc17e59642ee53`.
- Decoded remote program SHA: `65c948a81ce397651a092b0e20f771b9a820a6f130b94256f18d983c9c54047f`. It travels over SSH stdin; no remote source copy is staged.
- Last supplied delivered target: `673b39d75ec8ab2b7d1ca19cc6ec7e180444cb4e`. The required CLI revision must be the exact parent-selected delivered HEAD at invocation, rather than an invented future revision.

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 \
  /private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1.py \
  --delivered-revision 673b39d75ec8ab2b7d1ca19cc6ec7e180444cb4e \
  --dispatcher-sha256 dc4c1f1111a7339414e83cd8faaa4f4922439ab502258e6baecc17e59642ee53 \
  --output-directory /private/tmp/lanl14-reviewed-early-nonzero-dispatch-actual-20261007-a1
```

The local interpreter in this recipe is an explicit existing macOS path, not a remotely measured tool. SSH argv is `/usr/bin/ssh -T -o BatchMode=yes -o ConnectTimeout=20 mbit10`, followed by the shell-quoted remote `/usr/bin/python3.12 -B - <deliveredRevision> <dispatcherSHA> <decodedRemoteSHA>`. Only these reviewed public arguments are retained. No full environment, authentication file or process argv is dumped.

## Complete remote payload argv

```json
[
  "/usr/bin/timeout",
  "--signal=TERM",
  "--kill-after=60s",
  "360s",
  "/usr/bin/bash",
  "/data1/yanruj/Memacc-repro-20260925/AgenticRefiner/scripts/host/socket_lane.sh",
  "1",
  "swdb-lanl14-lifecycle-early-nonzero-20261007-a1",
  "--record",
  "/data/yanruj/EvolveSWDB_runs/lanl14-lifecycle-administration-20261007-a1/dispatch/lane.json",
  "--lease-timeout-s",
  "30",
  "--",
  "/usr/bin/python3.12",
  "-B",
  "/data1/yanruj/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-export-reader-lifecycle-supervisor-controls-20261007-a1/lanl14_export_reader_early_nonzero_linux_fixture_20261007_a1.py",
  "--fixture-sha",
  "388b9b1be3ce29c3d677ab2796c049793bf763504d4be7ad8e9f399c94354624",
  "--supervisor",
  "/data1/yanruj/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-export-reader-lifecycle-supervisor-controls-20261007-a1/lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py",
  "--supervisor-sha",
  "503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f",
  "--helper",
  "/data1/yanruj/lanl17-control-20261006.py",
  "--project",
  "/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project",
  "--selected-source",
  "/data1/yanruj/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-lossless-report-export-controls-20261007-a1/lanl14_final_export_lossless_gzip_20261007_a1.py",
  "--python",
  "/usr/bin/python3.12",
  "--python-sha",
  "e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f",
  "--cwd",
  "/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project",
  "--output",
  "/data/yanruj/EvolveSWDB_runs/lanl14-lifecycle-administration-20261007-a1/lanl14-export-reader-control-early-nonzero-a1"
]
```

The wrapper uses positional lane `1` and default alignment; `--no-align` is absent. Its Bash re-exec and lane-writer `python3` resolve through the explicit PATH below and are checked against the native paths.

```json
{
  "LC_ALL": "C",
  "MKL_NUM_THREADS": "1",
  "NUMEXPR_NUM_THREADS": "1",
  "OMP_DYNAMIC": "FALSE",
  "OMP_NUM_THREADS": "1",
  "OMP_THREAD_LIMIT": "1",
  "OPENBLAS_NUM_THREADS": "1",
  "PATH": "/usr/bin:/bin",
  "PYTHONDONTWRITEBYTECODE": "1",
  "PYTHONPATH": "/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project",
  "VECLIB_MAXIMUM_THREADS": "1"
}
```

`A5_PREREGISTRATION_SHA256` is additionally set only to the newly written actual preregistration identity. No unknown value is invented here.

## Future gates, originals and limits

The native root-owned ELF files are checked against the four exact SHA/size pins supplied in the original native-facts receipt (Python e50d, timeout1269, Bashbc59, Git06b2). Native host Linux/mbit10/account UID114316761 is required. Startup overrides listed by that original observation must be absent; no values are printed. No version or compiler commands are used.

Primary `yanrujhou_main` HEAD and `origin/yanrujhou_main` must equal the explicit delivered revision, with clean tracked/untracked status. Direct selected archive bytes must equal their exact delivered Git blobs and immutable 503f/388b/928 SHA/size pins. The C checkout must retain exact C HEAD f893fed and clean tracked/untracked status. Both portable source bundles must remain 185 modules/F6. Source-only local `git ls-tree` confirmed immutable C has **665 YAMLs**, while primary must have **686**; these separate memberships are checked without YAML parsing or Store. Ignored history is never removed.

MemAcc fetches **origin yanrujhou_main**, then compares both socket_lane.sh and hostlock.sh to that authority. Socket wrapper must retain 00c269. Only object/ref fetch and read-only Git operations occur: existing dirty working files are not modified; before/after dirty-status hashes are checked, without claiming a full concurrent dirty-byte audit.

Immediately before the fixture, node1 and legacy must be released. Node0 must independently remain the actual ticket14 job `swdb-lanl14-reports-final-20261007-a1`, generation510, with UID/PID/start, authoritative FD9, original lane/child route, e79 helper and NUMA confinement checks. Its scientific record bodies/outcomes are not opened. The test's completed lane must name node1, the exact payload, matching preregistration and bind:1 affinity, normal alignment and exit0. A changed or completed node0 holder causes refusal; it is not retrospectively declared safe.

Capacity gates retain MemAvailable≥80GiB, /data1 free≥21GiB, and the prior administrative fixture /data minimum≥2GiB. These are live future checks, not clearance or measured test duration. The already observed free values do not prove future readiness.

A fresh owned nonsymlink **0700** container and dispatch directory are required; fixture output is fresh and left to the original fixture. Original stdout/stderr, preregistration, lane record, wrapper exit, dispatcher cleanup and result are **0600**, never overwritten. Local SSH start/stdout/stderr/custody are separately preserved under a fresh **0700** private-tmp directory. Both new seals explicitly use canonical_ensure_ascii=False; original fixture False seals and original unsealed cleanup bytes retain their policies. No error or partial directory is deleted, normalized or retried.

GNU is exactly TERM360/KILL60. Remote metadata uses a shared540-second deadline, fixed Git calls capped25 seconds, and refuses launch unless460 seconds remain for the original GNU/cleanup window. The payload wait440, original stop_group15+5 and original31e cleanup15+5 remain bounded. The remote parent becomes a subreaper **before preflight Git children**, uses only those exact original cleanup primitives on every post-container exit, and retains cleanup custody. Local SSH is capped600 plus TERM20/KILL5 local-group cleanup. These enclosing administrative bounds are unproved and do not alter worker100, harness alarm240, original production exporter18000 or scientific limits.

Only one remote child launch exists; no tmux, source checkout/stage, provider, application timing or source/control main is introduced. Receipt success requires wrapper0, exactly one fixture case with original worker7, source/native pins, bound completed node1 lane, empty owned cleanup and unchanged independent source gates. Source preparation sets no actual passed/admitted fact. The parent must inspect original actual receipts and held sibling state after the selected one run.

No concrete source blocker remains in this preparation. Actual lease visibility, capacity, original output freshness, current delivered revision and timing are future checks. The native-probe receipt and all prior source/history remain byte-exact.
