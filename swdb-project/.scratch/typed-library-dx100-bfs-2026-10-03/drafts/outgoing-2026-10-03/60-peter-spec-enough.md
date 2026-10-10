# Draft: "Is the specification enough?" finding for Peter

Created: 2026-10-04 ET
Updated: 2026-10-05 18:20 ET (spec review C23: input A was the spec plus the lowering header, stated in the text and table)
Status: draft (Yan-Ru sends manually; the agent never sends)
To: Peter
Ticket: [60](../../issues/60-send-peter-spec-enough-finding.md) (from ticket [58](../../issues/58-spec-enough-experiment.md))

Subject: Your v1.1 BFS intrinsic spec: one gap stops every rewrite

Hi Peter,

I tested whether a rewrite agent can rebuild the TDStep read offload from your v1.1 BFS
intrinsic specification alone. It could not. Every sample failed on the same point, and a
small change to the spec should fix it.

**What I ran.** Codex (gpt-5.6-sol, xhigh) wrote 3 rewrites for each of 3 inputs. The 9
sessions ran one at a time on mbit10. Each input added documents:

- A: your spec (`docs/bfs-intrinsics-spec-yanru.md` at commit `0b56895`).
- B: A plus Josh's hardware-candidate draft.
- C: B plus our rewrite contract
  (`swdb-project/library/rewrite_contracts/bfs_read_offload.yaml`, branch `yanrujhou_main`,
  commit `f62401c`).

Every input also got the scalar BFS source, our lowering header
(`swdb-project/library/dx100/dxc_lowering.hpp`, commit `f62401c`) and a short build note;
without them no rewrite could build or be scored. So input A was your spec plus an executable
intrinsic interface, not the spec alone: the header's API already encodes part of the
per-thread contexts and the session lifecycle (our contract's E1 and E3). Our working rewrite
was hidden.
`swdb certify` scored each rewrite on the DX100 strict functional model: verifier, per-level
frontier sizes, the accelerated-chunk witness and 16 negative controls. As a check, our
working rewrite certified through the same path (10/10 cells, 16/16 controls).

| Input | Certified | Controls rejected | Patch applied |
|---|---:|---:|---:|
| A: spec (+ lowering header) | 0/3 | 0/48 | 2/3 |
| B: spec + draft | 0/3 | 1/48 | 3/3 |
| C: spec + draft + contract | 0/3 | 0/48 | 1/3 |

Three patches did not apply because their hand-written context did not match the source.
That failure is about patch writing, not your spec.

**The finding.** All 9 rewrites passed plain numbers where DX100 takes register handles.
For example, they called `__dxc_stream_load(queue.shared, chunk_begin, chunk_end, 1, tile0)`
and `__dxc_range_loop(..., 1, ...)`. Every applied rewrite failed the strict model's
register checks (`register_handle`, `thread_ownership_register`) in all 10 test cells, so
none reached the frontier or witness checks.

The rewrites followed the text:

- Your spec gives `start_idx`, `end_idx` and `stride` the type `int32_t`, as values, in §3.1
  (`__dxc_stream_load`, lines 62–73) and §3.3 (`__dxc_range_loop`, `stride` at line 113).
- The §5 template passes plain values (lines 241 and 257).
- Our lowering header types these operands as plain `int` (`dxc_lowering.hpp` lines 42–43).
- Our contract names the fix only as the label "E2 register handles" (line 339).

Our working rewrite loads each value first, `__dxc_const_i32(1, c.reg[2])`, then passes the
register (`swdb-project/library/dx100/bfs_read_offload.inc` lines 25–36, commit `ed8c233`).
Adding Josh's draft or our contract did not change what the agent wrote.

**Suggested spec change.** Give these operands a register type (for example
`dxc_reg_t start_reg`) and state the rule: a scalar operand of a DX100 operation is a
per-thread register, set with a constant-load before the operation. The §5 template would
then load its constants that way. I would also give tile capacity as the build's
`TILE_SIZE` rather than the fixed 16,384: most rewrites flagged that mismatch as an open
point.

**Scope.** These results come from the functional model only, with no timing. There were 3
samples per input, from one model.

Raw run output stays on mbit10 (`/data1/yanruj/EvolveSWDB_runs/extensa/extensa-gem5-bfs-20261004-s1/`).
The compact summary is
`swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/spec-enough-a3-summary.json`
(branch `yanrujhou_main` once merged; agent commit noted in ticket 58).

Best,
Yan-Ru
