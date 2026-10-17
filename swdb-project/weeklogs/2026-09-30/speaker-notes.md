# EvolveSWDB weekly update

Date: 2026-09-30 (Eastern Time). Created 2026-09-27. Updated 2026-09-29.

Ten-minute talk: slides 1–9. Slide 10 is backup.

## 1. Title

0:00–0:15. Title. This week covers 2026-09-23 to 2026-09-29.

## 2. Where we are

0:15–1:05 (50 s). Last week we built the Software Database: real code, memory access patterns, inputs, machines, and profiles, with queries and exports for the agents. It stored knowledge but could not act on it. This week I built the two parts that let an agent act: profiling, which tells the agent where a specific workload spends time and how it touches memory, and rewriting, which turns the agent's proposal into real, checked code. BFS is the first complete case. DX100 is one prototype evaluation target; the profiling and rewriting do not depend on it.

Sources:
- `weeklogs/2026-09-24/speaker-notes.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md`

## 3. Why profiling and rewriting?

1:05–2:05 (60 s). Motivation: the SW and HW ensemble agents will choose optimizations and propose code changes. Problem one: static source facts and whole-program counters do not say where a particular BFS run spends time, and a rewrite can create new hot code that no catalog lists. Problem two: a proposal in natural language is not code; someone must apply it to the exact source, keep it within scope, and check it. Solution: a profiling query that discovers hot functions and loops automatically and returns their code and memory behavior, and a rewrite path that turns four proposal forms into a checked candidate.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md`

## 4. Profiling: what the agent receives

2:05–3:30 (85 s). Given an implementation, a graph, a source vertex, and a thread count, the profiler parses the current source with libclang, finds every function and loop, and instruments them, with no annotations. It ranks them by CPU time, keeping inclusive and exclusive time separate. For memory, it runs the same code under Callgrind and records data reads, writes, and modeled cache misses for the BFS call; the cache model matches mbit10's L1 and L3 sizes. Everything is bundled into a profile package with the source code, callers, types, and a strategy lookup. We do not have hardware counters on the shared host, so memory numbers are simulated and labeled as such.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/06-function-hotspot-discovery.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/08-dynamic-memory-observations.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/09-profile-packages-and-strategy-lookup.md`

## 5. Example: a rewrite adds a new hot helper

3:30–4:45 (75 s). A small diagnostic test. We submitted a patch that adds a helper function with two nested loops to upstream BFS, then profiled before and after on a ten-vertex graph from three source vertices. The baseline had 11 functions and 20 loops. The rewritten code had 12 functions and 22 loops. The new helper was found without being named anywhere and ranked first by exclusive CPU time. Thirty unchanged code fragments were matched to their old measurements; changed fragments were measured fresh and not given old data. The memory view shows the same effect: data reads rose from 8,468 to 54,474 for source 0. This checks that profiling follows the code as it changes. It is not a performance result.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/06-function-hotspot-discovery.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/07-loop-discovery-and-reprofiling.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/08-dynamic-memory-observations.md`

## 6. Rewriting: four proposal forms, one path

4:45–6:05 (80 s). A proposal can arrive in four forms: natural-language instructions, structured instructions, annotated source, or a patch. All go through one path. The rewriter applies the proposal to an identified source snapshot, using Claude as a bounded worker for the instruction and annotation forms. The result must be a real code change; a comment-only edit is rejected. If the candidate fails to build or fails the correctness check, a limited number of repairs is allowed; repairs cannot change the intent and cannot tune performance. Every attempt, including failures, is stored. The table shows real examples from this week.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/04-instruction-rewriting-and-repair.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/05-annotated-source-rewriting.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/18-dx100-patch-route-acceptance.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/19-upstream-instruction-route-acceptance.md`

## 7. Measuring the rewrites: no change yet

6:05–7:25 (80 s). Setup: mbit10, Intel Xeon Gold 6326, one socket, one thread. Ten paired repetitions per graph, baseline and candidate alternating, timing only the BFS call. We claim a gain only with at least 1.05 speedup and a run-to-run spread under 10 percent. The first two rows are the scalar BFS from the DX100 prototype run natively on the CPU; the last two are upstream GAPBS BFS. Result: both candidates were correct on all 30 timed trials per role. Speedups are 1.000 to 1.002, and every 95 percent interval includes 1. Spread was above the limit, so the verdict is inconclusive. Analysis: these were deliberately small edits, so no gain is expected. What matters is that the path from proposal to verdict works and does not report noise as a win.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/18-dx100-patch-route-acceptance.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/19-upstream-instruction-route-acceptance.md`

## 8. Ongoing work and what we learned

7:25–8:40 (75 s). What is still in progress and what we learned. Rewriting: several LLM proposal attempts timed out, and one returned a patch that did not apply. We added a whole-file edit format, and it produced a new candidate that waits for a build. Profiling: coverage is partial; code in headers, libraries, and one OpenMP region is not yet attributed, and we report that explicitly. Evaluation on the DX100 prototype needs gem5 simulations that take hours, and the shared host runs at most two jobs. We also cut our harness cost per trial from 8.7 to 1.0 seconds.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/20-upstream-annotated-route-acceptance.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/06-function-hotspot-discovery.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/18-dx100-patch-route-acceptance.md`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/resume-plan-20260927.md`

## 9. Plan for this week

8:40–9:50 (70 s). This week the handoff comes first. At the 2026-09-24 meeting the team fixed a linear pipeline: my side, then Peter, then Josh and Eric, then back through Peter to me. So my first deliverable is for Peter's agent: the DX100 BFS top-down step with its exact source revision, build and graph commands, and raw logs, annotated with Josh's seven statement IDs so that Peter's per-statement features and Josh's hardware requests refer to the same lines. One detail to settle with Peter: this source stores edge offsets as 32-bit integers, while his feature report assumes 64-bit. Second, Eric asked who builds and tests the proposed hardware, and the pipeline names no owner for that yet. I already have a gem5 path for the DX100 prototype that checks BFS correctness and times the run, so I will offer it as the evaluator, at least for DX100-based designs. Then I continue with a profile-driven rewrite that targets a measured hot loop on a pilot-sized graph. The remaining proposal forms move after the handoff.

Sources:
- `../docs/meeting-2026-09-24.md`
- `../examples/bfs.source-observations.yaml`
- `apps/dx100/benchmarks/gapbs/src/graph.h`
- `.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md`

## 10. Backup: native measurement protocol

Backup. The native protocol was frozen from a one-thread pilot study. Baseline and candidate trials alternate in pairs to reduce drift on a shared host. Correctness is verified outside the timed region. A speedup is claimed only if the lower confidence bound exceeds 1 and the minimum speedup and spread rules pass. The host load is recorded with every run. No hardware counters are available to our account, so profiling uses region timers and Callgrind memory simulation.

Sources:
- `.scratch/bfs-rewrite-evaluation-2026-09-25/issues/18-dx100-patch-route-acceptance.md`
- `.claude/rules/remote_server.md`
