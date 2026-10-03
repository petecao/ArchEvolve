# Remaining-ticket audit

Audited: 2026-10-03 UTC. Source and remote checkout: `8959b4dfd149273e89884be87bee9c0adb60e0fc`. This note records observations; the parent task owns tracker updates.

| Ticket | Actual state from this audit | Concrete next action |
|---|---|---|
| 01 | Both messages sent through institutional Gmail and verified in Sent; exact body hashes and immutable message IDs are in `send-receipts-01-21.json`. | Parent records real channel/date receipts and closes ticket. |
| 02 | Working license authorized; Peter's actual license confirmation remains absent. User will ask Peter separately. | Await and record Peter's actual answer; no substitute approval or agent license request. |
| 03 | Parent confirmed ticket closed after reconciling the legacy handoff map/crosswalk with real 01 receipts. ADRs remain proposed. | No remaining action in this audit. |
| 04 | Three personal updates sent once and verified in Sent; exact body hashes and immutable message IDs are in `send-receipts-04.json`. | Parent records real channel/date receipts and closes ticket. |
| 21 | Published YAML link and exact file SHA sent to Peter and verified in Sent. | Parent records real date/channel and closes ticket. |
| 30 | First actual gem5 comparison and both point ratios do not yet exist; no result/claim send can truthfully complete. | Finish diagnostic companion and timed baseline/candidate runs, then send actual result and record `swdb claim` with both comparisons/audience. |
| 32 | Fresh public dry-run now limited strictly to the failed smoke owner: two proposed checkpoint files, 18,039,198 bytes, with nine compact files preserved. No approval or deletion performed. Earlier broad/small inventory is historical audit context only. | Parent reviews the new exact failed-smoke listing, records approval, applies guarded retention, then verifies receipts and before/after space. No heavy historical scan is needed for this bounded cleanup. |
| 37 | Real scored statement table does not yet exist; mapping email is a separate unscored artifact. | Complete real profile and guarded provider/scoring run, send resulting table to Josh with source/commit, retain actual send receipt. |

## Exact cleanup evidence

Public command: `/usr/bin/python3 -m swdb prune --dry-run --format json` from `/data1/yanruj/ArchEvolve/swdb-project`, with these explicit roots:

- `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925`
- `/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926`
- `/data/yanruj/EvolveSWDB_runs/bfs-t20-ac10-companion-20260929-b1`

Listing remains on mbit10 at `/data1/yanruj/EvolveSWDB_runs/typed-library-t32-small-dry-run-20261003-e69ebe7eb5dc4571ab7f49bc008ff217.json`. SHA-256: `acb99a1bab60aec841ef20a2819e78de38fdbf24c19c2d614672c8114b900fa2`. Created `2026-10-03T12:21:56.386128+00:00`.

463 files were classified: 430 compact, 25 input, 8 bulky. Four proposed files total 36,287,251 bytes (34.61 MiB); `deleted: []`. The six-owner shared checkpoint and unowned companion checkpoint files were not proposed. Broad roots contain symlinks and the public listing refuses them; no symlinks were removed. Name-only inventory of all historical roots contained 245 bulky-named files totaling 53,148,735,659 bytes (49.50 GiB), which is not an eligibility decision.

| Exact proposed path | Bytes | SHA-256 | Owner and review finding |
|---|---:|---|---|
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-smoke-20260925-a3/checkpoint/cpt.2117142500/m5.cpt` | 361,986 | `f335ddd7b5db4f4d741fefb3b415f8491f96eee55e567eee3e3b59c1c607ce20` | `bfs-dx100-smoke-20260925-a3`: checkpoint missing observation, correctness unverified; no checkpoint manifest. |
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-smoke-20260925-a3/checkpoint/cpt.2117142500/system.physmem.store0.pmem` | 17,677,212 | `903f6e87be7f977433c34a1ac1104c6332300d4fe1994495ad92de51e963c7f1` | Same failed owner. |
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926/bfs-dx100-coverage-20260926-a1/bfs-dx100-coverage-20260926-a1.execute/checkpoint/cpt.5606354000/m5.cpt` | 459,735 | `6fc9a38ce4738106aebf8eca38b37f03cca941ff87c2dd18ed66ba9d0d84ec1d` | `bfs-dx100-coverage-20260926-a1.execute`: still recorded running/simulation, correctness unverified; checkpoint manifest pinned. Hold pending custody decision. |
| `/data/yanruj/EvolveSWDB_runs/bfs-dx100-coverage-20260926/bfs-dx100-coverage-20260926-a1/bfs-dx100-coverage-20260926-a1.execute/checkpoint/cpt.5606354000/system.physmem.store0.pmem` | 17,788,318 | `b901d39bb81b746b2893804108f16698b7834176698db12d93d944575767d2b6` | Same running-record owner; hold. |

`fuser -v` on all four exact paths returned exit 1 with empty stdout/stderr: no accessible open handles were reported. This observation does not resolve a stranded running record or establish that a checkpoint has no future input use.

Before listing, `df -B1` reported 46,567,579,648 bytes available on `/data1` and 78,819,528,704 bytes on `/data`. No after-deletion figure exists because nothing was deleted. The heavy scan is deferred to avoid perturbing the active native/profile job on node 0; the cache inspection on the other review task concerns different roots.

## Replacement bounded listing for ticket 32

At the parent's direction, the cleanup proposal was narrowed to exactly `/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/bfs-dx100-smoke-20260925-a3`. The public CLI was run with CPU affinity 1 (node 1) and a new output path. This replacement listing excludes the still-running coverage owner and every other run root.

Listing: `/data1/yanruj/EvolveSWDB_runs/typed-library-t32-failed-smoke-dry-run-20261003-3399d76720944650bca75ef2074c9703.json`. SHA-256: `feb871b74833f8a88822af1321baeeaa762ac37e79dacdd2537521d46661c636`. Created: `2026-10-03T12:28:24.741472+00:00`. Eleven files: nine compact and two bulky/proposed, totaling 18,039,198 bytes (17.20 MiB), `deleted: []`.

The exact proposals are the first two smoke paths in the table above, with unchanged bytes and SHA-256. At `2026-10-03T12:29:31.848570+00:00`, fresh custody inspection found both are regular files owned by `yanruj`, resolve to the exact listed paths, and have no symlink component. Each has only one record reference: the failed smoke evaluation's `raw_artifacts.path`. Its outcome remains `missing_observation` at checkpoint, correctness is unverified, team state is pending (no team claim), and no checkpoint manifest is present. No matching active gem5/evaluation/verifier process was found; `fuser -v` reported no accessible open handles (exit 1, empty output). Source commit was still `8959b4dfd149273e89884be87bee9c0adb60e0fc`.

No approval/apply command or deletion was performed by this subtask. The parent owns the concrete listing review and guarded cleanup decision.
