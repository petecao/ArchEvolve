# T15 setup-failure recovery

Navigation updated: 2026-09-28 (Eastern Time).

Prepared: 2026-09-26 (Eastern Time). Prospective local preparation; no execution or export is implied.

The consumed `bfs-t15-correction-simulator-batch-20260926-a1` failed before
checkpoint or guest execution. Its public record retains one interrupted
`execution_identity` stage; its execution leaf contains only
`host-observation.json`. Its failed outcome, original checkout, IDs, output,
105-identity closure and generation 416 release remain historical evidence.
The allocator now handles a confirmed disappearing nested SQLite journal while
still rejecting missing roots, unsafe substitutions and unknown errors.

The new fixed selector is `t15-setup-recovery`, with batch ID
`bfs-t15-setup-recovery-simulator-batch-20260926-a1`. The
[request](../../.scratch/bfs-rewrite-evaluation-2026-09-25/requests/bfs-t15-setup-recovery-simulator-batch-20260926-a1.json)
keeps the original scientific settings, two ordered graph families, three
sources, two repetitions, exact model/author binary/diagnostic build, v2 checker,
ROI, flags, lossless transport, capacity limits and profitability policy.
Only the new batch/series IDs, preparation lineage and explicitly clamped clock
are different. There is one attempt, no automatic retry, no old-ID resume and
no candidate/provider work.

| Flat charge retained before the new batch | Seconds | Bytes |
|---|---:|---:|
| Original failed T15 through final closure | 1,124 | 11,014,971,392 |
| Gzip transport preparation through final closure | 472 | 200,704 |
| Consumed correction's Linux preparation reservation | 600 | 2,147,483,648 |
| Consumed pre-guest setup failure through final closure | 201 | 11,886,592 |
| Fresh complete Linux preparation reservation | 600 | 2,147,483,648 |
| Total | 2,997 | 15,322,025,984 |
| Remaining from the original 43,200 seconds / 40 GiB | 40,203 | 27,627,646,976 |

The old proof reservation is retained in full. The old correction's aggregate
charged bytes are not added again. The reader reopens its exact fixed plan,
admission, old Linux proofs and complete proof-preparation envelope, driver,
settled shared cleanup ledger, terminal/lane receipts, actual retained byte
count and exact public evaluation YAML. It requires the unchanged first grid
position, candidate/configuration/checker/transport and the sole pre-guest
stage/leaf. Another evaluation, series, checkpoint or simulation artifact
rejects this narrowly authorized lineage. The old generic failed-attempt reader
continues to reject nested corrective attempts.

The absolute hard end is **2026-09-27 09:14:09.851819 ET**, pinned from the
consumed driver's actual `outer_deadline`. The old admission's later
09:43:24 timestamp is not a usable extension. New usable time is the lesser of
40,203 seconds and time from the actual outer start to that fixed end. The
outer timestamp is captured before timeout/helper startup, and all startup,
preflight, public work, hashes, monitoring and finalization remain charged.
The admission's prospective latest start may be narrower than, and cannot
exceed, **2026-09-27 03:13:39.851819 ET**, which leaves one full
21,600-second series plus 30 seconds of shared cleanup. Prepared-at must precede
not-before; actual launch must lie within that sealed interval. Earlier review
or idle time is never added back to the absolute clock.

Every subsequent series still needs its full 21,600 + 30 allowance. Two series
cannot each consume their maximum within the remaining aggregate time. With
all 40,203 seconds usable, the first must finish within 18,573 seconds to admit
the second; a later launch can tighten that condition. Failure to fit means an
incomplete retained result, with no shortened series or threshold change.

The fresh fixed proof group is `bfs-t15-setup-recovery-linux-20260926-a1`.
Its same 600-second / 2-GiB envelope includes preflight, both fixture attempts,
independent audits, wrapper exits and final readbacks. Each fixture retains its
original 90-second outer clock (60 seconds work + the same 30 seconds cleanup):

- `bfs-simulator-owned-linux-20260926-a4`: five actual Linux cases, including the
  real SQLite DELETE-journal commit between enumeration/stat and quiescent
  `du -sk` parity, in the already pinned owned-execution test module.
- `bfs-simulator-interruption-linux-20260926-a4`: two public interruption cases.

The new recovery admission explicitly requires the fifth passed, unskipped
SQLite case. Historical four-case proof readers remain compatible. The unrun
native campaign proof retains its original a1 ID. No third fixture job,
additional proof kind, allowance refund or side budget is introduced.

After exact code review/export and fresh host admission, the existing command
shape is unchanged apart from the new selector and unused roots:

```sh
python3 scripts/bfs_simulator_batch.py t15-setup-recovery \
  --admission "$DISPATCH/admission.json" --admission-sha256 "$ADMISSION_SHA" \
  --runs-dir "$RUNS" --lane "$NODE" \
  --outer-started "$OUTER_STARTED" --outer-deadline "$OUTER_DEADLINE" \
  --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START_TICKS"
```

Here `RUNS` is the new exact batch ID under an approved raw root and `DISPATCH`
is exactly `RUNS.dispatch`; the surrounding named tmux, normal socket helper,
original timeout, controlled Python environment and admission remain required.
`OUTER_DEADLINE` is `min(actual outer start + 40203 seconds, fixed hard end)`.
No value is synthesized from a fresh clock after work begins. The current T16
checkout and lane remain untouched; at most two host lanes may be used.

Terminal handling reuses `bfs_simulator_batch_terminal` and the established full
PID/start-time union, settled shared ledger and independent lease/process
closure. Persist helper/outer/audit output first, then count both exact raw and
`.dispatch` roots with the same flat preparation charges. After the last write,
perform the final read-only recount. A passing local test is contract evidence,
not a Linux proof, completed BFS sample, protocol freeze or gain claim.
