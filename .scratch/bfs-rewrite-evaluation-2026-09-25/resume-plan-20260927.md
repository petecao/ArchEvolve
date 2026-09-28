# Resumed execution plan — 2026-09-27

Created: 2026-09-27 10:20 ET. Updated: 2026-09-27 10:20 ET.
Owner of this plan: root session resumed on 2026-09-27 at the user's request
("implement all tickets against the spec", proceed autonomously, use two mbit10 lanes).

The pause recorded in `resume.md` ended on 2026-09-27 at the user's request. Historical
evidence, failed runs, and their charges stay unchanged. Failed run IDs are never resumed.

## Decisions (made at resumption; the spec, rules and ADRs are unchanged)

R1. **Closure standard.** A run is closed when (a) no owned process identity remains,
(b) its lane lease is released and (c) its retained storage is stable across two reads.
T16's stop (2026-09-27 09:43 ET) satisfied all three (independent readback). The strict
ledger's residual 0.226 s nested grace reservation belongs to an absent process; per the
ledger's own rule ("a supervisor that dies with a reservation consumes that entire
reservation") it is charged as consumed. It is a ledger-validation defect, not a host-safety
or scientific issue, and it no longer blocks T15 admission. The validator is repaired
prospectively (dead-owner reservations count as spent). Old ledgers are not rewritten.

R2. **Resource-sample bound.** The fixed 20,000-sample reader cap is shorter than the
14,400 s per-run bound at the observed sampling rate. Replace it with a cap derived from the
declared coverage interval and sampling period (plus margin). Line-size and gap bounds stay.

R3. **Parallel simulation within one lane.** gem5 is single-threaded and deterministic:
simulated ticks and simulated statistics do not depend on host load. A lane job may therefore
run several gem5 processes concurrently inside its own socket (still one job per socket, at
most two jobs host-wide, confined by `socket_lane.sh`). Host wall time is experiment cost only;
record the concurrency and load with every run. Native timing jobs never run concurrently
with anything else in their lane.

R4. **Lane coordination.** Root assigns lanes. node0 is currently held by the owner's
MemAcc ceiling-audit job (not ours; never signal it). Our jobs use node1 now and node0
only after it is released. Workers ask root before taking a lease.

R5. **Storage.** `/data1` is under 20 GB free, so run output goes to `/data/yanruj/EvolveSWDB_runs/`.
Check `df -h /data1 /data` before every dispatch. When the aggregate retained output would
leave under 30 GiB free on `/data`, compressed ROI debug traces whose derived package has been
verified and publicly read back may be reduced to hash + size + derived summary (recorded).

R6. **Replay policy.** T15 keeps its approved grid (12 primary/diagnostic pairs, 2 replays).
If its replays show identical simulated ticks, the frozen controlled-simulator protocol used by
T17/T20 may specify one replay per ordered source (determinism is the evidence), cutting cost
in half without weakening source coverage. Native protocols keep their measured repetition rule.

R7. **Native protocol independence.** T18/T19 need only the native protocol. Its qualification
and publication proceed now from the completed one-thread study, not after T15's simulator
packages. This removes a sequencing rule, not an evidence requirement.

R8. **Provider allocation for T20.** Prior contexts 1–3 remain failed and charged. A fresh
bounded allocation (1,800 s pool, at most 900 s per call, USD 10 per call, at most two repairs)
uses a focused context (upstream BFS source, DX100 MAA API headers, the author `bfs_maa`
top-down step as a reference). This is a comparable bounded recovery allocation under the
user's standing approval. Unresolved outcomes are retained.

R9. **Reviews.** Heavy per-dispatch independent admission reviews are replaced by author tests
plus a root review of each diff before dispatch. The final Standards and Spec code review
(against `1bdb7d4037916dea782c40239a6415b61a47f3c1`) remains required after all tickets.

## Work streams

| Stream | Tickets | Lane | First step |
|---|---|---|---|
| A — simulator runtime + T15 pilot | 15 | node1 | R1/R2 validator fixes, parallel batch option, fresh T15 request, launch |
| B — native protocol + native routes | 18, 19 | node0 when free, else node1 gaps | qualify/publish native protocol, reopen candidates, native campaigns |
| C — DX100 candidates | 17, 20 | builds only until protocol freeze | T17 diagnostic build, T20 fresh candidate, builds |
| D — artifact reference | 16 | after A frees capacity | fresh T16 request on repaired runtime |
| E — report | 21 | none | coverage report, handoff, final reviews |

## Added decisions — 2026-09-27 12:30 ET

R10. **Shared identical executions.** When two protocol roles name the same binary,
configuration, graph, source and target (T16 artifact.maa and control.maa), one real
execution set satisfies both, with the identity match stated and both protocol IDs referenced.
This follows the spec's coverage-accounting rule that one run may satisfy several obligations
when identities and requirements actually match; it supersedes the earlier "relabeling" ruling.

R11. **T16 repetitions.** One repetition per role if T15's replays show identical simulated
ticks; otherwise two. The re-frozen T16 protocols get new IDs.

R12. **Fast post-ROI verification (opt-in, pending proof).** After ROI statistics are sealed,
the same simulation may switch to an atomic CPU for the in-guest verifier. The binary, process
and memory state are unchanged, so the verifier outcome is the same evidence; only host cost
falls. It is adopted only after a tiny-graph proof shows an identical verifier outcome and ROI
statistics identical to an unswitched run. T15's running protocol is not changed.

T16 measurements behind this (Stream D, 12:15 ET): uniform22 scalar ROI ≈ 27,000 host s, MAA ROI
≈ 13,000–20,000 s, O3 verification ≈ 30,000 s per execution, MAA trace ≈ 20 GiB per execution.

## Schedule compression — 2026-09-28 19:00 ET (user-approved options A + B + C)

R13. **T17/T20 one source per family.** Protocols re-frozen as version 2 with sources [0] only;
routes a1 is stopped and retained as interrupted (only baseline pairs existed, so the change
precedes candidate assessment). Deterministic simulation makes this a loss of source coverage,
not of statistical confidence.

R14. **T16 scalar diagnostics dropped.** Protocols re-frozen as version 3: scalar roles keep
primary timing, simulated statistics and memory observations; the MAA primary and diagnostic stay.
T16 b1 is stopped and retained as interrupted.

R15. **T16 split across lanes.** Scalar primaries run on node1; the MAA job runs on node0 after
routes a2. node0 then returns to the owner's MemAcc session (about 2026-09-29 18:00 ET).
Target: all tickets and the final review done 2026-09-29 evening.
