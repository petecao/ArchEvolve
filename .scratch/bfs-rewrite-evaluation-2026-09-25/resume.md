# BFS implementation and evaluation resume checkpoint

Updated: 2026-09-27 ET.

The user explicitly requested stopping work and synchronizing everything for later
resumption. No new implementation or evaluation is authorized to run while paused.
The 30-minute heartbeat was deleted on 2026-09-27; recreate it only when work resumes.

## Retained state

- Tickets 01–14 are resolved; 15–21 remain claimed and incomplete.
- Actual acceptance remains 0/8 cells, with no qualified gain. Fixtures, Linux
  supervision proofs and successful builds are not scientific acceptance.
- The latest scientific runtime is `2a64a188f08811baf09ab9c61e69633c3d45a7f2`;
  operator `f775fd0` launched T16 at 07:18:39.701921 ET on node1.
- T16 was stopped at the user’s request on 2026-09-27. No scientific sample
  was accepted. Consult the final stop observation and tracker before any restart.
- Never resume a failed or interrupted run ID or mutate its runtime/records.
  Use a fresh reviewed plan, exact runtime/protocol identities and fresh admission.

## Standing approval and remaining work

The direct user approval covers the reviewed incremental T15 allocation of 48 hours
and 96 GiB and comparable necessary bounded recovery allocations. This approval
remains valid after resumption; the current pause still forbids execution now.
Preserve all historical costs, original deadlines and failed evidence separately.
T15 execution is serialized after independently verified T16 closure and requires
fresh capacity checks, finite accounting, exact source/protocol/runtime checks,
matching Linux proof and independent admission review.

The reviewed T15 partition is 3,600 seconds preparation (including at most 600
seconds for proof), two 82,800-second family series, 3,570 seconds finalization,
and 30 seconds scientific cleanup: 172,800 seconds total. Its 96-GiB aggregate
contains a 4-GiB overhead reserve and 92 GiB shared by scientific series, each
clamped to at most 60 GiB. All 12 primary/diagnostic pairs remain required. The
first-pair 120-second collection gate remains a stopping condition.

Remaining T17–T20 route prerequisites and provenance bindings are recorded in
`observations/remaining-route-identity-audit-20260927.json`. T20 has no candidate;
its retained provider residual is 430.6789783677086 seconds. No old provider packet
is a fresh submission and no blind retry is implied.

After remaining implementation and actual native/DX100 acceptance, run final
independent Standards and Spec reviews against
`1bdb7d4037916dea782c40239a6415b61a47f3c1`, address findings, and synchronize all
21 tickets. Interim reviews and the fixed SQLite query finding are not final
all-task review completion. Keep unrelated `weeklogs/` out of task commits.

## T15 implementation status at pause

The new T15 continuation is design only: no new plan/request/helper/controller
code, runtime, proof ID, allocation clock, admission or dispatch was created. No
implementation tests ran for that unimplemented continuation. The approved
allocation has not begun. Start by implementing and independently reviewing its
bounded controller; do not mistake the reviewed allocation document for tested code.
See [review checkpoint](observations/t15-review-resume-checkpoint-20260927.md).

## Interruption evidence boundary

The owned supervisor received one verified graceful SIGTERM. The run exited 1
with an interrupted outcome. All owned process identities were checked twice;
no executing owned process remained, and node1 was released. The strict cleanup
ledger nevertheless reports outstanding reservations. Preserve that failed
ledger and do not claim successful strict cleanup or resume this run ID. Review
the recorded failure before any future admission; do not rewrite old evidence.
Raw data and logs remain under
`/data/yanruj/EvolveSWDB_runs/bfs-t16-protocol-recovery-simulator-batch-20260927-a1`
and its `.dispatch` sibling on mbit10. No raw traces or binaries were copied to
the Mac. The other user’s node0 job was not signaled.

Final evidence: [stop closure](observations/t16-user-stop-closure-20260927.json),
[independent check](observations/t16-user-stop-independent-20260927.json), and
[stop signal](observations/t16-user-stop-signal-20260927.json). The retained
strict ledger has 117 events, 20.861548168 seconds spent, and an outstanding
0.226152836-second nested grace reservation for an absent process. Final accounting
also records `resource sample read bound exceeded`. Physical quiescence is not
strict closure: this remains a blocker to the planned T15 serialization admission
until a prospectively reviewed recovery resolves it without changing old evidence.
The conservative current-attempt charge is 8,712 seconds and 619,712,512 bytes;
cumulative T16 retained charges are 24,325 seconds and 11,011,186,688 bytes.

## Main branch consolidation — 2026-09-27

The user requested consolidating all branch work into main. Resume from `main`;
BFS implementation and snapshot histories are consolidated there. Historical
branch refs and immutable runtime commits remain for provenance. Evaluation
remains paused and the heartbeat remains deleted.
