# BFS post-ROI termination diagnosis

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 (Eastern Time)

Status: source diagnosis and prospective diagnostic plan. No simulator patch,
new execution, protocol freeze, or acceptance change is authorized by this document.
The coordinator must review the concrete adapter change and one diagnostic request
before dispatch. This is a distinct diagnostic, not an automatic retry of a6.

## Retained observation and boundary

The authoritative records are
[a6 evaluation](../records/evaluations/bfs-dx100-smoke-20260925-a6.yaml) and
[a6 bounded observation](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/dx100-smoke-a6.json).
The latter retains raw-path hashes, lane/capacity receipts, phase memory, and the
checkpoint/config inspection. Raw files remain on mbit10; this review inspected
the imported metadata and the complete local pinned source checkout, not copied
remote raw files. The checkpoint/config excerpts were audited on-host by the
coordinator. Initial configuration is not a runtime Process-pointer observation.

| a6 fact | Retained value | Interpretation |
|---|---|---|
| Model | DX100 `e4fc4afdf894f295442cef3604667a469fab8e62`; model build `bfs-dx100-build-20260925-a2` | Pinned model, not a functional API run |
| SWDB execution revision | `08a373d14a64ed2b935601fd7f9ec47b137115a3` | Exact wrapper/evaluator checkout |
| Input | `bfs-dx100-smoke-20260925-a4.uniform64-diagnostic`, source 0 | Small bring-up input; not the prescribed uniform22 graph |
| Restore | a4 `cpt.2117142500`; manifest SHA `e3ddfe24fc06bdf8a5d36fdcfbd2a940c49e8b3500b45fa027e53576c4199601` | Same retained checkpoint |
| Peak sampled RSS | 33,719,536 KiB, under the fixed 48 GiB cap | This model/input was memory-feasible; no larger-graph inference |
| ROI seal | Tick 2,187,360,749; wrapper elapsed 113.5038 s | Guest ROI completed and its stats were sealed |
| Guest output | Lines 212–214: `Verification: PASS`, `Verification Time: 0.00001`, `Average Time: 0.00006` | Verifier and `BenchmarkKernel` reached their final prints |
| Continuation | `simulate() limit reached`, tick 1,002,187,360,749, code 0, allowance `10^12` ticks | No normal guest termination; code 0 is insufficient |
| Evaluation | `missing_observation`; correctness `unverified`; gain false | No correctness, performance, accelerator, or ticket-acceptance promotion |

The original 750-second restore wall cap and 2 GiB raw cap were not enlarged.
All four CPU progress counters became stationary after the final benchmark print.
Stationary counters alone identify neither syscall execution nor thread status.

The exact input/model bytes for any diagnostic are copied from a6's retained
request, then rehashed on-host: graph SHA
`00d156b95baa9806c8e7623400e0347770942aee64dbed227309886ee605f78b`,
author `bfs_maa` SHA
`6abd8190e4e1daf7c670c214dd0323393e3d29a9a26a3487c21f66e5ef194a5d`,
and `gem5.opt` SHA
`f4038c88318ee09085b6c07f163094a07a31a256f21b652d4f3cfa046feb1f6b`.
Retain and recheck the model receipt and its runtime dependencies as well.

## Pinned source mechanism

All source links below refer to that exact DX100 revision, inspected locally.

1. The author loads the graph before `m5_checkpoint` in
   [bfs.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc#L512).
   Serialized loading calls `GenIndex`, whose
   [OpenMP loop](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/graph.h#L233)
   can create worker threads before the checkpoint.
2. [se.py:242–248](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/deprecated/example/se.py#L242)
   assigns the same configured `Process` to all four CPUs. Runtime
   [doClone](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/syscall_emul.hh#L1604)
   creates a distinct child `Process`, replaces the worker's Process pointer,
   and establishes shared VM/thread-group state through `Process::clone`.
3. [ThreadState serialization](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/cpu/thread_state.cc#L54)
   retains only `_status`; generic thread serialization retains registers/PC.
   [Process serialization](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/process.cc#L371)
   retains `memState`, `pTable`, and `fds`, without clone Process association,
   PID/TGID, `childClearTID`, or shared `exitGroup` identity. Restore loads only
   configured `root.descendants()` in `src/python/m5/simulate.py:164–169`.
4. [exitImpl](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/syscall_emul.cc#L108)
   halts peers only inside a branch requiring `walk != p`, comparing Process
   pointers. If restored workers share the caller's Process pointer, that branch
   skips them, and only the caller is halted.
5. [numRunning](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/system.cc#L131)
   counts every context except `Halted` and `Halting`, including suspended
   workers. Any such survivors prevent the normal last-active-thread exit event.

The retained a4 checkpoint has four architectural `xc.0` sections, all
`_status=0` (`Active`), and one workload root `system.cpu0.workload`. Its
361,986-byte `m5.cpt` SHA is
`32342dae8e9da39b8183da8ac19e42912c75a67d5ab64590bb4543a7e60ad701`.
No process-identity fields were found; the four `_pid=4294967295` entries are
`BaseCPU::_pid` task/statistics fields, not `Process::_pid`. The actual a6
configuration maps all four original and four switched CPUs to that same workload,
PID 100. Its SHA is
`de1f55d5b8670324c45eab75bc314b8c7859f4fabfb38a63f5e3c5fa1e9c21fb`.
These observations support same-pointer aliasing, rather than divergent TGIDs.
They do not show the Process pointers or syscall at a6's final guest instruction.

The stale-Atomic explanation is weaker: `BaseCPU::init` registers only CPUs that
are not switched out; `BaseCPU::takeOverFrom` replaces each System thread slot;
generic takeover marks the old context `Halted`. O3's deferred halt sets
`Halting` immediately, and `numRunning` excludes that state. No missing terminal
event can be attributed to deferred teardown solely from the progress log.

## Python observation and restoration limits

The inspected exports in `src/sim/System.py`, `src/cpu/BaseCPU.py`,
`src/sim/Process.py`, and `src/python/pybind11` expose no read-only ThreadContext
status/Process-pointer query and no clone-state restoration API. `System` exports
memory-mode access; `BaseCPU` exports switching, TLB flushing, and instruction
counts; `Process` exposes address mapping. Reassigning a Python workload parameter
after instantiation does not establish a supported C++ thread-process reassociation.

Existing `SyscallBase` tracing is supported through
`m5.debug.flags['SyscallBase'].enable()`. It reports CPU/thread ID, syscall name,
arguments, and result; it does **not** report Process pointer identity or TGID.
This can distinguish a guest that reaches `exit_group(0)` from one stalled in
library/destructor work before exit. It cannot alone prove the alias mechanism.

## Same-process checkpoint continuation assessment

Writing a checkpoint does not destroy or reconstruct the instantiated machine.
Pinned `m5.checkpoint` (`src/python/m5/simulate.py:323–336`) drains, writes dirty
memory back, then serializes. It does not invalidate caches. A following
`m5.simulate` resumes the drained machine and does not rerun startup. Thus a live
checkpoint may be retained as provenance while process/VM/FD objects stay live.
It is not a promise that its serialized bytes can restore those associations.

The proposed live **Atomic → guest checkpoint → O3** route nevertheless has a
separate source-level obstacle. `Simulation.run` creates switched-out O3 CPUs
with the initial configured workload, then `BaseCPU::takeOverFrom` invokes
generic `ThreadContext::takeOverFrom`. That helper, at
[thread_context.cc:252–264](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/cpu/thread_context.cc#L252),
asserts that old and new contexts already have identical Process pointers and
does not transfer those pointers. A live cloned Atomic worker and a newly created
O3 worker violate that precondition. Disabling the assertion would not repair
the missing association. The host coordinator independently found no supported
reassociation path. Do not dispatch this route as a working repair.

There is also no built-in checkpoint-triggered CPU switch option. `setCPUClass`
creates the Atomic/O3 pair for serialized restore or instruction-count fast
forwarding. The restore path runs exactly `m5.simulate(10000)` before switching
(`Simulation.py:804–824`); at the configured `10^12` ticks/s that is 10 ns, not
10,000 instructions. The actual a6 phase receipt confirms tick 2,117,142,500 to
2,117,152,500. A custom live wrapper would have to preserve the checkpoint event,
drain timing, that explicit interval, and the CPU-pair setup. It still cannot
cross the Process-pointer handover precondition through the available bindings.

| State | Serialized a4 → a6 restore | Live checkpoint continuation |
|---|---|---|
| Thread/process/VM/FD ownership | Reconstructs configured objects; clone associations missing | Preserves live objects unless a CPU handover loses them |
| Cache lines | Classic cache checkpoint does not retain tags/data | `checkpoint` writes back but keeps valid lines; Atomic→timing switch does not invalidate them |
| Memory controller and prefetch state | Newly instantiated model | Existing state and prehistory remain; equality is not established |
| CPU/TLB/predictor | New O3 pipeline; takeover flushes old CPU TLBs | O3-from-start retains predictor/TLB prehistory; drain is not a reset |
| Startup/statistics | New simulator startup; guest later resets ROI stats | Startup runs once; guest still resets stats, which does not reset microarchitectural state |

These cache claims follow `BaseCache::serialize/unserialize` at
`src/mem/cache/base.cc:2057–2083` and `m5.switchCpus` at
`src/python/m5/simulate.py:350–430`. Switching to `atomic_noncaching` triggers
writeback/invalidation; switching from Atomic to timing does not. Moreover, the
current checkpoint command uses an Atomic setup without the final cache/MAA
configuration, whereas a live two-CPU-model configuration must instantiate its
final memory hierarchy up front. Adding `memInvalidate` cannot establish whole
model-state equivalence.

A single O3 CPU set from program start avoids both serialized reconstruction and
CPU handover. It is a possible **separate diagnostic/control**, not an equivalent
author pipeline. A finite implementation experiment would use the exact guest
binary/graph and final configuration, initialize once, stop at the guest
checkpoint, optionally write one provenance checkpoint, then continue the same
O3 instance to the sealed ROI and unchanged terminal checks. Its adapter must
explicitly handle pinned `Simulation.run`'s MAA loop over `testsys.switch_cpus`
when no switched CPU list exists, and reproduce the O3 resource settings that
the pinned runner otherwise applies to switched CPUs. These are preparation
requirements, not implemented behavior. Any future probe must declare the
startup/warm-cache/predictor treatment, have its own finite budget and record ID,
and cannot share a frozen comparison with serialized-restore trials. No second
probe or new live-mode implementation is scheduled by this document.

## One prospective post-seal syscall probe

Prefer this observation before a simulator modification. Prepare one opt-in
trusted-adapter change for review; do not change the pinned model or author binary.
The current public evaluator does not yet accept this trace option. Add a strict
optional `verification.post_roi_trace: SyscallBase`, default absent, and reject
other values. The wrapper enables that single additional flag only after writing
and hashing the ROI seal, immediately before the existing bounded verifier
continuation. Keep the existing MAATrace treatment through the ROI, and record
the post-ROI flag, enable tick, wrapper hash, and separate diagnostic purpose.
Do not enable O3CPU, Exec, or broad syscall tracing during the measured ROI.

Use a new unique diagnostic ID and dedicated raw directory. Copy all model,
binary, graph, source, checkpoint, mode/cache/tile, environment, and binding
inputs from the retained a6 request. Use the same 48 GiB RSS cap, 750-second
restore wall cap, 2 GiB total raw cap, and 1,100-second outer cap. Keep the existing
300-second checkpoint-resolution ceiling; create no new checkpoint. Set the
post-ROI allowance to exactly `10^10` ticks (10 ms at `10^12` ticks/s), below a6's
`10^12`. The printed 10 μs verifier time does not establish total exit cost, so
this plan does not infer a smaller safe limit. There is no memory or time ratchet.

Before dispatch, the coordinator reviews the adapter diff and exact request,
rehashes every retained input, checks both socket leases and the legacy lease,
then performs fresh capacity checks before and inside the selected lane. Stop on
capacity refusal, identity mismatch, or any declared bound. Preserve the failed
diagnostic and do not auto-dispatch another case.

Local tests must establish that the new flag is absent before seal, enabled once
after the seal is durable, and absent by default; that the existing terminal
checker still rejects PASS followed by a tick-limit event; and that malformed
trace requests fail before execution. The probe is admissible for diagnosis only
after those tests and coordinator review. No command is presented as runnable
before that public adapter support exists.

Retain the actual syscall trace, terminal event, code, checkpoint/model/input
hashes, phase memory, configuration, and all original verdicts. Interpret outcomes:

- `exit_group(0)` followed by no normal terminal event supports an exit/context
  problem. It still does not prove pointer aliasing.
- A final futex or another syscall with no `exit_group` redirects diagnosis to
  the exact post-benchmark operation; do not infer exit-group failure.
- A normal terminal event remains subject to the unchanged exact timed-parent,
  source/binary/ROI, output-count, and verifier checks. It does not make this
  diagnostic a frozen performance or artifact-reference comparison.
- Missing/truncated trace, capacity refusal, or a bound leaves the question
  unresolved. No PASS-only acceptance, automatic retry, or tick-limit increase.

## Minimal C++ alternative, not implemented

If runtime evidence confirms same-Process siblings at `exit_group`, the narrow
group-only proposal is to distinguish the caller's ThreadContext when Process
pointers alias. In the peer loop of `exitImpl`, with `tc` still naming the caller:

```diff
-        auto *tc = sys->threads[i];
-        if ((tc->status() != ThreadContext::Halted) &&
-            (tc->status() != ThreadContext::Halting) &&
-            (walk != p)) {
+        auto *peer_tc = sys->threads[i];
+        if ((peer_tc->status() != ThreadContext::Halted) &&
+            (peer_tc->status() != ThreadContext::Halting) &&
+            ((walk != p) || (group && peer_tc != tc))) {
             // Existing thread-group test and handling remain here.
             if (walk->tgid() == p->tgid()) {
                 if (*(p->exitGroup)) {
-                    tc->halt();
+                    peer_tc->halt();
```

This preserves the non-group branch and excludes the exiting context. It does
not restore general clone PID/TGID, futex wait-map, `childClearTID`, or shared
process state. It changes the simulator binary/model identity and therefore
requires a separately recorded model build and a disclosed artifact deviation.
Proving its changed branch is reached only after the sealed ROI in one run does
not establish general pre-ROI equivalence. Any future validation must include
same-pointer peers, distinct-process same-group peers, unrelated groups, and
non-group exits, then a bounded execution with strict terminal checking. This
patch is not applied, and a6 remains immutable and unverified.
