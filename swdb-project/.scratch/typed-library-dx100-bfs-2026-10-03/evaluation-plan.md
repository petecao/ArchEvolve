# Evaluation dispatch plan

Prepared: 2026-10-03 ET

Yan-Ru's ticket 1–37 instruction authorizes autonomous evaluation using two free
mbit10 lanes and the Codex/Claude CLIs. Record this instruction as the dispatch
approval reference. Source export approval is separately pending after automatic
approval review rejected the configured-origin push. No remote evaluation has started.

Use `/data1/yanruj/ArchEvolve/swdb-project` on `yanrujhou_main` after Git source sync.
Use the clean `/data1/yanruj/Memacc-evolveswdb-lane` lane dispatcher; its socket script
was verified against current origin. Refresh both socket leases, the legacy lease,
script revision, branch, commit, host load, disk and each selected node's memory
before each dispatch. Enter through `socket_lane.sh` inside a named `tmux` session,
with an outer `timeout`. Build remote x86_64 code locally on that host.

| Work | Preferred lane | Admission and dependencies | Result required |
|---|---|---|---|
| Tickets 27 and 34: scalar native correctness, ROI/profile package and per-line callgrind | node0 | Source sync; 8GiB node memory; planned bytes plus 20GiB disk reserve | Real complete package and exact retained per-line costs |
| Ticket 36: guarded profiling provider and independent scoring | whichever lane is free | Prior real profile; 8GiB stage preflight; pinned source/provider/schema | Seven statement claims, Spearman/top-three scores and Josh table |
| Ticket 28 preparation | whichever lane is free | Ticket 27 package; Yan-Ru promotion; source sync; 4GiB for serial build | Fresh protocol/package, exact submitted certified tree and three builds |
| Ticket 28 companion | node0 if admitted | Completed preparation; default 48GiB node budget; current leases | Completed read-only witness/frontier check and observed/refuted/inconclusive L3 outcome |
| Ticket 29 timed cells | two lanes only when both are admitted | Observed L3; normal completion; current target/protocol/build pins | Four real executions, point comparisons and summary |
| Ticket 31 fallback | after an actual L3 refutation | Never inferred from absent execution or ambiguous preparation | Separate CPU-parent-load contract with fresh certification |

The latest live read at 04:00 ET found both socket locks and the legacy lock free,
load approximately 1, node0 MemFree 26.4GiB and node1 15.7GiB. Free disk was about
43.4GiB on `/data1` and 73.4GiB on `/data`. These are observations, not reservations.
Neither node satisfies the default simulator budget. An explicit 36GiB budget is
appropriate only with a measured 32–34GiB simulator bound and headroom; the current
nodes still fail that admission. Do not substitute global available memory, clear
other users' workloads or bypass node memory binding.

Raw output stays under `/data1/yanruj/EvolveSWDB_runs` or the admitted `/data` fallback.
Commit and push metadata through Git; never copy remote raw artifacts to the Mac.
Historical cleanup needs its exact listing and human approval (ticket 32). No
retroactive cleanup has been applied.

The bounded `tools/typed_library_profile_driver.py` has `profile` and `annotate`
stages. `tools/typed_library_gem5_driver.py` has `prepare`, `companion` and `timed`
stages. They require an approval reference, retain progress and refuse invalid
admission. Consult their public `--help` for each concrete fresh run ID; do not
reuse paused/failed run identities or fabricate a promotion receipt.
