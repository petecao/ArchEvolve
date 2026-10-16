# Original partial u32 register observation

Created: 2026-10-16 ET. Preparation only; ticket28 remains claimed.

The admitted caller sets register0 to7, sets register1 to11, then returns
`100*get_reg(0)+get_reg(1)`. Correct result711 and wrong cross-register result1107
use identical original source, model, flags and frame. The new original contract
is explicitly partial from creation, with distinct `partial_library_summary`,
contract, semantics and method identities. It cannot replace an existing total
unit or satisfy a generic summary dependency. Its original explicit frame is
`assigns __swdb_dx_reg_words[0..1]`; admission preserves this frame without
rewriting an assigns-nothing contract. Helper bounds are caller obligations,
not added original-unit requires. Unsupported calls and u64 refuse.

The scalar source header casts its volatile32-bit address to a nonvolatile `T*`
for the actual pointed read/write. Only the getter's temporary is volatile.
Both helpers use `mfence` without a memory clobber. The certificate preserves
these exact properties; it adds no volatile behavior or portable compiler fence.

| Obligation | Admission/evidence | Remaining boundary |
| --- | --- | --- |
| Interface | All26 names/27 declarations retained; only `set_reg<unsigned int>` and `get_reg<unsigned int>` reachable | Other24 names/types unsupported in this fixture |
| Effective source | Original main TU preprocessing precedes appended probes; exact template bodies and closed caller selected from unique frozen AST families | Trusted compiler observation, no source theorem |
| Scalar ABI | `unsigned int`32-bit, alignment4, pointer64-bit, little endian | Concrete admitted compiler/runtime only |
| Address/geometry | Pinned source4-core layout; compiled scalar base17184063616,128bytes/32words and all adjacent mapping addresses | Explicit configured mapping premise; alloc/init do not imply entry state |
| Bounds | Only literal IDs0/1; helper requires0<=id<32 | Original source getter/setter perform no independent host bound check |
| Write/response | CpuSidePort.cc112-150 queues4-byte writes; MAA.cc510-538 updates RF before the response | Transport/scheduling implementation and contract/body correspondence remain owned TCB |
| Read | CpuSidePort.cc317-332 copies selected RF bytes; SPD.hh RF accessor checks index | Read is not a covering wait |
| Commands | No queued register packets or device commands in the entry epoch | No invented IF second-half stall or hardware ownership |
| Interference | Explicit exclusive one-thread/core0 epoch excludes all other CPU/device accesses to the entire128-byte scalar region | Conservative exclusion covers both64-byte physical lines; scalar MMIO itself is4bytes, not a full-line write |
| Values | Ordinary32-word projection, selected cell assignment/getter result; both observed cells overwritten before read | No desired-result axiom, fresh RF values or inherited constructor premise |
| Compiler effects | O2 source/reference SSA effects, actual nonvolatile load/store, signed index guard, stride4, fence/clobber and complete closed-caller ordering/elision retained | Does not prove actual MMIO ordering/transport or compiler correctness |
| RF runtime | Exact RF class/constructor finite native comparison under ASan/UBSan | Raw-byte storage typed accesses/object lifetime/alias validity remain simulator runtime/compiler TCB; sanitizer silence is no language theorem |
| Totality | Both helpers and the distinct original unit declare `terminates \false` in valid ACSL order | Normal return only; no fairness, finite progress or hardware termination |
| Verdict | Exact source certificates, rule assumption and five inherited TRUST metadata entries | Owner: Probata proof-semantics maintainer; pending Yan-Ru freeze review59 |

Public controls use an explicit exit99 verifier stand-in and must remain
not_proven/tool_crash. Native controls compare only scalar effects of exact RF
excerpts and generated C, not actual MMIO/fences or a simulator run. Actual
healthy positive/wrong-value acceptance requires a separately reviewed clean
source/runtime/command admission by the coordinator, full ordinary/RTE/init/
property/dependency/smoke inventory and all native prover results. Unknown or
timeout is nonproof, not refutation; solver/resource/Failed errors do not qualify
as healthy negatives. A real parser gate is likewise coordinator-owned.

Semantics0.1 library bytes remain unchanged. This slice does not establish a
production current0.2, full typed interface, interference/history theorem or
whole-ticket acceptance.
