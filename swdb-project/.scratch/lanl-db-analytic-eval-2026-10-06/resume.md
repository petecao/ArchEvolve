# Resume the analytic evaluator work

Updated: 2026-10-08 10:29 ET

**Paused at Yan-Ru's request.** Fourteen of fifteen assigned tickets are resolved.
Ticket 17 remains `claimed`, with work paused; its acceptance boxes stay unchecked.
The 30-minute heartbeat `lanl-analytic-evaluator-progress` is **PAUSED**.
No agent remains running. Resume monitoring only when work is explicitly resumed.

| Evaluation | Saved state | Next action |
|---|---|---|
| CPU ticket 11 | Resolved; held-out BFS passed its broad band, BC failed | Preserve both results |
| Generality ticket 14 | Resolved; nine pairs, 45 trials; seven whole-call totals unknown | Preserve qualified results |
| Corrected storage DEFAULT a3 | Original receipt reviewed; guard exit 0 | Do not repeat |
| Storage RETIRE a4, plan a5 | Launch transport 0; actual worker result unassessed | Collect this existing attempt once |
| Ticket 17 science | PREPARE/freeze NOTRUN; 0/4 substantive campaigns | Wait for genuine storage and capacity admission |
| Final Standards + Spec review | Pending after assigned work completes | Complete review and fixes before final ticket closure |

Read the [pause archive](evidence/17-user-pause-custody-20261008-a1/README.md)
and [manifest](evidence/17-user-pause-custody-20261008-a1/manifest.json) first.
Its 168 originals retain the successful DEFAULT receipt, failed preparations,
the launch custody, selected future controls and root checkpoints A53–A56.
Earlier [library-preserving custody](evidence/17-library-preserving-sparse-retirement-custody-20261008-a1/README.md)
and [read-budget correction](evidence/17-sparse-read-budget-custody-correction-20261008-a1/README.md)
are integrated too. Originals and earlier NOTRUN labels are unchanged.

## First action on resume: collect the existing retirement

**No mbit10 access before 2026-10-08 10:48:28 ET.** The exact quiet boundary is
`2026-10-08T14:48:27.171171+00:00`, saved in the
[launch/quiet original](evidence/17-user-pause-custody-20261008-a1/originals/lanl17-retirement-a4-launch-and-quiet-window-original-20261008-a1.json).
Waiting past this boundary establishes neither completion nor success.
The user pause stopped new launches and monitoring; it did not terminate this
already detached, bounded worker. Its terminal state is unknown.

The root agent alone should collect the existing control directory
`/data1/yanruj/lanl17-detached-sparse-retire-a4` exactly once. Use the reviewed
read-only capture, collector and decoder retained in the earlier correction archive.
Do not launch another retirement or default check.

The invocation below is **NOT RUN**. Before using it, verify all source/native pins,
the quiet boundary, private-file requirements and absence of the fresh destinations.
Existing original local files remain under `/private/tmp/`; do not overwrite them.
If they are missing, recover exact bytes from the manifest into private files and
review any new custody requirements. A Git clone does not preserve original inodes
or private modes; an archived stat is historical evidence, not a new live stat proof.

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12 -I -B \
  /private/tmp/lanl17_capture_readonly_sparse_collector_originals_20261008_a2.py \
  --source-sha256 00ca44196713cf443ac4d6a7d1b1aef2bfaaab0405c028062629587102c01d90 \
  --ssh-sha256 c7f9f9779c1dd141b04889c6cb214859d0702687e7fde34511bb5fa7af8951f1 \
  --ssh-bytes 1584560 \
  --control-directory /data1/yanruj/lanl17-detached-sparse-retire-a4 \
  --collector-source /private/tmp/lanl_read_detached_sparse_administration_originals_20261008_a2.py \
  --local-processes /Users/yanrujhou/.codex/worktrees/lanl-ticket17/ArchEvolve/swdb-project/swdb/processes.py \
  --capture-directory /private/tmp/lanl17-sparse-originals-read-20261008-a4
```

Require a complete original successful capture before decoding. Copy its `stdout`
byte-for-byte to a fresh private regular file whose parent is exactly `/private/tmp`:
`/private/tmp/lanl17-sparse-retire-a4-original-custody-packet-20261008.json`.
Retain before/open/after nine-field stat, size and SHA256 custody; use the unchanged
64 MiB packet bound. Then invoke the reviewed decoder once:

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12 -I -B \
  /private/tmp/lanl_decode_detached_sparse_original_custody_20261008_a2.py \
  --packet /private/tmp/lanl17-sparse-retire-a4-original-custody-packet-20261008.json \
  --output-directory /private/tmp/lanl17-detached-sparse-retire-a4-originals-20261008
```

Preserve and assess every returned original, including absent receipts, refusals,
partial journals or incomplete states. Transport exit 0 does not prove retirement.
Do not infer sixteen retired checkouts, recovered capacity or scientific clearance.

## Source synchronization and subsequent gates

GitHub and local main/integration receive the pause checkpoint. **mbit10 checkout
synchronization is deferred**: its last observed primary remains
`5e12a9796432654d88def24ecea617d16ca605b2`. Closeout makes no SSH calls.
Do not pull or change primary during the existing worker. After collection and
assessment, handle administrative checkpoint synchronization explicitly: the
retirement/host-query controls bind primary to `5e12a979`, so advancing it requires
reviewed new control pins or a deliberate retained frozen checkout. Never relabel
the expected primary or silently weaken its guard. Scientific source R remains
`5e12a979`; execution source C remains `f893fed400347ed23d92e917d8bde21b75e5375d`.

If genuine retirement succeeds, the prepared post-retirement host query is next;
then fresh storage/lease/consumer admission before PREPARE. The previous capacity
observation at 2026-10-08 09:42 ET is dated, not current capacity. Require actual
headroom `25,547,235,328` B for the planned allocation and unchanged policies.
Read the [concrete scientific guide](evidence/17-user-pause-custody-20261008-a1/originals/lanl17-concrete-scientific-next-step-argv-compact-source-review-20261008-a1.md),
[dispatch facts](evidence/17-user-pause-custody-20261008-a1/originals/lanl17-actual-campaign-dispatch-command-facts-20261008-a1.md),
[prepare/finalize facts](evidence/17-user-pause-custody-20261008-a1/originals/lanl17-prepare-finalize-command-facts-20261007.md)
and [FIRST worksheet](evidence/17-library-preserving-sparse-retirement-custody-20261008-a1/parent-analysis/lanl17-first-publication-construction-worksheet-20261008-a1.md).
All four substantive normal-terminal trajectories remain mandatory; zero eligible
DX100 numerical pairs or baselines alone do not fulfill them. D30 stays unchanged.

Keep raw output on mbit10, recheck both socket leases and legacy lease before any
actual evaluation, and use at most two lanes through the current `socket_lane.sh`.
The current dated storage plan favors serial campaigns; two free lanes are not
established by this checkpoint. Retain worktrees and remote raw/library state for resume.

Remote branch cleanup is a separate pending discussion. No branch deletion is
authorized by this checkpoint; see [the proposed list](branch-cleanup-proposal-20261008.md).
