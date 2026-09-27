# T20 context2 preparation

Prepared 2026-09-27 Eastern Time. No context2 provider call, build, simulation, or lane claim has occurred.

Context1 completed as unresolved. It treated the native baseline profile's compiler command as the requested evaluation target and reported missing per-thread allocation context. Context2 retains the same strategy, intent, annotated payload, source identity, operations, editable files, and correctness/ROI protections. It adds a read-only clarification of the already requested DX100 target and exact reference-source context. It does not add an optimization or imply that a new candidate has passed anything.

The existing `hardware_target` is `dx100-e4fc4af-4c`, `require_executable_backend` is true, and the retained public target declares `dx100-gem5-se` readiness `built`. The native profile describes historical CPU baseline execution. T17's existing successful primary build demonstrates the source-identified DX100 build route (`GEM5`, `MAA`, four cores, tile size 16,384 and m5 ABI source), for a different candidate. This establishes neither this proposal's correctness nor its execution or profitability.

The source SHA `6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465` binds `apps/dx100/benchmarks/gapbs/src/bfs.cc`. Context2 includes exact declarations at lines 63–64 and DOBFSMAA allocation at lines 366–403: tiles0–5 plus tilesi/tilesj, regs0–5 plus last_i_regs/last_j_regs, allocated per thread within an OpenMP critical section. The existing full headers remain byte-identical. Required setup stays inside the requested DOBFS complete-call ROI. The reference excerpts expand read-only context only; `src/bfs.cc` remains the sole editable upstream file.

The initial provider charge was 62.419636563397944 seconds. The original remaining allowance was conservatively floored to 1,737 seconds; context1 consumed another 104.55376222543418. Cumulative actual use is 166.97339878883213 seconds. After retaining the first floor, 1,632.4462377745658 seconds remain, floored again to 1,632 for context2 and any later bounded build repairs. Per-call limits remain 600 seconds and $10, with at most two later repairs sharing that remaining allowance. The operator makes one submission only, with no build or repair in this job.

The prepared request is 123,401 bytes. The exact rendered prompt is 523,066 bytes, SHA `3a42edd717c1ea13bdd28a935459cb0209709375d077b06504ff0f623ae5e992`. Rendering used the byte-identical local upstream source tree and the same `prompt_for` bytes as runtime8cb. As a control, the same procedure reproduced the previous 518,016-byte prompt and SHA exactly. No stored source record was changed. Fresh host verification must still verify raw artifact availability and reproduce the same prompt before a call.

The prior result is durably preserved as one exact 127,910-byte YAML blob, SHA `3ee48461ccb757686a3c32c42151d3e8758916c5ee1cbb902e0612e0a2baa6f8`, in private branch `codex/bfs-provider-context1-evidence-20260927-a1`, commit `1b2250670077a2f48c7dd8b28333685c4f757982`, sole parent5f. The original provider checkout and index were unchanged. The new operator archives records from commit1b while independently checking that the original checkout remains at5f; records become a fresh data-only view. It does not overwrite either unresolved proposal.

The new operator and wrapper retain context1's isolated pre-import full runtime guard, 750-second outer clock (720 work plus 30 shared cleanup), one public submit, strict PID/start ownership, fresh record retrieval and full final record inventory. The provider runtime stays `8cbfee600f23416a8e9578fa8d3ce3f0e19fced8`; the later batch consumer repair does not change this provider runtime. Prepared inputs are Git-carried read-only files next to the operational recipe. The original runtime remains pristine and separate from operational code.

Dispatch remains pending independent review, Git delivery of this packet, current helper/subtree verification, a fresh free lane with adequate resources, and the ordinary one-call preflight. The current reviewed wrapper and lease preflight both name node0; the prior node1 variant is retained as commit `ec4d8da5`. No operational budget or measurement evidence is created by these local contract tests.

## Host readiness and lane binding — 2026-09-27 01:10 ET

Read-only host verification reproduced the exact prompt and reopened the source,
headers, reference excerpts and retained build. No provider call or output root
was created. The prospective node0 variant `8e050d4` changes exactly the lease
assertion and socket argument, plus a wrong-lane regression; all request, prompt,
budget and import-guard bytes remain identical. Root independently reviewed the
Git delta and ran all 11 tests (passed in 0.12 seconds). The clean idle operator
checkout is now at that commit. Socket0 remains externally held (generation340
at 01:10 ET); dispatch waits for its release and fresh helper/capacity checks.
See [host readback](host-readonly-20260927.json) and
[Git delivery](node0-export-20260927.json).
