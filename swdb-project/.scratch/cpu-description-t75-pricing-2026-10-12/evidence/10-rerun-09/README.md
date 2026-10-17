# Ticket 10 runbook: time the t75 pair and run the split check

Updated: 2026-10-13 01:50 ET. Branch `cpud/10-split-check`. Ran at `75036363` on mbit10.

## Result

| Record (under `records/`) | File sha256 |
|---|---|
| `evaluations/cpud10.t75-baseline.uniform22.t1.s0.evaluation.a1.yaml` | `2ff08872…d6b15f54` |
| `evaluations/cpud10.t75-candidate.uniform22.t1.s0.evaluation.a1.yaml` | `a46f17c4…ede4ed21` |
| `region_profiles/cpud10.t75-baseline.uniform22.t1.s0.profile.a1.yaml` | `edb9fcbe…43528259` |
| `region_profiles/cpud10.t75-candidate.uniform22.t1.s0.profile.a1.yaml` | `4b0faaff…707e9241` |
| `attributions/fga03.t75.uniform22.t1.attribution.a3.split-check.yaml` | `3a94ee9d…5614d9d9` |

Full hashes: `host-records-sha256.txt`. The Mac copies match them byte for byte.
Whole-store check of the mbit10 full copy: `OK: 733 record(s) valid` (`host-validate.out`).

## Order and times (`host-order.log`, `host-*.stderr`)

| Step (2026-10-13 ET) | Wall | Peak RSS |
|---|---|---|
| guard + kept-binary identity, 01:10:56 → 01:16:45 | 5 min 49 s | — |
| view A (closure of both candidates, mbit10, workload): 120 of 728 records | 7 s | 0.1 GB |
| `evaluate` baseline (20 trials) | 3 min 42 s | 1.1 GB |
| `evaluate` candidate (20 trials) | 3 min 33 s | 1.1 GB |
| `bfs-profile` baseline (5 reps) | 1 min 39 s | 1.1 GB |
| `bfs-profile` candidate (5 reps) | 1 min 33 s | 1.1 GB |
| view B (adds both `.a3` estimates): 160 of 732 records | 1 min 16 s | 0.8 GB |
| `attribute` with both profiles | 2 min 4 s | 1.8 GB |
| whole-store `validate` | 14 min 11 s | 4.2 GB |

Lane: node0, `mbit10-evaluation-node0` generation 523, load1 6.09 at start (`host-lane-10.json`).
The other socket ran another session's test suite throughout.

## Files

- `run.sh`: the job. `when-free.sh`: waits for a free socket lease, then runs it.
- `make_view.py`: builds a reference-closed record view (the test suite's `copy_closure` rule).
- Requests: `cpud10.t75-{baseline,candidate}.uniform22.t1.s0.{evaluation,profile}.a1.request.yaml`.
- `lr06.sh`, `lr06-identity.txt`, `lr06-remove.txt`: LR-06 evidence and removal.
- `attempt-a1/`: logs of the stopped first attempt.

## Why record views (attempt a1 stopped)

- Attempt a1 started 2026-10-13 00:00:14 ET on the full 1.3 GB store copy.
- Every `evaluate`/`bfs-profile` save re-validates and re-indexes the whole store
  (`workflow.persist` → `writer.commit` + `db.build`).
- a1 spent 41 min in the start-up check and 20+ min in its first save, before any trial.
  At about 4 saves per trial, one evaluation would have taken days.
- Stopped at 01:07 ET (`kill -9`; no trial ran, nothing committed). Lease released cleanly.
- Attempt a2 runs each command on a view. The new records were then copied into a full-store copy
  and checked there by one whole-store `swdb validate`.
- The evaluation does not depend on the view: its paired-estimate lookup matches no `.a3` slot
  (sources `[0]`, 20 reps vs. the counted `[0, 1234, 7777]` scope) in either store.

## Code changes this ticket needed (found before any timing)

- `bfs-profile` could not read a scalable (v3) evaluation. Fixed in `134e68fa`.
- Discovery failed on Clang's `omp.h` (`_OPENMP` 202011 with OpenMP parsing off). Found by a static
  precheck on mbit10 (discovery + region build only, no execution); fixed in `574be6e2`.

## Kept-binary identity note

`host-kept-identity-before.txt` shows different manifests for the two wrapper folders than ticket
03's table. The cause is sort order only: `run.sh` ran under the C locale; ticket 03 used
`en_US.UTF-8`. `lr06-identity.txt` prints both. The en_US values equal ticket 03's table, and
every file is dated 2026-10-11.
